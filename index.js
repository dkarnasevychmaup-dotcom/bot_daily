import TelegramBot from "node-telegram-bot-api";
import cron from "node-cron";
import http from "http";

const TOKEN = process.env.BOT_TOKEN || "8495715709:AAGgpb8ds9n-hGaQFIZwyXyizUc00-jtk94";
const GROUP_ID = "-1002847487959"; // твоя група
const CHANNEL_ID = process.env.CHANNEL_ID || ""; // опціонально, якщо хочеш обмежити канал

const bot = new TelegramBot(TOKEN, { polling: true });

let dailyCount = 0;
let weeklyCount = 0;

bot.sendMessage(GROUP_ID, "🔔 Бот запущено і готовий рахувати повідомлення!");

// === Пересилання постів із каналу ===
bot.on("channel_post", async (msg) => {
  if (!msg.text) return;
  try {
    // Пересилаємо повідомлення з каналу в групу
    await bot.sendMessage(GROUP_ID, msg.text);
    console.log(`🔁 Переслано пост: "${msg.text}"`);

    // Якщо в тексті є "надруковано", бот зараховує це як відправлення
    if (msg.text.toLowerCase().includes("надруковано")) {
      dailyCount++;
      weeklyCount++;
      console.log(`📥 Зараховано пост із каналу | День: ${dailyCount}, Тиждень: ${weeklyCount}`);
    }

    // Якщо пост містить команду /check або /reset
    if (msg.text.toLowerCase().startsWith("/check")) {
      await bot.sendMessage(
        msg.chat.id,
        `✅ Бот активний.\n📦 Сьогодні: ${dailyCount} відправлень.\n🗓️ Цього тижня: ${weeklyCount}.`
      );
    }

    if (msg.text.toLowerCase().startsWith("/reset")) {
      dailyCount = 0;
      weeklyCount = 0;
      await bot.sendMessage(msg.chat.id, "♻️ Лічильники скинуто вручну.");
      console.log("🔄 Ресет через канал.");
    }
  } catch (e) {
    console.error("Помилка обробки каналу:", e.message);
  }
});

// === Обробка повідомлень у групі ===
bot.on("message", (msg) => {
  if (!msg.text) return;
  const text = msg.text.toLowerCase();

  // Рахує повідомлення "надруковано" навіть від бота
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
