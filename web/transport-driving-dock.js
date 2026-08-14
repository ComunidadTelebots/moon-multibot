const GROUPS = [
  { id: "vehicle", label: "Vehiculo", ids: ["truck", "bus", "ambulance", "fireEngine", "recoveryTruck", "fleetVehicle", "fleetLivery"] },
  { id: "route", label: "Ruta", ids: ["cam", "cruise", "parking", "mapButton", "europeMapButton", "worldMapButton"] },
  { id: "work", label: "Trabajo", ids: ["workMode", "toolButton", "interactButton", "contractButton", "cargoMonitorButton", "specialButton", "specialOperate"] },
  { id: "services", label: "Servicios", ids: ["engineButton", "rest", "rescue", "serviceButton", "sirenButton", "convoyButton", "academyButton", "achievementsButton", "eventsButton", "wheelButton", "full"] },
];

export function createTransportDrivingDock({ controls = document.querySelector(".controls:not(.drive)") } = {}) {
  if (!controls || controls.dataset.drivingDock === "ready") return { dispose() {} };
  controls.dataset.drivingDock = "ready";
  controls.classList.add("driving-dock");

  const style = document.createElement("style");
  style.textContent = `
    .driving-dock{--dock-accent:#4ce6d0;align-items:center!important;flex-wrap:nowrap!important;max-width:min(980px,calc(100vw - 240px))!important;padding:5px!important;overflow:visible!important}
    .driving-dock .dock-primary{display:flex;align-items:center;gap:5px;min-width:0;overflow-x:auto;scrollbar-width:none}.driving-dock .dock-primary::-webkit-scrollbar{display:none}
    .driving-dock .dock-tab{display:inline-flex!important;align-items:center;gap:7px;min-height:42px!important;white-space:nowrap}.driving-dock .dock-tab::before{content:"";width:7px;height:7px;border-radius:50%;background:#6f8792}.driving-dock .dock-tab[aria-expanded="true"]{border-color:var(--dock-accent)!important;color:#72f3df!important}.driving-dock .dock-tab[aria-expanded="true"]::before{background:var(--dock-accent);box-shadow:0 0 12px var(--dock-accent)}
    .driving-dock .dock-overflow{position:fixed;z-index:16;left:50%;bottom:68px;width:min(760px,calc(100vw - 24px));max-height:min(56vh,430px);transform:translateX(-50%);padding:12px;border:1px solid #4ce6d04d;border-radius:18px;background:linear-gradient(145deg,#0b1e29f7,#061019fa);box-shadow:0 20px 70px #000d;backdrop-filter:blur(20px);overflow:auto}.driving-dock .dock-overflow[hidden]{display:none}
    .driving-dock .dock-head{display:flex;align-items:center;justify-content:space-between;margin-bottom:10px}.driving-dock .dock-head b{font-size:14px}.driving-dock .dock-head small{color:#7f9ba8}.driving-dock .dock-grid{display:grid;grid-template-columns:repeat(4,minmax(125px,1fr));gap:7px}.driving-dock .dock-grid>button,.driving-dock .dock-grid>select{width:100%;min-width:0;min-height:44px!important;text-align:left}
    .driving-dock .dock-close{display:block!important;width:38px!important;min-height:38px!important;padding:4px!important;text-align:center!important}
    body:not(.controls-expanded) .driving-dock .dock-grid button{display:block!important}
    .driving-dock>#moreControls{margin-left:auto;flex:0 0 auto;font-size:0}.driving-dock>#moreControls::after{content:"Menu";font-size:12px}
    @media(max-width:900px){.driving-dock{max-width:calc(100vw - 205px)!important}.driving-dock .dock-grid{grid-template-columns:repeat(3,minmax(120px,1fr))}}
    @media(max-width:700px){.driving-dock{left:6px!important;right:6px!important;bottom:66px!important;max-width:none!important;transform:none!important;overflow:visible!important}.driving-dock .dock-primary{flex:1}.driving-dock .dock-tab{min-height:46px!important}.driving-dock .dock-overflow{bottom:124px;max-height:46vh;padding:10px}.driving-dock .dock-grid{grid-template-columns:repeat(2,minmax(0,1fr))}.driving-dock .dock-grid>button,.driving-dock .dock-grid>select{min-height:48px!important}.driving-dock>#moreControls{min-width:52px}}
    @media(max-width:390px){.driving-dock .dock-tab{padding-inline:9px!important}.driving-dock .dock-grid{grid-template-columns:1fr}}
    @media(prefers-reduced-motion:reduce){.driving-dock *{scroll-behavior:auto!important;transition:none!important}}
  `;
  document.head.append(style);

  const primary = document.createElement("div");
  primary.className = "dock-primary";
  const overflow = document.createElement("section");
  overflow.className = "dock-overflow";
  overflow.hidden = true;
  overflow.setAttribute("aria-label", "Controles del simulador");
  overflow.innerHTML = `<header class="dock-head"><div><b>Controles</b><br><small>Selecciona una categoria</small></div><button type="button" class="dock-close" aria-label="Cerrar controles">x</button></header><div class="dock-grid"></div>`;
  const grid = overflow.querySelector(".dock-grid");
  controls.prepend(primary);
  controls.append(overflow);

  let active = "";
  const tabs = new Map();
  const owner = new Map(GROUPS.flatMap(group => group.ids.map(id => [id, group.id])));
  GROUPS.forEach(group => {
    const tab = document.createElement("button");
    tab.type = "button";
    tab.className = "dock-tab";
    tab.textContent = group.label;
    tab.setAttribute("aria-expanded", "false");
    tab.setAttribute("aria-controls", `dock-${group.id}`);
    tab.onclick = () => show(active === group.id ? "" : group.id);
    primary.append(tab);
    tabs.set(group.id, tab);
  });

  function show(groupId) {
    active = groupId;
    tabs.forEach((tab, id) => tab.setAttribute("aria-expanded", String(id === active)));
    if (!active) { overflow.hidden = true; return; }
    const group = GROUPS.find(item => item.id === active);
    overflow.id = `dock-${active}`;
    overflow.querySelector(".dock-head b").textContent = group.label;
    Array.from(grid.children).forEach(element => { element.hidden = element.dataset.dockGroup !== active; });
    overflow.hidden = false;
    grid.querySelector("button:not([hidden]),select:not([hidden])")?.focus({ preventScroll: true });
  }

  function park(element) {
    if (!(element instanceof HTMLElement) || element === primary || element === overflow || element.id === "moreControls") return;
    const groupId = owner.get(element.id) || "services";
    if (!owner.has(element.id)) owner.set(element.id, groupId);
    element.dataset.dockGroup = groupId;
    element.hidden = active !== groupId;
    grid.append(element);
  }
  Array.from(controls.children).forEach(park);
  const originalMore = document.getElementById("moreControls");
  if (originalMore) {
    originalMore.hidden = false;
    originalMore.setAttribute("aria-label", "Abrir controles del simulador");
  }
  const interceptMore = event => {
    if (event.target?.closest?.("#moreControls")) {
      event.preventDefault();
      event.stopPropagation();
      show(active ? "" : "services");
    }
  };
  controls.addEventListener("click", interceptMore, true);
  overflow.querySelector(".dock-close").onclick = () => show("");

  const observer = new MutationObserver(records => records.forEach(record => record.addedNodes.forEach(park)));
  observer.observe(controls, { childList: true });
  const onKey = event => { if (event.key === "Escape" && !overflow.hidden) { show(""); event.stopPropagation(); } };
  document.addEventListener("keydown", onKey, true);

  return { close: () => show(""), dispose() { observer.disconnect(); controls.removeEventListener("click", interceptMore, true); document.removeEventListener("keydown", onKey, true); style.remove(); } };
}

export default createTransportDrivingDock;
