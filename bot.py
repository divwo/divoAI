"""
Основной файл Telegram бота
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

# Импортируем настройки
from config.settings import (
    API_TOKEN, COMFY_URL, WORKFLOW_FILE,
    ROOMS, STYLES, LIGHTING, BASE_QUALITY, NEGATIVE_PROMPT,
    DEBUG, LOG_LEVEL
)

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
        
    async def upload_image(self, file_path, file_name):
        """Загружает изображение в ComfyUI"""
        data = aiohttp.FormData()
        data.add_field('image', 
                      open(file_path, 'rb'),
                      filename=file_name,
                      content_type='image/jpeg')
        
        url = f"http://{self.base_url}/upload/image"
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=data) as resp:
                return await resp.json()
    
    async def queue_prompt(self, workflow):
        """Отправляет промпт на генерацию"""
        url = f"http://{self.base_url}/prompt"
        data = {"prompt": workflow}
        
        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            async with session.post(url, json=data) as resp:
                if resp.status == 200:
                    return await resp.json()
                else:
                    logger.error(f"Ошибка ComfyUI: {resp.status}")
                    return None
    
    async def get_history(self, prompt_id):
        """Получает историю выполнения"""
        url = f"http://{self.base_url}/history/{prompt_id}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    return await resp.json()
                return None
    
    async def get_image(self, filename, subfolder, folder_type):
        """Скачивает изображение"""
        params = {
            "filename": filename,
            "subfolder": subfolder,
            "type": folder_type
        }
        url = f"http://{self.base_url}/view"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as resp:
                if resp.status == 200:
                    return await resp.read()
                return None
    
    async def wait_for_completion(self, prompt_id, max_attempts=100, delay=3):
        """Ожидает завершения генерации"""
        for attempt in range(max_attempts):
            history = await self.get_history(prompt_id)
            if history and prompt_id in history:
                logger.info(f"✅ Генерация завершена (попытка {attempt + 1})")
                return True
            await asyncio.sleep(delay)
        
        logger.error(f"❌ Таймаут генерации")
        return False
    
    async def check_connection(self):
        """Проверяет подключение к ComfyUI"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"http://{self.base_url}", timeout=10) as resp:
                    return resp.status == 200
        except:
            return False

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

