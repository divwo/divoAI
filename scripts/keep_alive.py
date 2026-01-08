"""
Скрипт для поддержания активности Render.com
Запускайте на любом ПК для пробуждения сервиса
"""

import requests
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# URL вашего приложения на Render
RENDER_URL = "https://your-app-name.onrender.com"

def ping_service():
    """Отправляет запрос к сервису"""
    try:
        response = requests.get(f"{RENDER_URL}/wakeup", timeout=10)
        if response.status_code == 200:
            logger.info(f"✅ Пинг успешен")
            return True
        else:
            logger.warning(f"⚠️ Ответ: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
        return False

if __name__ == "__main__":
    logger.info("🔄 Запуск keep-alive скрипта...")
    
    # Пингуем каждые 10 минут
    while True:
        ping_service()
        time.sleep(600)  # 10 минут