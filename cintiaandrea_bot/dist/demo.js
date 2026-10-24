const demoState = { members: 128, events: 0, actions: 0 };
const demoFeed = document.getElementById('demo-feed');

function updateDemoCounters() {
  document.getElementById('demo-members').textContent = demoState.members;
  document.getElementById('demo-events').textContent = demoState.events;
  document.getElementById('demo-actions').textContent = demoState.actions;
}

function addDemoEvent(text, detail, type = '') {
  const event = document.createElement('div');
  const label = document.createElement('strong');
  const meta = document.createElement('small');
  event.className = `demo-event ${type}`.trim();
  label.textContent = text;
  meta.textContent = detail;
  event.append(label, meta);
  demoFeed.append(event);
  demoFeed.scrollTop = demoFeed.scrollHeight;
}

const demoActions = {
  member() {
    demoState.members += 1;
    demoState.events += 1;
    demoState.actions += 1;
    addDemoEvent('Lucía se ha unido al grupo', 'Cintia Andrea envió la bienvenida y enlazó las normas.', 'success');
  },
  message() {
    demoState.events += 1;
    addDemoEvent('Mensaje recibido', 'Conversación normal · Sin intervención necesaria');
  },
  flood() {
    demoState.events += 6;
    demoState.actions += 1;
    addDemoEvent('Ráfaga detectada', 'Un mensaje fue retirado y la cuenta recibió un aviso.', 'action');
  },
  rules() {
    demoState.events += 1;
    demoState.actions += 1;
    addDemoEvent('/rules', 'El bot publicó las normas configuradas por los administradores.', 'success');
  },
};

document.querySelectorAll('[data-demo-action]').forEach((button) => {
  button.addEventListener('click', () => {
    demoActions[button.dataset.demoAction]();
    updateDemoCounters();
  });
});

addDemoEvent('Demo preparada', 'Elige un escenario para ver la respuesta de Cintia Andrea.', 'success');
updateDemoCounters();
