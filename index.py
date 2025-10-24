from telethon import TelegramClient, events
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta
import asyncio, os, threading
from http.server import SimpleHTTPRequestHandler, HTTPServer

API_ID = 28285997
API_HASH = "ed9c2749be7b40b4395c6af26c2b6bad"
SESSION = "daily_summary_session"
CHANNEL_ID = -1003188966218

# ----------------------------- форматування дати -----------------------------
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

# ----------------------------- основна логіка -----------------------------
client = TelegramClient(SESSION, API_ID, API_HASH)

async def count_messages(days=1):
    """Підрахунок повідомлень зі словом 'надруковано' за останні N днів"""
    now = datetime.now()
    since = now - timedelta(days=days)
    count = 0
    async for msg in client.iter_messages(CHANNEL_ID, reverse=True):
        if msg.date < since:
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
    start = now - timedelta(days=6)
    start_str = start.strftime("%d %B").replace("October", "жовтня")
    end_str = now.strftime("%d %B").replace("October", "жовтня")
    await client.send_message(
        CHANNEL_ID,
        f"🗓️ Підсумок тижня, {start_str} — {end_str}\nУсього відправок: {count}"
    )

# ----------------------------- обробка команд -----------------------------
@client.on(events.NewMessage(chats=CHANNEL_ID))
async def handler(event):
    text = (event.message.message or "").strip().lower()
    if text == "/check":
        await send_day_summary()
    elif text == "/week":
        await send_week_summary()
    elif text == "/reset_day":
        await client.send_message(CHANNEL_ID, "ℹ️ Історія береться напряму з Telegram — скидати нічого не потрібно 🙂")
    elif text == "/reset_week":
        await client.send_message(CHANNEL_ID, "ℹ️ Історія береться напряму з Telegram — скидати нічого не потрібно 🙂")

# ----------------------------- планувальник -----------------------------
scheduler = AsyncIOScheduler(timezone="Europe/Kyiv")
scheduler.add_job(send_day_summary, "cron", hour=18, minute=0)
scheduler.add_job(send_week_summary, "cron", day_of_week="fri", hour=18, minute=1)

# ----------------------------- фейковий HTTP сервер -----------------------------
def run_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), SimpleHTTPRequestHandler)
    print(f"🌐 HTTP сервер запущено на порту {port}")
    server.serve_forever()

threading.Thread(target=run_server, daemon=True).start()

# ----------------------------- запуск -----------------------------
async def main():
    await client.start()
    print("✅ Userbot активовано, чекає на команди...")
    scheduler.start()
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
