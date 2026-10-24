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
