from telethon import TelegramClient, events
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta
import asyncio, json, os

API_ID = 28285997                   # свій з https://my.telegram.org/apps
API_HASH = "ed9c2749be7b40b4395c6af26c2b6bad"  # свій hash
SESSION = "daily_summary_session"    # ім’я сесії
CHANNEL_ID = "-1003188966218"          # твій канал
DATA_FILE = "data.json"

# ----------------------------- допоміжні функції -----------------------------
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def cleanup_old():
    data = load_data()
    week_ago = datetime.now() - timedelta(days=7)
    filtered = [d for d in data if d["ts"] > week_ago.timestamp()]
    if len(filtered) != len(data):
        save_data(filtered)
        print(f"🧹 Очистив {len(data)-len(filtered)} старих записів")

def format_date(date):
    return date.strftime("%d %B %Y").replace("January","січня").replace("February","лютого")\
        .replace("March","березня").replace("April","квітня").replace("May","травня")\
        .replace("June","червня").replace("July","липня").replace("August","серпня")\
        .replace("September","вересня").replace("October","жовтня").replace("November","листопада")\
        .replace("December","грудня")

# ----------------------------- основна логіка -----------------------------
client = TelegramClient(SESSION, API_ID, API_HASH)

@client.on(events.NewMessage(chats=CHANNEL_ID))
async def handler(event):
    text = event.message.message.lower()
    if "надруковано" in text:
        data = load_data()
        data.append({"ts": datetime.now().timestamp(), "text": event.message.message})
        save_data(data)
        print("📥 Нове повідомлення збережено")

    # ---- команди ----
    if text.strip() == "/check":
        await send_day_summary()
    elif text.strip() == "/week":
        await send_week_summary()
    elif text.strip() == "/reset_day":
        reset_day()
        await client.send_message(CHANNEL_ID, "♻️ Денний лічильник очищено.")
    elif text.strip() == "/reset_week":
        save_data([])
        await client.send_message(CHANNEL_ID, "♻️ Тижневий лічильник очищено.")

# ----------------------------- підрахунок -----------------------------
async def send_day_summary():
    data = load_data()
    now = datetime.now()
    start = datetime(now.year, now.month, now.day)
    end = start + timedelta(days=1)
    count = len([d for d in data if start.timestamp() <= d["ts"] < end.timestamp()])
    await client.send_message(CHANNEL_ID, f"📅 {format_date(now)}\n📦 Підсумок дня: {count} відправлень")

async def send_week_summary():
    data = load_data()
    now = datetime.now()
    start = now - timedelta(days=6)
    count = len([d for d in data if d["ts"] >= start.timestamp()])
    start_str = start.strftime("%d %B").replace("October","жовтня") # для прикладу
    end_str = now.strftime("%d %B").replace("October","жовтня")
    await client.send_message(CHANNEL_ID, f"🗓️ Підсумок тижня, {start_str} — {end_str}\nУсього відправок: {count}")

def reset_day():
    data = load_data()
    now = datetime.now()
    start = datetime(now.year, now.month, now.day)
    filtered = [d for d in data if d["ts"] < start.timestamp()]
    save_data(filtered)

# ----------------------------- планувальник -----------------------------
scheduler = AsyncIOScheduler(timezone="Europe/Kyiv")
scheduler.add_job(cleanup_old, "interval", hours=12)

# Щодня о 18:00
scheduler.add_job(send_day_summary, "cron", hour=18, minute=0)

# Щоп’ятниці одразу після денного
scheduler.add_job(send_week_summary, "cron", day_of_week="fri", hour=18, minute=1)
scheduler.start()

# ----------------------------- запуск -----------------------------
async def main():
    await client.start()
    print("✅ Userbot активовано, чекає на повідомлення...")
    await client.run_until_disconnected()

asyncio.run(main())
