import os
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from dotenv import load_dotenv
import openai
from gtts import gTTS
from uuid import uuid4

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
openai.api_key = os.getenv("OPENAI_API_KEY")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
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

        prompt = (
            f"Сочини добрую сказку с волшебным героем Бултыхвостом. "
            f"Имя ребёнка — {child_name}. Тема сказки: {text}. "
            f"Сказка должна быть поучительной, весёлой и интересной для детей 4–6 лет."
        )

        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.9,
                max_tokens=600,
                request_timeout=20
            )
            story = response.choices[0].message.content.strip()
            await message.answer(story)

        except Exception as e:
            await message.answer("Не удалось сочинить сказку 😢 Попробуй ещё раз позже.")
            print(f"[OpenAI ERROR]: {e}")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
