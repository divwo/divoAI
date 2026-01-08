"""
Flask приложение для Render.com
Исправленная версия без ошибки wakeup
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
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
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
        "description": "Преобразует эскизы в фотореалистичные рендеры",
        "endpoints": {
            "health": "/health",
            "wakeup": "/wakeup"
        },
        "docs": "https://github.com/divwo/divoAI"
    })

@app.route('/health')
def health():
    """Health check endpoint для Render"""
    try:
        # Базовая проверка здоровья
        return jsonify({
            "status": "healthy",
            "service": "telegram-bot",
            "timestamp": os.times().user
        }), 200
    except Exception as e:
        return jsonify({
            "status": "degraded",
            "error": str(e)[:100]
        }), 200

@app.route('/wakeup')
def wakeup():
    """Эндпоинт для пробуждения сервиса"""
    logger.info("🔔 Сервис пробужден по запросу")
    return jsonify({
        "status": "awake",
        "message": "Service is awake and running"
    }), 200

def run_bot_in_thread():
    """Запускает Telegram бота в отдельном потоке"""
    try:
        from bot import main as bot_main
        
        # Создаем новый event loop для этого потока
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        logger.info("🤖 Запуск Telegram бота в отдельном потоке...")
        loop.run_until_complete(bot_main())
        loop.close()
        
    except ImportError as e:
        logger.error(f"❌ Ошибка импорта: {e}")
    except Exception as e:
        logger.error(f"❌ Ошибка бота: {e}")

def start_bot():
    """Запускает бота в фоновом потоке"""
    bot_thread = threading.Thread(
        target=run_bot_in_thread,
        daemon=True,
        name="TelegramBotThread"
    )
    bot_thread.start()
    logger.info("✅ Telegram бот запущен в фоновом режиме")
    return bot_thread

if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("🚀 ЗАПУСК ПРИЛОЖЕНИЯ НА RENDER.COM")
    logger.info("=" * 60)
    
    # Проверяем обязательные переменные окружения
    required_vars = ['API_TOKEN', 'COMFY_URL']
    for var in required_vars:
        if not os.getenv(var):
            logger.warning(f"⚠️  Переменная окружения {var} не установлена")
    
    # Запускаем бота
    bot_thread = start_bot()
    
    # Запускаем Flask сервер
    port = int(os.environ.get("PORT", 10000))
    host = os.environ.get("HOST", "0.0.0.0")
    
    logger.info(f"🌐 Flask запускается на {host}:{port}")
    logger.info("📡 Сервис будет доступен по:")
    logger.info(f"   • https://divoai-1.onrender.com")
    logger.info(f"   • https://divoai-1.onrender.com/health")
    logger.info("=" * 60)
    
    # Запуск Flask в production режиме
    app.run(
        host=host,
        port=port,
        debug=False,
        threaded=True,
        use_reloader=False
    )