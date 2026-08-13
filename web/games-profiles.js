(() => {
  const profiles = {
    snake: ['snake', '🐍', 'Snake Moon', 'Arcade de reflejos y precisión', 'Arcade', '2D'],
    hauler: ['transport', '🚚', 'Rutas del Continente', 'Conducción, contratos y economía', 'Simulación', 'v0.2'],
    transport3d: ['transport', '🚚', 'Rutas del Continente', 'Vehículos, ciudades y cabinas tridimensionales', 'Simulación', 'v0.4'],
    race: ['race', '🏎️', 'Circuito Neón', 'Carrera arcade entre tráfico nocturno', 'Carreras', 'v0.1'],
    race3d: ['race', '🏎️', 'Circuito Neón', 'Velocidad WebGL con exterior y cockpit', 'Carreras', 'v0.2'],
    flight2d: ['flight', '🚁', 'Vuelo Rescate', 'Pilota, evita montañas y recoge balizas', 'Rescate', 'v0.1'],
    flight3d: ['flight', '🚁', 'Vuelo Rescate', 'Ciudad, helicóptero y cámara de cabina', 'Rescate', 'v0.1'],
    orbit: ['orbit', '🚀', 'Órbita Cero', 'Supervivencia espacial y recolección', 'Espacio', '2D'],
    tower: ['tower', '🏗️', 'Torre Pulso', 'Construcción basada en precisión', 'Puzzle', '2D'],
    royale: ['royale', '🧱', 'Block Royale', 'Supervivencia multijugador hasta el último', 'Online', 'v0.2'],
    ttt: ['ttt', '❌', 'Tres en raya', 'El clásico duelo estratégico', 'Estrategia', '2D'],
    memory: ['memory', '🧠', 'Memoria Lunar', 'Encuentra todas las parejas', 'Memoria', '2D'],
  };
  const pairs = { transport: ['hauler', 'transport3d'], race: ['race', 'race3d'], flight: ['flight2d', 'flight3d'] };
  const activate = id => {
    document.querySelectorAll('.game,[data-game]').forEach(node => node.classList.remove('on'));
    document.getElementById(id)?.classList.add('on');
    const family = Object.entries(pairs).find(([, ids]) => ids.includes(id));
    const tabId = family ? family[1][0] : id;
    document.querySelector(`[data-game="${tabId}"]`)?.classList.add('on');
    document.querySelector('.tabs')?.scrollIntoView({ block: 'nearest' });
  };
  Object.entries(profiles).forEach(([id, profile]) => {
    const game = document.getElementById(id); if (!game) return;
    const [theme, icon, title, tagline, genre, version] = profile;
    game.classList.add(`game-profile-${theme}`);
    const card = document.createElement('div'); card.className = 'game-profile';
    card.innerHTML = `<span class="game-profile-icon">${icon}</span><span class="game-profile-copy"><b>${title}</b><span>${tagline}</span></span><span class="game-profile-tags"><i>${genre}</i><i>${version}</i></span>`;
    game.querySelector('.head')?.after(card);
  });
  Object.entries(pairs).forEach(([family, [twoD, threeD]]) => {
    document.querySelector(`[data-game="${threeD}"]`)?.setAttribute('hidden', '');
    const baseTab = document.querySelector(`[data-game="${twoD}"]`);
    if (baseTab) baseTab.innerHTML = `${profiles[twoD][1]} ${profiles[twoD][2]} <small>${profiles[twoD][5]}–${profiles[threeD][5]}</small>`;
    [twoD, threeD].forEach((id, activeIndex) => {
      const game = document.getElementById(id); if (!game) return;
      const switcher = document.createElement('div'); switcher.className = 'version-switch';
      switcher.innerHTML = `<button class="${activeIndex === 0 ? 'on' : ''}" data-version-target="${twoD}">Versión 2D</button><button class="${activeIndex === 1 ? 'on' : ''}" data-version-target="${threeD}">Versión 3D · GPU</button>`;
      game.querySelector('.game-profile')?.after(switcher);
    });
  });
  document.querySelectorAll('[data-version-target]').forEach(button => button.onclick = () => activate(button.dataset.versionTarget));
  document.querySelectorAll('.game .btn').forEach(button => {
    if (/cambiar a versi.n 3d/i.test(button.textContent)) button.remove();
  });
})();
