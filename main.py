# main.py
import os
import logging
from typing import Dict

from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

TELEGRAM_API_TOKEN = os.getenv("TELEGRAM_API_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")  # можно переопределить в .env

if not TELEGRAM_API_TOKEN:
    raise EnvironmentError("TELEGRAM_API_TOKEN не установлен")
if not OPENAI_API_KEY:
    raise EnvironmentError("OPENAI_API_KEY не установлен")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)
log = logging.getLogger("bulthykhvost")

bot = Bot(token=TELEGRAM_API_TOKEN, parse_mode=types.ParseMode.HTML)
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())

client = OpenAI(api_key=OPENAI_API_KEY)

# простейшее состояние диалогов
state: Dict[int, Dict[str, str]] = {}

WELCOME = (
    "Привет! Я Бультыхвост-сказочник 🐾\n"
    "Как зовут ребёнка?"
)
ASK_TOPIC = "Имя ребёнка — <b>{name}</b>? Отлично! ✨ Теперь напиши тему сказки."
TYPING_MSG = "Пишу сказку... 📖"
FAILED_MSG = "⚠️ Не удалось сочинить сказку. Попробуй ещё чуть позже."

def build_prompt(child_name: str, topic: str) -> str:
    return (
        "Ты добрый сказочник. Сочини тёплую, добрую детскую сказку на русском языке.\n"
        f"Имя ребёнка: {child_name}\n"
        f"Тема: {topic}\n\n"
        "Требования:\n"
        "• 8–12 коротких абзацев\n"
        "• Простые образы, дружелюбный тон\n"
        "• Тёплая мораль в конце\n"
        "• Без насилия и пугающих сцен\n"
    )

async def generate_story(child_name: str, topic: str) -> str:
    prompt = build_prompt(child_name, topic)

    # 1-й заход с основной моделью
    try:
        resp = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "You are a kind storyteller."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.8,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e1:
        log.exception("OpenAI error (model=%s): %s", OPENAI_MODEL, e1)

        # 2-й заход с запасной моделью
        fallback = "gpt-4o-mini"
        if OPENAI_MODEL != fallback:
            try:
                log.info("Retry with fallback model: %s", fallback)
                resp = client.chat.completions.create(
                    model=fallback,
                    messages=[
                        {"role": "system", "content": "You are a kind storyteller."},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.8,
                )
                return resp.choices[0].message.content.strip()
            except Exception as e2:
                log.exception("OpenAI fallback error: %s", e2)

        raise  # пусть обработчик наверху покажет пользователю FAILED_MSG

@dp.message_handler(commands=["start"])
async def cmd_start(msg: types.Message):
    state[msg.from_user.id] = {"stage": "ask_name"}
    await msg.answer(WELCOME)

@dp.message_handler(commands=["ping"])
async def cmd_ping(msg: types.Message):
    # Быстрый самотест: видим ключ и модель в логах, но пользователю – ок
    log.info("PING: model=%s key_prefix=%s", OPENAI_MODEL, (OPENAI_API_KEY or "")[:10])
    await msg.answer("Я на месте ✅")

@dp.message_handler()
async def dialog(msg: types.Message):
    uid = msg.from_user.id
    s = state.get(uid, {"stage": "ask_name"})

    # 1) спрашиваем имя
    if s["stage"] == "ask_name":
        child_name = msg.text.strip()
        if len(child_name) > 40:
            child_name = child_name[:40]
        s["name"] = child_name
        s["stage"] = "ask_topic"
        state[uid] = s
        await msg.answer(ASK_TOPIC.format(name=child_name))
        return

    # 2) спрашиваем тему и генерим
    if s["stage"] == "ask_topic":
        topic = msg.text.strip()
        await msg.answer(TYPING_MSG)

        try:
            story = await generate_story(s["name"], topic)
            await msg.answer(story)
            s["stage"] = "idle"
            state[uid] = s
        except Exception as e:
            # В логи – полная ошибка. Пользователю – мягко.
            log.exception("Failed to generate story: %s", e)
            # Если ключ проектный – дадим явную подсказку в логах
            if (OPENAI_API_KEY or "").startswith("sk-proj-"):
                log.error("У вас проектный ключ (sk-proj-). Если нет доступа к модели/проекту, "
                          "получите обычный пользовательский ключ sk-… или настройте проект.")
            await msg.answer(FAILED_MSG)
        return

    # На "idle" перезапускаем
    await msg.answer("Начнём новую историю! Напиши /start")

if __name__ == "__main__":
    log.info("Starting bot… model=%s key_prefix=%s", OPENAI_MODEL, (OPENAI_API_KEY or "")[:10])
    executor.start_polling(dp, skip_updates=True)
