import os
from dotenv import load_dotenv

load_dotenv()


BOT_TOKEN = "8251869795:AAHlTRYf2yXj7_OIFhTpOhr2ydijI7zGf_k"



if not BOT_TOKEN:
    print("❌ ОШИБКА: BOT_TOKEN не установлен")
    print("📝 Пожалуйста, установите токен в config.py")
    exit(1)

ADMIN_ID = os.getenv('ADMIN_ID', '1148740361')
DB_NAME = 'KiLoKSS69_bot'

print("✅ Конфигурация загружена успешно")