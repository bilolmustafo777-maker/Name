FROM python:3.12-slim

WORKDIR /app

# requirements.txt'ni nusxala
COPY requirements.txt .

# Paketlarni o'rnatish
RUN pip install --no-cache-dir -r requirements.txt

# Barcha kodni nusxala
COPY . .

# Botni ishga tushirish
CMD ["python", "bot.py"]
