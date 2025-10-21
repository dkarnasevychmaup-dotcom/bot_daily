const TelegramBot = require('node-telegram-bot-api');
const cron = require('node-cron');

// === 🔐 Отримання даних із змінних середовища Render ===
const BOT_TOKEN = process.env.BOT_TOKEN;
const CHAT_ID = process.env.CHAT_ID;

if (!BOT_TOKEN || !CHAT_ID) {
  console.error("❌ Помилка: BOT_TOKEN або CHAT_ID не задано у Render Environment Variables!");
  process.exit(1);
}

// === 🤖 Ініціалізація Telegram-бота ===
const bot = new TelegramBot(BOT_TOKEN, { polling: true });

let counter = 0;

// === 📩 Лічильник повідомлень із ключовим словом ===
bot.on('message', (msg) => {
  if (!msg.text) return;
  if (msg.text.includes('Надруковано')) {
    counter++;
    console.log(`📥 Отримано повідомлення, загалом: ${counter}`);
  }
});

// === 🕕 Підсумок дня щодня о 18:00 (за Києвом) ===
cron.schedule('0 18 * * *', async () => {
  const message = `📦 Підсумок дня: ${counter} відправлень`;
  try {
    await bot.sendMessage(CHAT_ID, message);
    console.log(`[${new Date().toLocaleTimeString()}] ✅ Відправлено: ${message}`);
  } catch (err) {
    console.error("❌ Помилка надсилання:", err.message);
  }
  counter = 0;
}, {
  timezone: "Europe/Kyiv"
});

// === ✅ Статус при запуску ===
console.log('✅ Daily Summary Bot запущено і чекає на повідомлення...');
