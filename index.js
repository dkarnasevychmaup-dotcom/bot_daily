const TelegramBot = require('node-telegram-bot-api');
const cron = require('node-cron');

// === 🔑 ВСТАВ СВОЄ ДАНІ ===
const BOT_TOKEN = '8495715709:AAGgpb8ds9n-hGaQFIZwyXyizUc00-jtk94';
const CHAT_ID = '-1003188966218'; // той самий канал або чат, куди ти шлеш логи

const bot = new TelegramBot(BOT_TOKEN, { polling: true });

// Підрахунок кількості повідомлень
let counter = 0;

// Кожного разу, коли бот бачить повідомлення з "Надруковано", додаємо 1
bot.on('message', (msg) => {
  if (!msg.text) return;
  if (msg.text.includes('Надруковано')) {
    counter++;
  }
});

// 🕕 Кожного дня о 18:00 відправляємо підсумок
cron.schedule('0 18 * * *', async () => {
  const message = `📦 Підсумок дня: ${counter} відправлень`;
  await bot.sendMessage(CHAT_ID, message);
  counter = 0; // обнуляємо лічильник
  console.log(`[${new Date().toLocaleTimeString()}] Summary sent: ${message}`);
}, {
  timezone: "Europe/Kyiv"
});

// Перевірка, що бот запущено
console.log('✅ Daily Summary Bot запущено і чекає на повідомлення...');
