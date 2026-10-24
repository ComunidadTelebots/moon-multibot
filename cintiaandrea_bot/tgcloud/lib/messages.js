export function commandFromText(value) {
  const text = String(value || '').trim();
  const match = text.match(/^\/([a-z0-9_]+)(?:@[a-z0-9_]+)?(?:\s|$)/i);
  return match ? match[1].toLowerCase() : null;
}

export function startText(firstName) {
  const name = String(firstName || '').trim();
  return [
    `Hola${name ? `, ${name}` : ''}. Soy Cintia Andrea.`,
    '',
    'Estoy ejecutandome en Telegram Serverless y ya puedo registrar actividad en tiempo real.',
    '',
    'Usa /panel para administrar tus grupos desde Telegram.',
  ].join('\n');
}

export function helpText() {
  return [
    'Comandos disponibles',
    '',
    '/start - Presentacion del bot',
    '/id - Mostrar tu ID de Telegram',
    '/panel - Administrar tus grupos',
    '/rules - Consultar las normas del grupo',
    '/terms - Condiciones del servicio',
    '/help - Mostrar esta ayuda',
  ].join('\n');
}
