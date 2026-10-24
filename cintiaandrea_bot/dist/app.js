const webApp = window.Telegram?.WebApp;
const numberFormat = new Intl.NumberFormat('es-ES');

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

function render(data) {
  const totals = data.totals || {};
  const personal = data.personal || {};
  setText('users', numberFormat.format(Number(totals.users || 0)));
  setText('messages', numberFormat.format(Number(totals.messages || 0)));
  setText('commands', numberFormat.format(Number(totals.commands || 0)));
  setText('callbacks', numberFormat.format(Number(totals.callbacks || 0)));
  setText('personal-messages', numberFormat.format(Number(personal.messages || 0)));
  setText('viewer', data.viewer?.firstName || data.viewer?.username || 'usuario');
  setText('updated', `Actualizado ${new Intl.DateTimeFormat('es-ES', { hour: '2-digit', minute: '2-digit' }).format(new Date(data.generatedAt))}`);
  renderChart(data.daily);
}

function showError(message) {
  const error = document.getElementById('error');
  error.textContent = message;
  error.hidden = false;
  setText('updated', 'Sin conexión');
}

function loadStats() {
  const button = document.getElementById('refresh');
  const error = document.getElementById('error');
  button.disabled = true;
  button.classList.add('loading');
  error.hidden = true;

  if (!webApp?.Serverless?.call) {
    showError('Abre este panel desde el botón de AndreaBot en Telegram.');
    button.disabled = false;
    button.classList.remove('loading');
    return;
  }

  webApp.Serverless.call('getStats', {}, (requestError, result) => {
    button.disabled = false;
    button.classList.remove('loading');
    if (requestError) {
      showError(requestError.message || 'No se pudieron cargar las estadísticas.');
      return;
    }
    render(result);
  });
}

document.getElementById('refresh').addEventListener('click', loadStats);
webApp?.ready();
webApp?.expand();
loadStats();
