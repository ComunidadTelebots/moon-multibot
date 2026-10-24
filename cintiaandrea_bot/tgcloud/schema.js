import { table, integer, text, index, sql } from 'sdk/db';

export const users = table('users', {
  telegramId: integer('telegram_id').primaryKey(),
  username: text('username'),
  firstName: text('first_name'),
  languageCode: text('language_code'),
  messages: integer('messages').notNull().default(0),
  commands: integer('commands').notNull().default(0),
  callbacks: integer('callbacks').notNull().default(0),
  firstSeenAt: integer('first_seen_at').notNull().default(sql`(unixepoch())`),
  lastSeenAt: integer('last_seen_at').notNull().default(sql`(unixepoch())`),
});

export const events = table('events', {
  id: integer('id').primaryKey({ autoIncrement: true }),
  telegramId: integer('telegram_id').notNull(),
  chatId: integer('chat_id').notNull(),
  kind: text('kind').notNull(),
  command: text('command'),
  createdAt: integer('created_at').notNull().default(sql`(unixepoch())`),
}, (tableColumns) => ({
  createdAtIdx: index('idx_events_created_at').on(tableColumns.createdAt),
  telegramIdIdx: index('idx_events_telegram_id').on(tableColumns.telegramId),
}));

export const settings = table('settings', {
  key: text('key').primaryKey(),
  value: text('value').notNull(),
  updatedAt: integer('updated_at').notNull().default(sql`(unixepoch())`),
});

export const groups = table('groups', {
  chatId: integer('chat_id').primaryKey(),
  title: text('title').notNull(),
  username: text('username'),
  type: text('type').notNull(),
  status: text('status').notNull().default('active'),
  welcomeEnabled: integer('welcome_enabled').notNull().default(1),
  antifloodEnabled: integer('antiflood_enabled').notNull().default(0),
  rules: text('rules').notNull().default('Respeta a los demás miembros y evita el spam.'),
  updatedBy: integer('updated_by'),
  updatedAt: integer('updated_at').notNull().default(sql`(unixepoch())`),
  lastSeenAt: integer('last_seen_at').notNull().default(sql`(unixepoch())`),
}, (tableColumns) => ({
  statusIdx: index('idx_groups_status').on(tableColumns.status),
}));
