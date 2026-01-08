"""
Основной файл Telegram бота
Исправленная версия для работы с Flask
"""

import asyncio
import json
import logging
import os
import random
import uuid
import aiohttp
import sys
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

# Добавляем папку проекта в путь
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from config.settings import (
        API_TOKEN, COMFY_URL, WORKFLOW_FILE,
        ROOMS, STYLES, LIGHTING, BASE_QUALITY, NEGATIVE_PROMPT,
        DEBUG, LOG_LEVEL
    )
except ImportError as e:
    # Запасные значения если config не загрузился
    logging.error(f"Ошибка загрузки настроек: {e}")
    API_TOKEN = os.getenv('API_TOKEN', '')
    COMFY_URL = os.getenv('COMFY_URL', '')
    WORKFLOW_FILE = "sd35_sketch_to_renderV3.json"
    
    # Базовые настройки
    ROOMS = {"Гостиная": "Living room"}
    STYLES = {"Modern": "Modern style"}
    LIGHTING = {"Естественный свет": "Natural lighting"}
    BASE_QUALITY = "Photorealistic"
    NEGATIVE_PROMPT = "low quality"
    DEBUG = False
    LOG_LEVEL = "INFO"

# === НАСТРОЙКА ЛОГИРОВАНИЯ ===
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# === КЛАСС ДЛЯ РАБОТЫ С COMFYUI ===
class ComfyUIClient:
    def __init__(self, base_url):
        self.base_url = base_url
        self.timeout = aiohttp.ClientTimeout(total=300)
        
    async def check_connection(self):
        """Проверяет подключение к ComfyUI"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"http://{self.base_url}", timeout=10) as resp:
                    return resp.status == 200
        except Exception as e:
            logger.error(f"Ошибка подключения к ComfyUI: {e}")
            return False
    
    # ... остальные методы класса ComfyUIClient ...

# === ИНИЦИАЛИЗАЦИЯ ===
comfy_client = ComfyUIClient(COMFY_URL)
bot = Bot(token=API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# === СОСТОЯНИЯ FSM ===
class GenerationStates(StatesGroup):
    waiting_for_photo = State()
    waiting_for_room = State()
    waiting_for_style = State()
    waiting_for_light = State()

# === ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ===
def make_keyboard(items):
    """Создает клавиатуру из списка"""
    keyboard = []
    for i in range(0, len(items), 2):
        row = items[i:i+2]
        keyboard.append([KeyboardButton(text=item) for item in row])
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

# === КОМАНДЫ БОТА ===
@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    """Начало работы с ботом"""
    await message.answer(
        "👋 *Привет! Я превращаю эскизы в фотореалистичные рендеры.*\n\n"
        "📋 *Как это работает:*\n"
        "1. Отправь мне фото эскиза комнаты\n"
        "2. Выбери тип комнаты\n"
        "3. Выбери стиль интерьера\n"
        "4. Выбери освещение\n"
        "5. Получи результат!\n\n"
        "⏱️ *Время генерации:* 1-3 минуты\n"
        "🚀 *Начнем? Отправь фото эскиза!*",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(GenerationStates.waiting_for_photo)

@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    """Помощь по командам"""
    help_text = """
📚 *Доступные команды:*

/start - Начать создание рендера
/status - Статус бота и подключений
/connect - Проверить подключение к нейросети
/cancel - Отменить текущую операцию
/help - Эта справка

🔧 *Если что-то не работает:*
1. Проверьте подключение командой /connect
2. Убедитесь что Serveo запущен на вашем ПК
3. Проверьте что ComfyUI работает

🆘 *Поддержка:* Свяжитесь с разработчиком
    """
    await message.answer(help_text, parse_mode="Markdown")

@dp.message(Command("status"))
async def cmd_status(message: types.Message):
    """Статус бота"""
    try:
        # Проверяем подключение к ComfyUI
        is_connected = await comfy_client.check_connection()
        
        status_text = f"""
🤖 *Статус бота:*
✅ Активен и работает
🌐 ComfyUI: {'✅ Доступен' if is_connected else '❌ Недоступен'}
📡 Serveo URL: `{COMFY_URL}`
🔧 Готов к работе!

