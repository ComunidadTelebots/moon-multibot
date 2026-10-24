const webApp = window.Telegram?.WebApp;
const numberFormat = new Intl.NumberFormat('es-ES');
const loginView = document.getElementById('login-view');
const appView = document.getElementById('app-view');

const setText = (id, value) => {
  document.getElementById(id).textContent = value;
};

function normalizedDays(rows) {
  const byDay = new Map((rows || []).map((row) => [row.day, Number(row.events || 0)]));
  const days = [];
  for (let offset = 6; offset >= 0; offset -= 1) {
    const date = new Date();
    date.setHours(0, 0, 0, 0);
    date.setDate(date.getDate() - offset);
    const key = date.toISOString().slice(0, 10);
    days.push({
      key,
      label: new Intl.DateTimeFormat('es-ES', { weekday: 'short' }).format(date).replace('.', ''),
      value: byDay.get(key) || 0,
    });
  }
  return days;
}

function renderChart(rows) {
  const chart = document.getElementById('chart');
  const days = normalizedDays(rows);
  const maximum = Math.max(1, ...days.map((day) => day.value));
  const hasActivity = days.some((day) => day.value > 0);
  chart.classList.toggle('is-empty', !hasActivity);
  chart.dataset.emptyLabel = hasActivity ? '' : 'Aún no hay eventos. Envía /start al bot para iniciar la medición.';
  chart.replaceChildren(...days.map((day) => {
    const item = document.createElement('div');
    item.className = 'bar-item';

    const value = document.createElement('span');
    value.className = 'bar-value';
    value.textContent = numberFormat.format(day.value);

    const track = document.createElement('div');
    track.className = 'bar-track';
    const bar = document.createElement('div');
    bar.className = 'bar';
    bar.style.height = `${Math.max(5, Math.round((day.value / maximum) * 100))}%`;
    track.append(bar);

    const label = document.createElement('span');
    label.className = 'bar-label';
    label.textContent = day.label;
    item.append(value, track, label);
    return item;
  }));
}

function formatUnix(value) {
  const timestamp = Number(value || 0);
  if (!timestamp) return 'Sin actividad';
  return new Intl.DateTimeFormat('es-ES', {
    day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit',
  }).format(new Date(timestamp * 1000));
}

function renderCommands(commands) {
  const list = document.getElementById('top-commands');
  if (!commands?.length) {
    list.innerHTML = '<p class="empty-copy">Aún no hay comandos registrados.</p>';
    return;
  }
  list.replaceChildren(...commands.map((row) => {
    const item = document.createElement('div');
    const name = document.createElement('strong');
    const uses = document.createElement('span');
    name.textContent = `/${row.command}`;
    uses.textContent = `${numberFormat.format(Number(row.uses || 0))} usos`;
    item.append(name, uses);
    return item;
  }));
}

function render(data) {
  const totals = data.totals || {};
  const personal = data.personal || {};
  setText('users', numberFormat.format(Number(totals.users || 0)));
  setText('messages', numberFormat.format(Number(totals.messages || 0)));
  setText('commands', numberFormat.format(Number(totals.commands || 0)));
  setText('callbacks', numberFormat.format(Number(totals.callbacks || 0)));
  setText('personal-messages', numberFormat.format(Number(personal.messages || 0)));
  setText('personal-commands', numberFormat.format(Number(personal.commands || 0)));
  setText('personal-callbacks', numberFormat.format(Number(personal.callbacks || 0)));
  const viewer = data.viewer?.firstName || data.viewer?.username || 'master';
  setText('viewer', viewer);
  setText('viewer-handle', data.viewer?.username ? `@${data.viewer.username}` : 'Identidad validada por Telegram');
  setText('avatar', viewer.slice(0, 1).toUpperCase());
  setText('events-24h', numberFormat.format(Number(data.recent?.events_24h || 0)));
  setText('active-24h', numberFormat.format(Number(data.recent?.active_users_24h || 0)));
  setText('last-event', formatUnix(data.recent?.last_event_at));
  setText('activity-state', Number(data.recent?.events_24h || 0) ? 'Actividad recibida' : 'Sin eventos todavía');
  setText('updated', `Actualizado ${new Intl.DateTimeFormat('es-ES', { hour: '2-digit', minute: '2-digit' }).format(new Date(data.generatedAt))}`);
  renderChart(data.daily);
  renderCommands(data.topCommands);
  loginView.hidden = true;
  appView.hidden = false;
}

function showError(message) {
  if (appView.hidden) {
    setText('login-status', message);
    return;
  }
  const error = document.getElementById('error');
  error.textContent = message;
  error.hidden = false;
  setText('updated', 'Sin conexión');
}

function loadStats() {
  const button = document.getElementById('refresh');
  const loginButton = document.getElementById('login');
  const error = document.getElementById('error');
  button.disabled = true;
  loginButton.disabled = true;
  button.classList.add('loading');
  error.hidden = true;

  if (!webApp?.Serverless?.call) {
    showError('Abre este panel desde el botón de AndreaBot en Telegram.');
    button.disabled = false;
    loginButton.disabled = false;
    button.classList.remove('loading');
    return;
  }

  webApp.Serverless.call('getStats', {}, (requestError, result) => {
    button.disabled = false;
    loginButton.disabled = false;
    button.classList.remove('loading');
    if (requestError) {
      showError(requestError.message || 'No se pudieron cargar las estadísticas.');
      return;
    }
    render(result);
  });
}

function initLogin() {
  const loginButton = document.getElementById('login');
  const openTelegram = document.getElementById('open-telegram');
  const user = webApp?.initDataUnsafe?.user;
  if (!webApp?.Serverless?.call || !user) {
    setText('login-status', 'Abre el panel desde el botón privado de AndreaBot.');
    loginButton.hidden = true;
    openTelegram.hidden = false;
    return;
  }
  setText('login-status', `Cuenta detectada: ${user.first_name || user.username || 'Telegram'}`);
  loginButton.disabled = false;
}

document.getElementById('refresh').addEventListener('click', loadStats);
document.getElementById('login').addEventListener('click', loadStats);
webApp?.ready();
webApp?.expand();
initLogin();
