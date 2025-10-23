import TelegramBot from "node-telegram-bot-api";
import cron from "node-cron";
import fs from "fs";
import path from "path";
import http from "http";

const TOKEN = process.env.BOT_TOKEN || "8495715709:AAGgpb8ds9n-hGaQFIZwyXyizUc00-jtk94";
const CHANNEL_ID = process.env.CHANNEL_ID || "-1002847487959"; // ← твій канал

if (!TOKEN || !CHANNEL_ID) {
  console.error("❌ Вкажи BOT_TOKEN і CHANNEL_ID у Render Environment Variables!");
  process.exit(1);
}

const bot = new TelegramBot(TOKEN, { polling: true });
console.log("✅ Daily Summary Bot запущено!");

// === Файл для кешу ===
const DATA_PATH = path.join(process.cwd(), "data.json");

// === Допоміжні функції ===
function loadData() {
  try {
    if (!fs.existsSync(DATA_PATH)) return [];
    const data = JSON.parse(fs.readFileSync(DATA_PATH, "utf8"));
    return Array.isArray(data) ? data : [];
  } catch {
    return [];
  }
}

function saveData(data) {
  fs.writeFileSync(DATA_PATH, JSON.stringify(data, null, 2));
}

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
  return d.getTime();
}

function endOfDay(date) {
  const d = new Date(date);
  d.setHours(23, 59, 59, 999);
  return d.getTime();
}

function cleanupOldEntries() {
  const data = loadData();
  const weekAgo = Date.now() - 7 * 24 * 60 * 60 * 1000;
  const filtered = data.filter((item) => item.timestamp > weekAgo);
  if (filtered.length !== data.length) {
    saveData(filtered);
    console.log("🧹 Очищено старі записи:", data.length - filtered.length);
  }
}

// === Обробка нових постів із каналу ===
bot.on("channel_post", async (msg) => {
  if (!msg.text && !msg.caption) return;

  const text = (msg.text || msg.caption).toLowerCase();

  // Зберігаємо тільки якщо є слово "надруковано"
  if (text.includes("надруковано")) {
    const data = loadData();
    data.push({
      timestamp: Date.now(),
      text: msg.text || msg.caption,
    });
    saveData(data);
    console.log("📥 Нове відправлення збережено. Загалом:", data.length);
  }

  // Команди
  if (text === "/check") {
    const data = loadData();
    const now = new Date();
    const count = data.filter(
      (d) => d.timestamp >= startOfDay(now) && d.timestamp <= endOfDay(now)
    ).length;

    const formattedDate = formatDate(now);
    await bot.sendMessage(
      CHANNEL_ID,
      `📅 ${formattedDate}\n📦 Підсумок дня: ${count} відправлень`
    );
  }

  if (text === "/week") {
    const data = loadData();
    const now = Date.now();
    const weekAgo = now - 7 * 24 * 60 * 60 * 1000;
    const count = data.filter((d) => d.timestamp >= weekAgo).length;

    const end = new Date();
    const start = new Date(weekAgo);
    const startStr = start.toLocaleDateString("uk-UA", {
      day: "2-digit",
      month: "long",
    });
    const endStr = end.toLocaleDateString("uk-UA", {
      day: "2-digit",
      month: "long",
    });

    await bot.sendMessage(
      CHANNEL_ID,
      `🗓️ Підсумок тижня, ${startStr} — ${endStr}\nУсього відправок: ${count}`
    );
  }

  if (text === "/reset_day") {
    const data = loadData();
    const now = new Date();
    const filtered = data.filter((d) => d.timestamp < startOfDay(now));
    saveData(filtered);
    await bot.sendMessage(CHANNEL_ID, "♻️ Денний лічильник очищено.");
  }

  if (text === "/reset_week") {
    saveData([]);
    await bot.sendMessage(CHANNEL_ID, "♻️ Тижневий лічильник очищено.");
  }
});

// === Щоденний підсумок о 18:00 ===
cron.schedule(
  "0 18 * * *",
  async () => {
    cleanupOldEntries();
    const data = loadData();
    const now = new Date();
    const count = data.filter(
      (d) => d.timestamp >= startOfDay(now) && d.timestamp <= endOfDay(now)
    ).length;

    const formattedDate = formatDate(now);
    await bot.sendMessage(
      CHANNEL_ID,
      `📅 ${formattedDate}\n📦 Підсумок дня: ${count} відправлень`
    );

    // Якщо п'ятниця — додаємо тижневий
    if (now.getDay() === 5) {
      const weekAgo = Date.now() - 7 * 24 * 60 * 60 * 1000;
      const weekCount = data.filter((d) => d.timestamp >= weekAgo).length;

      const start = new Date(weekAgo);
      const startStr = start.toLocaleDateString("uk-UA", {
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

// === HTTP сервер для Render ===
http
  .createServer((req, res) => {
    res.writeHead(200, { "Content-Type": "text/plain; charset=utf-8" });
    res.end("✅ Bot is running");
  })
  .listen(process.env.PORT || 3000, () => {
    console.log("🌐 HTTP сервер запущено на порту", process.env.PORT || 3000);
  });
