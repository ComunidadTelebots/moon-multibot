import { EndpointError } from 'sdk';
import { getStats } from '../lib/stats.js';

const MOONBOT_CLI_ACTOR_ID = -5724481351;

export default async function (_input, ctx) {
  const actor = ctx.initData?.user;
  // Telegram validates real Mini App users, whose IDs are positive. Only an
  // authenticated tgcloud CLI session can inject this reserved admin context.
  if (actor?.id !== MOONBOT_CLI_ACTOR_ID || actor?.first_name !== 'Moonbot') {
    throw new EndpointError('Acceso administrativo no autorizado.', { code: 'UNAUTHORIZED' });
  }

  return JSON.stringify({
    generatedAt: new Date().toISOString(),
    ...(await getStats(null)),
  });
}
