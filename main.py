import os
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import ParseMode
from aiogram.utils import executor
from dotenv import load_dotenv
import openai

# --- Загружаем переменные окружения ---
load_dotenv()

TELEGRAM_API_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if TELEGRAM_API_KEY is None:
    raise ValueError("BOT_TOKEN is not set in environment")
if OPENAI_API_KEY is None:
    raise ValueError("OPENAI_API_KEY is not set in environment")

# --- Настройка логгера ---
logging.basicConfig(level=logging.INFO)

# --- Настройка OpenAI ---
openai.api_key = OPENAI_API_KEY

# --- Настройка бота ---
bot = Bot(token=TELEGRAM_API_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(bot)

# --- Состояние для сказки ---
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup

dp.storage = MemoryStorage()


class StoryStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_theme = State()


@dp.message_handler(commands=["start"])
async def cmd_start(message: types.Message):
    await message.reply("Привет! Я Бультыхвост-сказочник 🐾\nКак зовут ребёнка, для которого сочинять сказки?")
    await StoryStates.waiting_for_name.set()


@dp.message_handler(state=StoryStates.waiting_for_name)
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(child_name=mess

