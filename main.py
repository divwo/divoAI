"""
Основной файл для запуска бота на Render.com
Без Flask, только Telegram бот
"""

import os
import asyncio
import logging
import sys

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

async def run_bot():
    """Запускает Telegram бота"""
    try:
        # Импортируем бота
        from bot import main as bot_main
        logger.info("🤖 Запуск Telegram бота...")
        await bot_main()
    except ImportError as e:
        logger.error(f"❌ Ошибка импорта: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Ошибка бота: {e}")
        sys.exit(1)

def health_server():
    """Простой HTTP сервер для health checks"""
    from http.server import HTTPServer, BaseHTTPRequestHandler
    import threading
    
    class HealthHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path == '/health':
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(b'{"status": "healthy"}')
            else:
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(b'{"status": "running", "service": "Telegram Bot"}')
        
        def log_message(self, format, *args):
            logger.info(f"HTTP {self.address_string()} - {format % args}")
    
    port = int(os.environ.get('PORT', 10000))
    server = HTTPServer(('0.0.0.0', port), HealthHandler)
    
    def run_server():
        logger.info(f"🌐 Health server запущен на порту {port}")
        server.serve_forever()
    
    # Запускаем сервер в отдельном потоке
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    return server_thread

if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("🚀 ЗАПУСК TELEGRAM БОТА НА RENDER.COM")
    logger.info("=" * 60)
    
    # Проверяем переменные окружения
    required_vars = ['API_TOKEN']
    for var in required_vars:
        if not os.getenv(var):
            logger.warning(f"⚠️ Переменная {var} не установлена")
    
    # Запускаем health сервер
    health_server()
    
    # Запускаем бота
    try:
        asyncio.run(run_bot())
    except KeyboardInterrupt:
        logger.info("👋 Остановка бота...")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        sys.exit(1)