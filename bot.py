import os
import json
import logging
from flask import Flask
from dotenv import load_dotenv
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler

# Загрузка .env
load_dotenv()

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Flask сервер
app = Flask(__name__)

# Google таблица: парсим ключ из строки окружения
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
google_creds_str = os.getenv("GOOGLE_CREDS_JSON")

if not google_creds_str:
    raise Exception("GOOGLE_CREDS_JSON не найдена в переменных окружения")

# Парсим строку JSON в словарь
google_creds = json.loads(google_creds_str)

creds = ServiceAccountCredentials.from_json_keyfile_dict(google_creds, scope)
client = gspread.authorize(creds)
sheet = client.open("Andrey Tasks").sheet1

# Telegram bot
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# Словарь задач {user_id: [{"task": "text", "done": False}]}
tasks = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Я бот Андрей. Напиши /add чтобы добавить задачу.")

async def add_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    task_text = ' '.join(context.args)

    if not task_text:
        await update.message.reply_text("Пожалуйста, укажи текст задачи: /add Сделать отчёт")
        return

    tasks.setdefault(user_id, []).append({"task": task_text, "done": False})
    sheet.append_row([str(user_id), task_text, "FALSE"])
    await update.message.reply_text("Задача добавлена!")

async def list_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_tasks = tasks.get(user_id, [])

    if not user_tasks:
        await update.message.reply_text("У тебя пока нет задач.")
        return

    buttons = [
        [InlineKeyboardButton(f"{'✅' if t['done'] else '❌'} {t['task']}", callback_data=str(i))]
        for i, t in enumerate(user_tasks)
    ]
    reply_markup = InlineKeyboardMarkup(buttons)
    await update.message.reply_text("Вот твои задачи:", reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    index = int(query.data)
    user_tasks = tasks.get(user_id, [])

    if index < len(user_tasks):
        user_tasks[index]["done"] = not user_tasks[index]["done"]
        await query.edit_message_text(
            text="Задача обновлена. Используй /list чтобы посмотреть ещё раз."
        )

def main():
    app_bot = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CommandHandler("add", add_task))
    app_bot.add_handler(CommandHandler("list", list_tasks))
    app_bot.add_handler(CallbackQueryHandler(button_handler))

    app_bot.run_polling()

if __name__ == "__main__":
    main()
