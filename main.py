import os
import logging
from io import BytesIO

from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, executor, types
from gtts import gTTS

# Новый OpenAI SDK v1
from openai import OpenAI
from openai._exceptions import OpenAIError

# -------------------- базовая настройка --------------------
load_dotenv()  # локально прочитает .env; на Railway берёт из Variables

TELEGRAM_API_TOKEN = os.getenv("TELEGRAM_API_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")  # можешь сменить на gpt-3.5-turbo-0125

if not TELEGRAM_API_TOKEN:
    raise EnvironmentError("TELEGRAM_API_TOKEN не установлен")
if not OPENAI_API_KEY:
    raise EnvironmentError("OPENAI_API_KEY не установлен")

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")

bot = Bot(token=TELEGRAM_API_TOKEN)
dp = Dispatcher(bot)
client = OpenAI(api_key=OPENAI_API_KEY)

# Простое состояние: имя → тема
state = {}  # chat_id -> {"wait": "name"/"topic", "name": ...}

def make_story(name: str, topic: str) -> str:
    """Запрос к OpenAI с обработкой ошибок."""
    system = ("Ты добрый сказочник. Пиши короткие тёплые сказки на русском с героем Бултыхвост. "
              "Подходит детям 4–6 лет, без пугающих сцен.")
    user = f"Сочини сказку для ребёнка по имени {name}. Тема: {topic}. Объём ~8 абзацев, финал добрый."
    try:
        resp = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0.8,
            max_tokens=800,
        )
        return resp.choices[0].message.content.strip()
    except OpenAIError as e:
        logging.error(f"OpenAI error: {e}")
        raise
    except Exception as e:
        logging.exception("Unexpected error calling OpenAI")
        raise

@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    state[message.chat.id] = {"wait": "name"}
    await message.answer("Привет! Я Бультыхвост-сказочник 🐾\nКак зовут ребёнка?")

@dp.message_handler()
async def handle_all(message: types.Message):
    s = state.get(message.chat.id, {"wait": "name"})

    if s.get("wait") == "name":
        s["name"] = message.text.strip()
        s["wait"] = "topic"
        state[message.chat.id] = s
        await message.answer(f"Отлично, {s['name']}! Напиши тему сказки ✨")
        return

    if s.get("wait") == "topic":
        name = s.get("name", "Ребёнок")
        topic = message.text.strip()
        await message.answer("Пишу сказку... 📖")

        try:
            story = make_story(name, topic)
            # Текст сказки
            await message.answer(story)

            # Озвучка gTTS → голосовое
            try:
                tts = gTTS(story, lang="ru")
                buf = BytesIO()
                tts.write_to_fp(buf)
                buf.seek(0)
                await message.answer_voice(voice=buf, caption="Сказка Бултыхвост 🎙️")
            except Exception as e:
                logging.error(f"gTTS error: {e}")

            # Сброс
            state[message.chat.id] = {"wait": "name"}
            await message.answer("Хочешь ещё сказку? Напиши новое имя ребёнка или просто тему 😊")

        except Exception:
            await message.answer("⚠️ Не удалось сочинить сказку. Проверь ключ OpenAI и попробуй позже.")
        return

    # если внезапно нет состояния — начать заново
    state[message.chat.id] = {"wait": "name"}
    await message.answer("Давай начнём заново. Как зовут ребёнка?")

if __name
