import { getStats } from '../lib/stats.js';
import { requireMaster } from '../lib/access.js';

export default async function (_input, ctx) {
  const user = await requireMaster(ctx.initData?.user);

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
