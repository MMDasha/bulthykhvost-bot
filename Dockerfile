# Базовый образ Python
FROM python:3.11-slim

# Установка системных зависимостей (для gTTS и ffmpeg при необходимости)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Установка рабочей директории
WORKDIR /app

# Копируем зависимости и код
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Указываем команду запуска
CMD ["python", "main.py"]
