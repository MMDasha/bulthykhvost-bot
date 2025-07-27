import os
import logging
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ParseMode
from dotenv import load_dotenv
import openai

# Загрузка переменных из .env
load_dotenv()

TELEGRAM_API_TOKEN = os.getenv("TELEGRAM_API_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not TELEGRAM_API_TOKEN:
    raise ValueError("TELEGRAM_API_TOKEN is not set")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY is not set")

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Инициализация бота
bot = Bot(token=TELEGRAM_API_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(bot)
openai.api_key = OPENAI_API_KEY

# Состояние чата
user_context = {}

@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    await message.reply("Привет! Я Бультыхвост-сказочник 🐾\nКак зовут ребёнка, для которого сочинять сказки?")
    user_context[message.chat.id] = {"step": "awaiting_name"}

@dp.message_handler()
async def handle_message(message: types.Message):
    state = user_context.get(message.chat.id, {})
    step = state.get("step")

    if step == "awaiting_name":
        state["name"] = message.text
        state["step"] = "awaiting_topic"
        await message.reply(f"Имя ребёнка — {message.text}? Отлично! Теперь напиши тему сказки ✨")

    elif step == "awaiting_topic":
        name = state.get("name")
        topic = message.text

        await message.reply("Пишу сказку... 📖")

        try:


