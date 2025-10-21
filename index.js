const TelegramBot = require('node-telegram-bot-api');
const cron = require('node-cron');
const http = require('http');

// === 🔐 Змінні середовища (Render → Environment Variables) ===
const BOT_TOKEN = process.env.BOT_TOKEN;
const CHAT_ID = process.env.CHAT_ID;

if (!BOT_TOKEN || !CHAT_ID) {
  console.error("❌ BOT_TOKEN або CHAT_ID не задано у Render Environment Variables!");
  process.exit(1);
}

// === 🤖 Ініціалізація Telegram-бота ===
const bot = new TelegramBot(BOT_TOKEN, { polling: true });

// === 📊 Лічильник відправлень ===
let counter = 0;

// === 🧩 Функція для обробки тексту ===
const handleText = (msg) => {
  if (!msg.text) return;
  const text = msg.text.toLowerCase();
  if (text.includes('надруковано')) {
    counter++;
    console.log(`📥 Отримано повідомлення ("${msg.text}"). Поточна кількість: ${counter}`);
  }
};

// === 📩 Обробка повідомлень із груп, каналів і приватних чатів ===
bot.on('message', handleText);        // групи, чати
bot.on('channel_post', handleText);   // канали

// === 🕕 Кожного дня о 18:00 за Києвом надсилає підсумок ===
cron.schedule('0 18 * * *', async () => {
  const now = new Date();

  // форматування дати українською
  const formattedDate = now.toLocaleDateString('uk-UA', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
    weekday: 'long'
  });

  const message = `📅 ${formattedDate}\n📦 Підсумок дня: ${counter} відправлень`;

  try {
    await bot.sendMessage(CHAT_ID, message);
    console.log(`[${now.toLocaleTimeString()}] ✅ Відправлено підсумок: ${message}`);
  } catch (err) {
    console.error("❌ Помилка надсилання підсумку:", err.message);
  }

  counter = 0; // Скидаємо лічильник після відправлення
}, {
  timezone: "Europe/Kyiv"
});

// === 🩺 HTTP сервер для Render / UptimeRobot ===
http.createServer((req, res) => {
  res.writeHead(200, { 'Content-Type': 'text/plain; charset=utf-8' });
  res.end('✅ Bot is alive');
}).listen(process.env.PORT || 3000, () => {
  console.log('🌐 HTTP сервер запущено на порту', process.env.PORT || 3000);
});

// === ✅ Повідомлення у логах при старті ===
console.log('✅ Daily Summary Bot запущено і чекає на повідомлення...');
