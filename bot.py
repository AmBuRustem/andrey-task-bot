import os
import json
import logging
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes,
    MessageHandler, filters, ConversationHandler
)
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from flask import Flask, request

# Логирование
logging.basicConfig(level=logging.INFO)

# Загрузка переменных окружения
load_dotenv()
BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
google_creds_str = os.getenv("GOOGLE_CREDS_JSON")

# Авторизация Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = json.loads(google_creds_str)
credentials = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(credentials)
sheet = client.open_by_key(SPREADSHEET_ID).sheet1

# Flask app для Webhook
flask_app = Flask(__name__)
WEBHOOK_URL = f"https://andrey-task-bot.onrender.com/webhook"

# Состояния
ADDING_TASK = 1

# Хендлер старта
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["➕ Новая задача"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Привет! Я бот Андрей. Нажми кнопку, чтобы добавить задачу.", reply_markup=reply_markup)

# Хендлер кнопки
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "➕ Новая задача":
        await update.message.reply_text("Напиши текст задачи:")
        return ADDING_TASK

# Хендлер ввода задачи
async def add_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    task_text = update.message.text
    user_id = update.effective_user.id
    sheet.append_row([str(user_id), task_text, "FALSE"])
    await update.message.reply_text("Задача добавлена!")
    return ConversationHandler.END

# Хендлер отмены
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Отменено.")
    return ConversationHandler.END

# Flask webhook endpoint
@flask_app.post("/webhook")
def webhook():
    data = request.get_json(force=True)
    flask_app.bot_app.update_queue.put_nowait(data)
    return "ok"

# Запуск
async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    flask_app.bot_app = app

    # Команды и кнопки
    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("➕ Новая задача"), handle_message)],
        states={ADDING_TASK: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_task)]},
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv_handler)

    # Удалим старые webhooks, если есть
    await app.bot.delete_webhook()
    await app.bot.set_webhook(url=WEBHOOK_URL)

    logging.info("Бот Андрей запущен по Webhook...")

# Точка входа
if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
