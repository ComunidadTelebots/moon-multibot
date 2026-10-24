import { api, db, EndpointError } from 'sdk';
import { recentBridgeEvents } from '../lib/bridge.js';
import { getStats } from '../lib/stats.js';

const MOONBOT_CLI_ACTOR_ID = -5724481351;

function requireMoonbot(ctx) {
  const actor = ctx.initData?.user;
  if (actor?.id !== MOONBOT_CLI_ACTOR_ID || actor?.first_name !== 'Moonbot') {
    throw new EndpointError('Acceso administrativo no autorizado.', { code: 'UNAUTHORIZED' });
  }
}

function safeInteger(value, label) {
  const parsed = Number(value);
  if (!Number.isSafeInteger(parsed)) {
    throw new EndpointError(`${label} no válido.`, { code: 'INVALID_ARGUMENT' });
  }
  return parsed;
}

async function saveSetting(key, value) {
  await db.run(
    `INSERT INTO settings (key, value, updated_at) VALUES (:key, :value, unixepoch())
     ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = unixepoch()`,
    { ':key': key, ':value': value },
  );
}

export default async function (input, ctx) {
  requireMoonbot(ctx);
  const action = String(input?.action || 'pull');

  if (action === 'configure') {
    const url = String(input?.url || '').trim();
    const secret = String(input?.secret || '');
    if (!url.startsWith('https://') || secret.length < 32) {
      throw new EndpointError('Configuración del puente no válida.', { code: 'INVALID_BRIDGE' });
    }
    await saveSetting('moon_bridge_url', url.slice(0, 500));
    await saveSetting('moon_bridge_secret', secret.slice(0, 256));
    return JSON.stringify({ configured: true, url });
  }

  if (action === 'pull') {
    return JSON.stringify({
      generatedAt: new Date().toISOString(),
      stats: await getStats(null),
      events: await recentBridgeEvents(input?.after, input?.limit),
    });
  }

  if (action === 'send_message') {
    const chatId = safeInteger(input?.chatId, 'Chat');
    const text = String(input?.text || '').trim().slice(0, 4096);
    if (!text) throw new EndpointError('El mensaje está vacío.', { code: 'EMPTY_MESSAGE' });
    const request = { chat_id: chatId, text };
    if (input?.replyToMessageId) {
      request.reply_parameters = { message_id: safeInteger(input.replyToMessageId, 'Mensaje') };
    }
    const sent = await api.sendMessage(request);
    return JSON.stringify({ ok: true, action, chatId, messageId: sent.message_id });
  }

  if (action === 'delete_message') {
    const chatId = safeInteger(input?.chatId, 'Chat');
    const messageId = safeInteger(input?.messageId, 'Mensaje');
    await api.deleteMessage({ chat_id: chatId, message_id: messageId });
    return JSON.stringify({ ok: true, action, chatId, messageId });
  }

  throw new EndpointError('Acción remota no permitida.', { code: 'ACTION_NOT_ALLOWED' });
}
