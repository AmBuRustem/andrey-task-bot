import os
import json
import logging
import asyncio

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
    ConversationHandler,
)

import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Логгирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Подключение к Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
google_creds_str = os.environ["GOOGLE_CREDS_JSON"]
google_creds = json.loads(google_creds_str)
creds = ServiceAccountCredentials.from_json_keyfile_dict(google_creds, scope)
client = gspread.authorize(creds)

# Открытие таблицы
spreadsheet = client.open("Задачи Андрея")  # Название таблицы
worksheet = spreadsheet.sheet1              # Первая вкладка

# Состояние диалога
ADD_TASK = 1

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Я бот Андрей. Напиши /add чтобы добавить задачу или /list чтобы посмотреть список.")

# Команда /add
async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Введи задачу:")
    return ADD_TASK

async def save_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    task = update.message.text
    user = update.effective_user.first_name
    worksheet.append_row([user, task])
    await update.message.reply_text("Задача сохранена!")
    return ConversationHandler.END

# Команда /list
async def list_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    records = worksheet.get_all_records()
    if not records:
        await update.message.reply_text("Список задач пуст.")
        return

    message = "\n".join([f"{i+1}. {row['Задача']}" for i, row in enumerate(records)])
    await update.message.reply_text(f"Вот твои задачи:\n{message}")

# Отмена
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Добавление задачи отменено.")
    return ConversationHandler.END

# Запуск
def main():
    token = os.environ["TELEGRAM_TOKEN"]  # Токен Telegram должен быть в переменных окружения
    app = ApplicationBuilder().token(token).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("add", add)],
        states={ADD_TASK: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_task)]},
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("list", list_tasks))
    app.add_handler(conv_handler)

    app.run_polling()

if __name__ == "__main__":
    main()
