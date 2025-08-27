# main.py
import os
import io
import base64
import logging
import tempfile
import subprocess

from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, types
from aiogram.dispatcher.filters import Command
from aiogram.utils import executor

from openai import OpenAI

# ----------------------
# ЛОГИ
# ----------------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
log = logging.getLogger("bulthykhvost")
log.info("=== BULTHYKHOVOST BOT START v3 (aiogram v2) ===")

# ----------------------
# ENV
# ----------------------
load_dotenv(override=False)

BOT_TOKEN = os.getenv("TELEGRAM_API_TOKEN") or os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")       # можно переопределить переменной
OPENAI_IMAGE_MODEL = os.getenv("OPENAI_IMAGE_MODEL", "gpt-image-1")

log.info("ENV has TELEGRAM_API_TOKEN? %s", "TELEGRAM_API_TOKEN" in os.environ)
log.info("ENV has OPENAI_API_KEY? %s", "OPENAI_API_KEY" in os.environ)
log.info("BOT_TOKEN detected: %s", bool(BOT_TOKEN))
log.info("OPENAI_API_KEY detected: %s", bool(OPENAI_API_KEY))

if not BOT_TOKEN:
    raise EnvironmentError("TELEGRAM_API_TOKEN не установлен")
if not OPENAI_API_KEY:
    raise EnvironmentError("OPENAI_API_KEY не установлен")

# ----------------------
# Telegram / OpenAI
# ----------------------
bot = Bot(token=BOT_TOKEN, parse_mode=types.ParseMode.HTML)
dp = Dispatcher(bot)
client = OpenAI(api_key=OPENAI_API_KEY)

# Простая память по пользователям
STATE = {}  # chat_id: {"stage": "ask_name"/"ask_topic", "name": "Егор"}


# ----------------------
# Вспомогательное
# ----------------------
def safe_len(text: str, max_len: int = 3500) -> str:
    text = (text or "").strip()
    return text if len(text) <= max_len else text[:max_len] + "…"

