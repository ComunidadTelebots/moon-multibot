import { api } from 'sdk';
import { getStats, recordCallback, statsText } from '../lib/stats.js';
import { isMaster } from '../lib/access.js';
import { statsKeyboard } from '../lib/ui.js';

export default async function (query) {
  await recordCallback(query);

  if (query.data !== 'refresh_stats' || !query.message) {
    await api.answerCallbackQuery({ callback_query_id: query.id });
    return;
  }

  if (!(await isMaster(query.from.id))) {
    await api.answerCallbackQuery({ callback_query_id: query.id, text: 'Acceso master requerido', show_alert: true });
    return;
  }

  const stats = await getStats(query.from.id);
  await api.editMessageText({
    chat_id: query.message.chat.id,
    message_id: query.message.message_id,
    text: statsText(stats),
    reply_markup: statsKeyboard(),
  });
  await api.answerCallbackQuery({
    callback_query_id: query.id,
    text: 'Estadisticas actualizadas',
  });
}
