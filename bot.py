#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import telebot
import requests
import base64
import json
import cv2
import numpy as np
import os
import sys
import time
from threading import Thread
from PIL import Image
import io

# ==================== [ الإعدادات الأساسية ] ====================

BOT_TOKEN = "8667829421:AAEq2fYIqOJ_HrsEHnX5ByqkARlCj0_VKFc"
OWNER_ID = 7670426534  # آيدي حسابك الأساسي (المالك)

# مفتاح الـ api للذكاء الاصطناعي
GEMINI_API_KEY = "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"  

SETTINGS_FILE = "channel_ultra_settings.json"

# =======================================================

if not BOT_TOKEN or "ضع_توكن" in BOT_TOKEN:
    print("[!] خطأ: يرجى وضع توكن تليجرام الصحيح أولاً.")
    sys.exit(1)

bot = telebot.TeleBot(BOT_TOKEN)

user_messages = {}

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r") as f:
                data = json.load(f)
                default_keys = {
                    "protection_status": True,
                    "anti_spam": True,
                    "anti_edit": False,
                    "spam_limit": 3,
                    "spam_window": 5,
                    "banned_words": [],
                    "admins": [OWNER_ID],
                    "total_scanned": 0,
                    "total_deleted": 0,
                    "channels_monitored": [],
                    "custom_violations": [],
                    "panel_custom_text": "👑 أهلاً بك في لوحة التحكم الفولاذية:\n\n⚡ النظام يعمل بأقصى درجات التركيز لحذف المحتوى الإباحي بدقة مطلقة.",
                    "welcome_file_id": "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?q=80&w=1000&auto=format&fit=crop",
                    "welcome_type": "photo" # photo أو sticker
                }
                for k, v in default_keys.items():
                    if k not in data:
                        data[k] = v
                return data
        except:
            pass
    return {
        "protection_status": True, 
        "anti_spam": True,
        "anti_edit": False,
        "spam_limit": 3,
        "spam_window": 5,
        "banned_words": [],
        "admins": [OWNER_ID],
        "total_scanned": 0, 
        "total_deleted": 0,
        "channels_monitored": [],
        "custom_violations": [],
        "panel_custom_text": "👑 أهلاً بك في لوحة التحكم الفولاذية:\n\n⚡ النظام يعمل بأقصى درجات التركيز لحذف المحتوى الإباحي بدقة مطلقة.",
        "welcome_file_id": "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?q=80&w=1000&auto=format&fit=crop",
        "welcome_type": "photo"
    }

def save_settings(settings):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=4)

config = load_settings()
print("[-] تم تشغيل النظام الفولاذي الشامل بنجاح...")

def is_admin(user_id):
    return user_id == OWNER_ID or user_id in config.get("admins", [])

def notify_admins(text_alert):
    all_targets = [OWNER_ID] + config.get("admins", [])
    for admin_id in set(all_targets):
        try:
            bot.send_message(admin_id, text_alert, parse_mode="HTML")
        except:
            pass

def get_user_and_chat_info(message):
    chat = message.chat
    chat_name = chat.title if chat.title else "قناة/مجموعة بدون اسم"
    chat_username = f"@{chat.username}" if chat.username else f"ID: {chat.id}"
    
    user = message.from_user
    if user:
        name = f"{user.first_name}" + (f" {user.last_name}" if user.last_name else "")
        username = f"@{user.username}" if user.username else "لا يوجد معرف"
        user_id = user.id
    else:
        name = "غير معروف (منشور قناة مباشر)"
        username = "غير معروف"
        user_id = chat.id

    return chat_name, chat_username, name, username, user_id

def punish_user_only(chat_id, user_id):
    try:
        if user_id > 0:
            bot.promote_chat_member(
                chat_id=chat_id,
                user_id=user_id,
                can_post_messages=False,
                can_edit_messages=False,
                can_delete_messages=False,
                can_invite_users=True,
                can_restrict_members=False,
                can_promote_members=False
            )
            return True
    except Exception as e:
        print(f"[!] خطأ سحب الصلاحية: {e}")
    return False

