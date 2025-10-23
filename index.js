import TelegramBot from "node-telegram-bot-api";
import cron from "node-cron";
import http from "http";

const TOKEN = process.env.BOT_TOKEN || "8495715709:AAGgpb8ds9n-hGaQFIZwyXyizUc00-jtk94";
const CHANNEL_ID = process.env.CHANNEL_ID || "-1002847487959"; // ← твій канал

if (!TOKEN || !CHANNEL_ID) {
  console.error("❌ Вкажи BOT_TOKEN і CHANNEL_ID у Render Environment Variables!");
  process.exit(1);
}

const bot = new TelegramBot(TOKEN, { polling: true });
console.log("✅ Daily Summary Bot запущено!");

// === Допоміжні функції ===
function formatDate(date) {
  return date.toLocaleDateString("uk-UA", {
    day: "2-digit",
    month: "long",
    year: "numeric",
  });
}

function startOfDay(date) {
  const d = new Date(date);
  d.setHours(0, 0, 0, 0);
  return Math.floor(d.getTime() / 1000);
}

function endOfDay(date) {
  const d = new Date(date);
  d.setHours(23, 59, 59, 999);
  return Math.floor(d.getTime() / 1000);
}

// === Основна функція підрахунку ===
async function countMessagesInChannel(days = 1) {
  try {
    const updates = await bot.getUpdates({ limit: 1000 });
    const now = new Date();

    const fromDate = new Date(now);
    fromDate.setDate(now.getDate() - (days - 1));

    const start = startOfDay(fromDate);
    const end = endOfDay(now);

    const posts = updates
      .map((u) => u.channel_post)
      .filter((p) => p && p.chat && String(p.chat.id) === CHANNEL_ID);

    let count = 0;

    for (const post of posts) {
      if (!post.date) continue;
      if (post.date >= start && post.date <= end) {
        const text = (post.text || post.caption || "").toLowerCase();
        if (text.includes("надруковано")) count++;
      }
    }

    return count;
  } catch (err) {
    console.error("❌ Помилка підрахунку:", err.message);
    return 0;
  }
}

// === Команди каналу ===
bot.on("channel_post", async (msg) => {
  if (!msg.text) return;
  const text = msg.text.toLowerCase();

  if (text === "/check") {
    const todayCount = await countMessagesInChannel(1);
    const formattedDate = formatDate(new Date());
    await bot.sendMessage(
      CHANNEL_ID,
      `📅 ${formattedDate}\n📦 Підсумок дня: ${todayCount} відправлень`
    );
  }

  if (text === "/week") {
    const weekCount = await countMessagesInChannel(7);
    const now = new Date();
    const startOfWeek = new Date(now);
    startOfWeek.setDate(now.getDate() - 6);

    const startStr = startOfWeek.toLocaleDateString("uk-UA", {
      day: "2-digit",
      month: "long",
    });
    const endStr = now.toLocaleDateString("uk-UA", {
      day: "2-digit",
      month: "long",
    });

    await bot.sendMessage(
      CHANNEL_ID,
      `🗓️ Підсумок тижня, ${startStr} — ${endStr}\nУсього відправок: ${weekCount}`
    );
  }
});

// === Автоматичний підсумок щодня о 18:00 (Київ) ===
cron.schedule(
  "0 18 * * *",
  async () => {
    const now = new Date();
    const formattedDate = formatDate(now);

    const todayCount = await countMessagesInChannel(1);

    await bot.sendMessage(
      CHANNEL_ID,
      `📅 ${formattedDate}\n📦 Підсумок дня: ${todayCount} відправлень`
    );

    // якщо п’ятниця — додаємо підсумок тижня
    if (now.getDay() === 5) {
      const weekCount = await countMessagesInChannel(7);
      const startOfWeek = new Date(now);
      startOfWeek.setDate(now.getDate() - 6);

      const startStr = startOfWeek.toLocaleDateString("uk-UA", {
        day: "2-digit",
        month: "long",
      });
      const endStr = now.toLocaleDateString("uk-UA", {
        day: "2-digit",
        month: "long",
      });

      await bot.sendMessage(
        CHANNEL_ID,
        `🗓️ Підсумок тижня, ${startStr} — ${endStr}\nУсього відправок: ${weekCount}`
      );
    }
  },
  { timezone: "Europe/Kyiv" }
);

// === HTTP-сервер для Render ===
http
  .createServer((req, res) => {
    res.writeHead(200, { "Content-Type": "text/plain; charset=utf-8" });
    res.end("✅ Bot is running");
  })
  .listen(process.env.PORT || 3000, () => {
    console.log("🌐 HTTP сервер запущено на порту", process.env.PORT || 3000);
  });
