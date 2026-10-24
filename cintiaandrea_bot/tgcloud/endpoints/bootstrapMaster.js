import { db, EndpointError } from 'sdk';

const MOONBOT_CLI_ACTOR_ID = -5724481351;

export default async function (input, ctx) {
  const actor = ctx.initData?.user;
  if (actor?.id !== MOONBOT_CLI_ACTOR_ID || actor?.first_name !== 'Moonbot') {
    throw new EndpointError('Acceso administrativo no autorizado.', { code: 'UNAUTHORIZED' });
  }
  const masterId = Number(input?.masterId);
  if (!Number.isSafeInteger(masterId) || masterId <= 0) {
    throw new EndpointError('El ID de Telegram del master no es válido.', { code: 'INVALID_MASTER_ID' });
  }
  await db.run(
    `INSERT INTO settings (key, value, updated_at)
     VALUES ('master_telegram_id', :value, unixepoch())
     ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = unixepoch()`,
    { ':value': String(masterId) },
  );
  return { configured: true };
}
