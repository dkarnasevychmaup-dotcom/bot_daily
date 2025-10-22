import TelegramBot from "node-telegram-bot-api";
import cron from "node-cron";
import http from "http";

const TOKEN = process.env.BOT_TOKEN;
const GROUP_ID = process.env.GROUP_ID; // куди бот пересилає і рахує
const CHANNEL_ID = process.env.CHANNEL_ID; // звідки бере пости

const bot = new TelegramBot(TOKEN, { polling: true });

let dailyCount = 0;
let weeklyCount = 0;

// === Повідомлення про запуск ===
bot.sendMessage(GROUP_ID, "🔔 Бот запущено і готовий рахувати повідомлення!");

// === Пересилання постів з каналу ===
bot.on("channel_post", async (msg) => {
  if (!msg.text) return;
  try {
    await bot.sendMessage(GROUP_ID, msg.text);
    console.log(`🔁 Переслано пост: "${msg.text}"`);
  } catch (e) {
    console.error("Помилка пересилання:", e.message);
  }
});

// === Обробка повідомлень у групі ===
bot.on("message", (msg) => {
  if (!msg.text) return;
  const text = msg.text.toLowerCase();

  if (text.includes("надруковано")) {
    dailyCount++;
    weeklyCount++;
    console.log(`📥 "${msg.text}" | День: ${dailyCount}, Тиждень: ${weeklyCount}`);
  }

  if (text === "/check") {
    bot.sendMessage(
      msg.chat.id,
      `✅ Бот активний.\n📦 Сьогодні: ${dailyCount} відправлень.\n🗓️ Цього тижня: ${weeklyCount}.`
    );
  }

  if (text === "/reset") {
    dailyCount = 0;
    weeklyCount = 0;
    bot.sendMessage(msg.chat.id, "♻️ Лічильники скинуто вручну.");
    console.log("🔄 Лічильники обнулено вручну.");
  }
});

// === Форматування дати ===
function formatDate(date) {
  return date.toLocaleDateString("uk-UA", {
    day: "2-digit",
    month: "long",
    year: "numeric",
  });
}

// === Розклад: щодня о 18:00 ===
cron.schedule("0 18 * * *", async () => {
  const now = new Date();
  const formattedDate = formatDate(now);

  const dayMessage = `📅 ${formattedDate}\n📦 Підсумок дня: ${dailyCount} відправлень`;
  await bot.sendMessage(GROUP_ID, dayMessage);

  // якщо п'ятниця — також підсумок тижня
  if (now.getDay() === 5) {
    const startOfWeek = new Date(now);
    startOfWeek.setDate(now.getDate() - 4);
    const startStr = startOfWeek.toLocaleDateString("uk-UA", {
      day: "2-digit",
      month: "long",
    });
    const endStr = now.toLocaleDateString("uk-UA", {
      day: "2-digit",
      month: "long",
    });

    const weekMessage = `🗓️ Підсумок тижня, ${startStr} — ${endStr}\nУсього відправок: ${weeklyCount}`;
    await bot.sendMessage(GROUP_ID, weekMessage);

    weeklyCount = 0;
  }

  dailyCount = 0;
});

// === HTTP сервер ===
http
  .createServer((req, res) => {
    res.writeHead(200, { "Content-Type": "text/plain; charset=utf-8" });
    res.end("✅ Bot is running");
  })
  .listen(process.env.PORT || 3000, () => {
    console.log("🌐 HTTP сервер запущено на порту", process.env.PORT || 3000);
  });

console.log("✅ Daily Summary Bot запущено і чекає на повідомлення...");
