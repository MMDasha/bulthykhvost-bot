import os
import logging
import asyncio
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message
from openai import OpenAI

# === Настройка логирования ===
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
logging.info("=== BULTHYKHOVOST BOT START v3 ===")

# === Загрузка переменных окружения ===
load_dotenv(override=False)  # .env локально, Railway использует Service Variables

# === Проверка переменных окружения ===
logging.info("ENV has TELEGRAM_API_TOKEN? %s", "TELEGRAM_API_TOKEN" in os.environ)
logging.info("ENV has BOT_TOKEN? %s", "BOT_TOKEN" in os.environ)
logging.info("ENV has OPENAI_API_KEY? %s", "OPENAI_API_KEY" in os.environ)

TELEGRAM_API_TOKEN = os.getenv("TELEGRAM_API_TOKEN") or os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

logging.info("TELEGRAM_API_TOKEN detected: %s", bool(TELEGRAM_API_TOKEN))
logging.info("OPENAI_API_KEY detected: %s", bool(OPENAI_API_KEY))

if not TELEGRAM_API_TOKEN:
    raise EnvironmentError("TELEGRAM_API_TOKEN не установлен")
if not OPENAI_API_KEY:
    raise EnvironmentError("OPENAI_API_KEY не установлен")

# === Настройка бота ===
bot = Bot(token=TELEGRAM_API_TOKEN)
dp = Dispatcher()

# === Инициализация OpenAI клиента ===
client = OpenAI(api_key=OPENAI_API_KEY)

# === Обработчики ===
@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer("Привет! Я Бультыхвост 🐾 Напиши тему сказки, и я попробую её сочинить!")

@dp.message()
async def handle_message(message: Message):
    topic = message.text.strip()

    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Ты — сказочник, который придумывает короткие сказки для детей."},
                {"role": "user", "content": f"Сочини сказку на тему: {topic}"}
            ]
        )
        story = completion.choices[0].message.content
        await message.answer(story)

    except Exception as e:
        logging.error(f"Ошибка при генерации сказки: {e}")
        await message.answer("⚠️ Не удалось сочинить сказку. Попробуй снова.")

# === Запуск бота ===
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
