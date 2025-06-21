# Основной файл бота
print('Бот Андрей запущен')

from flask import Flask
import threading
import os

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# === Flask для Render ===
app = Flask(__name__)

@app.route('/')
def index():
    return "Бот Андрей работает"

def run_flask():
    app.run(host="0.0.0.0", port=10000)

flask_thread = threading.Thread(target=run_flask)
flask_thread.start()

# === Telegram-бот ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Я — Андрей, твой бот для задач. Чем могу помочь?")

if __name__ == '__main__':
    token = os.getenv("TELEGRAM_TOKEN")
    app_telegram = ApplicationBuilder().token(token).build()
    app_telegram.add_handler(CommandHandler("start", start))
    app_telegram.run_polling()
