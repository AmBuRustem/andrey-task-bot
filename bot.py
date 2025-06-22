import logging
import json
import os
import time
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters, ConversationHandler
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Логирование
logging.basicConfig(level=logging.INFO)

# Загрузка .env
load_dotenv()
BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")
GOOGLE_CREDS_JSON = os.getenv("GOOGLE_CREDS_JSON")

# Клавиатура
keyboard = ReplyKeyboardMarkup(
    keyboard=[
        ["➕ Новая задача", "📋 Список задач"],
        ["✅ Выполнить задачу", "❓ Помощь"]
    ],
    resize_keyboard=True
)

# Авторизация в Google Sheets
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
google_creds = json.loads(GOOGLE_CREDS_JSON)
creds = ServiceAccountCredentials.from_json_keyfile_dict(google_creds, scope)
client = gspread.authorize(creds)
sheet = client.open("Andrey Tasks").sheet1

# Состояние диалога
ADDING_TASK = 1

# Команды
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Я — Андрей, твой бот для задач. Чем могу помочь?", reply_markup=keyboard)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Напиши /add чтобы добавить задачу.\nИли нажми кнопку ниже.")

# Сценарий добавления задачи
async def handle_add_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Хорошо! Напиши текст задачи:")
    return ADDING_TASK

async def handle_task_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    task = update.message.text
    user_id = update.message.from_user.id
    sheet.append_row([str(user_id), task, "FALSE"])
    await update.message.reply_text("Задача добавлена!", reply_markup=keyboard)
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Добавление задачи отменено.", reply_markup=keyboard)
    return ConversationHandler.END

# Запуск
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^➕ Новая задача$"), handle_add_button)],
        states={ADDING_TASK: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_task_input)]},
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(conv_handler)

    logging.info("Бот запущен...")
    app.run_polling()

if __name__ == "__main__":
    main()
