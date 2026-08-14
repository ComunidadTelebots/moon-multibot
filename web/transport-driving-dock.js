const GROUPS = [
  { id: "vehicle", icon: "▰", label: "Vehículo", hint: "Flota y configuración", ids: ["truck", "bus", "ambulance", "fireEngine", "recoveryTruck", "fleetVehicle", "fleetLivery"] },
  { id: "route", icon: "⌁", label: "Ruta", hint: "Mapa, cámara y conducción", ids: ["cam", "cruise", "parking", "mapButton", "europeMapButton", "worldMapButton"] },
  { id: "work", icon: "◇", label: "Trabajo", hint: "Contratos y mercancía", ids: ["workMode", "toolButton", "interactButton", "contractButton", "cargoMonitorButton", "specialButton", "specialOperate"] },
  { id: "services", icon: "＋", label: "Servicios", hint: "Motor, taller y asistencia", ids: ["engineButton", "rest", "rescue", "serviceButton", "sirenButton", "convoyButton", "academyButton", "achievementsButton", "eventsButton", "wheelButton", "full"] },
];

export function createTransportDrivingDock({ controls = document.querySelector(".controls:not(.drive)") } = {}) {
  if (!controls || controls.dataset.drivingDock === "ready") return { dispose() {} };
  controls.dataset.drivingDock = "ready";
  controls.classList.add("driving-dock");

  const hud = document.querySelector(".hud");
  const driveHeader = document.createElement("header");
  driveHeader.className = "moon-drive-header";
  driveHeader.innerHTML = \`<div class="moon-drive-brand"><small>TODO SOBRE ALLTECH STUDIOS</small><b>Rutas del Continente</b></div><div class="moon-drive-route"><small>RUTA ACTIVA</small><b data-live-city>En carretera</b><span data-live-road>Sin incidencias</span></div><div><small>VEHÍCULO · CÁMARA</small><b data-live-vehicle>Aster Viento 3D</b><span data-live-view>Exterior</span></div>\`;
  document.body.append(driveHeader);
  if (hud) {
    hud.classList.add("moon-route-hud");
    hud.hidden = true;
    Array.from(hud.querySelectorAll(".pill")).forEach(pill => {
      const id = pill.querySelector("b")?.id;
      pill.classList.add(id === "vn" ? "moon-hud-vehicle" : id === "city" ? "moon-hud-city" : id === "roadEvent" ? "moon-hud-road" : id === "view" ? "moon-hud-view" : "moon-hud-secondary");
    });
    ["city", "roadEvent", "vn"].forEach(id => {
      const pill = document.getElementById(id)?.closest(".pill");
      if (pill) hud.append(pill);
    });
  }

  const style = document.createElement("style");
  style.textContent = `
    .driving-dock{--dock-accent:#54ead4;align-items:stretch!important;flex-wrap:nowrap!important;max-width:min(760px,calc(100vw - 270px))!important;padding:4px!important;border-radius:22px!important;overflow:visible!important}
    .driving-dock .dock-primary{display:grid;grid-template-columns:repeat(4,minmax(92px,1fr));align-items:stretch;gap:3px;min-width:0;overflow:visible}.driving-dock .dock-primary::-webkit-scrollbar{display:none}
    .driving-dock .dock-tab{position:relative;display:grid!important;grid-template-columns:24px 1fr;grid-template-rows:auto auto;column-gap:7px;align-items:center;min-height:50px!important;padding:7px 10px!important;border-color:transparent!important;background:transparent!important;text-align:left;white-space:nowrap}.driving-dock .dock-tab-icon{grid-row:1/3;display:grid;place-items:center;width:24px;height:24px;border:1px solid #47606c;border-radius:8px;color:#9db2bb;font-size:14px}.driving-dock .dock-tab-label{font-size:11px;line-height:1.1}.driving-dock .dock-tab small{color:#708994;font-size:8px;font-weight:500;line-height:1.1}.driving-dock .dock-tab[aria-expanded="true"]{border-color:#54ead455!important;background:linear-gradient(145deg,#153e3a,#0c2628)!important;color:#7bf5e3!important}.driving-dock .dock-tab[aria-expanded="true"] .dock-tab-icon{border-color:var(--dock-accent);background:#173f3b;color:#7bf5e3;box-shadow:0 0 18px #54ead42b}.driving-dock .dock-tab[aria-expanded="true"] small{color:#a7d8d1}
    .driving-dock .dock-overflow{position:fixed;z-index:16;left:50%;bottom:68px;width:min(760px,calc(100vw - 24px));max-height:min(56vh,430px);transform:translateX(-50%);padding:12px;border:1px solid #4ce6d04d;border-radius:18px;background:linear-gradient(145deg,#0b1e29f7,#061019fa);box-shadow:0 20px 70px #000d;backdrop-filter:blur(20px);overflow:auto}.driving-dock .dock-overflow[hidden]{display:none}
    .driving-dock .dock-head{display:flex;align-items:center;justify-content:space-between;margin-bottom:10px;padding:3px 3px 9px;border-bottom:1px solid #ffffff13}.driving-dock .dock-head b{font-size:16px}.driving-dock .dock-head small{color:#7f9ba8}.driving-dock .dock-grid{display:grid;grid-template-columns:repeat(4,minmax(125px,1fr));gap:7px}.driving-dock .dock-grid>button,.driving-dock .dock-grid>select{width:100%;min-width:0;min-height:48px!important;text-align:left}
    .driving-dock .dock-close{display:block!important;width:38px!important;min-height:38px!important;padding:4px!important;text-align:center!important}
    body:not(.controls-expanded) .driving-dock .dock-grid button{display:block!important}
    .driving-dock>#moreControls{margin-left:3px;flex:0 0 52px;font-size:0!important;border-color:#54ead455!important;background:#12302f!important}.driving-dock>#moreControls::before{content:"☰";display:block;color:#67efdc;font-size:18px}.driving-dock>#moreControls::after{content:"Menú";display:block;color:#9dc0c3;font-size:8px}
    .moon-drive-header{position:fixed;z-index:11;left:12px;top:12px;display:grid;grid-template-columns:minmax(180px,1fr) minmax(200px,1.25fr) minmax(170px,1fr);width:min(650px,calc(100vw - 390px));min-height:64px;padding:6px;border:1px solid #345462;border-radius:17px;background:linear-gradient(120deg,#07151ff2,#0d2b36e8);box-shadow:0 14px 44px #0009;backdrop-filter:blur(18px)}.moon-drive-header>div{display:flex;flex-direction:column;justify-content:center;min-width:0;padding:6px 10px;border-right:1px solid #ffffff12}.moon-drive-header>div:last-child{border:0}.moon-drive-header small{color:#6ccfc4;font-size:8px;font-weight:800;letter-spacing:.1em}.moon-drive-header b{margin-top:2px;overflow:hidden;color:#f2ffff;font-size:12px;text-overflow:ellipsis;white-space:nowrap}.moon-drive-header span{margin-top:2px;overflow:hidden;color:#8da9b5;font-size:9px;text-overflow:ellipsis;white-space:nowrap}.moon-drive-route span{color:#ffb363}.hud.moon-route-hud{display:none!important}
    @media(max-width:900px){.driving-dock{max-width:calc(100vw - 205px)!important}.driving-dock .dock-tab{grid-template-columns:22px 1fr;padding-inline:7px!important}.driving-dock .dock-tab small{display:none}.driving-dock .dock-grid{grid-template-columns:repeat(3,minmax(120px,1fr))}}
    @media(max-width:700px){.moon-drive-header{left:6px;right:6px;top:6px;width:auto;grid-template-columns:1fr 1fr;min-height:56px}.moon-drive-brand{display:none!important}.moon-drive-header>div{padding:4px 7px}.driving-dock{left:6px!important;right:6px!important;bottom:66px!important;max-width:none!important;transform:none!important;overflow:visible!important}.driving-dock .dock-primary{flex:1;grid-template-columns:repeat(4,1fr)}.driving-dock .dock-tab{display:flex!important;flex-direction:column;justify-content:center;gap:3px;min-height:52px!important;padding:5px 2px!important;text-align:center}.driving-dock .dock-tab-icon{width:22px;height:22px}.driving-dock .dock-tab-label{font-size:9px}.driving-dock .dock-tab small{display:none}.driving-dock .dock-overflow{bottom:124px;max-height:46vh;padding:10px}.driving-dock .dock-grid{grid-template-columns:repeat(2,minmax(0,1fr))}.driving-dock .dock-grid>button,.driving-dock .dock-grid>select{min-height:48px!important}.driving-dock>#moreControls{min-width:48px;flex-basis:48px}}
    @media(max-width:390px){.driving-dock .dock-grid{grid-template-columns:1fr}}
    @media(prefers-reduced-motion:reduce){.driving-dock *{scroll-behavior:auto!important;transition:none!important}}
  `;
  document.head.append(style);
  const liveSources={city:document.getElementById("city"),road:document.getElementById("roadEvent"),vehicle:document.getElementById("vn"),view:document.getElementById("view")};
  const syncHeader=()=>{driveHeader.querySelector("[data-live-city]").textContent=liveSources.city?.textContent||"En carretera";driveHeader.querySelector("[data-live-road]").textContent=liveSources.road?.textContent||"Sin incidencias";driveHeader.querySelector("[data-live-vehicle]").textContent=liveSources.vehicle?.textContent||"Aster Viento 3D";driveHeader.querySelector("[data-live-view]").textContent=liveSources.view?.textContent||"Exterior"};
  syncHeader();const liveObserver=new MutationObserver(syncHeader);Object.values(liveSources).forEach(node=>node&&liveObserver.observe(node,{childList:true,characterData:true,subtree:true}));

  const primary = document.createElement("div");
  primary.className = "dock-primary";
  const overflow = document.createElement("section");
  overflow.className = "dock-overflow";
  overflow.hidden = true;
  overflow.setAttribute("aria-label", "Controles del simulador");
  overflow.innerHTML = `<header class="dock-head"><div><b>Controles</b><br><small>Selecciona una categoría</small></div><button type="button" class="dock-close" aria-label="Cerrar controles">×</button></header><div class="dock-grid"></div>`;
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
    tab.innerHTML = `<span class="dock-tab-icon" aria-hidden="true">${group.icon}</span><span class="dock-tab-label">${group.label}</span><small>${group.hint}</small>`;
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
    overflow.querySelector(".dock-head small").textContent = group.hint;
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

  return { close: () => show(""), dispose() { observer.disconnect();liveObserver.disconnect();driveHeader.remove();if(hud)hud.hidden=false;controls.removeEventListener("click", interceptMore, true); document.removeEventListener("keydown", onKey, true); style.remove(); } };
}

export default createTransportDrivingDock;
