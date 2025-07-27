import os
from aiogram import Bot, Dispatcher, types
from aiogram.types import ParseMode
from aiogram.utils import executor
from dotenv import load_dotenv
import openai

# Загрузка .env
load_dotenv()

# Получение токенов из переменных окружения
TELEGRAM_API_TOKEN = os.getenv("TELEGRAM_API_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Проверка наличия токенов
if not TELEGRAM_API_TOKEN:
    raise ValueError("TELEGRAM_API_TOKEN is not set")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY is not set")

# Инициализация
bot = Bot(token=TELEGRAM_API_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(bot)
openai.api_key = OPENAI_API_KEY

# Простая FSM на словаре
user_state = {}

@dp.message_handler(commands=["start"])
async def cmd_start(message: types.Message):
    user_state[message.from_user.id] = {"step": "get_name"}
    await message.answer("Привет! Я Бультыхвост-сказочник 🐾\nКак зовут ребёнка, для которого сочинять сказки?")

@dp.message_handler()
async def handle_message(message: types.Message):
    user_id = message.from_user.id
    if user_id not in user_state:
        await message.answer("Пожалуйста, начни сначала с команды /start.")
        return

    state = user_state[user_id]

    if state["step"] == "get_name":
        child_name = message.text.strip()
        state["name"] = child_name
        state["step"] = "get_topic"
        await message.answer(f"Имя ребёнка — {child_name}? Отлично! Теперь напиши тему сказки ✨")
    elif state["step"] == "get_topic":
        topic = message.text.strip()
        name = state.get("name", "Ребёнок")
        await message.answer("Пишу сказку... 📖")

        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Ты добрый сказочник, рассказывающий интересные, добрые, волшебные сказки."},
                    {"role": "user", "content": f"Сочини короткую сказку для ребёнка по имени {name} на тему: {topic}."}
                ],
                max_tokens=500,
                temperature=0.9
            )
            story = response.choices[0].message["content"]
            await message.answer(story)
        except Exception as e:
            await message.answer(f"Не удалось сочинить сказку 😢 Попробуй ещё раз позже.")
            print(f"OpenAI Error: {e}")

        user_state.pop(user_id)
    else:
        await message.answer("Что-то пошло не так. Попробуй /start заново.")

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
