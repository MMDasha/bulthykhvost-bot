# main.py
import os
import logging
from io import BytesIO

from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, executor, types
from gtts import gTTS

# Новый официальный SDK OpenAI (v1)
from openai import OpenAI
from openai._exceptions import OpenAIError

# -------------------- Настройка логов и окружения --------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

# Локально прочитает .env; на Railway/Render значения нужно задать в Variables
load_dotenv()

TELEGRAM_API_TOKEN = os.getenv("TELEGRAM_API_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")  # при желании можно задать gpt-3.5-turbo-0125

if not TELEGRAM_API_TOKEN:
    raise EnvironmentError("TELEGRAM_API_TOKEN не установлен")
if not OPENAI_API_KEY:
    raise EnvironmentError("OPENAI_API_KEY не установлен")

# -------------------- Инициализация клиентов --------------------
bot = Bot(token=TELEGRAM_API_TOKEN)
dp = Dispatcher(bot)
client = OpenAI(api_key=OPENAI_API_KEY)

# Простое состояние: имя -> тема
user_state = {}  # chat_id -> {"wait": "name"|"topic", "name": str}

# -------------------- Генерация сказки --------------------
def generate_story(child_name: str, topic: str) -> str:
    """
    Запрос к OpenAI Chat Completions.
    Возвращает текст сказки или бросает исключение.
    """
    system_prompt = (
        "Ты добрый детский сказочник. Пиши на русском короткие, тёплые и понятные сказки "
        "с героем по имени Бултыхвост. Избегай страшных мотивов. В конце — светлый добрый финал."
    )
    user_prompt = (
        f"Сочини сказку для ребёнка по имени {child_name}. "
        f"Тема: {topic}. Объём 8–12 небольших абзацев."
    )

    try:
        resp = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.8,
            max_tokens=900,
        )
        return resp.choices[0].message.content.strip()
    except OpenAIError as e:
        logging.error(f"OpenAI error: {e}")
        # Попробуем мягкий фолбэк на gpt-3.5-turbo-0125, если модель недоступна
        try:
            resp = client.chat.completions.create(
                model="gpt-3.5-turbo-0125",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.8,
                max_tokens=900,
            )
            return resp.choices[0].message.content.strip()
        except Exception as e2:
            logging.error(f"Fallback model failed: {e2}")
            raise
    except Exception as e:
        logging.exception("Unexpected error while calling OpenAI")
        raise

# -------------------- Хэндлеры --------------------
@dp.message_handler(commands=["start", "help"])
async def cmd_start(message: types.Message):
    user_state[message.chat.id] = {"wait": "name"}
    await message.answer(
        "Привет! Я Бультыхвост-сказочник 🐾\n"
        "Как зовут ребёнка, для которого будем сочинять сказки?\n\n"
        "Команды: /start — начать заново, /cancel — очистить диалог."
    )

@dp.message_handler(commands=["cancel"])
async def cmd_cancel(message: types.Message):
    user_state[message.chat.id] = {"wait": "name"}
    await message.answer("Окей, всё сбросил. Напиши имя ребёнка 🙂")

@dp.message_handler()
async def handle_dialog(message: types.Message):
    chat_id = message.chat.id
    st = user_state.get(chat_id, {"wait": "name"})

    # Ждём имя
    if st.get("wait") == "name":
        name = message.text.strip()
        if not name:
            await message.answer("Напиши, пожалуйста, имя ребёнка.")
            return

        st["name"] = name
        st["wait"] = "topic"
        user_state[chat_id] = st

        await message.answer(
            f"Имя ребёнка — {name}? Отлично! Теперь напиши тему сказки ✨"
        )
        return

    # Ждём тему
    if st.get("wait") == "topic":
        topic = message.text.strip()
        name = st.get("name", "Ребёнок")

        if not topic:
            await message.answer("Напиши, пожалуйста, тему сказки.")
            return

        await message.answer("Пишу сказку... 📖")

        # Генерация сказки
        try:
            story = generate_story(name, topic)
        except Exception:
            await message.answer("⚠️ Не удалось сочинить сказку. Попробуй ещё раз позже.")
            return

        # Отправляем текст
        await message.answer(story)

        # Пробуем озвучить и отправить голосовое
        try:
            tts = gTTS(story, lang="ru")
            buf = BytesIO()
            tts.write_to_fp(buf)
            buf.seek(0)
            await message.answer_voice(voice=buf, caption="Сказка Бултыхвост 🎙️")
        except Exception as e:
            logging.error(f"gTTS error: {e}")

        # Сбрасываем состояние и предлагаем новую сказку
        user_state[chat_id] = {"wait": "name"}
        await message.answer("Хочешь ещё сказку? Напиши новое имя ребёнка или просто тему 😊")
        return

    # Если состояние потеряно — начнём заново
    user_state[chat_id] = {"wait": "name"}
    await message.answer("Давай начнём заново. Как зовут ребёнка?")

# -------------------- Точка входа --------------------
if __name__ == "__main__":
    logging.info(f"Starting Bulthykhvost bot with model: {OPENAI_MODEL}")
    executor.start_polling(dp, skip_updates=True)
