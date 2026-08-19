const AIRPORTS = [
  { id: "nova", code: "NVL", name: "Nova Liria Internacional", runway: "09 / 27", x: 0, z: 60 },
  { id: "alba", code: "PBA", name: "Puerto Alba Costa", runway: "04 / 22", x: -34, z: -760 },
  { id: "valle", code: "VVE", name: "Valleverde Regional", runway: "16 / 34", x: 42, z: -1540 },
  { id: "solar", code: "BHS", name: "Bahía Solar Aeropuerto", runway: "11 / 29", x: -18, z: -2320 },
];

const MISSIONS = {
  helicopter: ["Rescate urbano", "Patrulla de costa", "Evacuación médica"],
  glider: ["Vuelo de precisión", "Ascenso térmico", "Circuito silencioso"],
  turboprop: ["Enlace regional", "Carga urgente", "Inspección aérea"],
  airliner: ["Ruta de pasajeros", "Aproximación instrumental", "Vuelo nocturno"],
  widebody: ["Corredor intercontinental", "Operación de alta capacidad", "Vuelo nocturno"],
  cargo_plane: ["Puente logístico", "Carga especial", "Ayuda humanitaria"],
};

function injectStyles() {
  if (document.querySelector("#aviationUiStyles")) return;
  const style = document.createElement("style");
  style.id = "aviationUiStyles";
  style.textContent = `
    .aviation-deck{position:fixed;z-index:7;inset:74px 14px auto auto;width:min(390px,calc(100vw - 28px));border:1px solid #5c8794;border-radius:20px;background:linear-gradient(145deg,#07151ff2,#102b35ed);box-shadow:0 24px 70px #000b;backdrop-filter:blur(18px);overflow:hidden}
    .aviation-deck[hidden]{display:none}.aviation-head{display:flex;justify-content:space-between;align-items:flex-start;padding:14px 15px 10px;border-bottom:1px solid #ffffff17}.aviation-head small{display:block;color:#55e7d1;text-transform:uppercase;letter-spacing:.13em;font-size:9px}.aviation-head h3{margin:3px 0 0;font-size:17px}.aviation-head button{padding:5px 9px}
    .aviation-instruments{display:grid;grid-template-columns:repeat(3,1fr);gap:7px;padding:10px}.aviation-gauge{min-width:0;padding:9px;border:1px solid #ffffff14;border-radius:12px;background:#06121bbb;text-align:center}.aviation-gauge small{display:block;color:#77929f;font-size:8px;text-transform:uppercase;letter-spacing:.08em}.aviation-gauge b{display:block;margin-top:4px;color:#eafbf9;font-size:17px}.aviation-gauge i{display:block;height:3px;margin-top:6px;border-radius:4px;background:linear-gradient(90deg,#4ce6d0 var(--value,0%),#1c3440 0)}
    .aviation-route{margin:0 10px 10px;padding:10px;border:1px solid #2b5562;border-radius:14px;background:#081b24}.aviation-route-line{display:flex;align-items:center;gap:9px}.aviation-airport{flex:1}.aviation-airport span{display:block;color:#60ead6;font-size:19px;font-weight:900}.aviation-airport small{display:block;color:#8da5af;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.aviation-track{height:2px;flex:1;background:#315260;position:relative}.aviation-track:after{content:'✈';position:absolute;left:var(--progress,0%);top:50%;transform:translate(-50%,-52%);color:#65eed9;font-size:17px;transition:left .25s}
    .aviation-form{display:grid;grid-template-columns:1fr 1fr;gap:7px;padding:0 10px 10px}.aviation-form label{color:#829aa5;font-size:9px;text-transform:uppercase}.aviation-form select,.aviation-form button{width:100%;margin-top:4px;padding:8px;border:1px solid #36536c;border-radius:10px;background:#0c202a;color:#eefafa}.aviation-form button{align-self:end;color:#65eed9;font-weight:800}.aviation-status{grid-column:1/-1;padding:8px;border-radius:9px;background:#102b32;color:#9be8dd;font-size:10px}
    body.aviation-active .controls.drive button[data-key="w"]:after{content:' · Potencia'}body.aviation-active .controls.drive button[data-key="s"]:after{content:' · Aerofreno'}body.aviation-active .osm-attribution{opacity:.45}
    @media(max-width:700px){.aviation-deck{inset:74px 6px auto;width:calc(100vw - 12px)}.aviation-instruments{grid-template-columns:repeat(3,1fr)}.aviation-gauge b{font-size:14px}.aviation-form{grid-template-columns:1fr}.aviation-route{display:none}}
  `;
  document.head.append(style);
}

