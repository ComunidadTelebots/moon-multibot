const webApp = window.Telegram?.WebApp;
const state = { groups: [], selected: null };

const byId = (id) => document.getElementById(id);
const setText = (id, value) => { byId(id).textContent = value; };

function showError(message) {
  const error = byId('user-error');
  error.textContent = message;
  error.hidden = false;
}

function callServerless(name, input = {}) {
  return new Promise((resolve, reject) => {
    webApp.Serverless.call(name, input, (error, result) => error ? reject(error) : resolve(result));
  });
}

function renderGroups() {
  const list = byId('group-list');
  list.replaceChildren(...state.groups.map((group) => {
    const button = document.createElement('button');
    const title = document.createElement('strong');
    const detail = document.createElement('small');
    button.type = 'button';
    button.className = `group-item${state.selected?.chatId === group.chatId ? ' active' : ''}`;
    title.textContent = group.title;
    detail.textContent = group.username ? `@${group.username}` : `${group.type} · ${group.welcomeEnabled ? 'Bienvenida activa' : 'Bienvenida desactivada'}`;
    button.append(title, detail);
    button.addEventListener('click', () => selectGroup(group.chatId));
    return button;
  }));
  byId('group-empty').hidden = state.groups.length > 0;
  if (!state.groups.length) byId('settings-panel').hidden = true;
}

function selectGroup(chatId) {
  state.selected = state.groups.find((group) => group.chatId === chatId) || null;
  if (!state.selected) return;
  setText('settings-title', state.selected.title);
  byId('welcome-enabled').checked = state.selected.welcomeEnabled;
  byId('antiflood-enabled').checked = state.selected.antifloodEnabled;
  byId('group-rules').value = state.selected.rules;
  setText('rules-count', state.selected.rules.length);
  setText('save-state', 'Sin cambios');
  byId('settings-panel').hidden = false;
  renderGroups();
}

async function loadGroups() {
  byId('reload-groups').disabled = true;
  byId('user-error').hidden = true;
  try {
    const result = await callServerless('getUserGroups');
    state.groups = result.groups || [];
    const name = result.viewer?.firstName || result.viewer?.username || 'Usuario';
    setText('user-name', name);
    setText('user-handle', result.viewer?.username ? `@${result.viewer.username}` : 'Telegram');
    setText('user-avatar', name.slice(0, 1).toUpperCase());
    byId('user-login').hidden = true;
    byId('user-app').hidden = false;
    renderGroups();
    if (state.groups.length) selectGroup(state.groups[0].chatId);
  } catch (error) {
    if (!byId('user-app').hidden) showError(error.message || 'No se pudieron cargar tus grupos.');
    else setText('user-login-status', error.message || 'No se pudo validar la sesión.');
  } finally {
    byId('reload-groups').disabled = false;
    byId('user-login-button').disabled = false;
  }
}

async function saveSettings(event) {
  event.preventDefault();
  if (!state.selected) return;
  const button = byId('save-settings');
  button.disabled = true;
  setText('save-state', 'Guardando...');
  try {
    const updated = await callServerless('updateGroup', {
      chatId: state.selected.chatId,
      welcomeEnabled: byId('welcome-enabled').checked,
      antifloodEnabled: byId('antiflood-enabled').checked,
      rules: byId('group-rules').value,
    });
    Object.assign(state.selected, updated);
    setText('save-state', 'Guardado');
    renderGroups();
  } catch (error) {
    setText('save-state', 'Error');
    showError(error.message || 'No se pudieron guardar los cambios.');
  } finally {
    button.disabled = false;
  }
}

function init() {
  const loginButton = byId('user-login-button');
  const openBot = byId('user-open-bot');
  const user = webApp?.initDataUnsafe?.user;
  if (!webApp?.Serverless?.call || !user) {
    setText('user-login-status', 'Abre esta aplicación desde el botón /panel de Cintia Andrea.');
    loginButton.hidden = true;
    openBot.hidden = false;
    return;
  }
  setText('user-login-status', `Cuenta detectada: ${user.first_name || user.username || 'Telegram'}`);
  loginButton.disabled = false;
}

byId('user-login-button').addEventListener('click', loadGroups);
byId('reload-groups').addEventListener('click', loadGroups);
byId('group-settings').addEventListener('submit', saveSettings);
byId('group-rules').addEventListener('input', (event) => setText('rules-count', event.target.value.length));
webApp?.ready();
webApp?.expand();
init();
