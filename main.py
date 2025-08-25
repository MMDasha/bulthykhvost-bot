import os
import logging
from aiogram import Bot, Dispatcher, executor, types
from dotenv import load_dotenv
import openai
from gtts import gTTS
from aiogram.types import InputFile

# ==============================
# Настройка логирования
# ==============================
logging.basicConfig(level=logging.INFO)

# ==============================
# Загружаем переменные окружения
# ==============================
load_dotenv()

TELEGRAM_API_TOKEN = os.getenv("TELEGRAM_API_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not TELEGRAM_API_TOKEN:
    raise ValueError("TELEGRAM_API_TOKEN is not set")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY is not set")

# ==============================
# Настройка OpenAI
# ==============================
openai.api_key = OPENAI_API_KEY

# ==============================
# Создаём Telegram-бота
# ==============================
bot = Bot(token=TELEGRAM_API_TOKEN)
dp = Dispatcher(bot)

# ==============================
# Хранилище данных пользователя
# ==============================
user_data = {}

# ==============================
# Генерация сказки через OpenAI
# ==============================
async def generate_story(child_name: str, topic: str) -> str:
    try:
        response = openai.Completion.create(
            model="text-davinci-003",
            prompt=f"Сочини добрую и весёлую детскую сказку для ребёнка по имени {child_name} на тему {topic}.",
            max_tokens=500,
            temperature=0.8,
            top_p=1,
        )
        return response.choices[0].text.strip()
    except Exception as e:
        logging.error(f"Ошибка OpenAI: {e}")
        return None

# ==============================
# Генерация озвучки
# ==============================
def generate_audio(text: str, filename="story.mp3") -> str:
    try:
        tts = gTTS(text=text, lang="ru")
        tts.save(filename)
        return filename
    except Exception as e:
        logging.error(f"Ошибка генерации аудио: {e}")
        return None

# ==============================
# Команда /start
# ==============================
@dp.message_handler(commands=["start"])
async def start_command(message: types.Message):
    await message.answer("Привет! Я Бультыхвост-сказочник 🐾\nКак зовут ребёнка, для которого сочинять сказки?")
    user_data[message.from_user.id] = {}

# ==============================
# Обработка текстов
# ==============================
@dp.message_handler()
async def handle_message(message: types.Message):
    user_id = message.from_user.id

    # Если имени ребёнка ещё нет → сохраняем
    if "child_name" not in user_data[user_id]:
        user_data[user_id]["child_name"] = message.text
        await message.answer(f"Имя ребёнка — {message.text}? Отлично! Теперь напиши тему сказки ✨")
        return

    # Если имя уже есть → сохраняем тему
    if "topic" not in user_data[user_id]:
        user_data[user_id]["topic"] = message.text
        await message.answer("Пишу сказку... 📖")

        child_name = user_data[user_id]["child_name"]
        topic = user_data[user_id]["topic"]

        # Генерация сказки
        story = await generate_story(child_name, topic)
        if not story:
            await message.answer("Не удалось сочинить сказку 😢 Попробуй ещё раз позже.")
            return

        # Отправляем текст сказки
        await message.answer(f"Вот твоя сказка:\n\n{story}")

        # Генерация и отправка аудио
        audio_path = generate_audio(story)
        if audio_path:
            await message.answer_audio(InputFile(audio_path))
        else:
            await message.answer("Не удалось создать аудио 😢")

        # Сбрасываем данные
        user_data.pop(user_id, None)

# ==============================
# Запуск бота
# ==============================
if __name__ == "__main__":
    logging.info("Бот запущен...")
    executor.start_polling(dp, skip_updates=True)
