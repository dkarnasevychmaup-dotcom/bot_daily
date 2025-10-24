from telethon import TelegramClient, events
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta, timezone
import asyncio
import pytz

API_ID = 28285997
API_HASH = "ed9c2749be7b40b4395c6af26c2b6bad"
SESSION = "daily_summary_session"
CHANNEL_ID = -1003188966218  # ID каналу

# Часовий пояс Києва
kyiv_tz = pytz.timezone("Europe/Kyiv")

client = TelegramClient(SESSION, API_ID, API_HASH)

# ----------------- функція для підрахунку -----------------
async def count_messages(days):
    """Підрахунок повідомлень з текстом 'надруковано' за останні days днів."""
    now = datetime.now(kyiv_tz)
    since = now - timedelta(days=days)
    count = 0

    async for msg in client.iter_messages(CHANNEL_ID, search="надруковано"):
        msg_time = msg.date.replace(tzinfo=timezone.utc).astimezone(kyiv_tz)
        if msg_time >= since:
            count += 1

    return count

# ----------------- команди -----------------
@client.on(events.NewMessage(chats=CHANNEL_ID))
async def handler(event):
    text = event.message.message.strip().lower()

    if text == "/check":
        count = await count_messages(1)
        date_str = datetime.now(kyiv_tz).strftime("%d %B %Y").replace("October", "жовтня")
        await client.send_message(
            CHANNEL_ID,
            f"📅 {date_str}\n📦 Підсумок дня: {count} відправлень"
        )

    elif text == "/week":
        count = await count_messages(7)
        now = datetime.now(kyiv_tz)
        start = (now - timedelta(days=6)).strftime("%d %B").replace("October", "жовтня")
        end = now.strftime("%d %B").replace("October", "жовтня")
        await client.send_message(
            CHANNEL_ID,
            f"🗓️ Підсумок тижня, {start} — {end}\nУсього відправок: {count}"
        )

    elif text == "/check_all":
        count = await count_messages(9999)
        await client.send_message(CHANNEL_ID, f"📦 Усього відправлень за весь час: {count}")

# ----------------- щоденний і тижневий підсумок -----------------
async def send_day_summary():
    count = await count_messages(1)
    now = datetime.now(kyiv_tz)
    date_str = now.strftime("%d %B %Y").replace("October", "жовтня")
    await client.send_message(CHANNEL_ID, f"📅 {date_str}\n📦 Підсумок дня: {count} відправлень")

async def send_week_summary():
    count = await count_messages(7)
    now = datetime.now(kyiv_tz)
    start = (now - timedelta(days=6)).strftime("%d %B").replace("October", "жовтня")
    end = now.strftime("%d %B").replace("October", "жовтня")
    await client.send_message(CHANNEL_ID, f"🗓️ Підсумок тижня, {start} — {end}\nУсього відправок: {count}")

# ----------------- планувальник -----------------
scheduler = AsyncIOScheduler(timezone="Europe/Kyiv")
scheduler.add_job(send_day_summary, "cron", hour=18, minute=0)
scheduler.add_job(send_week_summary, "cron", day_of_week="fri", hour=18, minute=1)

# ----------------- запуск -----------------
async def main():
    await client.start()
    print("✅ Userbot активовано, чекає на повідомлення...")
    scheduler.start()
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
