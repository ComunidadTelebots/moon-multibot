import { EndpointError } from 'sdk';
import { getStats } from '../lib/stats.js';

export default async function (_input, ctx) {
  const user = ctx.initData?.user;
  if (!user?.id) {
    throw new EndpointError('Abre el panel desde AndreaBot.', { code: 'UNAUTHORIZED' });
  }

  const stats = await getStats(user.id);
  return {
    generatedAt: new Date().toISOString(),
    viewer: {
      id: user.id,
      firstName: user.first_name || '',
      username: user.username || '',
    },
    ...stats,
  };
}
