from telethon import TelegramClient, events
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta, timezone
import asyncio, os, pytz, threading
from http.server import SimpleHTTPRequestHandler, HTTPServer

# ----------------------------- Налаштування -----------------------------
API_ID = 28285997
API_HASH = "ed9c2749be7b40b4395c6af26c2b6bad"
SESSION = "daily_summary_session"
CHANNEL_ID = -1003188966218  # ID твого каналу
kyiv_tz = pytz.timezone("Europe/Kyiv")

client = TelegramClient(SESSION, API_ID, API_HASH)

# ----------------------------- Підрахунок повідомлень -----------------------------
async def count_messages(days=None):
    """Підрахунок повідомлень з 'надруковано' за останні N днів або за весь час."""
    now = datetime.now(kyiv_tz)
    since = now - timedelta(days=days) if days else None
    count = 0

    async for msg in client.iter_messages(CHANNEL_ID, search="надруковано"):
        msg_time = msg.date.replace(tzinfo=timezone.utc).astimezone(kyiv_tz)
        if since and msg_time < since:
            break
        count += 1
    return count

# ----------------------------- Форматування дати -----------------------------
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

# ----------------------------- Надсилання підсумків -----------------------------
async def send_day_summary():
    count = await count_messages(1)
    now = datetime.now(kyiv_tz)
    await client.send_message(CHANNEL_ID, f"📅 {format_date(now)}\n📦 Підсумок дня: {count} відправлень")

async def send_week_summary():
    count = await count_messages(7)
    now = datetime.now(kyiv_tz)
    start = now - timedelta(days=6)
    start_str = start.strftime("%d %B").replace("October", "жовтня")
    end_str = now.strftime("%d %B").replace("October", "жовтня")
    await client.send_message(CHANNEL_ID, f"🗓️ Підсумок тижня, {start_str} — {end_str}\nУсього відправок: {count}")

async def send_all_summary():
    count = await count_messages(None)
    await client.send_message(CHANNEL_ID, f"📊 Усього повідомлень з 'надруковано' за весь час: {count}")

# ----------------------------- Обробка команд -----------------------------
@client.on(events.NewMessage())
async def handler(event):
    if event.chat_id != CHANNEL_ID:
        return
    text = (event.message.message or "").strip().lower()

    if text == "/check":
        await send_day_summary()
    elif text == "/week":
        await send_week_summary()
    elif text == "/check_all":
        await send_all_summary()
    elif text in ["/reset_day", "/reset_week"]:
        await client.send_message(CHANNEL_ID, "ℹ️ Історія береться напряму з Telegram — скидати нічого не потрібно 🙂")

# ----------------------------- Планувальник -----------------------------
scheduler = AsyncIOScheduler(timezone="Europe/Kyiv")
scheduler.add_job(send_day_summary, "cron", hour=18, minute=0)           # кожного дня о 18:00
scheduler.add_job(send_week_summary, "cron", day_of_week="fri", hour=18, minute=1)  # щоп’ятниці о 18:01

# ----------------------------- HTTP сервер для Render -----------------------------
def run_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), SimpleHTTPRequestHandler)
    print(f"🌐 HTTP сервер запущено на порту {port}")
    server.serve_forever()

threading.Thread(target=run_server, daemon=True).start()

# ----------------------------- Запуск -----------------------------
async def main():
    await client.start()
    print("✅ Userbot активовано, чекає на команди...")
    scheduler.start()
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