💡 *Совет:* Используй /start чтобы начать
        """
        await message.answer(status_text, parse_mode="Markdown")
    except Exception as e:
        await message.answer(f"❌ Ошибка получения статуса: {str(e)[:100]}")

@dp.message(Command("connect"))
async def cmd_connect(message: types.Message):
    """Проверка подключения к ComfyUI"""
    try:
        await message.answer("🔍 Проверяю подключение к нейросети...")
        
        is_connected = await comfy_client.check_connection()
        
        if is_connected:
            await message.answer(
                f"✅ *Подключение установлено!*\n\n"
                f"🌐 URL: `{COMFY_URL}`\n"
                f"📡 Статус: Доступен\n"
                f"🚀 Можно начинать генерацию!\n\n"
                f"Используй /start чтобы начать",
                parse_mode="Markdown"
            )
        else:
            await message.answer(
                f"❌ *Не удалось подключиться*\n\n"
                f"🌐 URL: `{COMFY_URL}`\n"
                f"💡 *Что проверить:*\n"
                f"1. Запущен ли Serveo на вашем ПК\n"
                f"2. Работает ли ComfyUI (localhost:8188)\n"
                f"3. Правильный ли URL\n\n"
                f"🔄 *Решение:*\n"
                f"- Перезапустите Serveo на ПК\n"
                f"- Обновите COMFY_URL на Render.com",
                parse_mode="Markdown"
            )
    except Exception as e:
        await message.answer(f"❌ Ошибка проверки: {str(e)[:100]}")

@dp.message(Command("cancel"))
async def cmd_cancel(message: types.Message, state: FSMContext):
    """Отмена текущей операции"""
    current_state = await state.get_state()
    if current_state:
        await state.clear()
        await message.answer(
            "✅ Операция отменена.\nИспользуй /start чтобы начать заново.",
            reply_markup=ReplyKeyboardRemove()
        )
    else:
        await message.answer("Нет активных операций для отмены.")

# === ОСНОВНЫЕ ОБРАБОТЧИКИ ===
@dp.message(GenerationStates.waiting_for_photo, F.photo)
async def process_photo(message: types.Message, state: FSMContext):
    """Обработка фотографии"""
    try:
        # Скачиваем фото
        photo = message.photo[-1]
        file = await bot.get_file(photo.file_id)
        filename = f"user_{message.from_user.id}_{uuid.uuid4()}.jpg"
        
        await bot.download_file(file.file_path, filename)
        
        await state.update_data(image_path=filename)
        await message.answer(
            "✅ Фото получено!\n\nТеперь выбери *тип комнаты:*",
            parse_mode="Markdown",
            reply_markup=make_keyboard(list(ROOMS.keys()))
        )
        await state.set_state(GenerationStates.waiting_for_room)
        
    except Exception as e:
        logger.error(f"Ошибка обработки фото: {e}")
        await message.answer("❌ Ошибка загрузки фото. Попробуйте еще раз.")

# ... остальные обработчики (process_room, process_style, process_light) ...

async def main():
    """Основная функция запуска"""
    logger.info("=" * 50)
    logger.info("🤖 ЗАПУСК TELEGRAM БОТА")
    logger.info("=" * 50)
    
    if not API_TOKEN:
        logger.error("❌ API_TOKEN не установлен!")
        return
    
    if not COMFY_URL:
        logger.warning("⚠️ COMFY_URL не установлен")
    
    logger.info(f"🔑 API Token: {'✅ Установлен' if API_TOKEN else '❌ Нет'}")
    logger.info(f"🌐 ComfyUI URL: {COMFY_URL}")
    logger.info("=" * 50)
    
    try:
        # Проверка подключения
        logger.info("🔍 Проверка подключения к ComfyUI...")
        is_connected = await comfy_client.check_connection()
        
        if is_connected:
            logger.info("✅ ComfyUI доступен")
        else:
            logger.warning("⚠️ ComfyUI недоступен. Проверьте Serveo.")
        
        # Запуск бота
        logger.info("🚀 Запуск бота...")
        await dp.start_polling(bot)
        
    except Exception as e:
        logger.error(f"❌ Ошибка запуска бота: {e}")
    finally:
        await bot.session.close()

# Точка входа для запуска из app.py
if __name__ == "__main__":
    # Для прямого запуска (без Flask)
    asyncio.run(main())