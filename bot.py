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

# مفاتيح الفحص المخصص (Sightengine API للرصد الدقيق للإباحية واستغلال الأطفال)
SIGHTENGINE_USER = "YOUR_API_USER"       # ضع هنا الـ API User الخاص بك في Sightengine
SIGHTENGINE_SECRET = "YOUR_API_SECRET"   # ضع هنا الـ API Secret الخاص بك في Sightengine

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
                    "panel_custom_text": "👑 أهلاً بك في لوحة التحكم الفولاذية:\n\n⚡ النظام يعمل بفحص Sightengine المتخصص لكشف المحتوى الإباحي.",
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
        "panel_custom_text": "👑 أهلاً بك في لوحة التحكم الفولاذية:\n\n⚡ النظام يعمل بفحص Sightengine المتخصص لكشف المحتوى الإباحي.",
        "welcome_file_id": "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?q=80&w=1000&auto=format&fit=crop",
        "welcome_type": "photo"
    }

def save_settings(settings):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=4)

config = load_settings()
print("[-] تم تشغيل النظام الأمني المتخصص (Sightengine) بنجاح...")

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

# ==================== [ فحص الوسائط عبر Sightengine الاحترافي ] ====================
def analyze_media_with_sightengine(file_bytes):
    try:
        # معالجة الملصقات (WebP) وتوحيدها إلى JPEG نقي
        image = Image.open(io.BytesIO(file_bytes))
        if image.mode in ("RGBA", "P"):
            image = image.convert("RGB")
        
        output_io = io.BytesIO()
        image.save(output_io, format="JPEG", quality=95)
        processed_bytes = output_io.getvalue()
        
        # إرسال الصورة إلى محرك الفحص المتخصص (يطلب كشف العري، المحتوى الجنسي، والأطفال)
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
                # فحص نسب العري أو المحتوى الجنسي الصريح أو المظهر غير اللائق
                nudity = res_data.get('nudity', {})
                raw_sexual = nudity.get('raw', 0.0)
                partial_sexual = nudity.get('partial', 0.0)
                
                # فحص محتوى الأطفال أو الاستغلال إن وجد في الـ wad models
                wad = res_data.get('wad', {})
                wad_score = wad.get('prob', 0.0)

                # إذا تجاوز أي مؤشر نسبة الأمان (أكثر من 50% يعتبر مخالفاً وصريحاً)
                if raw_sexual > 0.5 or partial_sexual > 0.7 or wad_score > 0.5:
                    return True
    except Exception as e:
        print(f"[!] خطأ في فحص Sightengine: {e}")
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
            # فحص عينة من الفيديو
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
                    f"🚫 <b>تم حذف محتوى إباحي عبر محرك الأمان المخصص</b>\n\n"
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
                bot.delete_message(chat_id, message_id)
                chat_name, chat_username, name, username, user_id = get_user_and_chat_info(message)
                punished_status = ""
                if punish_user_only(chat_id, user_id):
                    punished_status = f"\n⚖️ <b>الإجراء:</b> تم سحب صلاحية النشر لتجاوز حد السبام!"

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

# ==================== [ لوحة التحكم ] ====================
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
    kb.row(telebot.types.InlineKeyboardButton(f"📊 المحذوفات: {config['total_deleted']}", callback_data="stats"))
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

@bot.callback_query_handler(func=lambda call: is_admin(call.from_user.id))
def handle_callbacks(call):
    global config
    if call.data == "toggle_protection":
        config["protection_status"] = not config["protection_status"]
    elif call.data == "toggle_spam":
        config["anti_spam"] = not config["anti_spam"]
    elif call.data == "toggle_edit":
        config["anti_edit"] = not config["anti_edit"]
    elif call.data == "stats":
        bot.answer_callback_query(call.id, f"إجمالي المحذوفات: {config['total_deleted']}", show_alert=True)
        return

    save_settings(config)
    bot.answer_callback_query(call.id, "تم التحديث بنجاح!")
    try:
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=generate_markup())
    except:
        pass

# ==================== [ معالجة الرسائل ] ====================

@bot.channel_post_handler(content_types=['text', 'photo', 'sticker', 'video', 'animation'])
def on_new_post(message):
    global config
    if message.chat.id not in config["channels_monitored"]:
        config["channels_monitored"].append(message.chat.id)
        save_settings(config)
    if check_message_text_and_spam(message):
        return
    process_channel_message(message)

@bot.message_handler(content_types=['text', 'photo', 'sticker', 'video', 'animation'], func=lambda m: True)
def on_group_message(message):
    global config
    if message.chat.id not in config["channels_monitored"]:
        config["channels_monitored"].append(message.chat.id)
        save_settings(config)
    check_message_text_and_spam(message)

# ==================== [ تشغيل البوت ] ====================
if __name__ == "__main__":
    while True:
        try:
            print("[*] تم تشغيل البوت بنجاح عبر نظام Sightengine المخصص...")
            bot.infinity_polling(interval=1, timeout=60, long_polling_timeout=60, skip_pending=True)
        except Exception as err:
            print(f"[!] خطأ بالاتصال: {err}")
            time.sleep(3)
