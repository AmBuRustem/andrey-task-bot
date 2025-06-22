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
WEBHOOK_URL = os.getenv("RENDER_EXTERNAL_URL") + "/webhook"

# Авторизация Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = json.loads(google_creds_str)
credentials = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(credentials)
sheet = client.open_by_key(SPREADSHEET_ID).sheet1

# Flask app
flask_app = Flask(__name__)
application = None  # глобальная переменная для доступа к Telegram Application

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

# Webhook endpoint для Telegram
@flask_app.post("/webhook")
def webhook():
    data = request.get_json(force=True)
    if application:
        application.update_queue.put_nowait(data)
    return "ok"

# Запуск Flask и Telegram бота
async def start_bot():
    global application
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    # Хендлеры
    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("➕ Новая задача"), handle_message)],
        states={ADDING_TASK: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_task)]},
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    application.add_handler(CommandHandler("start", start))
    application.add_handler(conv_handler)

    await application.bot.delete_webhook()
    await application.bot.set_webhook(url=WEBHOOK_URL)

    logging.info("Бот Андрей запущен по Webhook...")

if __name__ == "__main__":
    import asyncio
    loop = asyncio.get_event_loop()
    loop.create_task(start_bot())
    flask_app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
