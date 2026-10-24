import { api } from 'sdk';
import { commandFromText, helpText, startText } from '../lib/messages.js';
import { getStats, recordMessage, statsText } from '../lib/stats.js';
import { isMaster } from '../lib/access.js';
import { groupSettings, recordGroup } from '../lib/groups.js';
import { enforceAntiflood, welcomeMembers } from '../lib/moderation.js';
import { managementKeyboard, masterKeyboard, PUBLIC_URL, statsKeyboard } from '../lib/ui.js';

export default async function (message) {
  const command = commandFromText(message.text);
  await recordGroup(message.chat);
  await recordMessage(message, command);

  if (await welcomeMembers(message)) return;
  if (await enforceAntiflood(message)) return;

  if (command === 'start') {
    await api.sendMessage({
      chat_id: message.chat.id,
      text: startText(message.from?.first_name),
      reply_markup: managementKeyboard(),
    });
    return;
  }

  if (command === 'help') {
    await api.sendMessage({
      chat_id: message.chat.id,
      text: helpText(),
      reply_markup: managementKeyboard(),
    });
    return;
  }

  if (command === 'id') {
    await api.sendMessage({
      chat_id: message.chat.id,
      text: `Tu ID de Telegram es: ${message.from?.id || 'no disponible'}`,
    });
    return;
  }

  if (command === 'panel') {
    await api.sendMessage({
      chat_id: message.chat.id,
      text: 'Abre la Mini App para administrar los grupos donde eres administrador.',
      reply_markup: managementKeyboard(),
    });
    return;
  }

  if (command === 'terms') {
    await api.sendMessage({
      chat_id: message.chat.id,
      text: 'Consulta las condiciones del servicio de TodoSobreAllTech.',
      reply_markup: { inline_keyboard: [[{ text: 'Condiciones del servicio', url: `${PUBLIC_URL}terms.html` }]] },
    });
    return;
  }

  if (command === 'rules' && message.chat?.type !== 'private') {
    const settings = await groupSettings(message.chat.id);
    await api.sendMessage({
      chat_id: message.chat.id,
      text: settings?.rules || 'Este grupo todavía no tiene normas configuradas.',
    });
    return;
  }

  if (command === 'admin') {
    const allowed = await isMaster(message.from?.id);
    await api.sendMessage({
      chat_id: message.chat.id,
      text: allowed ? 'Acceso master autorizado.' : 'Esta cuenta no tiene acceso al panel master.',
      reply_markup: allowed ? masterKeyboard() : undefined,
    });
    return;
  }

  if (command === 'stats') {
    if (!(await isMaster(message.from?.id))) {
      await api.sendMessage({ chat_id: message.chat.id, text: 'Las estadísticas globales son privadas.' });
      return;
    }
    const stats = await getStats(message.from?.id);
    await api.sendMessage({
      chat_id: message.chat.id,
      text: statsText(stats),
      reply_markup: statsKeyboard(),
    });
    return;
  }

  if (message.chat?.type === 'private') {
    await api.sendMessage({
      chat_id: message.chat.id,
      text: 'Mensaje recibido. Usa /help para ver las funciones disponibles.',
      reply_markup: managementKeyboard(),
    });
  }
}