def unpunish_user_in_chat(chat_id, user_id):
    try:
        if user_id > 0:
            bot.promote_chat_member(
                chat_id=chat_id,
                user_id=user_id,
                can_post_messages=True,
                can_edit_messages=True,
                can_delete_messages=False,
                can_invite_users=True,
                can_restrict_members=False,
                can_promote_members=False
            )
            return True
    except Exception as e:
        print(f"[!] خطأ رفع الصلاحية: {e}")
    return False

# ==================== [ فحص الذكاء الاصطناعي (تركيز مكثف على الإباحية) ] ====================
def normalize_image(file_bytes):
    try:
        img = Image.open(io.BytesIO(file_bytes))
        if img.mode != 'RGB':
            img = img.convert('RGB')
        img = img.resize((768, 768), Image.Resampling.LANCZOS)
        output = io.BytesIO()
        img.save(output, format="JPEG", quality=95)
        return output.getvalue()
    except:
        return file_bytes

def local_backup_scan(file_bytes):
    try:
        nparr = np.frombuffer(file_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            return False
        height, width, _ = img.shape
        total_pixels = width * height
        img_ycrcb = cv2.cvtColor(img, cv2.COLOR_BGR2YCrCb)
        mask = cv2.inRange(img_ycrcb, np.array([0, 133, 77]), np.array([255, 177, 127]))
        explicit_pixels = cv2.countNonZero(mask)
        ratio = (explicit_pixels / total_pixels) * 100
        if ratio > 40.0:
            return True
    except:
        pass
    return False

def analyze_media(file_bytes, mime_type="image/jpeg"):
    try:
        encoded_string = base64.b64encode(file_bytes).decode("utf-8")
        api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
        
        prompt = (
            "You are an extreme, highly focused AI content moderation expert designed specifically to detect pornography and adult explicit content. "
            "Analyze this media image meticulously. Does it contain ANY form of pornography, explicit sexual acts, full or partial nudity, "
            "suggestive adult poses, lingerie intended for adult content, or explicit sexual organs? "
            "If it contains ANY explicit or hardcore pornographic material, you MUST reply with 'true'. "
            "If the image is an ordinary photo, selfie, landscape, cartoon, meme, or completely safe family-friendly image, reply 'false'. "
            "Focus strongly and strictly on purging pornographic content without compromise."
        )
        payload = {
            "contents": [{
                "parts": [
                    {"text": prompt},
                    {"inlineData": {"mimeType": mime_type, "data": encoded_string}}
                ]
            }]
        }
        response = requests.post(api_url, json=payload, headers={"Content-Type": "application/json"}, timeout=20)
        if response.status_code == 200:
            res_data = response.json()
            raw_text = res_data["candidates"][0]["content"]["parts"][0]["text"].strip().lower()
            if "true" in raw_text:
                return True
    except:
        return local_backup_scan(file_bytes)
        
    return local_backup_scan(file_bytes)

def process_channel_message(message):
    global config
    if not config["protection_status"]:
        return

    chat_id = message.chat.id
    message_id = message.message_id
    file_id = None
    mime_type = "image/jpeg"
    media_type_name = "صورة/وسائط"
    
    if message.photo:
        file_id = message.photo[-1].file_id
        media_type_name = "🖼️ صورة"
    elif message.sticker:
        file_id = message.sticker.file_id
        mime_type = "image/webp"
        media_type_name = "🎭 ملصق"
    elif message.animation:
        file_id = message.animation.file_id
        media_type_name = "🎬 متحركة GIF"
    elif message.video:
        file_id = message.video.file_id
        media_type_name = "🎥 فيديو"

    if not file_id:
        return

    is_custom_violated = file_id in config.get("custom_violations", [])

    config["total_scanned"] += 1
    save_settings(config)

    try:
        file_info = bot.get_file(file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        processed_file = normalize_image(downloaded_file)
        
        if is_custom_violated or analyze_media(processed_file, mime_type=mime_type):
            config["total_deleted"] += 1
            save_settings(config)
            
            chat_name, chat_username, name, username, user_id = get_user_and_chat_info(message)
            
            try:
                bot.delete_message(chat_id, message_id)
                alert_text = (
                    f"🚫 <b>تم حذف محتوى إباحي (بدون سحب صلاحية النشر)</b>\n\n"
                    f"📌 <b>المكان:</b> {chat_name} ({chat_username})\n"
                    f"👤 <b>اسم الشخص:</b> {name} (<code>{user_id}</code>)\n"
                    f"🏷️ <b>نوع المحتوى:</b> {media_type_name}\n"
                    f"📊 <b>إجمالي المحذوفات:</b> {config['total_deleted']}"
                )
                notify_admins(alert_text)
            except:
                pass
    except:
        pass

def check_message_text_and_spam(message):
    global config
    chat_id = message.chat.id
    message_id = message.message_id
    message_text = message.text or message.caption or ""

    if message_text:
        for word in config["banned_words"]:
            if word.lower() in message_text.lower():
                try:
                    bot.delete_message(chat_id, message_id)
                    chat_name, chat_username, name, username, user_id = get_user_and_chat_info(message)
                    
                    punished_status = ""
                    if punish_user_only(chat_id, user_id):
                        punished_status = "\n⚖️ <b>الإجراء:</b> تم سحب صلاحية النشر بسبب كلمة محظورة!"

                    alert_text = (
                        f"🚫 <b>تم حذف رسالة تحتوي على كلمة محظورة</b>\n\n"
                        f"📌 <b>المكان:</b> {chat_name} ({chat_username})\n"
                        f"👤 <b>اسم الشخص:</b> {name} (<code>{user_id}</code>)\n"
                        f"💬 <b>الكلمة:</b> {word}"
                        f"{punished_status}"
                    )
                    notify_admins(alert_text)
                    return True
                except:
                    return True

    if config["anti_spam"]:
        sender_id = message.from_user.id if message.from_user else chat_id
        current_time = time.time()

        if sender_id not in user_messages:
            user_messages[sender_id] = []

        user_messages[sender_id].append(current_time)
        user_messages[sender_id] = [t for t in user_messages[sender_id] if current_time - t < config["spam_window"]]

        if len(user_messages[sender_id]) > config["spam_limit"]:
            try:
                chat_name, chat_username, name, username, user_id = get_user_and_chat_info(message)
                punished_status = ""
                if punish_user_only(chat_id, user_id):
                    punished_status = "\n⚖️ <b>الإجراء:</b> تم سحب صلاحية النشر بسبب السبام!"

                alert_text = (
                    f"⚠️ <b>رصد حالة سبام من عضو</b>\n\n"
                    f"📌 <b>المكان:</b> {chat_name} ({chat_username})\n"
                    f"👤 <b>اسم الشخص:</b> {name} (<code>{user_id}</code>)"
                    f"{punished_status}"
                )
                notify_admins(alert_text)
                user_messages[sender_id] = []
                return True
            except:
                return True
                
    return False

# ==================== [ لوحة التحكم المتقدمة ] ====================
def generate_markup():
    kb = telebot.types.InlineKeyboardMarkup()
    
    status_text = "🟢 مفعلة" if config["protection_status"] else "🔴 معطلة"
    spam_text = "🟢 مفعل" if config["anti_spam"] else "🔴 معطل"
    edit_text = "🟢 مفعل" if config["anti_edit"] else "🔴 معطل"
    
    kb.row(
        telebot.types.InlineKeyboardButton(f"🛡️ حماية الوسائط: {status_text} 🛡️", callback_data="toggle_protection")
    )
    kb.row(
        telebot.types.InlineKeyboardButton(f"⚡ منع السبام: {spam_text} ⚡", callback_data="toggle_spam"),
        telebot.types.InlineKeyboardButton(f"✏️ منع التعديل: {edit_text} ✏️", callback_data="toggle_edit")
    )
    kb.row(
        telebot.types.InlineKeyboardButton("⚙️ تعديل نص اللوحة", callback_data="edit_panel_text"),
        telebot.types.InlineKeyboardButton("🖼️ تغيير صورة/ملصق الترحيب", callback_data="info_welcome")
    )
    kb.row(
        telebot.types.InlineKeyboardButton("👤 رفع شخص بالآيدي", callback_data="unpunish_by_id_prompt"),
        telebot.types.InlineKeyboardButton("➕ إضافة كلمة", callback_data="add_word")
    )
    kb.row(
        telebot.types.InlineKeyboardButton(f"📋 إدارة الكلمات ({len(config['banned_words'])})", callback_data="manage_banned_words_panel"),
        telebot.types.InlineKeyboardButton(f"👑 إدارة المشرفين ({len(config['admins'])})", callback_data="manage_admins")
    )
    kb.row(
        telebot.types.InlineKeyboardButton(f"📊 المحذوفات: {config['total_deleted']}", callback_data="stats")
    )
    return kb

@bot.message_handler(commands=['start', 'panel'])
def open_panel(message):
    if not is_admin(message.from_user.id):
        return
    
    caption_text = config.get("panel_custom_text", "👑 لوحة التحكم:")
    w_id = config.get("welcome_file_id", "")
    w_type = config.get("welcome_type", "photo")
    
    try:
        if w_type == "sticker":
            bot.send_sticker(message.chat.id, sticker=w_id)
            bot.send_message(message.chat.id, caption_text, parse_mode="HTML", reply_markup=generate_markup())
        else:
            bot.send_photo(message.chat.id, photo=w_id, caption=caption_text, parse_mode="HTML", reply_markup=generate_markup())
    except:
        bot.send_message(message.chat.id, caption_text, parse_mode="HTML", reply_markup=generate_markup())

@bot.message_handler(commands=['setwelcome'])
def set_welcome_cmd(message):
    if not is_admin(message.from_user.id):
        return
    if not message.reply_to_message:
        bot.reply_to(message, "❌ يرجى الرد بـ `/setwelcome` مباشرة على **الصورة** أو **الملصق** الذي أرسلته للبوت لتعتمده كرسالة ترحيب رسمية.")
        return
    
    reply = message.reply_to_message
    if reply.photo:
        config["welcome_file_id"] = reply.photo[-1].file_id
        config["welcome_type"] = "photo"
        save_settings(config)
        bot.reply_to(message, "✅ تم حفظ الصورة الجديدة كرسالة ترحيب رسمية للبوت بنجاح!")
    elif reply.sticker:
        config["welcome_file_id"] = reply.sticker.file_id
        config["welcome_type"] = "sticker"
        save_settings(config)
        bot.reply_to(message, "✅ تم حفظ الملصق المميز كرسالة ترحيب رسمية للبوت بنجاح!")
    else:
        bot.reply_to(message, "❌ يرجى الرد على صورة أو ملصق فقط.")

@bot.message_handler(commands=['addviolation'])
def add_violation_cmd(message):
    if not is_admin(message.from_user.id):
        return
    if not message.reply_to_message:
        bot.reply_to(message, "❌ أرسل المحتوى (صورة/فيديو/ملصق) للبوت مباشرة، ثم رد عليه بالأمر `/addviolation` لتحضيره ومنعه نهائياً.")
        return
    
    reply = message.reply_to_message
    f_id = None
    if reply.photo: f_id = reply.photo[-1].file_id
    elif reply.sticker: f_id = reply.sticker.file_id
    elif reply.animation: f_id = reply.animation.file_id
    elif reply.video: f_id = reply.video.file_id

    if not f_id:
        bot.reply_to(message, "❌ نوع الوسائط غير مدعوم للتحضير.")
        return

    if "custom_violations" not in config:
        config["custom_violations"] = []

    if f_id not in config["custom_violations"]:
        config["custom_violations"].append(f_id)
        save_settings(config)
        bot.reply_to(message, "✅ تم تحضير وحفظ هذا المحتوى في القائمة السوداء بنجاح! سيتم حذفه فوراً لو تم نشره.")
    else:
        bot.reply_to(message, "⚠️ هذا المحتوى محضور ومضاف مسبقاً.")

@bot.message_handler(commands=['unpunish'])
def unpunish_cmd(message):
    if not is_admin(message.from_user.id):
        return
    try:
        args = message.text.split()
        if len(args) < 2:
            bot.reply_to(message, "❌ الاستخدام الصحيح:\n`/unpunish آيدي_الشخص آيدي_القناة`\nأو يمكنك استخدام زر لوحة التحكم.")
            return
        target_user_id = int(args[1])
        target_chat_id = int(args[2]) if len(args) > 2 else (config["channels_monitored"][0] if config["channels_monitored"] else message.chat.id)
        
        if unpunish_user_in_chat(target_chat_id, target_user_id):
            bot.reply_to(message, f"✅ تم رفع وتقييد حظر النشر عن العضو `{target_user_id}` في القناة بنجاح!")
        else:
            bot.reply_to(message, "❌ حدث خطأ أثناء محاولة رفع العضو. تأكد من آيدي القناة وصلاحيات البوت.")
    except Exception as e:
        bot.reply_to(message, f"❌ حدث خطأ: {e}")

@bot.message_handler(commands=['addadmin'])
def add_admin_cmd(message):
    if message.from_user.id != OWNER_ID:
        bot.reply_to(message, "❌ هذا الأمر مخصص للمالك الأساسي فقط.")
        return
    try:
        args = message.text.split()
        if len(args) < 2:
            if message.reply_to_message and message.reply_to_message.from_user:
                replied_id = message.reply_to_message.from_user.id
                if replied_id not in config["admins"]:
                    config["admins"].append(replied_id)
                    save_settings(config)
                    bot.reply_to(message, f"✅ تم ترقية المشرف `{replied_id}` بنجاح عبر الرد.")
                    return
            bot.reply_to(message, "❌ الاستخدام: `/addadmin الآيدي` أو الرد على رسالة الشخص بـ `/addadmin`")
            return
        new_admin_id = int(args[1])
        if new_admin_id not in config["admins"]:
            config["admins"].append(new_admin_id)
            save_settings(config)
            bot.reply_to(message, f"✅ تم ترقية المشرف `{new_admin_id}` بنجاح.")
        else:
            bot.reply_to(message, "⚠️ المشرف موجود مسبقاً.")
    except Exception as e:
        bot.reply_to(message, f"❌ حدث خطأ: {e}")

@bot.message_handler(commands=['deladmin'])
def del_admin_cmd(message):
    if message.from_user.id != OWNER_ID:
        return
    try:
        args = message.text.split()
        target_id = int(args[1])
        if target_id == OWNER_ID:
            bot.reply_to(message, "❌ لا يمكن حذف المالك الأساسي.")
            return
        if target_id in config["admins"]:
            config["admins"].remove(target_id)
            save_settings(config)
            bot.reply_to(message, f"✅ تم إزالة المشرف `{target_id}` بنجاح.")
        else:
            bot.reply_to(message, "⚠️ المستخدم ليس مشرفاً.")
    except:
        bot.reply_to(message, "❌ الاستخدام: `/deladmin الآيدي`")

@bot.callback_query_handler(func=lambda call: is_admin(call.from_user.id))
def handle_callbacks(call):
    global config
    action_performed = False

    if call.data == "toggle_protection":
        config["protection_status"] = not config["protection_status"]
        action_performed = True
    elif call.data == "toggle_spam":
        config["anti_spam"] = not config["anti_spam"]
        action_performed = True
    elif call.data == "toggle_edit":
        config["anti_edit"] = not config["anti_edit"]
        action_performed = True
    elif call.data == "edit_panel_text":
        sent_msg = bot.send_message(call.message.chat.id, "✏️ أرسل الآن النص الجديد الذي تريد ظهوره في لوحة التحكم:")
        bot.register_next_step_handler(sent_msg, process_panel_text_input)
        bot.answer_callback_query(call.id)
        return
    elif call.data == "info_welcome":
        bot.answer_callback_query(call.id, "أرسل الصورة أو الملصق مباشرة للبوت في الخاص، ثم رد عليه بالأمر: /setwelcome", show_alert=True)
        return
    elif call.data == "unpunish_by_id_prompt":
        sent_msg = bot.send_message(call.message.chat.id, "👤 أرسل الآن آيدي الشخص المراد رفع وإعادة صلاحية النشر له في القناة (مثال: `123456789`):", parse_mode="MARKDOWN")
        bot.register_next_step_handler(sent_msg, process_unpunish_id_input)
        bot.answer_callback_query(call.id)
        return
    elif call.data == "add_word":
        sent_msg = bot.send_message(call.message.chat.id, "✏️ أرسل الكلمة أو الجملة المراد حظرها:")
        bot.register_next_step_handler(sent_msg, process_banned_word_input)
        bot.answer_callback_query(call.id)
        return
    elif call.data == "manage_banned_words_panel":
        words = config.get("banned_words", [])
        kb = telebot.types.InlineKeyboardMarkup()
        kb.add(telebot.types.InlineKeyboardButton("➕ إضافة كلمة", callback_data="add_word"))
        for idx, word in enumerate(words):
            kb.add(telebot.types.InlineKeyboardButton(f"❌ حذف: {word}", callback_data=f"del_word_{idx}"))
        if words:
            kb.add(telebot.types.InlineKeyboardButton("🗑️ مسح الكل", callback_data="clear_words"))
        kb.add(telebot.types.InlineKeyboardButton("🔙 رجوع", callback_data="back_to_panel"))
        
        try:
            bot.edit_message_caption(call.message.chat.id, call.message.message_id, caption=f"⚙️ إدارة الكلمات المحظورة:\nالعدد: `{len(words)}`", parse_mode="MARKDOWN", reply_markup=kb)
        except:
            bot.edit_message_text(f"⚙️ إدارة الكلمات المحظورة:\nالعدد: `{len(words)}`", call.message.chat.id, call.message.message_id, parse_mode="MARKDOWN", reply_markup=kb)
        bot.answer_callback_query(call.id)
        return
    elif call.data.startswith("del_word_"):
        try:
            idx = int(call.data.split("_")[2])
            words = config.get("banned_words", [])
            if 0 <= idx < len(words):
                removed = words.pop(idx)
                config["banned_words"] = words
                save_settings(config)
                bot.answer_callback_query(call.id, f"تم حذف: {removed}", show_alert=True)
        except:
            pass
        call.data = "manage_banned_words_panel"
        handle_callbacks(call)
        return
    elif call.data == "clear_words":
        config["banned_words"] = []
        save_settings(config)
        bot.answer_callback_query(call.id, "تم مسح جميع الكلمات!", show_alert=True)
        call.data = "manage_banned_words_panel"
        handle_callbacks(call)
        return
    elif call.data == "manage_admins":
        bot.answer_callback_query(call.id, f"عدد المشرفين: {len(config['admins'])}\nأضف مشرفاً عبر: /addadmin الآيدي", show_alert=True)
        return
    elif call.data == "back_to_panel":
        caption_text = config.get("panel_custom_text", "👑 لوحة التحكم:")
        try:
            bot.edit_message_caption(call.message.chat.id, call.message.message_id, caption=caption_text, parse_mode="HTML", reply_markup=generate_markup())
        except:
            bot.edit_message_text(caption_text, call.message.chat.id, call.message.message_id, parse_mode="HTML", reply_markup=generate_markup())
        return
    elif call.data == "stats":
        bot.answer_callback_query(call.id, f"إجمالي المحذوفات: {config['total_deleted']}", show_alert=True)
        return

    if action_performed:
        save_settings(config)
        bot.answer_callback_query(call.id, "تم التحديث بنجاح!")
        try:
            bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=generate_markup())
        except: 
            pass

def process_panel_text_input(message):
    if not is_admin(message.from_user.id): return
    new_text = message.text.strip()
    if new_text:
        config["panel_custom_text"] = new_text
        save_settings(config)
        bot.reply_to(message, "✅ تم حفظ نص لوحة التحكم الجديد بنجاح!")

def process_unpunish_id_input(message):
    if not is_admin(message.from_user.id): return
    try:
        target_user_id = int(message.text.strip())
        channels = config.get("channels_monitored", [])
        if not channels:
            bot.reply_to(message, "❌ لا توجد قناة مسجلة في النظام بعد. قم بنشر رسالة من القناة أولاً.")
            return
        
        success_count = 0
        for ch_id in channels:
            if unpunish_user_in_chat(ch_id, target_user_id):
                success_count += 1
                
        if success_count > 0:
            bot.reply_to(message, f"✅ تم رفع وإعادة صلاحية النشر للعضو `{target_user_id}` في جميع القنوات المرتبطة بنجاح!")
        else:
            bot.reply_to(message, "❌ فشل رفع العضو. تأكد أن آيدي الشخص صحيح وأن البوت مشرف بصلاحيات كاملة.")
    except Exception as e:
        bot.reply_to(message, "❌ الآيدي المدخل غير صالح. يرجى إرسال رقم الآيدي صحيحاً.")

def process_banned_word_input(message):
    if not is_admin(message.from_user.id): return
    word = message.text.strip()
    if word and word not in config["banned_words"]:
        config["banned_words"].append(word)
        save_settings(config)
        bot.reply_to(message, f"✅ تمت إضافة الكلمة المحظورة '{word}' بنجاح.")

# ==================== [ الأحداث والمجموعات ] ====================

@bot.channel_post_handler(content_types=['text', 'photo', 'sticker', 'video', 'animation'])
def on_new_post(message):
    global config
    if message.chat.id not in config["channels_monitored"]:
        config["channels_monitored"].append(message.chat.id)
        save_settings(config)
    if check_message_text_and_spam(message):
        return
    process_channel_message(message)

@bot.edited_channel_post_handler(content_types=['text', 'photo', 'sticker', 'video', 'animation'])
def on_edited_post(message):
    global config
    if config["anti_edit"]:
        try:
            chat_name, chat_username, name, username, user_id = get_user_and_chat_info(message)
            bot.delete_message(message.chat.id, message.message_id)
            punish_user_only(message.chat.id, user_id)
            return
        except:
            pass
    process_channel_message(message)

@bot.message_handler(content_types=['text', 'photo', 'sticker', 'video', 'animation'], func=lambda m: True)
def on_group_message(message):
    global config
    if message.chat.id not in config["channels_monitored"]:
        config["channels_monitored"].append(message.chat.id)
        save_settings(config)
    check_message_text_and_spam(message)

@bot.edited_message_handler(content_types=['text', 'photo', 'sticker', 'video', 'animation'], func=lambda m: True)
def on_edited_group_message(message):
    global config
    if config["anti_edit"]:
        try:
            bot.delete_message(message.chat.id, message.message_id)
            punish_user_only(message.chat.id, message.from_user.id if message.from_user else message.chat.id)
        except:
            pass

# ==================== [ تشغيل البوت المستقر ] ====================
if __name__ == "__main__":
    while True:
        try:
            print("[*] تم تشغيل البوت واستقرار الاتصال تماماً...")
            bot.infinity_polling(interval=1, timeout=60, long_polling_timeout=60, skip_pending=True)
        except Exception as err:
            print(f"[!] خطأ بالاتصال: {err}")
            time.sleep(3)