@dp.message(Command("connect"))
async def cmd_connect(message: types.Message):
    """Проверка подключения к ComfyUI"""
    checking_msg = await message.answer("🔍 Проверяю подключение к нейросети...")
    
    is_connected = await comfy_client.check_connection()
    
    if is_connected:
        await checking_msg.edit_text(
            f"✅ *Подключение установлено!*\n\n"
            f"🌐 URL: `{COMFY_URL}`\n"
            f"📡 Статус: Доступен\n"
            f"🚀 Можно начинать генерацию!\n\n"
            f"Используй /start чтобы начать",
            parse_mode="Markdown"
        )
    else:
        await checking_msg.edit_text(
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

@dp.message(GenerationStates.waiting_for_room)
async def process_room(message: types.Message, state: FSMContext):
    """Обработка выбора комнаты"""
    if message.text not in ROOMS:
        await message.answer("Пожалуйста, выбери вариант из списка ниже:")
        return
    
    await state.update_data(room=message.text)
    await message.answer(
        f"✅ {message.text}\n\nТеперь выбери *стиль интерьера:*",
        parse_mode="Markdown",
        reply_markup=make_keyboard(list(STYLES.keys()))
    )
    await state.set_state(GenerationStates.waiting_for_style)

@dp.message(GenerationStates.waiting_for_style)
async def process_style(message: types.Message, state: FSMContext):
    """Обработка выбора стиля"""
    if message.text not in STYLES:
        await message.answer("Пожалуйста, выбери стиль из списка:")
        return
    
    await state.update_data(style=message.text)
    await message.answer(
        f"✅ {message.text}\n\nИ последнее: выбери *освещение и атмосферу:*",
        parse_mode="Markdown",
        reply_markup=make_keyboard(list(LIGHTING.keys()))
    )
    await state.set_state(GenerationStates.waiting_for_light)

@dp.message(GenerationStates.waiting_for_light)
async def process_light(message: types.Message, state: FSMContext):
    """Обработка выбора освещения и запуск генерации"""
    if message.text not in LIGHTING:
        await message.answer("Пожалуйста, выбери освещение из списка:")
        return
    
    await state.update_data(lighting=message.text)
    
    # Получаем все данные
    data = await state.get_data()
    
    # Формируем промпт
    room_eng = ROOMS[data['room']]
    style_eng = STYLES[data['style']]
    lighting_eng = LIGHTING[message.text]
    final_prompt = f"{room_eng}, {style_eng}, {lighting_eng}, {BASE_QUALITY}"
    
    # Информируем пользователя
    status_msg = await message.answer(
        f"🎨 *Генерация началась!*\n\n"
        f"🏠 Комната: {data['room']}\n"
        f"🎨 Стиль: {data['style']}\n"
        f"💡 Освещение: {message.text}\n\n"
        f"⏳ *Примерное время:* 1-3 минуты\n"
        f"Пожалуйста, подождите...",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove()
    )
    
    try:
        # 1. Загружаем изображение
        comfy_filename = os.path.basename(data['image_path'])
        await comfy_client.upload_image(data['image_path'], comfy_filename)
        
        # 2. Загружаем workflow
        with open(WORKFLOW_FILE, 'r', encoding='utf-8') as f:
            workflow = json.load(f)
        
        # 3. Вставляем значения
        for node_id, node in workflow.items():
            if node.get("class_type") == "LoadImage":
                node["inputs"]["image"] = comfy_filename
            
            if node.get("class_type") == "KSampler":
                node["inputs"]["seed"] = random.randint(1, 10**14)
            
            if node.get("class_type") == "CLIPTextEncode":
                text = node["inputs"].get("text", "")
                meta_title = node.get("_meta", {}).get("title", "").lower()
                if "positive" in meta_title or "prompt" in meta_title:
                    node["inputs"]["text"] = final_prompt
                elif "negative" in meta_title or "worst quality" in text.lower():
                    node["inputs"]["text"] = NEGATIVE_PROMPT
        
        # 4. Запускаем генерацию
        await status_msg.edit_text("🚀 Отправляю запрос в нейросеть...")
        
        result = await comfy_client.queue_prompt(workflow)
        if not result or 'prompt_id' not in result:
            await message.answer("❌ Ошибка: нейросеть не ответила")
            return
        
        prompt_id = result['prompt_id']
        
        # 5. Ожидаем завершения
        await status_msg.edit_text("⏳ Генерация в процессе...")
        
        completed = await comfy_client.wait_for_completion(prompt_id)
        if not completed:
            await message.answer("❌ Генерация заняла слишком много времени")
            return
        
        # 6. Получаем результат
        history = await comfy_client.get_history(prompt_id)
        if not history or prompt_id not in history:
            await message.answer("❌ Не удалось получить результат")
            return
        
        outputs = history[prompt_id]['outputs']
        
        # Ищем изображение
        image_data = None
        for node_output in outputs.values():
            if 'images' in node_output and node_output['images']:
                image_data = node_output['images'][0]
                break
        
        if not image_data:
            await message.answer("❌ Изображение не сгенерировано")
            return
        
        # 7. Скачиваем и отправляем
        img_bytes = await comfy_client.get_image(
            image_data['filename'],
            image_data.get('subfolder', ''),
            image_data.get('type', 'output')
        )
        
        if not img_bytes:
            await message.answer("❌ Ошибка загрузки изображения")
            return
        
        # Отправляем результат
        result_file = types.BufferedInputFile(img_bytes, filename="render.png")
        await message.answer_photo(
            result_file,
            caption=f"✅ *Готово!*\n\n"
                   f"🏠 Комната: {data['room']}\n"
                   f"🎨 Стиль: {data['style']}\n"
                   f"💡 Освещение: {message.text}\n\n"
                   f"✨ Хотите еще? Отправьте новое фото или /start",
            parse_mode="Markdown"
        )
        
        # Удаляем временный файл
        try:
            os.remove(data['image_path'])
        except:
            pass
        
        await state.clear()
        
    except Exception as e:
        logger.error(f"Ошибка генерации: {e}", exc_info=True)
        await message.answer(f"❌ Ошибка: {str(e)[:200]}")
        
        # Очистка при ошибке
        try:
            if 'image_path' in data:
                os.remove(data['image_path'])
        except:
            pass
        
        await state.clear()

# === ОБРАБОТЧИК ОШИБОК ===
@dp.message()
async def handle_other_messages(message: types.Message, state: FSMContext):
    """Обработка всех остальных сообщений"""
    current_state = await state.get_state()
    
    if not current_state and message.text:
        await message.answer(
            "👋 Отправьте фото эскиза комнаты чтобы начать.\n"
            "Или используйте /start для инструкций."
        )
    elif current_state == GenerationStates.waiting_for_photo and not message.photo:
        await message.answer("Пожалуйста, отправьте фото эскиза.")
    else:
        await message.answer("Пожалуйста, используйте кнопки или /cancel")

# === ЗАПУСК БОТА ===
async def main():
    """Основная функция запуска"""
    logger.info("=" * 50)
    logger.info("🤖 ЗАПУСК TELEGRAM БОТА")
    logger.info("=" * 50)
    logger.info(f"🔑 API Token: {'✅ Установлен' if API_TOKEN else '❌ Нет'}")
    logger.info(f"🌐 ComfyUI URL: {COMFY_URL}")
    logger.info(f"🔧 Debug mode: {DEBUG}")
    logger.info("=" * 50)
    
    # Проверка подключения при старте
    logger.info("🔍 Проверка подключения к ComfyUI...")
    if await comfy_client.check_connection():
        logger.info("✅ ComfyUI доступен")
    else:
        logger.warning("⚠️ ComfyUI недоступен. Проверьте Serveo.")
    
    try:
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"❌ Ошибка запуска бота: {e}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())