# Основной файл бота
print('Бот Андрей запущен')
# Внизу файла bot.py
from flask import Flask
import threading

app = Flask(__name__)

@app.route('/')
def index():
    return "Бот Андрей работает"

def run_flask():
    app.run(host="0.0.0.0", port=10000)

# Запуск Flask в отдельном потоке
flask_thread = threading.Thread(target=run_flask)
flask_thread.start()
