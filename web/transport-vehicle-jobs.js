import { createMissionRuntime } from "./transport-mission-runtime.js";

export const VEHICLE_JOB_STORAGE_KEY = "moon.transport.vehicle-jobs.v1";

const objective = (id, label, event, match, action) => Object.freeze({ id, label, event, ...(match ? { match } : {}), ...(action ? { action } : {}) });

export const VEHICLE_JOBS = Object.freeze([
  Object.freeze({ id:"bus-city-line", campaign:"transporte-público", title:"Línea Puerto Alba", summary:"Recoge pasajeros, completa las paradas y termina en la estación.", vehicle:"bus", reward:{xp:220,money:1450}, objectives:Object.freeze([
    objective("vehicle","Selecciona el autobús","vehicle:selected",{vehicle:"bus"}), objective("board","Abre la parada y embarca pasajeros","job:bus_boarded",null,"Embarcar pasajeros"), objective("stop","Atiende la parada central","job:bus_stop_served",null,"Completar parada"), objective("finish","Finaliza la línea sin abandonar pasajeros","job:bus_finished",null,"Finalizar línea")
  ])}),
  Object.freeze({ id:"ambulance-priority", campaign:"emergencias", title:"Código prioritario", summary:"Acude al aviso, estabiliza al paciente y realiza el traslado hospitalario.", vehicle:"ambulance", reward:{xp:360,money:2600}, objectives:Object.freeze([
    objective("vehicle","Selecciona la ambulancia","vehicle:selected",{vehicle:"ambulance"}), objective("siren","Activa luces y sirena","siren:enabled",{vehicle:"ambulance"}), objective("stabilize","Estabiliza al paciente en el lugar","job:patient_stabilized",null,"Estabilizar paciente"), objective("handover","Entrega al paciente en urgencias","job:patient_handover",null,"Entregar en urgencias")
  ])}),
  Object.freeze({ id:"fire-industrial-response", campaign:"emergencias", title:"Incendio industrial", summary:"Despliega el equipo, controla el foco y asegura el recinto.", vehicle:"fire", reward:{xp:440,money:3400}, objectives:Object.freeze([
    objective("vehicle","Selecciona el vehículo de bomberos","vehicle:selected",{vehicle:"fire"}), objective("siren","Activa la respuesta prioritaria","siren:enabled",{vehicle:"fire"}), objective("deploy","Despliega mangueras y equipo","job:fire_equipment_deployed",null,"Desplegar equipo"), objective("contain","Controla el incendio","job:fire_contained",null,"Controlar incendio"), objective("secure","Declara segura la zona","job:fire_scene_secured",null,"Asegurar zona")
  ])}),
  Object.freeze({ id:"recovery-motorway", campaign:"asistencia", title:"Rescate en autopista", summary:"Señaliza la avería, engancha el vehículo y retíralo con seguridad.", vehicle:"recovery", reward:{xp:300,money:2100}, objectives:Object.freeze([
    objective("vehicle","Selecciona la grúa","vehicle:selected",{vehicle:"recovery"}), objective("secure","Señaliza y protege la zona","job:recovery_scene_secured",null,"Señalizar zona"), objective("hook","Engancha el vehículo averiado","job:vehicle_hooked",null,"Enganchar vehículo"), objective("tow","Entrega el vehículo en el taller","job:vehicle_recovered",null,"Entregar en taller")
  ])}),
  Object.freeze({ id:"air-medical-cargo", campaign:"red-multimodal", title:"Puente aéreo médico", summary:"Carga suministros urgentes y completa el enlace aéreo.", vehicle:"cargo_plane", reward:{xp:620,money:7900}, objectives:Object.freeze([
    objective("vehicle","Selecciona el avión de carga","vehicle:selected",{vehicle:"cargo_plane"}), objective("load","Carga suministros médicos","job:air_cargo_loaded",null,"Cargar suministros"), objective("depart","Inicia el tramo aéreo","multimodal:air_started"), objective("deliver","Descarga en el aeropuerto de destino","job:air_cargo_delivered",null,"Entregar carga")
  ])}),
  Object.freeze({ id:"sea-relief-convoy", campaign:"red-multimodal", title:"Convoy marítimo de ayuda", summary:"Prepara contenedores humanitarios y completa la travesía portuaria.", vehicle:"container_ship", reward:{xp:680,money:9200}, objectives:Object.freeze([
    objective("vehicle","Selecciona el portacontenedores","vehicle:selected",{vehicle:"container_ship"}), objective("load","Estiba la ayuda humanitaria","job:sea_cargo_loaded",null,"Estibar contenedores"), objective("depart","Inicia el tramo marítimo","multimodal:sea_started"), objective("deliver","Descarga en el puerto de destino","job:sea_cargo_delivered",null,"Descargar en puerto")
  ])}),
]);

