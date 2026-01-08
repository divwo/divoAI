"""
Скрипт для запуска Serveo на вашем ПК
"""

import subprocess
import time
import sys
import os

def check_comfyui():
    """Проверяет, запущен ли ComfyUI"""
    import requests
    try:
        response = requests.get("http://localhost:8188", timeout=5)
        return response.status_code == 200
    except:
        return False

def main():
    print("🚀 ЗАПУСК SERVEO ТУННЕЛЯ")
    print("=" * 50)
    
    # Проверка ComfyUI
    if not check_comfyui():
        print("❌ ComfyUI не запущен на localhost:8188")
        print("Запустите ComfyUI и повторите попытку")
        input("Нажмите Enter для выхода...")
        return
    
    print("✅ ComfyUI запущен")
    
    # Запрос имени для фиксированного URL
    print("\n🌐 Хотите фиксированный URL?")
    print("Пример: dimasketch.serveo.net")
    custom_name = input("Введите имя (или Enter для случайного): ").strip()
    
    # Формируем команду
    if custom_name:
        command = f"ssh -R {custom_name}:80:localhost:8188 serveo.net"
        print(f"\n🔗 Фиксированный URL будет:")
        print(f"   https://{custom_name}.serveo.net")
    else:
        command = "ssh -R 80:localhost:8188 serveo.net"
        print("\n🎲 Будет сгенерирован случайный URL")
    
    print(f"\n📋 Команда: {command}")
    print("\n⏳ Запускаю туннель... (может занять 10-20 сек)")
    print("=" * 50)
    
    try:
        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        url_found = False
        
        # Читаем вывод
        for line in iter(process.stdout.readline, ''):
            line = line.strip()
            if line:
                print(f"SERVEO: {line}")
                
                # Ищем URL
                if "serveousercontent.com" in line or "serveo.net" in line:
                    words = line.split()
                    for word in words:
                        if "serveousercontent.com" in word or "serveo.net" in word:
                            url = word.strip()
                            if url.startswith("https://"):
                                url = url[8:]
                            
                            print("\n" + "=" * 50)
                            print("🎉 URL ДЛЯ RENDER.COM:")
                            print("=" * 50)
                            print(f"\n🌐 Ваш URL: {url}")
                            print(f"\n📋 На Render.com установите:")
                            print(f"   COMFY_URL = {url}")
                            print("\n⚠️  Сохраните этот URL!")
                            print("=" * 50)
                            
                            # Сохраняем в файл
                            with open("serveo_url.txt", "w") as f:
                                f.write(url)
                            
                            url_found = True
        
        process.wait()
        
    except KeyboardInterrupt:
        print("\n\n👋 Остановка Serveo...")
        if 'process' in locals():
            process.terminate()
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    main()