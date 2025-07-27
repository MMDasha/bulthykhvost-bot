import logging
import os
import openai
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.utils import executor
from aiogram.dispatcher.filters import CommandStart
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup

# Настройка логов
logging.basicConfig(level=logging.INFO)

# Получение токенов
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not BOT_TOKEN:
    raise ValueError("❌ Переменная окружения BOT_TOKEN не задана")
if not OPENAI_API_KEY:
    raise ValueError("❌ Переменная окружения OPENAI_API_KEY не задана")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())
openai.api_key = OPENAI_API_KEY

# Машина состояний
class StoryState(StatesGroup):
    waiting_for_name = State()
    waiting_for_theme = State()

# Обработка /start
@dp.message_handler(CommandStart())
async def start(message: Message, state: FSMContext):
    await message.answer("Привет! Я Бультыхвост-сказочник 🐾\nКак зовут ребёнка, для которого сочинять сказки?")
    await state.set_state(StoryState.waiting_for_name.state)

# Имя ребёнка
@dp.message_handler(state=StoryState.waiting_for_name)
async def get_name(message: Message, state: FSMContext):
    await state.update_data(child_name=message.text)
    await message.answer(f"Имя ребёнка — {message.text}? Отлично! Теперь напиши тему сказки 🌟")
    await state.set_state(StoryState.waiting_for_theme.state)

# Тема сказки
@dp.message_handler(state=StoryState.waiting_for_theme)
async def get_theme(message: Message, state: FSMContext):
    await state.update_data(theme=message.text)
    await message.answer("Пишу сказку... 📖")

    data = await state.get_data()
    child_name = data["child_name"]
    theme = data["theme"]

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{
                "role": "user",
                "content": f"Сочини добрую сказку для ребёнка по имени {child_name} на тему: {theme}"
            }],
            max_tokens=600,
            temperature=0.9,
        )
        story = response["choices"][0]["message"]["content"]
        await message.answer(story)
    except Exception as e:
        await message.answer(f"Не удалось сочинить сказку 😢\nОшибка: {e}")

    await state.finish()

# Обработка любого сообщения до /start
@dp.message_handler()
async def fallback(message: Message):
    await message.answer("Пожалуйста, начни сначала с команды /start.")

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)


