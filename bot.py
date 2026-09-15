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
import re

# ==================== [ الإعدادات الأساسية ] ====================

BOT_TOKEN = "8667829421:AAEq2fYIqOJ_HrsEHnX5ByqkARlCj0_VKFc"
OWNER_ID = 7670426534  # آيدي حسابك الأساسي (المالك)

# مفاتيح الفحص المخصص (Sightengine API)
SIGHTENGINE_USER = "69518445"                     
SIGHTENGINE_SECRET = "brsUxCqbzAbgKpm4SGwDEnGvL8Zp3ZTL"   

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
                    "anti_edit": True,
                    "anti_links": True,
                    "block_all_stickers": False,
                    "spam_limit": 3,
                    "spam_window": 5,
                    "banned_words": [],
                    "admins": [OWNER_ID],
                    "total_scanned": 0,
                    "total_deleted": 0,
                    "channels_monitored": [],
                    "custom_violations": [],
                    "panel_custom_text": "👑 لوحة الحماية الفولاذية القصوى:\n\n⚡ النظام يعمل بذكاء اصطناعي فائق الصرامة لفلترة كافة الوسائط والمحتوى.",
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
        "anti_edit": True,
        "anti_links": True,
        "block_all_stickers": False,
        "spam_limit": 3,
        "spam_window": 5,
        "banned_words": [],
        "admins": [OWNER_ID],
        "total_scanned": 0, 
        "total_deleted": 0,
        "channels_monitored": [],
        "custom_violations": [],
        "panel_custom_text": "👑 لوحة الحماية الفولاذية القصوى:\n\n⚡ النظام يعمل بذكاء اصطناعي فائق الصرامة لفلترة كافة الوسائط والمحتوى.",
        "welcome_file_id": "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?q=80&w=1000&auto=format&fit=crop",
        "welcome_type": "photo"
    }

def save_settings(settings):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=4)

config = load_settings()
print("[-] تم تشغيل نظام الحماية الفولاذي الأقصى بنجاح...")

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

