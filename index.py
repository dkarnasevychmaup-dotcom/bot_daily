import json
import os
import asyncio
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# === КОНФІГ ===
TOKEN = "8495715709:AAGgpb8ds9n-hGaQFIZwyXyizUc00-jtk94"  # твій токен
GROUP_ID = -1002999914756  # твоя група
DATA_FILE = "data.json"

bot = Bot(token=TOKEN)
dp = Dispatcher()
scheduler = AsyncIOScheduler(timezone="Europe/Kyiv")

# === ФУНКЦІЇ ДАНИХ ===
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def add_entry(text):
    data = load_data()
    data.append({"ts": datetime.now().timestamp(), "text": text})
    save_data(data)

def filter_data(days):
    data = load_data()
    since = datetime.now() - timedelta(days=days)
    return [d for d in data if d["ts"] >= since.timestamp()]

def reset_day():
    data = load_data()
    start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    filtered = [d for d in data if d["ts"] < start.timestamp()]
    save_data(filtered)

def reset_week():
    save_data([])

# === ФОРМАТ ДАТИ ===
def format_date(date):
    months = {
        "January": "січня", "February": "лютого", "March": "березня",
        "April": "квітня", "May": "травня", "June": "червня",
        "July": "липня", "August": "серпня", "September": "вересня",
        "October": "жовтня", "November": "листопада", "December": "грудня"
    }
    eng = date.strftime("%d %B %Y")
    for en, ua in months.items():
        eng = eng.replace(en, ua)
    return eng

# === ОБРОБКА ПОВІДОМЛЕНЬ ===
@dp.message()
async def handle_message(message: types.Message):
    if not message.text:
        return
    text = message.text.lower()

    # Якщо є "надруковано" — зберігаємо
    if "надруковано" in text:
        add_entry(message.text)
        print(f"📥 Додано: {message.text}")

    # Команди
    if text.strip() == "/check":
        await send_day_summary()
    elif text.strip() == "/week":
        await send_week_summary()
    elif text.strip() == "/check_all":
        await send_total_summary()
    elif text.strip() == "/reset_day":
        reset_day()
        await bot.send_message(GROUP_ID, "♻️ Денний лічильник очищено.")
    elif text.strip() == "/reset_week":
        reset_week()
        await bot.send_message(GROUP_ID, "♻️ Тижневий лічильник очищено.")

# === ПІДСУМКИ ===
async def send_day_summary():
    data = filter_data(1)
    count = len(data)
    now = datetime.now()
    await bot.send_message(GROUP_ID, f"📅 {format_date(now)}\n📦 Підсумок дня: {count} відправлень")

async def send_week_summary():
    data = filter_data(7)
    count = len(data)
    now = datetime.now()
    start = now - timedelta(days=6)
    start_str = start.strftime("%d %B").replace("October", "жовтня")
    end_str = now.strftime("%d %B").replace("October", "жовтня")
    await bot.send_message(GROUP_ID, f"🗓️ Підсумок тижня, {start_str} — {end_str}\nУсього відправок: {count}")

async def send_total_summary():
    data = load_data()
    count = len(data)
    await bot.send_message(GROUP_ID, f"📊 Усього відправлень за весь час: {count}")

# === АВТОМАТИЧНІ ЗАПУСКИ ===
scheduler.add_job(send_day_summary, "cron", hour=18, minute=0)
scheduler.add_job(send_week_summary, "cron", day_of_week="fri", hour=18, minute=1)

# === HTTP SERVER (для Render) ===
from flask import Flask
import threading

app = Flask(__name__)

@app.route('/')
def index():
    return "✅ Bot is running", 200

def run_server():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# === ЗАПУСК ===
async def main():
    scheduler.start()
    threading.Thread(target=run_server, daemon=True).start()
    print("✅ Бот активований і чекає на повідомлення...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
