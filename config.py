import os

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0") or "0")
DB_PATH = os.getenv("DB_PATH", "taxi.db")

# Joyni band qilish uchun garov puli (so'm)
DEPOSIT_AMOUNT = 35_000

# Botda taklif qilinadigan shaharlar ro'yxati (kerak bo'lsa qo'shib/o'chirib turing)
CITIES = [
    "Toshkent", "Termiz", "Samarqand", "Buxoro", "Andijon",
    "Farg'ona", "Namangan", "Qarshi", "Nukus", "Urganch",
    "Guliston", "Jizzax", "Navoiy",
]

# Ruxsat etilgan mashina turlari
CAR_TYPES = ["Gentra", "Cobalt", "Onix", "Tracker", "Monza"]
