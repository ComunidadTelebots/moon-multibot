import { api, EndpointError } from 'sdk';
import { USER_APP_URL } from '../lib/ui.js';

const MOONBOT_CLI_ACTOR_ID = -5724481351;

export default async function (_input, ctx) {
  const actor = ctx.initData?.user;
  if (actor?.id !== MOONBOT_CLI_ACTOR_ID || actor?.first_name !== 'Moonbot') {
    throw new EndpointError('Acceso administrativo no autorizado.', { code: 'UNAUTHORIZED' });
  }
  await api.setMyCommands({
    commands: [
      { command: 'start', description: 'Iniciar Cintia Andrea' },
      { command: 'panel', description: 'Administrar mis grupos' },
      { command: 'rules', description: 'Consultar las normas del grupo' },
      { command: 'terms', description: 'Condiciones del servicio' },
      { command: 'id', description: 'Mostrar mi ID de Telegram' },
      { command: 'help', description: 'Mostrar la ayuda' },
    ],
  });
  await api.setChatMenuButton({
    menu_button: {
      type: 'web_app',
      text: 'Mis grupos',
      web_app: { url: USER_APP_URL },
    },
  });
  return { configured: true, menu: USER_APP_URL };
}
