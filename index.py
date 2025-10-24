from telethon import TelegramClient, events
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta
import asyncio, os, threading
from http.server import SimpleHTTPRequestHandler, HTTPServer

API_ID = 28285997                   # свій з https://my.telegram.org/apps
API_HASH = "ed9c2749be7b40b4395c6af26c2b6bad"  # свій hash
SESSION = "daily_summary_session"    # ім’я сесії
CHANNEL_ID = -1003188966218          # твій канал

# === Ініціалізація клієнта ===
client = TelegramClient(SESSION, API_ID, API_HASH)

# ----------------------------- функції підрахунку -----------------------------
async def count_messages_in_period(days=1):
    """Повертає кількість повідомлень з 'надруковано' за останні N днів."""
    from_time = datetime.now() - timedelta(days=days)
    total = 0
    async for msg in client.iter_messages(CHANNEL_ID, offset_date=None, reverse=False):
        if msg.date < from_time:
            break
        if msg.text and "надруковано" in msg.text.lower():
            total += 1
    return total

async def send_day_summary():
    count = await count_messages_in_period(1)
    now = datetime.now()
    date_str = now.strftime("%d.%m.%Y")
    await client.send_message(CHANNEL_ID, f"📅 {date_str}\n📦 Підсумок дня: {count} відправлень")

async def send_week_summary():
    count = await count_messages_in_period(7)
    now = datetime.now()
    start = (now - timedelta(days=6)).strftime("%d.%m")
    end = now.strftime("%d.%m")
    await client.send_message(CHANNEL_ID, f"🗓️ Підсумок тижня {start}–{end}\n📦 Усього відправок: {count}")

# ----------------------------- обробка команд -----------------------------
@client.on(events.NewMessage(chats=CHANNEL_ID))
async def handler(event):
    text = event.message.message.lower().strip()

    if text == "/check":
        await send_day_summary()
    elif text == "/week":
        await send_week_summary()
    elif text == "/reset_day" or text == "/reset_week":
        await client.send_message(CHANNEL_ID, "ℹ️ Тепер підрахунок виконується динамічно — нічого не потрібно скидати 🙂")

# ----------------------------- планувальник -----------------------------
scheduler = AsyncIOScheduler(timezone="Europe/Kyiv")

# щодня о 18:00
scheduler.add_job(send_day_summary, "cron", hour=18, minute=0)

# щоп’ятниці о 18:01
scheduler.add_job(send_week_summary, "cron", day_of_week="fri", hour=18, minute=1)

# ----------------------------- фейковий HTTP сервер для Render -----------------------------
def run_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), SimpleHTTPRequestHandler)
    print(f"🌐 HTTP сервер запущено на порту {port}")
    server.serve_forever()

threading.Thread(target=run_server, daemon=True).start()

# ----------------------------- запуск -----------------------------
async def main():
    await client.start()
    print("✅ Userbot активовано, чекає на повідомлення...")
    scheduler.start()
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
