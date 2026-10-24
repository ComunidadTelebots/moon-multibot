import { db } from 'sdk';

export async function recordMessage(message, command) {
  const user = message.from;
  if (!user?.id || !message.chat?.id) return;

  await db.run(
    `INSERT INTO users (
       telegram_id, username, first_name, language_code,
       messages, commands, callbacks, first_seen_at, last_seen_at
     ) VALUES (
       :telegram_id, :username, :first_name, :language_code,
       1, :command_increment, 0, unixepoch(), unixepoch()
     )
     ON CONFLICT(telegram_id) DO UPDATE SET
       username = excluded.username,
       first_name = excluded.first_name,
       language_code = excluded.language_code,
       messages = users.messages + 1,
       commands = users.commands + excluded.commands,
       last_seen_at = unixepoch()`,
    {
      ':telegram_id': user.id,
      ':username': user.username || null,
      ':first_name': user.first_name || null,
      ':language_code': user.language_code || null,
      ':command_increment': command ? 1 : 0,
    },
  );

  await db.run(
    `INSERT INTO events (telegram_id, chat_id, kind, command, created_at)
     VALUES (:telegram_id, :chat_id, 'message', :command, unixepoch())`,
    {
      ':telegram_id': user.id,
      ':chat_id': message.chat.id,
      ':command': command,
    },
  );
}

export async function recordCallback(query) {
  if (!query.from?.id || !query.message?.chat?.id) return;
  await db.run(
    `UPDATE users
     SET callbacks = callbacks + 1, last_seen_at = unixepoch()
     WHERE telegram_id = :telegram_id`,
    { ':telegram_id': query.from.id },
  );
  await db.run(
    `INSERT INTO events (telegram_id, chat_id, kind, command, created_at)
     VALUES (:telegram_id, :chat_id, 'callback', :command, unixepoch())`,
    {
      ':telegram_id': query.from.id,
      ':chat_id': query.message.chat.id,
      ':command': query.data || null,
    },
  );
}

export async function getStats(telegramId) {
  const totals = await db.get(`
    SELECT
      COUNT(*) AS users,
      COALESCE(SUM(messages), 0) AS messages,
      COALESCE(SUM(commands), 0) AS commands,
      COALESCE(SUM(callbacks), 0) AS callbacks
    FROM users
  `);
  const personal = telegramId
    ? await db.get(
      `SELECT messages, commands, callbacks, first_seen_at, last_seen_at
       FROM users WHERE telegram_id = :telegram_id`,
      { ':telegram_id': telegramId },
    )
    : null;
  const daily = await db.all(`
    SELECT
      strftime('%Y-%m-%d', created_at, 'unixepoch') AS day,
      COUNT(*) AS events,
      COUNT(DISTINCT telegram_id) AS users
    FROM events
    WHERE created_at >= unixepoch('now', '-6 days', 'start of day')
    GROUP BY day
    ORDER BY day ASC
  `);
  const recent = await db.get(`
    SELECT
      COUNT(*) AS events_24h,
      COUNT(DISTINCT telegram_id) AS active_users_24h,
      MAX(created_at) AS last_event_at
    FROM events
    WHERE created_at >= unixepoch('now', '-1 day')
  `);
  const topCommands = await db.all(`
    SELECT command, COUNT(*) AS uses
    FROM events
    WHERE command IS NOT NULL AND command != ''
    GROUP BY command
    ORDER BY uses DESC, command ASC
    LIMIT 5
  `);
  return {
    totals: totals || {},
    personal: personal || {},
    daily: daily || [],
    recent: recent || {},
    topCommands: topCommands || [],
  };
}

export function statsText(stats) {
  const totals = stats?.totals || {};
  const personal = stats?.personal || {};
  return [
    'Estadisticas de Cintia Andrea',
    '',
    `Usuarios: ${Number(totals.users || 0)}`,
    `Mensajes: ${Number(totals.messages || 0)}`,
    `Comandos: ${Number(totals.commands || 0)}`,
    `Interacciones: ${Number(totals.callbacks || 0)}`,
    '',
    `Tus mensajes: ${Number(personal.messages || 0)}`,
  ].join('\n');
}