const escapeHtml = value => String(value ?? "").replace(/[&<>"']/g, character => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[character]));

export function createVehicleJobSystem({ storage, career, eventLog, controls, selectVehicle } = {}) {
  const runtime = createMissionRuntime({ storage, storageKey:VEHICLE_JOB_STORAGE_KEY, catalog:VEHICLE_JOBS });
  const record = (type, detail = {}) => eventLog?.record?.("jobs", type, detail, { severity:/failed/.test(type)?"warning":"info" });
  eventLog?.subscribe?.(event => runtime.handleEvent(event));
  runtime.subscribe(event => {
    if (event.type === "mission:completed") {
      const reward = event.detail.reward || {};
      if (reward.money) career?.record?.(reward.money, `Trabajo: ${event.detail.title}`, { jobId:event.detail.missionId });
      if (reward.xp) career?.addXp?.(reward.xp);
      career?.emit?.("job:completed", { jobId:event.detail.missionId, reward });
    } else if (event.type === "mission:failed") career?.emit?.("job:failed", { jobId:event.detail.missionId, reason:event.detail.reason });
    record(event.type.replace("mission:", "job:"), event.detail);
    render();
  });

  let panel = null, launcher = null;
  const currentObjective = () => { const active=runtime.activeMission; return active?.objectives?.[active.progress.objectiveIndex] || null; };
  const performAction = () => { const active=runtime.activeMission, item=currentObjective(); if (!active || !item?.action) return false; record(item.event, { vehicle:active.vehicle, jobId:active.id }); return true; };
  const start = id => { const job=VEHICLE_JOBS.find(item=>item.id===id); if (!job) return null; const active=runtime.start(id); selectVehicle?.(job.vehicle); record("vehicle:selected", { vehicle:job.vehicle, jobId:id }); render(); return active; };
  const fail = reason => runtime.fail(reason);

  function render() {
    if (!panel) return;
    const active=runtime.activeMission, snapshot=runtime.snapshot;
    if (active) {
      const index=active.progress.objectiveIndex, item=active.objectives[index];
      panel.innerHTML=`<header><div><small>${escapeHtml(active.campaign)}</small><h3>${escapeHtml(active.title)}</h3></div><button data-close aria-label="Cerrar">&times;</button></header><p>${escapeHtml(active.summary)}</p><div class="vehicle-job-progress"><i style="width:${Math.round(index/active.objectives.length*100)}%"></i></div><ol>${active.objectives.map((entry,i)=>`<li class="${i<index?"done":i===index?"current":""}">${escapeHtml(entry.label)}</li>`).join("")}</ol><footer>${item?.action?`<button data-action>${escapeHtml(item.action)}</button>`:"<span>Completa el objetivo en el mundo</span>"}<button data-fail>Abandonar</button></footer>`;
    } else {
      panel.innerHTML=`<header><div><small>TodoSobreAllTech Studios</small><h3>Central de trabajos</h3></div><button data-close aria-label="Cerrar">&times;</button></header><p>Elige una profesión. El progreso y las recompensas se guardan automáticamente.</p><div class="vehicle-job-grid">${VEHICLE_JOBS.map(job=>{const status=snapshot.completed.includes(job.id)?"Completado":"Disponible";return `<article><b>${escapeHtml(job.title)}</b><small>${escapeHtml(job.vehicle)} · ${job.reward.money.toLocaleString("es-ES")} € · ${job.reward.xp} XP</small><p>${escapeHtml(job.summary)}</p><button data-start="${job.id}" ${status==="Completado"?"disabled":""}>${status}</button></article>`}).join("")}</div>`;
    }
    panel.querySelector("[data-close]").onclick=()=>{panel.hidden=true;launcher?.classList.remove("on")};
    panel.querySelectorAll("[data-start]").forEach(button=>button.onclick=()=>start(button.dataset.start));
    panel.querySelector("[data-action]")?.addEventListener("click",performAction);
    panel.querySelector("[data-fail]")?.addEventListener("click",()=>fail("Trabajo abandonado por el jugador"));
  }

  if (globalThis.document) {
    const style=document.createElement("style"); style.textContent=`.vehicle-jobs-panel{position:fixed;z-index:24;inset:76px 16px 80px auto;width:min(520px,calc(100vw - 32px));overflow:auto;padding:16px;border:1px solid #35d9cb;border-radius:18px;background:#07141bf2;color:#eef;box-shadow:0 24px 80px #000c}.vehicle-jobs-panel[hidden]{display:none}.vehicle-jobs-panel header,.vehicle-jobs-panel footer{display:flex;align-items:center;justify-content:space-between;gap:10px}.vehicle-jobs-panel h3{margin:2px 0}.vehicle-jobs-panel p,.vehicle-jobs-panel small{color:#9bb6bf}.vehicle-job-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(205px,1fr));gap:10px}.vehicle-job-grid article,.vehicle-jobs-panel li{padding:10px;border:1px solid #294a55;border-radius:11px;background:#0b2029}.vehicle-job-grid small{display:block;margin-top:4px}.vehicle-jobs-panel ol{display:grid;gap:7px;padding:0;list-style:none}.vehicle-jobs-panel li.done{color:#65e9d6}.vehicle-jobs-panel li.current{border-color:#f39b36;color:#ffd098}.vehicle-job-progress{height:6px;background:#183039;border-radius:6px;overflow:hidden}.vehicle-job-progress i{display:block;height:100%;background:linear-gradient(90deg,#3ee0cc,#f39b36)}@media(max-width:600px){.vehicle-jobs-panel{inset:66px 8px 72px;width:auto}.vehicle-job-grid{grid-template-columns:1fr}}`;
    document.head.append(style); panel=document.createElement("aside"); panel.className="vehicle-jobs-panel";panel.hidden=true;panel.setAttribute("aria-label","Central de trabajos por vehículo");document.body.append(panel);
    launcher=document.createElement("button");launcher.id="vehicleJobsButton";launcher.textContent="Trabajos";controls?.append(launcher);launcher.onclick=()=>{panel.hidden=!panel.hidden;launcher.classList.toggle("on",!panel.hidden);render()}; render();
  }
  return { runtime, start, fail, performAction, render, get activeJob(){return runtime.activeMission;} };
}
