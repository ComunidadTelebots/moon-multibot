import { api } from 'sdk';
import { commandFromText, helpText, startText } from '../lib/messages.js';
import { getStats, recordMessage, statsText } from '../lib/stats.js';
import { statsKeyboard } from '../lib/ui.js';

export default async function (message) {
  const command = commandFromText(message.text);
  await recordMessage(message, command);

  if (command === 'start') {
    await api.sendMessage({
      chat_id: message.chat.id,
      text: startText(message.from?.first_name),
      reply_markup: statsKeyboard(),
    });
    return;
  }

  if (command === 'help') {
    await api.sendMessage({
      chat_id: message.chat.id,
      text: helpText(),
      reply_markup: statsKeyboard(),
    });
    return;
  }

  if (command === 'stats') {
    const stats = await getStats(message.from?.id);
    await api.sendMessage({
      chat_id: message.chat.id,
      text: statsText(stats),
      reply_markup: statsKeyboard(),
    });
    return;
  }

  await api.sendMessage({
    chat_id: message.chat.id,
    text: 'Mensaje recibido. Usa /help para ver las funciones disponibles.',
    reply_markup: statsKeyboard(),
  });
}