def have_ffmpeg() -> bool:
    try:
        subprocess.run(["ffmpeg", "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except Exception:
        return False

def tts_to_file(text: str) -> str:
    """
    Возвращает путь к аудиофайлу (OGG-voice если есть ffmpeg, иначе MP3),
    либо бросает исключение, если даже gTTS недоступен.
    """
    # gTTS может не быть в requirements — импортируем лениво
    try:
        from gtts import gTTS
    except Exception as e:
        raise RuntimeError("gTTS не установлен") from e

    text = safe_len(text, 3000)
    tmp_dir = tempfile.mkdtemp(prefix="tts_")
    mp3_path = os.path.join(tmp_dir, "voice.mp3")
    ogg_path = os.path.join(tmp_dir, "voice.ogg")

    # Генерация MP3
    gTTS(text=text, lang="ru").save(mp3_path)

    # Конвертация в OGG/OPUS для send_voice (если есть ffmpeg)
    if have_ffmpeg():
        try:
            subprocess.check_call([
                "ffmpeg", "-y", "-i", mp3_path,
                "-acodec", "libopus", "-b:a", "64k",
                "-vn", ogg_path
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return ogg_path
        except Exception:
            # если конверт не удался — вернём mp3
            return mp3_path
    else:
        return mp3_path


async def send_voice_or_audio(chat_id: int, path: str, caption: str = None):
    """
    Если файл .ogg — отправляем как voice, иначе как audio.
    """
    try:
        if path.lower().endswith(".ogg"):
            with open(path, "rb") as f:
                await bot.send_voice(chat_id, voice=f, caption=caption)
        else:
            with open(path, "rb") as f:
                await bot.send_audio(chat_id, audio=f, caption=caption or "Озвучка")
    except Exception as e:
        log.exception("Не удалось отправить голос/аудио: %s", e)


def build_story_prompt(child_name: str, topic: str) -> list:
    return [
        {"role": "system",
         "content": (
             "Ты — добрый сказочник Бультыхвост. Пиши короткие (8–12 предложений) "
             "добрые сказки для детей на русском языке. "
             "Используй простые фразы, немного магии, тёплый тон и обязательно счастливый финал."
         )},
        {"role": "user",
         "content": f"Сочини сказку для ребёнка по имени {child_name}. Тема: {topic}."}
    ]


def build_image_prompt(child_name: str, topic: str) -> str:
    return (
        f"Нарисуй иллюстрацию в детском книжном стиле по сказке на тему «{topic}» "
        f"для ребёнка по имени {child_name}. Яркие, добрые цвета, мягкие формы, "
        f"акцент на главного героя. Без текста."
    )


# ----------------------
# Генерация сказки
# ----------------------
def generate_story(child_name: str, topic: str) -> str:
    completion = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=build_story_prompt(child_name, topic),
        temperature=0.9,
        max_tokens=600
    )
    return (completion.choices[0].message.content or "").strip()


# ----------------------
# Генерация иллюстрации (опционально)
# ----------------------
def generate_image_b64(child_name: str, topic: str) -> bytes:
    """
    Возвращает PNG-байты или бросает исключение. Использует gpt-image-1.
    """
    result = client.images.generate(
        model=OPENAI_IMAGE_MODEL,
        prompt=build_image_prompt(child_name, topic),
        size="1024x1024"
    )
    b64 = result.data[0].b64_json
    return base64.b64decode(b64)


# ----------------------
# Handlers
# ----------------------
@dp.message_handler(Command("start"))
async def on_start(message: types.Message):
    chat_id = message.chat.id
    STATE[chat_id] = {"stage": "ask_name"}
    await message.answer(
        "Привет! Я <b>Бультыхвост</b> 🐾\n"
        "Давай сочиним сказку. Как зовут ребёнка?"
    )


@dp.message_handler(content_types=types.ContentTypes.TEXT)
async def on_text(message: types.Message):
    chat_id = message.chat.id
    text = (message.text or "").strip()

    # начнём сценарий, если нет состояния
    if chat_id not in STATE:
        STATE[chat_id] = {"stage": "ask_name"}
        await message.answer("Как зовут ребёнка?")
        return

    stage = STATE[chat_id].get("stage")

    if stage == "ask_name":
        # сохраним имя и попросим тему
        STATE[chat_id]["name"] = safe_len(text, 64)
        STATE[chat_id]["stage"] = "ask_topic"
        await message.answer(f"Имя ребёнка — <b>{STATE[chat_id]['name']}</b>. Отлично! Теперь напиши тему сказки ✨")
        return

    if stage == "ask_topic":
        name = STATE[chat_id].get("name") or "Малыш"
        topic = safe_len(text, 200)
        await message.answer("Пишу сказку… 📖")

        # Генерим сказку
        try:
            story = generate_story(name, topic)
            if not story:
                raise RuntimeError("Пустой ответ модели")

            # отправим текст
            await message.answer(story)

            # Попробуем сгенерить иллюстрацию (не критично)
            try:
                png_bytes = generate_image_b64(name, topic)
                await bot.send_photo(chat_id, photo=io.BytesIO(png_bytes), caption="Иллюстрация 📷")
            except Exception as e_img:
                log.warning("Иллюстрация не создана: %s", e_img)

            # Попробуем озвучить (не критично)
            try:
                voice_path = tts_to_file(story)
                await send_voice_or_audio(chat_id, voice_path, caption="Озвучка сказки 🎙️")
            except Exception as e_tts:
                log.warning("Озвучка не создана: %s", e_tts)

        except Exception as e:
            log.exception("Ошибка при генерации сказки: %s", e)
            await message.answer(f"⚠️ Не удалось сочинить сказку. Причина: {e}")

        # сброс состояния — можно снова начать с темы (имя сохраним)
        STATE[chat_id]["stage"] = "ask_topic"
        await message.answer("Хочешь ещё тему? Просто напиши её 🙂")
        return

    # На всякий случай
    STATE[chat_id] = {"stage": "ask_name"}
    await message.answer("Давай начнём сначала. Как зовут ребёнка?")


# ----------------------
# main
# ----------------------
def main():
    log.info("Starting polling (aiogram v2)…")
    executor.start_polling(dp, skip_updates=True)


if __name__ == "__main__":
    main()
