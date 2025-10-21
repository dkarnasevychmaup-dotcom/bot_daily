const TelegramBot = require('node-telegram-bot-api');
const cron = require('node-cron');
const http = require('http');

// === 🔐 Отримання даних із середовища (Render → Environment Variables) ===
const BOT_TOKEN = process.env.BOT_TOKEN;
const CHAT_ID = process.env.CHAT_ID;

if (!BOT_TOKEN || !CHAT_ID) {
  console.error("❌ Помилка: BOT_TOKEN або CHAT_ID не задано у Render Environment Variables!");
  process.exit(1);
}

// === 🤖 Ініціалізація Telegram-бота ===
const bot = new TelegramBot(BOT_TOKEN, { polling: true });

// === 📊 Лічильник відправлень ===
let counter = 0;

// === 🧩 Функція для обробки тексту з груп, каналів і приватних чатів ===
const handleText = (msg) => {
  if (!msg.text) return;
  const text = msg.text.toLowerCase();

  if (text.includes('надруковано')) {
    counter++;
    console.log(`📥 Отримано повідомлення ("${msg.text}"). Поточна кількість: ${counter}`);
  }
};

// === 📩 Слухачі для різних типів повідомлень ===
// Групи та приватні чати
bot.on('message', handleText);

// Канали (тип події інший!)
bot.on('channel_post', handleText);

// === 🕕 Кожного дня о 18:00 надсилає підсумок ===
cron.schedule('0 18 * * *', async () => {
  const message = `📦 Підсумок дня: ${counter} відправлень`;
  try {
    await bot.sendMessage(CHAT_ID, message);
    console.log(`[${new Date().toLocaleTimeString()}] ✅ Відправлено підсумок: ${message}`);
  } catch (err) {
    console.error("❌ Помилка надсилання підсумку:", err.message);
  }
  counter = 0; // Скидаємо лічильник
}, {
  timezone: "Europe/Kyiv"
});

// === 🩺 HTTP сервер для Render / UptimeRobot ===
http.createServer((req, res) => {
  res.writeHead(200, { 'Content-Type': 'text/plain' });
  res.end('✅ Bot is alive');
}).listen(process.env.PORT || 3000, () => {
  console.log('🌐 HTTP сервер запущено на порту', process.env.PORT || 3000);
});

// === ✅ Повідомлення у логах при старті ===
console.log('✅ Daily Summary Bot запущено і чекає на повідомлення...');
