import TelegramBot from 'node-telegram-bot-api';
import cron from 'node-cron';
import http from 'http';

const TOKEN = process.env.BOT_TOKEN;
const CHAT_ID = process.env.CHAT_ID;

const bot = new TelegramBot(TOKEN, { polling: true });

// === Лічильники ===
let dailyCount = 0;
let weeklyCount = 0;

// === Реакція на повідомлення ===
bot.on('message', (msg) => {
  if (!msg.text) return;

  const text = msg.text.toLowerCase();

  // якщо є слово "надруковано"
  if (text.includes('надруковано')) {
    dailyCount++;
    weeklyCount++;
    console.log(`📥 Отримано повідомлення: "${msg.text}" | День: ${dailyCount}, Тиждень: ${weeklyCount}`);
  }

  // команда перевірки
  if (text === '/check') {
    bot.sendMessage(
      msg.chat.id,
      `✅ Бот активний.\n📦 Сьогодні зафіксовано: ${dailyCount} відправлень.\n🗓️ Цього тижня: ${weeklyCount}.`
    );
  }

  // команда ресет
  if (text === '/reset') {
    dailyCount = 0;
    weeklyCount = 0;
    bot.sendMessage(msg.chat.id, '♻️ Лічильники скинуто вручну.');
    console.log('🔄 Лічильники скинуто вручну.');
  }
});

// === Форматування дати ===
function formatDate(date) {
  return date.toLocaleDateString('uk-UA', {
    day: '2-digit',
    month: 'long',
    year: 'numeric',
  });
}

// === Підсумок дня ===
cron.schedule('0 18 * * *', async () => {
  const now = new Date();
  const formattedDate = formatDate(now);

  const dayMessage = `📅 ${formattedDate}\n📦 Підсумок дня: ${dailyCount} відправлень`;
  await bot.sendMessage(CHAT_ID, dayMessage);

  // якщо п’ятниця — відправляємо підсумок тижня
  if (now.getDay() === 5) {
    const startOfWeek = new Date(now);
    startOfWeek.setDate(now.getDate() - 4);
    const startStr = startOfWeek.toLocaleDateString('uk-UA', { day: '2-digit', month: 'long' });
    const endStr = now.toLocaleDateString('uk-UA', { day: '2-digit', month: 'long' });

    const weekMessage = `🗓️ Підсумок тижня, ${startStr} — ${endStr}\nУсього відправок: ${weeklyCount}`;
    await bot.sendMessage(CHAT_ID, weekMessage);

    weeklyCount = 0;
  }

  dailyCount = 0;
});

// === HTTP сервер ===
http
  .createServer((req, res) => {
    res.writeHead(200, { 'Content-Type': 'text/plain; charset=utf-8' });
    res.end('✅ Bot is running');
  })
  .listen(process.env.PORT || 3000, () => {
    console.log('🌐 HTTP сервер запущено на порту', process.env.PORT || 3000);
  });

console.log('✅ Daily Summary Bot запущено і чекає на повідомлення...');
