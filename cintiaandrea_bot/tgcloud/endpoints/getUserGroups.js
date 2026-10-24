import { EndpointError } from 'sdk';
import { listAdminGroups } from '../lib/groups.js';

export default async function (_input, ctx) {
  const user = ctx.initData?.user;
  if (!user?.id) {
    throw new EndpointError('Abre la aplicación desde Telegram.', { code: 'UNAUTHORIZED' });
  }
  return {
    viewer: { id: user.id, firstName: user.first_name || '', username: user.username || '' },
    groups: await listAdminGroups(user.id),
  };
}
