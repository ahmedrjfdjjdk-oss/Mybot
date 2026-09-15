#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import telebot
import requests
import json
import os
import sys
import time
from PIL import Image
import io

# ==================== [ الإعدادات الأساسية ] ====================

BOT_TOKEN = "8667829421:AAEq2fYIqOJ_HrsEHnX5ByqkARlCj0_VKFc"
OWNER_ID = 7670426534  # آيدي حسابك الأساسي (المالك)

# مفاتيح الفحص المخصص (Sightengine API)
SIGHTENGINE_USER = "YOUR_API_USER"       # ضع هنا الـ API User الخاص بك
SIGHTENGINE_SECRET = "YOUR_API_SECRET"   # ضع هنا الـ API Secret الخاص بك

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
                    "panel_custom_text": "👑 أهلاً بك في لوحة التحكم الفولاذية:\n\n⚡ النظام يعمل بفلترة صارمة وقوية جداً للوسائط.",
                    "welcome_file_id": "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?q=80&w=1000&auto=format&fit=crop",
                    "welcome_type": "photo"
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
        "panel_custom_text": "👑 أهلاً بك في لوحة التحكم الفولاذية:\n\n⚡ النظام يعمل بفلترة صارمة وقوية جداً للوسائط.",
        "welcome_file_id": "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?q=80&w=1000&auto=format&fit=crop",
        "welcome_type": "photo"
    }

def save_settings(settings):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=4)

config = load_settings()
print("[-] تم تشغيل البوت بنجاح وبأقصى درجات الحماية والصرامة...")

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
    except:
        pass
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
    except:
        pass
    return False

# ==================== [ الفحص الصارم والدقيق عبر Sightengine ] ====================
def analyze_media_with_sightengine(file_bytes):
    try:
        image = Image.open(io.BytesIO(file_bytes))
        if image.mode in ("RGBA", "P"):
            image = image.convert("RGB")
        
        output_io = io.BytesIO()
        image.save(output_io, format="JPEG", quality=95)
        processed_bytes = output_io.getvalue()
        
        # تفعيل نماذج العري المتقدم والاستغلال (nudity-2.0, wad, scam)
        params = {
            'models': 'nudity-2.0,wad,scam',
            'api_user': SIGHTENGINE_USER,
            'api_secret': SIGHTENGINE_SECRET
        }
        files = {
            'media': ('image.jpg', processed_bytes, 'image/jpeg')
        }
        
        response = requests.post('https://api.sightengine.com/1.0/check.json', files=files, data=params, timeout=20)
        if response.status_code == 200:
            res_data = response.json()
            if res_data.get('status') == 'success':
                nudity = res_data.get('nudity', {})
                raw_sexual = nudity.get('raw', 0.0)          # العري الصريح
                partial_sexual = nudity.get('partial', 0.0)  # العري الجزئي أو المثير
                
                wad = res_data.get('wad', {})
                wad_score = wad.get('prob', 0.0)             # محتوى استغلال الأطفال أو المخالفات الخطيرة

                # شروط صارمة جداً تمنع الأخطاء وتحذف الإباحية بدقة تامة
                if raw_sexual >= 0.65 or partial_sexual >= 0.75 or wad_score >= 0.60:
                    return True
    except Exception as e:
        print(f"[!] خطأ في الفحص الصارم: {e}")
    return False

