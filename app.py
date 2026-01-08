"""
Flask приложение для Render.com
Этот файл ОБЯЗАТЕЛЕН для работы на Render
"""

import os
import threading
import asyncio
from flask import Flask, jsonify
import logging
import sys

# Добавляем папку проекта в путь
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Создаем Flask приложение
app = Flask(__name__)

@app.route('/')
def home():
    """Главная страница"""
    return jsonify({
        "status": "running",
        "service": "Telegram Sketch to Render Bot",
        "message": "Бот активен и работает",
        "docs": "/health для проверки состояния"
    })

@app.route('/health')
def health():
    """Health check endpoint для Render"""
    return jsonify({
        "status": "healthy",
        "timestamp": os.times().user,
        "service": "telegram-bot"
    }), 200

@app.route('/wakeup')
def wakeup():
    """Эндпоинт для пробуждения сервиса"""
    logger.info("🔔 Сервис пробужден по запросу")
    return jsonify({"status": "awake"}), 200

def run_bot():
    """Запускает Telegram бота в отдельном потоке"""
    try:
        from bot import main as bot_main
        asyncio.run(bot_main())
    except ImportError as e:
        logger.error(f"❌ Ошибка импорта: {e}")
    except Exception as e:
        logger.error(f"❌ Ошибка бота: {e}")

if __name__ == "__main__":
    logger.info("🚀 Запуск Flask приложения...")
    
    # Запускаем бота в отдельном потоке
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    logger.info("🤖 Telegram бот запущен в фоновом режиме")
    
    # Запускаем Flask сервер
    port = int(os.environ.get("PORT", 10000))
    logger.info(f"🌐 Flask запущен на порту {port}")
    app.run(host='0.0.0.0', port=port, debug=False)