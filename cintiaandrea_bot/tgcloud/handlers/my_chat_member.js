import { recordGroup } from '../lib/groups.js';

export default async function (membership) {
  const status = membership.new_chat_member?.status;
  const active = ['member', 'administrator'].includes(status);
  await recordGroup(membership.chat, active ? 'active' : 'inactive');
}
