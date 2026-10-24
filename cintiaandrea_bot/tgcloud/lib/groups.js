import { api, db, EndpointError } from 'sdk';

const DEFAULT_RULES = 'Respeta a los demás miembros y evita el spam.';

export async function recordGroup(chat, status = 'active') {
  if (!chat?.id || chat.type === 'private') return;
  await db.run(
    `INSERT INTO groups (
       chat_id, title, username, type, status, welcome_enabled,
       antiflood_enabled, rules, updated_at, last_seen_at
     ) VALUES (
       :chat_id, :title, :username, :type, :status, 1, 0, :rules,
       unixepoch(), unixepoch()
     )
     ON CONFLICT(chat_id) DO UPDATE SET
       title = excluded.title,
       username = excluded.username,
       type = excluded.type,
       status = excluded.status,
       last_seen_at = unixepoch()`,
    {
      ':chat_id': chat.id,
      ':title': String(chat.title || 'Grupo de Telegram').slice(0, 255),
      ':username': chat.username || null,
      ':type': chat.type || 'group',
      ':status': status,
      ':rules': DEFAULT_RULES,
    },
  );
}

async function isGroupAdmin(chatId, userId) {
  try {
    const member = await api.getChatMember({ chat_id: chatId, user_id: userId });
    return member?.status === 'creator' || member?.status === 'administrator';
  } catch (_error) {
    return false;
  }
}

export async function listAdminGroups(userId) {
  const rows = await db.all(`
    SELECT chat_id, title, username, type, welcome_enabled,
           antiflood_enabled, rules, updated_at, last_seen_at
    FROM groups
    WHERE status = 'active'
    ORDER BY last_seen_at DESC
    LIMIT 100
  `);
  const allowed = [];
  for (const row of rows || []) {
    if (await isGroupAdmin(row.chat_id, userId)) {
      allowed.push({
        chatId: row.chat_id,
        title: row.title,
        username: row.username || '',
        type: row.type,
        welcomeEnabled: Boolean(row.welcome_enabled),
        antifloodEnabled: Boolean(row.antiflood_enabled),
        rules: row.rules || DEFAULT_RULES,
        updatedAt: row.updated_at,
        lastSeenAt: row.last_seen_at,
      });
    }
  }
  return allowed;
}

export async function updateGroup(userId, input) {
  const chatId = Number(input?.chatId);
  if (!Number.isSafeInteger(chatId)) {
    throw new EndpointError('Grupo no válido.', { code: 'INVALID_GROUP' });
  }
  const group = await db.get(`SELECT chat_id FROM groups WHERE chat_id = :chat_id AND status = 'active'`, {
    ':chat_id': chatId,
  });
  if (!group || !(await isGroupAdmin(chatId, userId))) {
    throw new EndpointError('No administras este grupo.', { code: 'GROUP_ADMIN_REQUIRED' });
  }
  const rules = String(input?.rules || '').trim().slice(0, 1000) || DEFAULT_RULES;
  await db.run(
    `UPDATE groups SET
       welcome_enabled = :welcome_enabled,
       antiflood_enabled = :antiflood_enabled,
       rules = :rules,
       updated_by = :updated_by,
       updated_at = unixepoch()
     WHERE chat_id = :chat_id`,
    {
      ':welcome_enabled': input?.welcomeEnabled ? 1 : 0,
      ':antiflood_enabled': input?.antifloodEnabled ? 1 : 0,
      ':rules': rules,
      ':updated_by': userId,
      ':chat_id': chatId,
    },
  );
  return { chatId, welcomeEnabled: Boolean(input?.welcomeEnabled), antifloodEnabled: Boolean(input?.antifloodEnabled), rules };
}

export async function groupSettings(chatId) {
  return db.get(`
    SELECT welcome_enabled, antiflood_enabled, rules
    FROM groups WHERE chat_id = :chat_id AND status = 'active'
  `, { ':chat_id': chatId });
}
