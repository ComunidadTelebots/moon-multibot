export const PUBLIC_URL = 'https://app5724481351.tgcloud.ai/';
export const USER_APP_URL = 'https://app5724481351.tgcloud.ai/manage.html';
export const MASTER_PANEL_URL = 'https://app5724481351.tgcloud.ai/panel.html';

export function statsKeyboard() {
  return {
    inline_keyboard: [
      [{ text: 'Abrir estadisticas', web_app: { url: MASTER_PANEL_URL } }],
      [{ text: 'Actualizar', callback_data: 'refresh_stats' }],
    ],
  };
}

export function managementKeyboard() {
  return {
    inline_keyboard: [
      [{ text: 'Administrar mis grupos', web_app: { url: USER_APP_URL } }],
      [{ text: 'Conocer Cintia Andrea', url: PUBLIC_URL }],
    ],
  };
}

export function masterKeyboard() {
  return {
    inline_keyboard: [[{ text: 'Abrir panel master', web_app: { url: MASTER_PANEL_URL } }]],
  };
}
