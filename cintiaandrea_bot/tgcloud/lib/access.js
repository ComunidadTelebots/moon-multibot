import { db, EndpointError } from 'sdk';

export async function requireMaster(user) {
  if (!user?.id) {
    throw new EndpointError('Abre el panel desde Telegram.', { code: 'UNAUTHORIZED' });
  }
  const setting = await db.get(
    `SELECT value FROM settings WHERE key = 'master_telegram_id'`,
  );
  if (!setting?.value) {
    throw new EndpointError('El acceso master todavía no está configurado.', {
      code: 'MASTER_NOT_CONFIGURED',
    });
  }
  if (String(user.id) !== String(setting.value)) {
    throw new EndpointError('Esta cuenta no tiene acceso al panel master.', {
      code: 'MASTER_REQUIRED',
    });
  }
  return user;
}

export async function isMaster(userId) {
  if (!userId) return false;
  const setting = await db.get(
    `SELECT value FROM settings WHERE key = 'master_telegram_id'`,
  );
  return Boolean(setting?.value && String(userId) === String(setting.value));
}
