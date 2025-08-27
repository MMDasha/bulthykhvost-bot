import os
import logging
from aiogram import Bot, Dispatcher, executor, types
from openai import OpenAI
from gtts import gTTS

# Логирование
logging.basicConfig(level=logging.INFO)

# Получаем переменные окружения
TELEGRAM_API_TOKEN = os.getenv("TELEGRAM_API_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not TELEGRAM_API_TOKEN:
    raise EnvironmentError("TELEGRAM_API_TOKEN не установлен")
if not OPENAI_API_KEY:
    raise EnvironmentError("OPENAI_API_KEY не установлен")

# Инициализация бота и клиента OpenAI
bot = Bot(token=TELEGRAM_API_TOKEN, parse_mode=types.ParseMode.HTML)
dp = Dispatcher(bot)

client = OpenAI(api_key=OPENAI_API_KEY)

# Состояния для сказки
user_state = {}


@dp.message_handler(commands=["start"])
async def start_command(message: types.Message):
    await message.answer("Привет! Я Бультыхвост-сказочник 🐾\nКак зовут ребёнка?")
    user_state[message.from_user.id] = {"step": "child_name"}


@dp.message_handler()
async def handle_message(message: types.Message):
    state = user_state.get(message.from_user.id, {})

    if state.get("step") == "child_name":
        child_name = message.text.strip()
        state["child_name"] = child_name
        state["step"] = "story_theme"
        await message.answer(f"Имя ребёнка — {child_name}? Отлично! ✨ Теперь напиши тему сказки.")
        return

    if state.get("step") == "story_theme":
        theme = message.text.strip()
        child_name = state.get("child_name")

        await message.answer("Пишу сказку... 📖")

        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Ты детский сказочник. Придумывай короткие сказки (10-15 предложений)."},
                    {"role": "user", "content": f"Придумай сказку для ребёнка {child_name} на тему: {theme}"}
                ],
                max_tokens=400
            )

            story = response.choices[0].message["content"].strip()

            # Отправляем текст сказки
            await message.answer(story)

            # Дополнительно — озвучка сказки
            tts = gTTS(text=story, lang="ru")
            voice_file = f"story_{message.from_user.id}.mp3"
            tts.save(voice_file)

            with open(voice_file, "rb") as f:
                await message.answer_voice(f)

            os.remove(voice_file)

        except Exception as e:
            logging.error(f"Ошибка при генерации сказки: {e}")
            await message.answer("⚠️ Не удалось сочинить сказку. Попробуй ещё раз чуть позже.")


if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
