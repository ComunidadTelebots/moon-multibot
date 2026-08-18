export const MISSION_STORAGE_KEY = "moon.transport.missions.v1";
export const MISSION_SCHEMA_VERSION = 1;

const clone = value => JSON.parse(JSON.stringify(value));

export const TRANSPORT_MISSIONS = Object.freeze([
  Object.freeze({
    id: "cabrera-fire-corridor",
    campaign: "emergency-network",
    title: "Cabrera bajo humo",
    summary: "Abre un corredor seguro para que bomberos y suministros alcancen los pueblos aislados.",
    vehicle: "fire",
    reward: { xp: 480, money: 7200 },
    objectives: Object.freeze([
      Object.freeze({ id: "deploy", label: "Despliega el camión de bomberos", event: "engine:started", match: { vehicle: "fire" } }),
      Object.freeze({ id: "secure", label: "Asegura una carga de apoyo", event: "cargo:secured" }),
      Object.freeze({ id: "corridor", label: "Inicia el corredor multimodal de emergencia", event: "multimodal:road_started" }),
    ]),
  }),
  Object.freeze({
    id: "aurora-mountain-night",
    campaign: "aurora-legacy",
    chapter: "chapter-1",
    storyMission: "mountain-night",
    requires: Object.freeze(["cabrera-fire-corridor"]),
    title: "La noche de la montaña",
    summary: "Lleva medicinas y provisiones refrigeradas a Valleverde tras el temporal.",
    vehicle: "truck",
    reward: { xp: 620, money: 9400 },
    objectives: Object.freeze([
      Object.freeze({ id: "cold-profile", label: "Prepara la carga refrigerada", event: "cargo:profile_selected", match: { type: "cold" } }),
      Object.freeze({ id: "reefer", label: "Activa la cadena de frío", event: "cargo:reefer_started" }),
      Object.freeze({ id: "secure", label: "Asegura las medicinas", event: "cargo:secured" }),
      Object.freeze({ id: "depart", label: "Arranca el camión rumbo a Valleverde", event: "engine:started", match: { vehicle: "truck" } }),
      Object.freeze({ id: "deliver", label: "Completa la entrega de emergencia", event: "contract:completed" }),
    ]),
  }),
  Object.freeze({
    id: "legal-weight-corridor",
    campaign: "continental-haulage",
    title: "Carga dentro de la ley",
    summary: "Prepara el conjunto y supera el primer control de peso de la red continental.",
    vehicle: "truck",
    reward: { xp: 260, money: 1800 },
    objectives: Object.freeze([
      Object.freeze({ id: "start", label: "Arranca el camión", event: "engine:started", match: { vehicle: "truck" } }),
      Object.freeze({ id: "secure", label: "Revisa y asegura la mercancía", event: "cargo:secured" }),
      Object.freeze({ id: "inspect", label: "Supera un control de peso", event: "inspection:passed" }),
    ]),
  }),
]);

const freshState = () => ({ schema: MISSION_SCHEMA_VERSION, activeId: null, missions: {}, completed: [] });

function normalize(raw, catalog) {
  const state = raw && typeof raw === "object" ? raw : freshState();
  const validIds = new Set(catalog.map(item => item.id));
  const missions = {};
  for (const [id, progress] of Object.entries(state.missions || {})) {
    if (!validIds.has(id) || !progress || typeof progress !== "object") continue;
    missions[id] = {
      status: ["available", "active", "completed", "failed"].includes(progress.status) ? progress.status : "available",
      objectiveIndex: Math.max(0, Number(progress.objectiveIndex) || 0),
      startedAt: Number(progress.startedAt) || null,
      completedAt: Number(progress.completedAt) || null,
    };
  }
  const completed = [...new Set((state.completed || []).filter(id => validIds.has(id)))];
  const activeId = validIds.has(state.activeId) && missions[state.activeId]?.status === "active" ? state.activeId : null;
  return { schema: MISSION_SCHEMA_VERSION, activeId, missions, completed };
}

const matches = (expected, detail) => Object.entries(expected || {}).every(([key, value]) => detail?.[key] === value);

