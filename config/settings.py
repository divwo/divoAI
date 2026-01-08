"""
Настройки приложения
Безопасно для Git
"""

import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# === ОБЯЗАТЕЛЬНЫЕ ПЕРЕМЕННЫЕ ===
def get_required_env(key):
    """Получает обязательную переменную окружения"""
    value = os.getenv(key)
    if not value:
        raise ValueError(f"❌ Не задана переменная окружения: {key}")
    return value

API_TOKEN = get_required_env('API_TOKEN')
COMFY_URL = get_required_env('COMFY_URL')

# === ОПЦИОНАЛЬНЫЕ ПЕРЕМЕННЫЕ ===
DEBUG = os.getenv('DEBUG', 'false').lower() == 'true'
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
PORT = int(os.getenv('PORT', 10000))

# === ПУТИ К ФАЙЛАМ ===
WORKFLOW_FILE = "sd35_sketch_to_renderV3.json"

# === НАСТРОЙКИ БОТА ===
# Комнаты (Русское -> Английское)
ROOMS = {
    "Гостиная": "Living room",
    "Кухня": "Kitchen",
    "Спальня": "Bedroom",
    "Ванная": "Bathroom",
    "Офис": "Home office",
    "Детская": "Kids room"
}

# Стили
STYLES = {
    "Modern (Современный)": "Modern style, Clean lines, minimalism, functional furniture, open space",
    "Minimalist (Минимализм)": "Minimalist style, Ultra-clean, monochromatic or neutral palette, clutter-free, emphasis on space and light",
    "Scandinavian (Скандинавский)": "Scandinavian style, Light wood, cozy textiles (wool, linen), functional design, plenty of natural light, hygge atmosphere",
    "Industrial (Лофт)": "Industrial loft style, Exposed brick, concrete floors, visible pipes and ducts, metal accents, high ceilings",
    "Mid-Century": "Mid-Century Modern style, Organic shapes, tapered legs, bold colors (olive, mustard, orange), wood tones",
    "Bohemian (Бохо)": "Bohemian style, Layered textures, eclectic mix of patterns, plants, global-inspired decor, warm colors",
    "Art Deco": "Art Deco style, Geometric patterns, luxurious materials (marble, brass, velvet), rich colors, symmetrical forms",
    "Japanese (Японский)": "Japanese style, Wabi-sabi, natural materials, low furniture, sliding doors, zen atmosphere, minimal decor",
    "Classic (Классика)": "Classic style, Timeless elegance, symmetry, rich textures, detailed moldings"
}

# Освещение
LIGHTING = {
    "☀️ Естественный свет": "Natural lighting, sun rays streaming through the window, golden hour, soft shadows, bright and airy",
    "🕯️ Уютное/Вечернее": "Cozy ambiance, warm lighting, atmospheric, moody lighting, hygge",
    "💡 Студийное/Чистое": "Bright and airy, studio lighting, clean light, interior design magazine photo",
    "🎬 Драматичное": "Dramatic lighting, cinematic lighting, volumetric light, high contrast"
}

# Промпты
BASE_QUALITY = "Photorealistic, hyperrealistic, 8K, detailed render, architectural visualization, Unreal Engine 5 render, Corona render, V-Ray, detailed textures, sense of depth, perfectly staged"
NEGATIVE_PROMPT = "(uworst quality, low quality, normal quality:1.5), (blurry, grainy, noisy:1.3), jpeg artifacts, signature, watermark, username, artist name, (CGI, 3D render, cartoon, anime, doll, plastic, fake:1.4), (bad anatomy, deformed, disfigured, malformed:1.3), cloned face, ugly, asymmetrical, distorted, gross proportions, text, error"

# === ВАЛИДАЦИЯ ===
if __name__ == "__main__":
    print("✅ Настройки загружены:")
    print(f"   API_TOKEN: {'✅' if API_TOKEN else '❌'}")
    print(f"   COMFY_URL: {COMFY_URL}")
    print(f"   DEBUG: {DEBUG}")
    print(f"   LOG_LEVEL: {LOG_LEVEL}")