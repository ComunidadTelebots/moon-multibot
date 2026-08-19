const BASE_VIEWS = [
  ["Persecución", "Vista exterior elevada"],
  ["Cabina", "Conducción con movimiento de cabeza"],
  ["Interior", "Segunda posición interior"],
  ["Cinemática", "Órbita exterior dinámica"],
  ["Techo", "Vista superior del vehículo"],
  ["Parachoques", "Perspectiva a ras de carretera"],
  ["Rueda", "Rueda delantera y firme"],
  ["Lateral", "Vehículo y carga desde el lateral"],
  ["Trasera", "Seguimiento posterior de la carga"],
];

export function cameraViewsFor(kind = "truck") {
  return BASE_VIEWS.map(([name, description], index) => {
    if (index === 2 && kind === "bus") return { index, key: index + 1, name: "Salón", description: "Interior de pasajeros" };
    if (index === 2 && ["helicopter", "glider", "cargo_plane", "airliner", "widebody"].includes(kind)) return { index, key: index + 1, name: "Cabina vuelo", description: "Instrumentos y horizonte" };
    if (index === 2 && ["container_ship", "ferry", "tanker", "rescue_ship"].includes(kind)) return { index, key: index + 1, name: "Puente", description: "Puesto de navegación" };
    return { index, key: index + 1, name, description };
  });
}

export function createCameraSelector({ trigger, getKind = () => "truck", onSelect } = {}) {
  if (!trigger || typeof onSelect !== "function") throw new TypeError("Camera selector requires trigger and onSelect");
  const style = document.createElement("style");
  style.textContent = `
    .camera-sheet{position:fixed;z-index:46;inset:0;display:grid;place-items:end center;padding:18px;background:#02070db8;backdrop-filter:blur(8px)}
    .camera-sheet[hidden]{display:none}.camera-dialog{width:min(760px,100%);max-height:min(620px,calc(100dvh - 36px));overflow:auto;padding:18px;border:1px solid #59ead74a;border-radius:22px;background:linear-gradient(145deg,#0b1a25,#07111a);box-shadow:0 24px 80px #000b;color:#eefcfd}
    .camera-head{display:flex;align-items:start;justify-content:space-between;gap:12px}.camera-head h2{margin:0;font-size:22px}.camera-head p{margin:5px 0 0;color:#91aab5}.camera-close{min-width:44px;min-height:44px;font-size:22px}
    .camera-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:9px;margin-top:16px}.camera-option{display:grid;grid-template-columns:32px 1fr;gap:9px;min-height:78px;padding:11px;text-align:left;border:1px solid #ffffff18;border-radius:14px;background:#10222d;color:#edfafd}.camera-option:hover,.camera-option:focus-visible{border-color:#60ead7;background:#15312f}.camera-option.on{border-color:#f59c35;background:linear-gradient(145deg,#3c2918,#17302e)}.camera-key{display:grid;width:30px;height:30px;place-items:center;border-radius:9px;background:#07131c;color:#64ead7;font-weight:900}.camera-copy b,.camera-copy small{display:block}.camera-copy small{margin-top:4px;color:#91aab5;line-height:1.25}
    @media(max-width:600px){.camera-sheet{padding:0;align-items:end}.camera-dialog{max-height:78dvh;padding:14px;border-radius:20px 20px 0 0}.camera-grid{grid-template-columns:repeat(2,minmax(0,1fr))}.camera-option{min-height:70px;padding:9px}.camera-head h2{font-size:19px}}
    @media(prefers-reduced-motion:no-preference){.camera-dialog{animation:cameraSheetIn .2s ease-out}@keyframes cameraSheetIn{from{opacity:.5;transform:translateY(18px)}}}
  `;
  document.head.append(style);
  const sheet = document.createElement("section");
  sheet.className = "camera-sheet"; sheet.hidden = true;
  sheet.setAttribute("role", "dialog"); sheet.setAttribute("aria-modal", "true"); sheet.setAttribute("aria-labelledby", "cameraTitle");
  sheet.innerHTML = `<div class="camera-dialog"><header class="camera-head"><div><h2 id="cameraTitle">Seleccionar cámara</h2><p>Elige una posición o utiliza las teclas 1–9.</p></div><button class="camera-close" aria-label="Cerrar selector de cámaras">×</button></header><div class="camera-grid"></div></div>`;
  document.body.append(sheet);
  const grid = sheet.querySelector(".camera-grid");
  let active = 0, returnFocus = null;
  function render() {
    grid.replaceChildren(...cameraViewsFor(getKind()).map(view => {
      const button = document.createElement("button"); button.className = "camera-option"; button.dataset.camera = String(view.index);
      button.classList.toggle("on", view.index === active); button.setAttribute("aria-pressed", String(view.index === active));
      button.innerHTML = `<span class="camera-key">${view.key}</span><span class="camera-copy"><b>${view.name}</b><small>${view.description}</small></span>`;
      button.onclick = () => { onSelect(view.index); setActive(view.index); close(); };
      return button;
    }));
  }
  function open() { returnFocus = document.activeElement; render(); sheet.hidden = false; grid.querySelector(".on")?.focus(); }
  function close() { sheet.hidden = true; returnFocus?.focus?.(); }
  function setActive(index) { active = index; grid.querySelectorAll(".camera-option").forEach(button => { const selected = Number(button.dataset.camera) === index; button.classList.toggle("on", selected); button.setAttribute("aria-pressed", String(selected)); }); }
  trigger.addEventListener("click", open); sheet.querySelector(".camera-close").onclick = close;
  sheet.addEventListener("click", event => { if (event.target === sheet) close(); });
  sheet.addEventListener("keydown", event => { if (event.key === "Escape") { event.stopPropagation(); close(); } });
  return { open, close, setActive, refresh: render, dispose() { trigger.removeEventListener("click", open); sheet.remove(); style.remove(); } };
}

export default createCameraSelector;
