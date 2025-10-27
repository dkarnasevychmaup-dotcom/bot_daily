import json
import os
import re
import asyncio
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from flask import Flask
import threading

# === КОНФІГ ===
TOKEN = "8495715709:AAGgpb8ds9n-hGaQFIZwyXyizUc00-jtk94"  # токен з BotFather
GROUP_ID = -1002999914756                                  # твоя група
DATA_FILE = "data.json"                                    # локальний лічильник

bot = Bot(token=TOKEN)
dp = Dispatcher()
scheduler = AsyncIOScheduler(timezone="Europe/Kyiv")

# ---------- зберігання мінімуму даних: тільки message_id + timestamp ----------
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"events": []}  # [{"mid": int, "ts": float}]

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def add_event(message_id: int):
    data = load_data()
    # уникаємо дублів по message_id
    if any(e["mid"] == message_id for e in data["events"]):
        return
    data["events"].append({"mid": message_id, "ts": datetime.now().timestamp()})
    save_data(data)

def filter_events(days: int | None):
    data = load_data()["events"]
    if days is None:
        return data
    since = datetime.now() - timedelta(days=days)
    return [e for e in data if e["ts"] >= since.timestamp()]

def reset_day():
    data = load_data()
    start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    data["events"] = [e for e in data["events"] if e["ts"] < start.timestamp()]
    save_data(data)

def reset_week():
    save_data({"events": []})

# --------------------------- форматування дати ---------------------------
def format_date(date: datetime):
    months = {
        "January": "січня", "February": "лютого", "March": "березня",
        "April": "квітня", "May": "травня", "June": "червня",
        "July": "липня", "August": "серпня", "September": "вересня",
        "October": "жовтня", "November": "листопада", "December": "грудня"
    }
    s = date.strftime("%d %B %Y")
    for en, ua in months.items():
        s = s.replace(en, ua)
    return s

# --------------------------- обробка повідомлень ---------------------------
@dp.message()
async def handle_message(message: types.Message):
    # реагуємо тільки на групу
    if message.chat.id != GROUP_ID:
        return

    text = (message.text or "").strip()

    # ✅ враховує і надруковано, і Надруковано, і з емодзі попереду
    if re.search(r"[✅🟢🔵🟩⬜⬛⚪⚫]*\s*надруковано", text, re.IGNORECASE):
        add_event(message.message_id)
        print(f"📥 Зараховано повідомлення з 'надруковано': {text}")

    lower = text.lower().strip()

    # команди
    if lower == "/check":
        await send_day_summary()
    elif lower == "/week":
        await send_week_summary()
    elif lower == "/check_all":
        await send_total_summary()
    elif lower == "/reset_day":
        reset_day()
        await bot.send_message(GROUP_ID, "♻️ Денний лічильник очищено.")
    elif lower == "/reset_week":
        reset_week()
        await bot.send_message(GROUP_ID, "♻️ Тижневий лічильник очищено.")

# --------------------------- побудова підсумків ---------------------------
async def send_day_summary():
    cnt = len(filter_events(1))
    now = datetime.now()
    await bot.send_message(GROUP_ID, f"📅 {format_date(now)}\n📦 Підсумок дня: {cnt} відправлень")

async def send_week_summary():
    cnt = len(filter_events(7))
    now = datetime.now()
    start = now - timedelta(days=6)
    start_str = start.strftime("%d %B").replace("October", "жовтня")
    end_str = now.strftime("%d %B").replace("October", "жовтня")
    await bot.send_message(GROUP_ID, f"🗓️ Підсумок тижня, {start_str} — {end_str}\nУсього відправок: {cnt}")

async def send_total_summary():
    cnt = len(filter_events(None))
    await bot.send_message(GROUP_ID, f"📊 Усього відправлень за весь час: {cnt}")

# --------------------------- розклад ---------------------------
scheduler.add_job(send_day_summary, "cron", hour=18, minute=0)                 # щодня 18:00
scheduler.add_job(send_week_summary, "cron", day_of_week="fri", hour=18, minute=1)  # п’ятниця 18:01

# --------------------------- http-сервер для Render ---------------------------
app = Flask(__name__)

@app.route("/")
def index():
    return "✅ Bot is running", 200

def run_server():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# --------------------------- запуск ---------------------------
async def main():
    scheduler.start()
    threading.Thread(target=run_server, daemon=True).start()
    print("✅ Бот активований і чекає на повідомлення...")
    # раз на старт — маркер у групу (необов’язково)
    try:
        await bot.send_message(GROUP_ID, "♻️ Бот перезапущено, підключення відновлено")
    except Exception as e:
        print("⚠️ Не вдалось надіслати стартове повідомлення:", e)
    # запуск поллінгу
    from aiogram import F
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
