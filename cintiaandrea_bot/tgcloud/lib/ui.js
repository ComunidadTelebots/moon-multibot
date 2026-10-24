export const MINI_APP_URL = 'https://app5724481351.tgcloud.ai/';

export function statsKeyboard() {
  return {
    inline_keyboard: [
      [{ text: 'Abrir estadisticas', web_app: { url: MINI_APP_URL } }],
      [{ text: 'Actualizar', callback_data: 'refresh_stats' }],
    ],
  };
}