export function createMissionRuntime(options = {}) {
  const storage = options.storage ?? globalThis.localStorage ?? null;
  const storageKey = options.storageKey || MISSION_STORAGE_KEY;
  const catalog = options.catalog || TRANSPORT_MISSIONS;
  const listeners = new Set();
  let parsed = null;
  try { parsed = JSON.parse(storage?.getItem(storageKey) || "null"); } catch {}
  let state = normalize(parsed, catalog);
  const persist = () => { try { storage?.setItem(storageKey, JSON.stringify(state)); } catch {} };
  const emit = (type, detail = {}) => {
    const payload = { type, detail: clone(detail), state: clone(state) };
    listeners.forEach(listener => listener(payload));
    persist();
    return payload;
  };
  const definition = id => catalog.find(item => item.id === id) || null;
  const progressFor = id => state.missions[id] || { status: "available", objectiveIndex: 0, startedAt: null, completedAt: null };
  const requirementsMet = mission => (mission?.requires || []).every(id => state.completed.includes(id));

  return {
    get catalog() { return clone(catalog); },
    get snapshot() { return clone(state); },
    get activeMission() {
      const mission = definition(state.activeId);
      return mission ? { ...clone(mission), progress: clone(progressFor(mission.id)) } : null;
    },
    isUnlocked(id) {
      const mission = definition(id);
      return Boolean(mission && requirementsMet(mission));
    },
    subscribe(listener) { listeners.add(listener); return () => listeners.delete(listener); },
    start(id) {
      const mission = definition(id);
      if (!mission) throw new Error("Misión desconocida");
      if (!requirementsMet(mission)) throw new Error("Misión bloqueada");
      if (state.activeId && state.activeId !== id) throw new Error("Ya hay una misión activa");
      const previous = progressFor(id);
      if (previous.status === "completed") return this.activeMission;
      state.activeId = id;
      state.missions[id] = previous.status === "failed"
        ? { status: "active", objectiveIndex: 0, startedAt: Date.now(), completedAt: null }
        : { ...previous, status: "active", startedAt: previous.startedAt || Date.now() };
      emit("mission:started", { missionId: id, title: mission.title });
      return this.activeMission;
    },
    handleEvent(event) {
      const mission = definition(state.activeId);
      if (!mission || !event) return null;
      const progress = progressFor(mission.id);
      const objective = mission.objectives[progress.objectiveIndex];
      if (!objective || event.type !== objective.event || !matches(objective.match, event.detail)) return null;
      progress.objectiveIndex += 1;
      if (progress.objectiveIndex >= mission.objectives.length) {
        progress.status = "completed";
        progress.completedAt = Date.now();
        state.completed = [...new Set([...state.completed, mission.id])];
        state.activeId = null;
        state.missions[mission.id] = progress;
        return emit("mission:completed", { missionId: mission.id, title: mission.title, reward: mission.reward });
      }
      state.missions[mission.id] = progress;
      return emit("mission:objective_completed", { missionId: mission.id, objectiveId: objective.id, nextObjective: mission.objectives[progress.objectiveIndex].id });
    },
    fail(reason = "Misión cancelada") {
      const mission = definition(state.activeId);
      if (!mission) return null;
      const progress = progressFor(mission.id);
      progress.status = "failed";
      progress.failedAt = Date.now();
      progress.failureReason = String(reason).slice(0, 240);
      state.missions[mission.id] = progress;
      state.activeId = null;
      return emit("mission:failed", { missionId: mission.id, title: mission.title, reason: progress.failureReason });
    },
  };
}

export function createMissionPanel({ runtime, controls, eventLog } = {}) {
  if (!runtime || !globalThis.document) return null;
  const style = document.createElement("style");
  style.textContent = `.mission-panel{position:fixed;z-index:15;inset:72px 14px auto auto;width:min(420px,calc(100vw - 28px));padding:14px;border:1px solid #35d9cb;border-radius:18px;background:linear-gradient(145deg,#07131df5,#102a33f2);box-shadow:0 24px 70px #000b;color:#eff}.mission-panel[hidden]{display:none}.mission-panel header{display:flex;justify-content:space-between;gap:8px}.mission-panel h3{margin:0}.mission-panel p{color:#9bb6bf}.mission-objectives{display:grid;gap:7px;padding:0;list-style:none}.mission-objectives li{padding:9px;border:1px solid #294a55;border-radius:10px;background:#0a1a24}.mission-objectives li.done{color:#65e9d6;text-decoration:line-through}.mission-objectives li.current{border-color:#f39b36;color:#ffd098}.mission-panel footer{display:flex;justify-content:flex-end}`;
  document.head.append(style);
  const panel = document.createElement("aside"); panel.className = "mission-panel"; panel.hidden = true;
  const button = document.createElement("button"); button.id = "missionsButton"; button.textContent = "Misiones"; controls?.append(button);
  document.body.append(panel);
  const render = () => {
    const active = runtime.activeMission;
    const mission = active || runtime.catalog.find(item => !runtime.snapshot.completed.includes(item.id) && runtime.isUnlocked(item.id));
    if (!mission) { panel.innerHTML = `<header><h3>Misiones completadas</h3><button data-close>×</button></header><p>Has completado las operaciones disponibles.</p>`; }
    else {
      const index = active?.progress.objectiveIndex ?? 0;
      panel.innerHTML = `<header><div><small>${mission.campaign}</small><h3>${mission.title}</h3></div><button data-close>×</button></header><p>${mission.summary}</p><ol class="mission-objectives">${mission.objectives.map((objective, i) => `<li class="${i < index ? "done" : i === index && active ? "current" : ""}">${objective.label}</li>`).join("")}</ol><footer>${active ? "<b>Misión activa</b>" : `<button data-start="${mission.id}">Comenzar misión</button>`}</footer>`;
    }
    panel.querySelector("[data-close]").onclick = () => { panel.hidden = true; button.classList.remove("on"); };
    const start = panel.querySelector("[data-start]"); if (start) start.onclick = () => { runtime.start(start.dataset.start); render(); };
  };
  button.onclick = () => { panel.hidden = !panel.hidden; button.classList.toggle("on", !panel.hidden); render(); };
  runtime.subscribe(event => { eventLog?.record("missions", event.type, event.detail); if (!panel.hidden) render(); });
  render();
  return { panel, button, render };
}
