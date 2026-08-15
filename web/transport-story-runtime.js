import { STORY_TRUCK_ORIGINS, transportStoryOrigins } from "./transport-story-campaign.js";

export const STORY_STORAGE_KEY = "moon.transport.story.v1";

const copy = value => JSON.parse(JSON.stringify(value));
const initialState = () => ({ version: 1, origin: null, choices: {}, variables: {}, intro: { sceneId:null, completed:false, skipped:false }, startedAt: null, updatedAt: null });

function mergeEffects(target, effects = {}) {
  for (const [key, value] of Object.entries(effects)) {
    target[key] = typeof value === "number" ? (Number(target[key]) || 0) + value : value;
  }
}

function normalize(raw) {
  const state = raw && typeof raw === "object" ? raw : initialState();
  const origin = STORY_TRUCK_ORIGINS[state.origin] ? state.origin : null;
  return {
    ...initialState(), ...state, origin,
    choices: state.choices && typeof state.choices === "object" ? state.choices : {},
    variables: state.variables && typeof state.variables === "object" ? state.variables : {},
    intro: state.intro && typeof state.intro === "object" ? { sceneId:null, completed:false, skipped:false, ...state.intro } : { sceneId:null, completed:false, skipped:false },
  };
}

export function createStoryRuntime({ storage = globalThis.localStorage ?? null, storageKey = STORY_STORAGE_KEY } = {}) {
  const listeners = new Set();
  let parsed = null;
  try { parsed = JSON.parse(storage?.getItem(storageKey) || "null"); } catch {}
  let state = normalize(parsed);
  const persist = () => { try { storage?.setItem(storageKey, JSON.stringify(state)); } catch {} };
  const emit = (type, detail) => {
    const event = { type, detail: copy(detail), state: copy(state) };
    listeners.forEach(listener => listener(event)); persist(); return event;
  };
  return {
    get snapshot() { return copy(state); },
    get origin() { return state.origin ? copy(STORY_TRUCK_ORIGINS[state.origin]) : null; },
    subscribe(listener) { listeners.add(listener); return () => listeners.delete(listener); },
    selectOrigin(originId) {
      const origin = STORY_TRUCK_ORIGINS[originId];
      if (!origin) throw new Error("Origen de campaña desconocido");
      state = { ...initialState(), origin: originId, startedAt: Date.now(), updatedAt: Date.now(), variables: { truckOrigin: originId, debt: origin.startingDebt } };
      // Aurora's shared prologue contains an earlier truck picker; selecting the
      // campaign already resolves it, so the panel can continue to the route choice.
      if (originId === "aurora") state.choices["truck-origin"] = "aurora";
      return emit("story:origin_selected", { originId, title: transportStoryOrigins[originId].title, debt: origin.startingDebt });
    },
    choose(sceneId, choiceId) {
      if (!state.origin) throw new Error("Elige primero una campaña");
      const scenes = transportStoryOrigins[state.origin]?.chapter?.scenes || [];
      const scene = scenes.find(item => item.id === sceneId);
      const choice = scene?.choices?.find(item => item.id === choiceId);
      if (!choice) throw new Error("Decisión no disponible para esta campaña");
      state.choices[sceneId] = choiceId;
      mergeEffects(state.variables, choice.effects);
      state.updatedAt = Date.now();
      return emit("story:choice_made", { originId: state.origin, sceneId, choiceId, label: choice.label, effects: choice.effects || {}, next: choice.next || null });
    },
    updateIntro(sceneId) {
      if (!state.origin) throw new Error("Elige primero una campaña");
      state.intro = { sceneId:String(sceneId || ""), completed:false, skipped:false }; state.updatedAt = Date.now();
      return emit("story:intro_scene", { originId:state.origin, sceneId:state.intro.sceneId });
    },
    completeIntro({ skipped = false } = {}) {
      if (!state.origin) throw new Error("Elige primero una campaña");
      state.intro = { ...state.intro, completed:true, skipped:Boolean(skipped) }; state.updatedAt = Date.now();
      return emit(skipped ? "story:intro_skipped" : "story:intro_completed", { originId:state.origin, sceneId:state.intro.sceneId });
    },
    reset() { state = initialState(); return emit("story:reset", {}); },
  };
}

export function createStoryPanel({ runtime, controls, eventLog, introPlayer } = {}) {
  if (!runtime || !globalThis.document) return null;
  const button = document.createElement("button"); button.id = "storyButton"; button.textContent = "Historia"; controls?.append(button);
  const panel = document.createElement("aside"); panel.className = "mission-panel story-panel"; panel.hidden = true; document.body.append(panel);
  const render = () => {
    const state = runtime.snapshot;
    if (!state.origin) {
      panel.innerHTML = `<header><div><small>Rutas del Continente</small><h3>Elige tu comienzo</h3></div><button data-close>×</button></header><p>Cada campaña conserva sus decisiones y abre una carrera diferente.</p><div class="story-options">${Object.values(STORY_TRUCK_ORIGINS).map(origin => `<button data-origin="${origin.id}"><b>${origin.name}</b><small>${transportStoryOrigins[origin.id].title}</small></button>`).join("")}</div>`;
    } else {
      const chapter = transportStoryOrigins[state.origin].chapter;
      const pending = (chapter.scenes || []).find(scene => scene.choices?.length && !state.choices[scene.id]);
      panel.innerHTML = `<header><div><small>${runtime.origin.name}</small><h3>${transportStoryOrigins[state.origin].title}</h3></div><button data-close>×</button></header>${pending ? `<p>${pending.prompt}</p><div class="story-options">${pending.choices.map(choice => `<button data-scene="${pending.id}" data-choice="${choice.id}">${choice.label}</button>`).join("")}</div>` : `<p>Prólogo configurado. Tus decisiones quedarán activas durante la partida.</p><ol class="mission-objectives">${Object.entries(state.choices).map(([scene, choice]) => `<li class="done">${scene}: ${choice}</li>`).join("")}</ol>`}<footer><button data-reset>Cambiar campaña</button></footer>`;
    }
    panel.querySelector("[data-close]").onclick = () => { panel.hidden = true; button.classList.remove("on"); };
    panel.querySelectorAll("[data-origin]").forEach(item => item.onclick = () => { runtime.selectOrigin(item.dataset.origin); render(); panel.hidden = true; button.classList.remove("on"); introPlayer?.play(); });
    panel.querySelectorAll("[data-choice]").forEach(item => item.onclick = () => { runtime.choose(item.dataset.scene, item.dataset.choice); render(); });
    const reset = panel.querySelector("[data-reset]"); if (reset) reset.onclick = () => { runtime.reset(); render(); };
  };
  const style = document.createElement("style"); style.textContent = `.story-panel{inset:72px auto auto 14px}.story-options{display:grid;gap:8px}.story-options button{text-align:left;border-color:#315864;background:#0a2029}.story-options button b,.story-options button small{display:block}.story-options button small{margin-top:3px;color:#8fb0ba}`; document.head.append(style);
  button.onclick = () => { panel.hidden = !panel.hidden; button.classList.toggle("on", !panel.hidden); render(); };
  runtime.subscribe(event => eventLog?.record("career", event.type, event.detail)); render();
  return { button, panel, render };
}

export default createStoryRuntime;
