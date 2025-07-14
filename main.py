import os
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from dotenv import load_dotenv
from openai import OpenAI
from gtts import gTTS
from uuid import uuid4

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

openai = OpenAI(api_key=OPENAI_API_KEY)
user_data = {}

@dp.message(CommandStart())
async def start(message: types.Message):
    await message.answer("Привет! Я Бултыхвост-сказочник 🐾\nКак зовут ребёнка, для которого сочинять сказки?")
    user_data[message.from_user.id] = {}

@dp.message(F.text)
async def handle_text(message: types.Message):
    user_id = message.from_user.id
    text = message.text.strip()

    if 'child_name' not in user_data.get(user_id, {}):
        user_data[user_id] = {'child_name': text}
        await message.answer(f"Имя ребёнка — {text}? Отлично! Теперь напиши тему сказки 🌟")
    else:
        child_name = user_data[user_id]['child_name']
        await message.answer("Пишу сказку... 📖")

        prompt = f"Сочини сказку с героем по имени Бултыхвост. Сказка должна быть волшебной, доброй, с поучительным концом. Имя ребёнка — {child_name}. Тема: {text}."
        story_response = openai.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.95,
            max_tokens=800
        )
        story = story_response.choices[0].message.content.strip()
        await message.answer(story)

        await message.answer("Создаю иллюстрацию... 🖼")
        image_prompt = f"Иллюстрация к детской сказке с героем Бултыхвост, на тему: {text}. Волшебный стиль, яркие цвета."
        image_response = openai.images.generate(
            model="dall-e-3",
            prompt=image_prompt,
            size="1024x1024",
            n=1
        )
        await message.answer_photo(image_response.data[0].url)

        await message.answer("Готовлю озвучку... 🎤")
        tts = gTTS(story, lang="ru")
        filename = f"/tmp/{uuid4().hex}.mp3"
        tts.save(filename)
        await message.answer_voice(types.FSInputFile(filename))
        os.remove(filename)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
