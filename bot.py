import os
import telebot
import google.generativeai as genai
from flask import Flask
from threading import Thread

# --- تنظیمات امنیتی (دریافت از Environment Variables) ---
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
MODEL_NAME = 'gemini-2.0-flash-lite'

# لیست ادمین‌های تایید شده
ADMIN_IDS = [7670169712, 1385881211, 8325728053]
warns_count = {}

# --- راه‌اندازی سرور Flask (برای زنده نگه داشتن در Render) ---
app = Flask('')

@app.route('/')
def home():
    return "Bot is Online! 🚀"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

# --- راه‌اندازی هوش مصنوعی و ربات ---
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel(MODEL_NAME)
bot = telebot.TeleBot(TELEGRAM_TOKEN)

def is_admin(user_id):
    return user_id in ADMIN_IDS

# --- دستورات مدیریتی ---

@bot.message_handler(commands=['ban'])
def ban(message):
    if is_admin(message.from_user.id) and message.reply_to_message:
        bot.ban_chat_member(message.chat.id, message.reply_to_message.from_user.id)
        bot.reply_to(message, "🚫 کاربر اخراج شد.")

@bot.message_handler(commands=['mute'])
def mute(message):
    if is_admin(message.from_user.id) and message.reply_to_message:
        bot.restrict_chat_member(message.chat.id, message.reply_to_message.from_user.id, can_send_messages=False)
        bot.reply_to(message, "🔇 کاربر بی‌صدا شد.")

@bot.message_handler(commands=['unmute'])
def unmute(message):
    if is_admin(message.from_user.id) and message.reply_to_message:
        bot.restrict_chat_member(message.chat.id, message.reply_to_message.from_user.id, 
                                 can_send_messages=True, can_send_media_messages=True, 
                                 can_send_other_messages=True, can_add_web_page_previews=True)
        bot.reply_to(message, "🔊 کاربر مجاز به ارسال پیام شد.")

@bot.message_handler(commands=['warn'])
def warn(message):
    if is_admin(message.from_user.id) and message.reply_to_message:
        uid = message.reply_to_message.from_user.id
        warns_count[uid] = warns_count.get(uid, 0) + 1
        if warns_count[uid] >= 3:
            bot.ban_chat_member(message.chat.id, uid)
            bot.reply_to(message, "🚫 کاربر به دلیل ۳ اخطار بن شد.")
            warns_count[uid] = 0
        else:
            bot.reply_to(message, f"⚠️ اخطار {warns_count[uid]}/3 ثبت شد.")

@bot.message_handler(commands=['pin'])
def pin(message):
    if is_admin(message.from_user.id) and message.reply_to_message:
        bot.pin_chat_message(message.chat.id, message.reply_to_message.message_id)
        bot.reply_to(message, "📌 پیام پین شد.")

# --- بخش هوش مصنوعی ---

@bot.message_handler(func=lambda message: True)
def ai_chat(message):
    bot_info = bot.get_me()
    is_private = message.chat.type == 'private'
    is_reply = message.reply_to_message and message.reply_to_message.from_user.id == bot_info.id
    is_mentioned = f"@{bot_info.username}" in (message.text or "")

    if is_private or is_reply or is_mentioned:
        bot.send_chat_action(message.chat.id, 'typing')
        try:
            clean_text = message.text.replace(f"@{bot_info.username}", "").strip()
            response = model.generate_content(clean_text)
            bot.reply_to(message, response.text, parse_mode='Markdown')
        except:
            bot.reply_to(message, "خطایی در پاسخگویی رخ داد. ⚠️")

# --- اجرای همزمان ---
if __name__ == "__main__":
    Thread(target=run_flask).start()
    print("✅ Bot is running...")
    bot.infinity_polling()
