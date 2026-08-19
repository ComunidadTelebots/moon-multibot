(() => {
  const KEY = 'moonGraphicsV1';
  const defaults = { mode: 'auto', quality: matchMedia('(min-width:900px)').matches ? 'high' : 'medium' };
  let settings = defaults;
  try { settings = { ...defaults, ...JSON.parse(localStorage.getItem(KEY) || '{}') }; } catch (_) {}

  const probe = document.createElement('canvas');
  const gl = probe.getContext('webgl2', { powerPreference: 'high-performance' }) || probe.getContext('webgl');
  const webgl2 = typeof WebGL2RenderingContext !== 'undefined' && gl instanceof WebGL2RenderingContext;
  const panel = document.createElement('section');
  panel.className = 'graphics-panel';
  panel.innerHTML = `<label>Aceleración gráfica<select id="graphicsMode"><option value="auto">Automática</option><option value="gpu">GPU · alto rendimiento</option><option value="compat">Compatibilidad 2D</option></select></label><label>Calidad<select id="graphicsQuality"><option value="low">Baja</option><option value="medium">Media</option><option value="high">Alta</option><option value="ultra">Ultra</option></select></label><button class="btn" id="graphicsApply">Aplicar gráficos</button><p class="graphics-state" id="graphicsState"></p>`;
  document.querySelector('.hero')?.after(panel);
  const mode = panel.querySelector('#graphicsMode'), quality = panel.querySelector('#graphicsQuality'), state = panel.querySelector('#graphicsState');
  mode.value = settings.mode; quality.value = settings.quality;

  const status = () => {
    const accelerated = !!gl && settings.mode !== 'compat';
    const engine = settings.mode === 'compat' ? 'Canvas 2D' : accelerated ? `${webgl2 ? 'WebGL 2' : 'WebGL'} acelerado` : 'Canvas 2D (GPU no disponible)';
    state.innerHTML = `Motor activo: <b class="${accelerated ? 'gpu-on' : ''}">${engine}</b> · calidad ${settings.quality}. Los juegos 3D ya renderizan con la GPU mediante WebGL.`;
  };
  const pairs = { hauler: 'transport3d', race: 'race3d', flight2d: 'flight3d' };
  panel.querySelector('#graphicsApply').onclick = () => {
    settings = { mode: mode.value, quality: quality.value };
    localStorage.setItem(KEY, JSON.stringify(settings));
    document.documentElement.dataset.graphicsQuality = settings.quality;
    document.querySelectorAll('.game iframe').forEach(frame => {
      const url = new URL(frame.getAttribute('src'), location.href);
      url.searchParams.set('graphics', settings.mode);
      url.searchParams.set('quality', settings.quality);
      frame.src = url;
    });
    const current = document.querySelector('.game.on')?.id;
    if (settings.mode === 'gpu' && pairs[current]) document.querySelector(`[data-game="${pairs[current]}"]`)?.click();
    if (settings.mode === 'compat') {
      const fallback = Object.entries(pairs).find(([, three]) => three === current)?.[0];
      if (fallback) document.querySelector(`[data-game="${fallback}"]`)?.click();
    }
    status();
  };
  document.documentElement.dataset.graphicsQuality = settings.quality;
  status();
})();
