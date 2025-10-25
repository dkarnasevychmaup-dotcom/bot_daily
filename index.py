from telethon import TelegramClient, events
from datetime import datetime, timedelta, timezone
from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask
import threading, os, asyncio

# === КОНФІГ ===
API_ID = 28285997
API_HASH = "ed9c2749be7b40b4395c6af26c2b6bad"
SESSION = "daily_summary_session"
CHANNEL_ID = -1003188966218  # твій канал

# === ІНІЦІАЛІЗАЦІЯ ===
client = TelegramClient(SESSION, API_ID, API_HASH)
app = Flask(__name__)

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

# === ПІДРАХУНОК ПОВІДОМЛЕНЬ ===
async def count_messages(days=1):
    now = datetime.now(timezone.utc)
    since = now - timedelta(days=days)
    count = 0
    async for msg in client.iter_messages(CHANNEL_ID, limit=5000):
        if msg.date.replace(tzinfo=timezone.utc) < since:
            break
        if msg.message and "надруковано" in msg.message.lower():
            count += 1
    return count

async def send_day_summary():
    count = await count_messages(1)
    now = datetime.now()
    await client.send_message(
        CHANNEL_ID,
        f"📅 {format_date(now)}\n📦 Підсумок дня: {count} відправлень"
    )

async def send_week_summary():
    count = await count_messages(7)
    now = datetime.now()
    start = (now - timedelta(days=6)).strftime("%d %B").replace("October", "жовтня")
    end = now.strftime("%d %B").replace("October", "жовтня")
    await client.send_message(
        CHANNEL_ID,
        f"🗓️ Підсумок тижня, {start} — {end}\nУсього відправок: {count}"
    )

async def send_all_summary():
    count = 0
    async for msg in client.iter_messages(CHANNEL_ID, limit=None):
        if msg.message and "надруковано" in msg.message.lower():
            count += 1
    await client.send_message(
        CHANNEL_ID,
        f"📊 Усього відправлень за весь час: {count}"
    )

# === КОМАНДИ ===
@client.on(events.NewMessage(chats=CHANNEL_ID))
async def command_handler(event):
    text = event.message.message.lower().strip()
    if text == "/check":
        await send_day_summary()
    elif text == "/week":
        await send_week_summary()
    elif text == "/check_all":
        await send_all_summary()

# === ЩОДЕННИЙ РОЗКЛАД ===
scheduler = BackgroundScheduler(timezone="Europe/Kyiv")
scheduler.add_job(lambda: asyncio.run(send_day_summary()), "cron", hour=18, minute=0)
scheduler.add_job(lambda: asyncio.run(send_week_summary()), "cron", day_of_week="fri", hour=18, minute=1)
scheduler.start()

# === KEEP-ALIVE FLASK ===
@app.route("/")
def home():
    return "✅ Userbot активний і працює стабільно."

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# === СТАРТ ===
async def main():
    await client.start()
    print("✅ Userbot активовано...")
    await client.send_message(CHANNEL_ID, "♻️ Бот перезапущено, підключення відновлено")
    await client.run_until_disconnected()

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    asyncio.run(main())
