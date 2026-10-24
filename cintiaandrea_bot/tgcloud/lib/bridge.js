import { db, fetch } from 'sdk';
import { getStats } from './stats.js';

const BOT_ID = 'cintiaandrea';

async function bridgeSetting(key) {
  const row = await db.get(`SELECT value FROM settings WHERE key = :key`, { ':key': key });
  return String(row?.value || '');
}

export async function recordBridgeMessage(message, updateId) {
  if (!message?.chat?.id) return null;
  const senderName = [message.from?.first_name, message.from?.last_name].filter(Boolean).join(' ');
  const body = String(message.text || message.caption || '').slice(0, 2000);
  const result = await db.run(
    `INSERT INTO bridge_events (
       update_id, kind, telegram_id, chat_id, message_id, chat_title,
       sender_name, body, created_at
     ) VALUES (
       :update_id, 'message', :telegram_id, :chat_id, :message_id,
       :chat_title, :sender_name, :body, unixepoch()
     )`,
    {
      ':update_id': updateId || null,
      ':telegram_id': message.from?.id || null,
      ':chat_id': message.chat.id,
      ':message_id': message.message_id || null,
      ':chat_title': String(message.chat.title || message.chat.username || 'Chat privado').slice(0, 255),
      ':sender_name': String(senderName || message.from?.username || 'Usuario').slice(0, 255),
      ':body': body,
    },
  );
  await db.run(`DELETE FROM bridge_events WHERE created_at < unixepoch('now', '-7 days')`);
  await db.run(`
    DELETE FROM bridge_events
    WHERE id NOT IN (SELECT id FROM bridge_events ORDER BY id DESC LIMIT 5000)
  `);
  return {
    id: result?.lastInsertRowid || null,
    kind: 'message',
    telegramId: message.from?.id || null,
    chatId: message.chat.id,
    messageId: message.message_id || null,
    chatTitle: String(message.chat.title || message.chat.username || 'Chat privado').slice(0, 255),
    senderName: String(senderName || message.from?.username || 'Usuario').slice(0, 255),
    body,
    createdAt: Math.floor(Date.now() / 1000),
  };
}

export async function pushBridgeEvent(event) {
  if (!event) return false;
  const url = await bridgeSetting('moon_bridge_url');
  const secret = await bridgeSetting('moon_bridge_secret');
  if (!url || !secret) return false;
  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${secret}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        botId: BOT_ID,
        generatedAt: new Date().toISOString(),
        event,
        stats: await getStats(null),
      }),
    });
    return response.ok;
  } catch (error) {
    console.warn('Moonbot bridge delivery failed', error?.message || error);
    return false;
  }
}

export async function recentBridgeEvents(after = 0, limit = 40) {
  const safeAfter = Number.isSafeInteger(Number(after)) ? Number(after) : 0;
  const safeLimit = Math.max(1, Math.min(Number(limit) || 40, 100));
  return db.all(
    `SELECT id, update_id, kind, telegram_id, chat_id, message_id,
            chat_title, sender_name, body, created_at
     FROM bridge_events
     WHERE id > :after
     ORDER BY id DESC
     LIMIT :limit`,
    { ':after': safeAfter, ':limit': safeLimit },
  );
}
