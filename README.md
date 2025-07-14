# 🤖 Бултыхвост бот — Telegram-сказочник

Этот Telegram-бот сочиняет сказки с участием персонажа Бултыхвост и ребёнка по имени, которое вы укажете. Он также создаёт иллюстрации к сказке и озвучивает её голосом.

## 🧩 Возможности
- Принимает имя ребёнка
- Генерирует волшебную сказку с Бултыхвостом
- Рисует иллюстрацию с помощью DALL·E
- Озвучивает сказку с помощью TTS

## 🚀 Запуск

1. Клонируй репозиторий:
   ```bash
   git clone https://github.com/MMDasha/bulthykhvost-bot.git
   cd bulthykhvost-bot
   ```

2. Создай `.env` файл, используя `.env.example`:
   ```bash
   cp .env.example .env
   ```

3. Установи зависимости:
   ```bash
   pip install -r requirements.txt
   ```

4. Запусти бота:
   ```bash
   python main.py
   ```

## 📝 Переменные окружения

- `BOT_TOKEN` — токен Telegram-бота от [@BotFather](https://t.me/BotFather)
- `OPENAI_API_KEY` — API-ключ от [OpenAI](https://platform.openai.com/account/api-keys)

## 📷 Пример работы

1. Ввод: `/start`
2. Имя ребёнка: `Маша`
3. Тема сказки: `про затерянный остров`
4. Бот пришлёт:
   - 📖 Сказку
   - 🖼 Иллюстрацию
   - 🔊 Озвучку

---

## 🤝 Лицензия
MIT
