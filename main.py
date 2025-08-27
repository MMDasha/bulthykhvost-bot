import os
import logging
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, types
from aiogram.dispatcher.filters import Command  # <-- v2 импорт
from aiogram.utils import executor

from openai import OpenAI

# === ЛОГИРОВАНИЕ ===
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logging.info("=== BULTHYKHOVOST BOT START v3 (aiogram v2) ===")

# === ENV ===
load_dotenv(override=False)

logging.info("ENV has TELEGRAM_API_TOKEN? %s", "TELEGRAM_API_TOKEN" in os.environ)
logging.info("ENV has BOT_TOKEN? %s", "BOT_TOKEN" in os.environ)
logging.info("ENV has OPENAI_API_KEY? %s", "OPENAI_API_KEY" in os.environ)

TELEGRAM_API_TOKEN = os.getenv("TELEGRAM_API_TOKEN") or os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

logging.info("TELEGRAM_API_TOKEN detected: %s", bool(TELEGRAM_API_TOKEN))
logging.info("OPENAI_API_KEY detected: %s", bool(OPENAI_API_KEY))

if not TELEGRAM_API_TOKEN:
    raise EnvironmentError("TELEGRAM_API_TOKEN не установлен")
if not OPENAI_API_KEY:
    raise EnvironmentError("OPENAI_API_KEY не установлен")

# === OpenAI ===
client = OpenAI(api_key=OPENAI_API_KEY)

# === Telegram Bot (aiogram v2) ===
bot = Bot(token=TELEGRAM_API_TOKEN, parse_mode=types.ParseMode.HTML)
dp = Dispatcher(bot)

@dp.message_handler(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Привет! Я Бультыхвост 🐾 Напиши тему сказки — сочиню короткую историю!")

@dp.message_handler(content_types=types.ContentTypes.TEXT)
async def handle_text(message: types.Message):
    topic = (message.text or "").strip()
    if not topic:
        await message.answer("Напиши тему сказки одним сообщением ✍️")
        return

    try:
        # Генерация сказки
        completion = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "Ты — добрый сказочник, который пишет короткие сказки для детей на заданную тему."},
                {"role": "user", "content": f"Сочини сказку на тему: {topic}. Сделай её тёплой и доброй."}
            ],
            temperature=0.9,
            max_tokens=500,
        )
        story = completion.choices[0].message.content.strip()
        if not story:
            raise RuntimeError("Пустой ответ от модели")

        await message.answer(story)

    except Exception as e:
        logging.exception("Ошибка при генерации сказки: %s", e)
        await message.answer("⚠️ Не удалось сочинить сказку. Попробуй ещё раз чуть позже.")

def main():
    # aiogram v2 — запуск через executor
    logging.info("Starting polling (aiogram v2)...")
    executor.start_polling(dp, skip_updates=True)

if __name__ == "__main__":
    main()
