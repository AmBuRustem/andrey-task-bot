import os
import logging
import threading
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import gspread
import json
from oauth2client.service_account import ServiceAccountCredentials

# Логирование
logging.basicConfig(level=logging.INFO)

# Подключение к Google Таблице
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
google_creds = json.loads(os.environ["GOOGLE_CREDS_JSON"])
creds = ServiceAccountCredentials.from_json_keyfile_dict(google_creds, scope)
client = gspread.authorize(creds)
spreadsheet_id = os.environ["SPREADSHEET_ID"]
sheet = client.open_by_key(spreadsheet_id).sheet1

# Telegram токен
TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]

# Команды
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Я — Андрей, твой бот для задач. Чем могу помочь?")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "/new Задача — создать\n"
        "/list — список задач\n"
        "/done 1 — завершить задачу 1\n"
        "/help — помощь"
    )

async def new_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    task_text = " ".join(context.args)
    if not task_text:
        await update.message.reply_text("Пожалуйста, напиши задачу после команды, например: /new Купить молоко")
        return
    sheet.append_row([task_text, "🕒 В процессе"])
    await update.message.reply_text(f"✅ Задача добавлена: {task_text}")

async def list_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rows = sheet.get_all_values()
    if not rows:
        await update.message.reply_text("Задач пока нет.")
        return
    msg = ""
    for i, row in enumerate(rows, start=1):
        msg += f"{i}. {row[0]} — {row[1]}\n"
    await update.message.reply_text(msg)

async def done_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Укажи номер задачи, которую нужно завершить. Например: /done 2")
        return
    try:
        idx = int(context.args[0])
        sheet.update_cell(idx, 2, "✅ Готово")
        await update.message.reply_text(f"Задача №{idx} отмечена как выполненная.")
    except:
        await update.message.reply_text("Произошла ошибка. Убедись, что ввёл правильный номер.")

# Flask — для Render (он требует порт)
app = Flask(__name__)

@app.route('/')
def index():
    return "Бот Андрей работает"

def run_flask():
    app.run(host="0.0.0.0", port=10000)

# Запуск Flask в отдельном потоке
flask_thread = threading.Thread(target=run_flask)
flask_thread.start()

# Запуск Telegram-бота
async def main():
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("new", new_task))
    application.add_handler(CommandHandler("list", list_tasks))
    application.add_handler(CommandHandler("done", done_task))

    await application.run_polling()

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
