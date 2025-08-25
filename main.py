import os
import logging
import asyncio
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
import openai
from gtts import gTTS
from io import BytesIO

# Загружаем переменные окружения
load_dotenv()
TELEGRAM_API_TOKEN = os.getenv("TELEGRAM_API_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Настройка OpenAI
openai.api_key = OPENAI_API_KEY

# Настройка логов
logging.basicConfig(level=logging.INFO)

# Создаём объекты бота и диспетчера
bot = Bot(token=TELEGRAM_API_TOKEN)
dp = Dispatcher(bot)

# Храним имя ребёнка в памяти
user_name = {}

# Команда /start
@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    await message.answer("Привет! 🐬 Я бот Бултыхвост.\nКак зовут ребёнка?")
    user_name[message.from_user.id] = None

# Сохраняем имя ребёнка
@dp.message_handler(lambda msg: user_name.get(msg.from_user.id) is None)
async def save_child_name(message: types.Message):
    user_name[message.from_user.id] = message.text
    await message.answer(f"Отлично, {message.text}! 🎉\nТеперь напиши тему сказки.")

# Генерация сказки, иллюстрации и озвучки
@dp.message_handler()
async def generate_story(message: types.Message):
    try:
        child = user_name.get(message.from_user.id, "ребёнок")
        topic = message.text

        # Генерация сказки
        prompt = f"Сочини добрую сказку про персонажа Бултыхвост и ребёнка по имени {child}. Тема: {topic}."
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=prompt,
            max_tokens=600,
            temperature=0.8
        )
        story = response.choices[0].text.strip()

        # Отправляем текст сказки
        await message.answer(f"📖 Вот твоя сказка:\n\n{story}")

        # Создаём озвучку
        tts = gTTS(text=story, lang="ru")
        audio_bytes = BytesIO()
        tts.write_to_fp(audio_bytes)
        audio_bytes.seek(0)

        # Отправляем аудио
        await message.answer_audio(audio=audio_bytes, title="Сказка Бултыхвост")

    except Exception as e:
        logging.error(f"Ошибка: {e}")
        await message.answer("⚠️ Не удалось сочинить сказку. Попробуй снова.")

# Основная точка входа
if __name__ == "__main__":
    asyncio.run(dp.start_polling())
