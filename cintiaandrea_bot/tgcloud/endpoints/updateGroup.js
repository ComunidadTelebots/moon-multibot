import { EndpointError } from 'sdk';
import { updateGroup } from '../lib/groups.js';

export default async function (input, ctx) {
  const user = ctx.initData?.user;
  if (!user?.id) {
    throw new EndpointError('Abre la aplicación desde Telegram.', { code: 'UNAUTHORIZED' });
  }
  return updateGroup(user.id, input);
}
