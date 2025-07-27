import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram import Router
from aiogram.types import ReplyKeyboardRemove
from dotenv import load_dotenv
import openai

# Load environment variables
load_dotenv()
TELEGRAM_API_TOKEN = os.getenv("TELEGRAM_API_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

# Logging
logging.basicConfig(level=logging.INFO)

# States
class Form(StatesGroup):
    name = State()
    topic = State()

# Initialize bot and dispatcher
bot = Bot(token=TELEGRAM_API_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(storage=MemoryStorage())
router = Router()
dp.include_router(router)

@router.message(commands=["start"])
async def cmd_start(message: Message, state: FSMContext):
    await message.answer("Привет! Я Бультыхвост-сказочник 🐾\nКак зовут ребёнка, для которого сочинять сказки?")
    await state.set_state(Form.name)

@router.message(Form.name)
async def process_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer(f"Имя ребёнка — {message.text}? Отлично! Теперь напиши тему сказки 🌟")
    await state.set_state(Form.topic)

@router.message(Form.topic)
async def process_topic(message: Message, state: FSMContext):
    data = await state.get_data()
    name = data.get("name")
    topic = message.text
    await message.answer("Пишу сказку... 📖")

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Ты волшебный сказочник."},
                {"role": "user", "content": f"Сочини добрую и весёлую сказку для ребёнка по имени {name} на тему '{topic}'. Напиши на русском."}
            ]
        )
        story = response.choices[0].message.content
        await message.answer(story)
    except Exception as e:
        logging.error(e)
        await message.answer("Не удалось сочинить сказку 😢 Попробуй ещё раз позже.")
    await state.clear()

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())


