# main.py
import os
import logging
import asyncio
from typing import Dict

from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.utils.exceptions import Throttled
from dotenv import load_dotenv

# OpenAI (новый клиент)
from openai import OpenAI

# -------------------
# Конфигурация / токены
# -------------------
load_dotenv()

TELEGRAM_API_TOKEN = os.getenv("TELEGRAM_API_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not TELEGRAM_API_TOKEN:
    raise EnvironmentError("TELEGRAM_API_TOKEN не установлен")
if not OPENAI_API_KEY:
    raise EnvironmentError("OPENAI_API_KEY не установлен")

# -------------------
# Логирование
# -------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)
logger = logging.getLogger("bulthykhvost-bot")

# -------------------
# Telegram
# -------------------
bot = Bot(token=TELEGRAM_API_TOKEN, parse_mode=types.ParseMode.HTML)
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())

# -------------------
# OpenAI клиент
# -------------------
client = OpenAI(api_key=OPENAI_API_KEY)

# -------------------
# Очень простой сторедж состояния пользователей
# stage: "ask_name" -> "ask_topic" -> "idle"
# -------------------
UserState = Dict[int, Dict[str, str]]
state: UserState = {}

WELCOME = (
    "Привет! Я Бультыхвост-сказочник 🐾\n"
    "Как зовут ребёнка?"
)

ASK_TOPIC = "Имя ребёнка — <b>{name}</b>? Отлично! ✨ Теперь напиши тему сказки."

TYPING = "Пишу сказку... 📖"

FAILED = "⚠️ Не удалось сочинить сказку. Попробуй ещё чуть позже."


async def throttle_message(message: types.Message, key: str, rate: float = 1.0):
    """
    Короткий антиспам, чтобы не спамить генерацией.
    """
    try:
        await dp.throttle(key, rate=rate)
    except Throttled:
        await message.answer("Слишком часто. Дай мне секундочку…")
        raise


def build_prompt(child_name: str, topic: str) -> str:
    return (
        "Ты добрый сказочник. Сочини тёплую, добрую детскую сказку на русском языке.\n"
        f"Имя ребёнка: {child_name}\n"
        f"Тема: {topic}\n\n"
        "Требования:\n"
        "• 8–12 коротких абзацев (не слишком длинно)\n"
        "• Яркие, но простые образы\n"
        "• Дружелюбный тон и тёплая мораль в конце\n"
        "• Без насилия и пугающих сцен\n"
    )


async def generate_story(child_name: str, topic: str) -> str:
    """
    Вызов OpenAI Chat Completions (новый клиент
