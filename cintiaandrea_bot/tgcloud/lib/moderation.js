import { api, db } from 'sdk';
import { groupSettings } from './groups.js';

export async function welcomeMembers(message) {
  if (!message.new_chat_members?.length) return false;
  const settings = await groupSettings(message.chat.id);
  if (!settings?.welcome_enabled) return true;
  const names = message.new_chat_members.map((member) => member.first_name || 'nuevo miembro').join(', ');
  await api.sendMessage({
    chat_id: message.chat.id,
    text: `Bienvenido, ${names}. Usa /rules para consultar las normas del grupo.`,
  });
  return true;
}

export async function enforceAntiflood(message) {
  if (!message.from?.id || message.chat?.type === 'private') return false;
  const settings = await groupSettings(message.chat.id);
  if (!settings?.antiflood_enabled) return false;
  const recent = await db.get(
    `SELECT COUNT(*) AS total FROM events
     WHERE chat_id = :chat_id AND telegram_id = :telegram_id
       AND created_at >= unixepoch('now', '-8 seconds')`,
    { ':chat_id': message.chat.id, ':telegram_id': message.from.id },
  );
  if (Number(recent?.total || 0) < 6) return false;
  try {
    await api.deleteMessage({ chat_id: message.chat.id, message_id: message.message_id });
    await api.sendMessage({ chat_id: message.chat.id, text: 'Mensaje retirado por exceso de actividad. Espera unos segundos.' });
  } catch (_error) {
    // El bot puede no tener permiso para borrar; no interrumpimos el handler.
  }
  return true;
}