export function createAviationUI({ fleetSelect, onSelectVehicle, onFlightMode }) {
  injectStyles();
  const panel = document.createElement("aside");
  panel.className = "aviation-deck";
  panel.id = "aviationDeck";
  panel.hidden = true;
  panel.innerHTML = `
    <header class="aviation-head"><div><small>Moon Aviation</small><h3 id="aviationVehicle">Operaciones aéreas</h3></div><button id="aviationClose" aria-label="Cerrar">×</button></header>
    <div class="aviation-instruments">
      <div class="aviation-gauge"><small>Velocidad</small><b id="aviationSpeed">0 kt</b><i id="aviationSpeedBar"></i></div>
      <div class="aviation-gauge"><small>Altitud</small><b id="aviationAltitude">0 ft</b><i id="aviationAltitudeBar"></i></div>
      <div class="aviation-gauge"><small>Vertical</small><b id="aviationVertical">0 fpm</b><i id="aviationVerticalBar"></i></div>
    </div>
    <div class="aviation-route"><div class="aviation-route-line"><div class="aviation-airport"><span id="aviationFromCode">NVL</span><small id="aviationFromName">Nova Liria</small></div><div class="aviation-track" id="aviationTrack"></div><div class="aviation-airport"><span id="aviationToCode">PBA</span><small id="aviationToName">Puerto Alba</small></div></div></div>
    <div class="aviation-form">
      <label>Destino<select id="aviationDestination"></select></label>
      <label>Misión<select id="aviationMission"></select></label>
      <button id="aviationFlightMode">Iniciar vuelo</button>
      <div class="aviation-status" id="aviationStatus">Selecciona una aeronave en Flota aire y mar.</div>
    </div>`;
  document.body.append(panel);
  const q = selector => panel.querySelector(selector);
  const destination = q("#aviationDestination"), mission = q("#aviationMission");
  destination.innerHTML = AIRPORTS.slice(1).map(a => `<option value="${a.id}">${a.code} · ${a.name}</option>`).join("");
  let active = false, descriptor = null, origin = AIRPORTS[0], target = AIRPORTS[1];
  const syncMissionOptions = () => {
    const list = descriptor ? (MISSIONS[descriptor.kind] || MISSIONS.turboprop) : [];
    mission.innerHTML = list.map(name => `<option>${name}</option>`).join("");
  };
  destination.onchange = () => { target = AIRPORTS.find(a => a.id === destination.value) || AIRPORTS[1]; renderRoute(); };
  const renderRoute = () => {
    q("#aviationFromCode").textContent = origin.code; q("#aviationFromName").textContent = origin.name;
    q("#aviationToCode").textContent = target.code; q("#aviationToName").textContent = target.name;
  };
  q("#aviationClose").onclick = () => { panel.hidden = true; };
  q("#aviationFlightMode").onclick = () => {
    if (!descriptor) return;
    active = !active; document.body.classList.toggle("aviation-active", active);
    q("#aviationFlightMode").textContent = active ? "Finalizar vuelo" : "Iniciar vuelo";
    q("#aviationStatus").textContent = active ? `${mission.value} · pista ${origin.runway} · rumbo a ${target.code}` : "Vuelo en espera en plataforma";
    onFlightMode?.(active, { origin, target, mission: mission.value, descriptor });
  };
  fleetSelect?.addEventListener("change", () => { if (fleetSelect.value) onSelectVehicle?.(fleetSelect.value); });
  renderRoute();
  return {
    setVehicle(nextDescriptor) {
      descriptor = nextDescriptor || null;
      const isAir = Boolean(descriptor);
      document.body.classList.toggle("aviation-selected", isAir);
      panel.hidden = !isAir;
      active = false; document.body.classList.remove("aviation-active"); q("#aviationFlightMode").textContent = "Iniciar vuelo";
      if (!isAir) return;
      q("#aviationVehicle").textContent = descriptor.name; syncMissionOptions();
      q("#aviationStatus").textContent = `${descriptor.kind === "helicopter" ? "Helipuerto" : "Puerta A12"} · listo para planificación`;
    },
    update({ speedKmh = 0, altitudeMeters = 0, verticalSpeed = 0, progress = 0 }) {
      if (!descriptor || panel.hidden) return;
      const knots = Math.round(speedKmh * .539957), feet = Math.round(altitudeMeters * 3.28084), fpm = Math.round(verticalSpeed * 196.85);
      q("#aviationSpeed").textContent = `${knots} kt`; q("#aviationAltitude").textContent = `${feet} ft`; q("#aviationVertical").textContent = `${fpm >= 0 ? "+" : ""}${fpm} fpm`;
      q("#aviationSpeedBar").style.setProperty("--value", `${Math.min(100, knots / 4)}%`); q("#aviationAltitudeBar").style.setProperty("--value", `${Math.min(100, feet / 100)}%`); q("#aviationVerticalBar").style.setProperty("--value", `${Math.min(100, 50 + fpm / 30)}%`);
      q("#aviationTrack").style.setProperty("--progress", `${Math.max(0, Math.min(100, progress * 100))}%`);
    },
    isActive: () => active,
    dispose() { panel.remove(); document.body.classList.remove("aviation-active", "aviation-selected"); },
  };
}

export { AIRPORTS };
