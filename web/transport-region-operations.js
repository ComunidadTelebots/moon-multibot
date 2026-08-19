const REGION_PROFILES = Object.freeze({
  "Nova Liria": { code:"NL", kind:"Capital industrial", climate:"Meseta", hub:"Centro intermodal Norte", access:"A-10 · E-27", facilities:["Aduana", "Taller 24 h", "Carga EV"] },
  "Puerto Alba": { code:"PA", kind:"Distrito portuario", climate:"Atlántico", hub:"Terminal marítima Alba", access:"A-10 · Muelle 4", facilities:["Ferri", "Combustible", "Descanso"] },
  "Valleverde": { code:"VV", kind:"Corredor agrícola", climate:"Interior", hub:"Mercado logístico Verde", access:"E-27 · N-6", facilities:["Pesaje", "Taller", "Área segura"] },
  "Bahía Solar": { code:"BS", kind:"Costa logística", climate:"Mediterráneo", hub:"Puerto y aeropuerto Solar", access:"A-42 · AP-7", facilities:["Aeropuerto", "Puerto", "Carga pesada"] },
});

const fallbackProfile = city => ({ code:(city || "--").slice(0,2).toUpperCase(), kind:"Región conectada", climate:"Datos en ruta", hub:`Nodo logístico ${city || "regional"}`, access:"Red europea", facilities:["Combustible", "Descanso", "Asistencia"] });

export function createRegionOperationsPanel({ controls, cityElement }) {
  const style=document.createElement("style");
  style.textContent=`
    .region-ops{position:fixed;z-index:7;right:12px;top:84px;width:min(328px,calc(100vw - 24px));border:1px solid #ffffff20;border-radius:19px;background:linear-gradient(145deg,#08131df2,#102a33e8);box-shadow:0 22px 60px #0009;backdrop-filter:blur(18px);overflow:hidden;transition:.22s transform,.22s opacity}.region-ops[hidden]{display:none}.region-ops__hero{display:grid;grid-template-columns:48px 1fr auto;gap:10px;align-items:center;padding:12px;border-bottom:1px solid #ffffff14;background:linear-gradient(105deg,#12323c,#0a1822)}.region-ops__code{display:grid;place-items:center;width:48px;height:48px;border:1px solid #5ee8d2;border-radius:14px;background:#0b2529;color:#62f0db;font:900 16px system-ui;box-shadow:inset 0 0 22px #45dcc51d}.region-ops h2{margin:0;color:#f1fffc;font-size:15px}.region-ops__hero p{margin:3px 0 0;color:#80aab3;font-size:10px;text-transform:uppercase;letter-spacing:.09em}.region-ops__close{align-self:start;padding:4px 7px!important;border:0;background:transparent;color:#8fa8b0}.region-ops__body{padding:11px}.region-ops__route{display:grid;grid-template-columns:1fr auto;gap:5px 10px;padding:9px 10px;border:1px solid #31515d;border-radius:12px;background:#091923}.region-ops__route small{color:#7595a0;font-size:9px;text-transform:uppercase;letter-spacing:.1em}.region-ops__route b{grid-column:1/-1;color:#e9fffb;font-size:13px}.region-ops__access{color:#59e7d1;font-size:11px}.region-ops__signals{display:flex;gap:6px;margin:9px 0}.region-ops__signal{flex:1;padding:7px;border-radius:9px;background:#10232c;color:#90aab2;font-size:9px;text-align:center}.region-ops__signal i{display:inline-block;width:6px;height:6px;margin-right:4px;border-radius:50%;background:#55e6cf;box-shadow:0 0 8px #55e6cf}.region-ops__signal.warn i{background:#ffc65b;box-shadow:0 0 8px #ffc65b}.region-ops__facilities{display:grid;grid-template-columns:repeat(3,1fr);gap:6px}.region-ops__facility{min-width:0;padding:8px 5px;border:1px solid #ffffff12;border-radius:9px;background:#0d1b24;color:#bcd0d4;font-size:9px;text-align:center;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.region-ops__footer{display:flex;justify-content:space-between;margin-top:9px;color:#76939c;font-size:9px}.region-ops__footer b{color:#d9f9f3}@media(max-width:700px){.region-ops{top:76px;right:6px;width:min(320px,calc(100vw - 12px))}.region-ops__signals{display:none}.region-ops__body{padding:8px}.region-ops__hero{padding:9px}.region-ops__code{width:40px;height:40px}.region-ops__facility{padding:6px 4px}}
  `;
  document.head.append(style);
  const panel=document.createElement("aside"); panel.className="region-ops"; panel.hidden=true; panel.setAttribute("aria-label","Centro operativo regional");
  panel.innerHTML=`<div class="region-ops__hero"><div class="region-ops__code">NL</div><div><h2>Nova Liria</h2><p>Capital industrial · Meseta</p></div><button class="region-ops__close" aria-label="Cerrar">×</button></div><div class="region-ops__body"><div class="region-ops__route"><small>Nodo de esta región</small><span class="region-ops__access">A-10 · E-27</span><b>Centro intermodal Norte</b></div><div class="region-ops__signals"><span class="region-ops__signal"><i></i>Vía abierta</span><span class="region-ops__signal"><i></i>Servicios activos</span><span class="region-ops__signal"><i></i>Zona segura</span></div><div class="region-ops__facilities"></div><div class="region-ops__footer"><span>Próximo servicio <b data-next>En ruta</b></span><span>PK <b data-km>0.0</b></span></div></div>`;
  document.body.append(panel);
  const button=document.createElement("button"); button.id="regionOperationsButton"; button.textContent="Región / servicios"; controls?.append(button);
  const close=()=>{panel.hidden=true;button.classList.remove("on")};
  panel.querySelector(".region-ops__close").onclick=close;
  button.onclick=()=>{panel.hidden=!panel.hidden;button.classList.toggle("on",!panel.hidden)};
  let current="", lastPaint=0;
  function update({ city=cityElement?.textContent, distance=0, service=null, roadState="Vía abierta", now=performance.now() }={}) {
    if(now-lastPaint<180 && city===current)return; lastPaint=now;
    const profile=REGION_PROFILES[city]||fallbackProfile(city); current=city;
    panel.querySelector(".region-ops__code").textContent=profile.code;
    panel.querySelector("h2").textContent=city||"Región";
    panel.querySelector(".region-ops__hero p").textContent=`${profile.kind} · ${profile.climate}`;
    panel.querySelector(".region-ops__access").textContent=profile.access;
    panel.querySelector(".region-ops__route b").textContent=profile.hub;
    panel.querySelector(".region-ops__facilities").replaceChildren(...profile.facilities.map(name=>{const item=document.createElement("span");item.className="region-ops__facility";item.textContent=name;item.title=name;return item}));
    const signal=panel.querySelector(".region-ops__signal"); signal.lastChild.textContent=roadState||"Vía abierta"; signal.classList.toggle("warn",/obra|incidencia|reduzca/i.test(roadState||""));
    panel.querySelector("[data-next]").textContent=service&&service.distance<1200?`${service.name||({workshop:"Taller",fuel:"Combustible",rest:"Descanso",charging:"Carga EV"}[service.type]||"Servicio")} · ${Math.round(service.distance)} m`:"En ruta";
    panel.querySelector("[data-km]").textContent=(distance/1000).toFixed(1);
  }
  update();
  return { panel, button, update, open(){panel.hidden=false;button.classList.add("on")}, close };
}
