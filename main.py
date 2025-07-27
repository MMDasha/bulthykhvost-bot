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
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

user_data = {}

@dp.message(CommandStart())
async def start_handler(message: types.Message):
    await message.answer("Привет! Я Бультыхвост-сказочник 🐾\nКак зовут ребёнка, для которого сочинять сказки?")
    user_data[message.from_user.id] = {"stage": "name"}

@dp.message()
async def handle_message(message: types.Message):
    user_id = message.from_user.id
    if user_id not in user_data:
        await message.answer("Пожалуйста, начни сначала с команды /start.")
        return

    stage = user_data[user_id].get("stage")

    if stage == "name":
        child_name = message.text.strip()
        user_data[user_id]["child_name"] = child_name
        user_data[user_id]["stage"] = "topic"
        await message.answer(f"Имя ребёнка — {child_name}? Отлично! Теперь напиши тему сказки 🌟")

    elif stage == "topic":
        story_topic = message.text.strip()
        child_name = user_data[user_id].get("child_name", "Малыш")
        await message.answer("Пишу сказку... 📖")

        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Ты добрый сказочник, сочиняй сказки для детей."},
                    {"role": "user", "content": f"Сочини сказку для ребёнка по имени {child_name} на тему {story_topic}."}
                ]
            )
            story_text = response['choices'][0]['message']['content']
            await message.answer(story_text)
        except Exception as e:
            print(f"OpenAI Error: {e}")
            await message.answer("Не удалось сочинить сказку 😢 Попробуй ещё раз позже.")

        user_data[user_id]["stage"] = "done"

    else:
        await message.answer("Если хочешь начать сначала, отправь /start")


async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())