def process_channel_message(message):
    global config
    if not config["protection_status"]:
        return

    chat_id = message.chat.id
    message_id = message.message_id
    file_id = None
    media_type_name = "صورة/وسائط"
    
    if message.photo:
        file_id = message.photo[-1].file_id
        media_type_name = "🖼️ صورة"
    elif message.sticker:
        file_id = message.sticker.file_id
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

    # القائمة السوداء اليدوية
    if is_custom_violated:
        config["total_deleted"] += 1
        save_settings(config)
        try:
            bot.delete_message(chat_id, message_id)
            chat_name, chat_username, name, username, user_id = get_user_and_chat_info(message)
            alert_text = (
                f"🚫 <b>تم حذف محتوى مخالف (من القائمة السوداء)</b>\n\n"
                f"📌 <b>المكان:</b> {chat_name} ({chat_username})\n"
                f"👤 <b>اسم الشخص:</b> {name} (<code>{user_id}</code>)\n"
                f"🏷️ <b>نوع المحتوى:</b> {media_type_name}"
            )
            notify_admins(alert_text)
        except:
            pass
        return

    try:
        file_info = bot.get_file(file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        is_violating = False
        if message.video or message.animation:
            if analyze_media_with_sightengine(downloaded_file[:1000000]):
                is_violating = True
        else:
            if analyze_media_with_sightengine(downloaded_file):
                is_violating = True

        if is_violating:
            config["total_deleted"] += 1
            save_settings(config)
            
            chat_name, chat_username, name, username, user_id = get_user_and_chat_info(message)
            try:
                bot.delete_message(chat_id, message_id)
                alert_text = (
                    f"🚫 <b>تم حذف محتوى إباحي مؤكد وصارم</b>\n\n"
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

    # 1. الكلمات المحظورة
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

    # 2. منع السبام
    if config["anti_spam"]:
        sender_id = message.from_user.id if message.from_user else chat_id
        current_time = time.time()

        if sender_id not in user_messages:
            user_messages[sender_id] = []

        user_messages[sender_id].append(current_time)
        user_messages[sender_id] = [t for t in user_messages[sender_id] if current_time - t < config["spam_window"]]

        if len(user_messages[sender_id]) > config["spam_limit"]:
            try:
                bot.delete_message(chat_id, message_id)
                chat_name, chat_username, name, username, user_id = get_user_and_chat_info(message)
                punished_status = ""
                if punish_user_only(chat_id, user_id):
                    punished_status = f"\n⚖️ <b>الإجراء:</b> تم سحب صلاحية النشر لتجاوز حد السبام ({config['spam_limit']} رسائل)!"

                alert_text = (
                    f"⚠️ <b>رصد وتجاوز حد السبام وحذف الرسالة</b>\n\n"
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

# ==================== [ لوحة التحكم الكاملة ] ====================
def generate_markup():
    kb = telebot.types.InlineKeyboardMarkup()
    status_text = "🟢 مفعلة" if config["protection_status"] else "🔴 معطلة"
    spam_text = "🟢 مفعل" if config["anti_spam"] else "🔴 معطل"
    edit_text = "🟢 مفعل" if config["anti_edit"] else "🔴 معطل"
    
    kb.row(telebot.types.InlineKeyboardButton(f"🛡️ حماية الوسائط: {status_text} 🛡️", callback_data="toggle_protection"))
    kb.row(
        telebot.types.InlineKeyboardButton(f"⚡ منع السبام: {spam_text} ⚡", callback_data="toggle_spam"),
        telebot.types.InlineKeyboardButton(f"✏️ منع التعديل: {edit_text} ✏️", callback_data="toggle_edit")
    )
    kb.row(telebot.types.InlineKeyboardButton(f"🔢 حد رسائل السبام: ({config['spam_limit']})", callback_data="set_spam_limit_prompt"))
    kb.row(
        telebot.types.InlineKeyboardButton("⚙️ تعديل نص اللوحة", callback_data="edit_panel_text"),
        telebot.types.InlineKeyboardButton("🖼️ تغيير صورة الترحيب", callback_data="info_welcome")
    )
    kb.row(
        telebot.types.InlineKeyboardButton("👤 رفع شخص بالآيدي", callback_data="unpunish_by_id_prompt"),
        telebot.types.InlineKeyboardButton("➕ إضافة كلمة", callback_data="add_word")
    )
    kb.row(
        telebot.types.InlineKeyboardButton(f"📋 إدارة الكلمات ({len(config['banned_words'])})", callback_data="manage_banned_words_panel"),
        telebot.types.InlineKeyboardButton(f"👑 إدارة المشرفين ({len(config['admins'])})", callback_data="manage_admins")
    )
    kb.row(telebot.types.InlineKeyboardButton(f"📊 المحذوفات الصارمة: {config['total_deleted']}", callback_data="stats"))
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
        bot.reply_to(message, "❌ يرجى الرد بـ `/setwelcome` مباشرة على **الصورة** أو **الملصق** الذي أرسلتَه للبوت لتعتمده كرسالة ترحيب رسمية.")
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
        bot.reply_to(message, "❌ أرسل المحتوى للبوت مباشرة، ثم رد عليه بالأمر `/addviolation` لتحضيره ومنعه نهائياً.")
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
        bot.reply_to(message, "✅ تم تحضير وحفظ هذا المحتوى في القائمة السوداء بنجاح!")
    else:
        bot.reply_to(message, "⚠️ هذا المحتوى محضور ومضاف مسبقاً.")

@bot.message_handler(commands=['unpunish'])
def unpunish_cmd(message):
    if not is_admin(message.from_user.id):
        return
    try:
        args = message.text.split()
        if len(args) < 2:
            bot.reply_to(message, "❌ الاستخدام الصحيح:\n`/unpunish آيدي_الشخص آيدي_القناة`")
            return
        target_user_id = int(args[1])
        target_chat_id = int(args[2]) if len(args) > 2 else (config["channels_monitored"][0] if config["channels_monitored"] else message.chat.id)
        
        if unpunish_user_in_chat(target_chat_id, target_user_id):
            bot.reply_to(message, f"✅ تم رفع وتقييد حظر النشر عن العضو `{target_user_id}` بنجاح!")
        else:
            bot.reply_to(message, "❌ حدث خطأ أثناء محاولة رفع العضو.")
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
                    bot.reply_to(message, f"✅ تم ترقية المشرف `{replied_id}` بنجاح.")
                    return
            bot.reply_to(message, "❌ الاستخدام: `/addadmin الآيدي`")
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
    elif call.data == "set_spam_limit_prompt":
        sent_msg = bot.send_message(call.message.chat.id, "🔢 أرسل الآن عدد الرسائل المسموحة للسبام قبل سحب الصلاحية:", parse_mode="MARKDOWN")
        bot.register_next_step_handler(sent_msg, process_spam_limit_input)
        bot.answer_callback_query(call.id)
        return
    elif call.data == "edit_panel_text":
        sent_msg = bot.send_message(call.message.chat.id, "✏️ أرسل الآن النص الجديد الذي تريد ظهوره في لوحة التحكم:")
        bot.register_next_step_handler(sent_msg, process_panel_text_input)
        bot.answer_callback_query(call.id)
        return
    elif call.data == "info_welcome":
        bot.answer_callback_query(call.id, "أرسل الصورة أو الملصق مباشرة للبوت في الخاص، ثم رد عليه بالأمر: /setwelcome", show_alert=True)
        return
    elif call.data == "unpunish_by_id_prompt":
        sent_msg = bot.send_message(call.message.chat.id, "👤 أرسل الآن آيدي الشخص المراد رفع وإعادة صلاحية النشر له:", parse_mode="MARKDOWN")
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
        bot.answer_callback_query(call.id, f"إجمالي المحذوفات الصارمة: {config['total_deleted']}", show_alert=True)
        return

    if action_performed:
        save_settings(config)
        bot.answer_callback_query(call.id, "تم التحديث بنجاح!")
        try:
            bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=generate_markup())
        except: 
            pass

def process_spam_limit_input(message):
    if not is_admin(message.from_user.id): return
    try:
        limit = int(message.text.strip())
        if limit > 0:
            config["spam_limit"] = limit
            save_settings(config)
            bot.reply_to(message, f"✅ تم تحديث حد رسائل السبام بنجاح إلى: `{limit}` رسائل.")
        else:
            bot.reply_to(message, "❌ يرجى إرسال رقم أكبر من الصفر.")
    except:
        bot.reply_to(message, "❌ يرجى إرسال رقم صحيح.")

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
            bot.reply_to(message, "❌ لا توجد قناة مسجلة في النظام بعد.")
            return
        
        success_count = 0
        for ch_id in channels:
            if unpunish_user_in_chat(ch_id, target_user_id):
                success_count += 1
                
        if success_count > 0:
            bot.reply_to(message, f"✅ تم رفع وإعادة صلاحية النشر للعضو `{target_user_id}` بنجاح!")
        else:
            bot.reply_to(message, "❌ فشل رفع العضو.")
    except:
        bot.reply_to(message, "❌ الآيدي المدخل غير صالح.")

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
            print("[*] تم تشغيل البوت بنجاح تام وبأعلى معايير الحماية والصرامة...")
            bot.infinity_polling(interval=1, timeout=60, long_polling_timeout=60, skip_pending=True)
        except Exception as err:
            print(f"[!] خطأ بالاتصال: {err}")
            time.sleep(3)