# ==================== [ محرك الذكاء الاصطناعي فائق الحساسية ] ====================
def analyze_media_with_sightengine(file_bytes):
    try:
        image = Image.open(io.BytesIO(file_bytes))
        if image.mode in ("RGBA", "P"):
            image = image.convert("RGB")
        
        output_io = io.BytesIO()
        image.save(output_io, format="JPEG", quality=95)
        processed_bytes = output_io.getvalue()
        
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
            print(f"[AI Scan Result]: {res_data}")
            
            if res_data.get('status') == 'success':
                nudity = res_data.get('nudity', {})
                raw_sexual = nudity.get('raw', 0.0)          
                partial_sexual = nudity.get('partial', 0.0)  
                wad = res_data.get('wad', {})
                wad_score = wad.get('prob', 0.0)             

                if raw_sexual >= 0.05 or partial_sexual >= 0.08 or wad_score >= 0.10:
                    return True
    except Exception as e:
        print(f"[!] خطأ في فحص الذكاء الاصطناعي: {e}")
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

    if is_custom_violated or (message.sticker and config.get("block_all_stickers", False)):
        config["total_deleted"] += 1
        save_settings(config)
        try:
            bot.delete_message(chat_id, message_id)
            chat_name, chat_username, name, username, user_id = get_user_and_chat_info(message)
            alert_text = (
                f"🚫 <b>تم حذف محتوى مخالف (محظور كلياً / قائمة سوداء)</b>\n\n"
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
        if message.sticker:
            if analyze_media_with_sightengine(downloaded_file):
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
                punish_user_only(chat_id, user_id)
                alert_text = (
                    f"🚫 <b>تم رصد وحذف محتوى مخالف بواسطة الذكاء الاصطناعي</b>\n\n"
                    f"📌 <b>المكان:</b> {chat_name} ({chat_username})\n"
                    f"👤 <b>اسم الشخص:</b> {name} (<code>{user_id}</code>)\n"
                    f"🏷️ <b>نوع المحتوى:</b> {media_type_name}\n"
                    f"⚖️ <b>الإجراء:</b> تم سحب صلاحية النشر تلقائياً!"
                )
                notify_admins(alert_text)
            except:
                pass
    except Exception as e:
        print(f"[!] خطأ في المعالجة: {e}")

def check_message_text_and_spam(message):
    global config
    chat_id = message.chat.id
    message_id = message.message_id
    message_text = message.text or message.caption or ""

    if config["anti_links"] and message_text:
        link_pattern = re.compile(r'https?://(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&//=]*)')
        if link_pattern.search(message_text) or "t.me/" in message_text or "telegram.me/" in message_text:
            if not is_admin(message.from_user.id if message.from_user else 0):
                try:
                    bot.delete_message(chat_id, message_id)
                    chat_name, chat_username, name, username, user_id = get_user_and_chat_info(message)
                    punish_user_only(chat_id, user_id)
                    notify_admins(f"🚫 <b>تم حذف رابط إعلاني/خارجي</b>\n📌 المكان: {chat_name}\n👤 العضو: {name}")
                    return True
                except:
                    return True

    if message_text:
        for word in config["banned_words"]:
            if word.lower() in message_text.lower():
                try:
                    bot.delete_message(chat_id, message_id)
                    chat_name, chat_username, name, username, user_id = get_user_and_chat_info(message)
                    punish_user_only(chat_id, user_id)
                    notify_admins(f"🚫 <b>تم حذف كلمة محظورة</b>\n📌 المكان: {chat_name}\n💬 الكلمة: {word}")
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
                bot.delete_message(chat_id, message_id)
                chat_name, chat_username, name, username, user_id = get_user_and_chat_info(message)
                punish_user_only(chat_id, user_id)
                notify_admins(f"⚠️ <b>حظر سبام وسحب صلاحية</b>\n📌 المكان: {chat_name}\n👤 العضو: {name}")
                user_messages[sender_id] = []
                return True
            except:
                return True
    return False

# ==================== [ لوحة التحكم الفولاذية ] ====================
def generate_markup():
    kb = telebot.types.InlineKeyboardMarkup()
    status_text = "🟢 مفعلة" if config["protection_status"] else "🔴 معطلة"
    spam_text = "🟢 مفعل" if config["anti_spam"] else "🔴 معطل"
    edit_text = "🟢 مفعل" if config["anti_edit"] else "🔴 معطل"
    links_text = "🟢 مفعل" if config["anti_links"] else "🔴 معطل"
    stickers_text = "🔴 حظر الكل معطل" if not config["block_all_stickers"] else "🟢 حظر الملصقات مفعل"
    
    kb.row(telebot.types.InlineKeyboardButton(f"🛡️ حماية الذكاء الاصطناعي: {status_text}", callback_data="toggle_protection"))
    kb.row(
        telebot.types.InlineKeyboardButton(f"⚡ منع السبام: {spam_text}", callback_data="toggle_spam"),
        telebot.types.InlineKeyboardButton(f"✏️ منع التعديل: {edit_text}", callback_data="toggle_edit")
    )
    kb.row(
        telebot.types.InlineKeyboardButton(f"🔗 منع الروابط: {links_text}", callback_data="toggle_links"),
        telebot.types.InlineKeyboardButton(f"🎭 {stickers_text}", callback_data="toggle_stickers")
    )
    kb.row(telebot.types.InlineKeyboardButton(f"🔢 حد رسائل السبام: ({config['spam_limit']})", callback_data="set_spam_limit_prompt"))
    kb.row(
        telebot.types.InlineKeyboardButton("⚙️ تعديل نص اللوحة", callback_data="edit_panel_text"),
        telebot.types.InlineKeyboardButton("🖼️ تغيير صورة الترحيب", callback_data="info_welcome")
    )
    kb.row(
        telebot.types.InlineKeyboardButton("👤 رفع شخص بالآيدي", callback_data="unpunish_by_id_prompt"),
        telebot.types.InlineKeyboardButton("➕ إضافة كلمة محظورة", callback_data="add_word")
    )
    kb.row(
        telebot.types.InlineKeyboardButton(f"📋 إدارة الكلمات ({len(config['banned_words'])})", callback_data="manage_banned_words_panel"),
        telebot.types.InlineKeyboardButton(f"👑 المشرفين ({len(config['admins'])})", callback_data="manage_admins")
    )
    kb.row(telebot.types.InlineKeyboardButton(f"📊 إجمالي المحذوفات الصارمة: {config['total_deleted']}", callback_data="stats"))
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
        bot.reply_to(message, "❌ يرجى الرد بـ `/setwelcome` على صورة أو ملصق.")
        return
    reply = message.reply_to_message
    if reply.photo:
        config["welcome_file_id"] = reply.photo[-1].file_id
        config["welcome_type"] = "photo"
        save_settings(config)
        bot.reply_to(message, "✅ تم حفظ صورة الترحيب بنجاح!")
    elif reply.sticker:
        config["welcome_file_id"] = reply.sticker.file_id
        config["welcome_type"] = "sticker"
        save_settings(config)
        bot.reply_to(message, "✅ تم حفظ ملصق الترحيب بنجاح!")

@bot.message_handler(commands=['addviolation'])
def add_violation_cmd(message):
    if not is_admin(message.from_user.id):
        return
    if not message.reply_to_message:
        bot.reply_to(message, "❌ رد على الوسائط بـ `/addviolation` لإضافتها للقائمة السوداء.")
        return
    reply = message.reply_to_message
    f_id = None
    if reply.photo: f_id = reply.photo[-1].file_id
    elif reply.sticker: f_id = reply.sticker.file_id
    elif reply.animation: f_id = reply.animation.file_id
    elif reply.video: f_id = reply.video.file_id

    if f_id:
        if f_id not in config["custom_violations"]:
            config["custom_violations"].append(f_id)
            save_settings(config)
            bot.reply_to(message, "✅ تم إضافة المحتوى للقائمة السوداء بنجاح!")

@bot.message_handler(commands=['unpunish'])
def unpunish_cmd(message):
    if not is_admin(message.from_user.id):
        return
    try:
        args = message.text.split()
        target_user_id = int(args[1])
        target_chat_id = int(args[2]) if len(args) > 2 else message.chat.id
        if unpunish_user_in_chat(target_chat_id, target_user_id):
            bot.reply_to(message, f"✅ تم رفع الحظر عن العضو `{target_user_id}` بنجاح!")
    except:
        bot.reply_to(message, "❌ استخدام خاطئ للأمر.")

@bot.message_handler(commands=['addadmin'])
def add_admin_cmd(message):
    if message.from_user.id != OWNER_ID:
        return
    try:
        args = message.text.split()
        new_admin_id = int(args[1])
        if new_admin_id not in config["admins"]:
            config["admins"].append(new_admin_id)
            save_settings(config)
            bot.reply_to(message, f"✅ تم ترقية المشرف `{new_admin_id}` بنجاح.")
    except:
        pass

@bot.message_handler(commands=['deladmin'])
def del_admin_cmd(message):
    if message.from_user.id != OWNER_ID:
        return
    try:
        args = message.text.split()
        target_id = int(args[1])
        if target_id in config["admins"]:
            config["admins"].remove(target_id)
            save_settings(config)
            bot.reply_to(message, f"✅ تم إزالة المشرف `{target_id}` بنجاح.")
    except:
        pass

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
    elif call.data == "toggle_links":
        config["anti_links"] = not config["anti_links"]
        action_performed = True
    elif call.data == "toggle_stickers":
        config["block_all_stickers"] = not config.get("block_all_stickers", False)
        action_performed = True
    elif call.data == "set_spam_limit_prompt":
        sent_msg = bot.send_message(call.message.chat.id, "🔢 أرسل عدد رسائل السبام المسموحة:")
        bot.register_next_step_handler(sent_msg, process_spam_limit_input)
        bot.answer_callback_query(call.id)
        return
    elif call.data == "edit_panel_text":
        sent_msg = bot.send_message(call.message.chat.id, "✏️ أرسل النص الجديد للوحة التحكم:")
        bot.register_next_step_handler(sent_msg, process_panel_text_input)
        bot.answer_callback_query(call.id)
        return
    elif call.data == "info_welcome":
        bot.answer_callback_query(call.id, "أرسل الصورة أو الملصق في الخاص ثم رد عليه بـ /setwelcome", show_alert=True)
        return
    elif call.data == "unpunish_by_id_prompt":
        sent_msg = bot.send_message(call.message.chat.id, "👤 أرسل آيدي العضو لرفع الحظر عنه:")
        bot.register_next_step_handler(sent_msg, process_unpunish_id_input)
        bot.answer_callback_query(call.id)
        return
    elif call.data == "add_word":
        sent_msg = bot.send_message(call.message.chat.id, "✏️ أرسل الكلمة المراد حظرها:")
        bot.register_next_step_handler(sent_msg, process_banned_word_input)
        bot.answer_callback_query(call.id)
        return
    elif call.data == "manage_banned_words_panel":
        words = config.get("banned_words", [])
        kb = telebot.types.InlineKeyboardMarkup()
        kb.add(telebot.types.InlineKeyboardButton("➕ إضافة كلمة", callback_data="add_word"))
        for idx, word in enumerate(words):
            kb.add(telebot.types.InlineKeyboardButton(f"❌ حذف: {word}", callback_data=f"del_word_{idx}"))
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
    elif call.data == "manage_admins":
        bot.answer_callback_query(call.id, f"عدد المشرفين: {len(config['admins'])}", show_alert=True)
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
            bot.reply_to(message, f"✅ تم تحديث حد السبام إلى: `{limit}` رسائل.")
    except:
        pass

def process_panel_text_input(message):
    if not is_admin(message.from_user.id): return
    new_text = message.text.strip()
    if new_text:
        config["panel_custom_text"] = new_text
        save_settings(config)
        bot.reply_to(message, "✅ تم حفظ نص اللوحة بنجاح!")

def process_unpunish_id_input(message):
    if not is_admin(message.from_user.id): return
    try:
        target_user_id = int(message.text.strip())
        channels = config.get("channels_monitored", [])
        if not channels:
            channels = [message.chat.id]
        for ch_id in channels:
            unpunish_user_in_chat(ch_id, target_user_id)
        bot.reply_to(message, f"✅ تم رفع الحظر عن العضو `{target_user_id}` بنجاح!")
    except:
        bot.reply_to(message, "❌ الآيدي غير صحيح.")

def process_banned_word_input(message):
    if not is_admin(message.from_user.id): return
    word = message.text.strip()
    if word and word not in config["banned_words"]:
        config["banned_words"].append(word)
        save_settings(config)
        bot.reply_to(message, f"✅ تمت إضافة الكلمة '{word}' بنجاح.")

# ==================== [ الأحداث والمجموعات والقنوات ] ====================

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

# ==================== [ تشغيل البوت ] ====================
if __name__ == "__main__":
    while True:
        try:
            print("[*] البوت يعمل الآن بكامل طاقة الحماية والفلاتر الذكية...")
            bot.infinity_polling(interval=1, timeout=60, long_polling_timeout=60, skip_pending=True)
        except Exception as err:
            print(f"[!] خطأ بالاتصال: {err}")
            time.sleep(3)
