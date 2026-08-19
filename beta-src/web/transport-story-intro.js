import { transportStoryOrigins } from "./transport-story-campaign.js";

const titleOf = scene => scene.caption || scene.speaker || scene.id.replaceAll("-", " ");
const textOf = scene => scene.dialogue || scene.action || scene.prompt || "La ruta continúa.";

export function createStoryIntroSequence({ origin, choices = {} } = {}) {
  const scenes = (transportStoryOrigins[origin]?.chapter?.scenes || []).filter(scene => {
    if (scene.id === "truck-origin") return false;
    if (!scene.condition) return true;
    const expected = scene.condition.split(":")[1];
    return Object.values(choices).includes(expected) || expected === origin;
  });
  let index = 0;
  return {
    get current() { return scenes[index] || null; }, get index() { return index; }, get length() { return scenes.length; },
    next() { index += 1; return scenes[index] || null; },
    jumpTo(id) { const found = scenes.findIndex(scene => scene.id === id); index = found < 0 ? 0 : found; return scenes[index] || null; },
  };
}

export function createStoryIntro({ runtime, eventLog, reducedMotion = globalThis.matchMedia?.("(prefers-reduced-motion: reduce)")?.matches } = {}) {
  if (!runtime || !globalThis.document) return null;
  const root = document.createElement("section"); root.className = "story-intro"; root.hidden = true; root.setAttribute("role", "dialog"); root.setAttribute("aria-modal", "true");
  root.innerHTML = `<div class="story-intro-visual"><div class="story-intro-copy"><small>TODO SOBRE ALLTECH STUDIOS</small><h2 data-title></h2><p data-text></p><div data-choices class="story-intro-choices"></div><i data-progress></i><nav><button data-skip>Saltar</button><button data-next>Continuar</button></nav></div></div>`;
  document.body.append(root);
  const style = document.createElement("style"); style.textContent = `.story-intro{position:fixed;z-index:9000;inset:0;background:#02080ded;color:#fff;font-family:system-ui}.story-intro[hidden]{display:none}.story-intro-visual{position:absolute;inset:0;display:grid;align-items:end;padding:16px;background:radial-gradient(circle at 72% 24%,#19505c,#07151f 45%,#02070b);overflow:hidden}.story-intro-visual:before{content:"";position:absolute;inset:7% 7% 29%;border:1px solid #57e8d534;border-radius:36px;box-shadow:inset 0 0 100px #4ce6d016;transition:transform 7s ease}.story-intro.is-playing .story-intro-visual:before{transform:scale(1.08)}.story-intro-copy{position:relative;width:min(780px,100%);box-sizing:border-box;margin:0 auto max(12px,env(safe-area-inset-bottom));padding:clamp(20px,4vw,38px);border:1px solid #4ce6d04d;border-radius:24px;background:#06151de8;box-shadow:0 25px 90px #000c;backdrop-filter:blur(16px)}.story-intro small{color:#66ead8;font-weight:800;letter-spacing:.16em}.story-intro h2{margin:8px 0;font-size:clamp(26px,6vw,54px);text-transform:capitalize}.story-intro p{min-height:3em;color:#cce0e3;font-size:clamp(15px,2.4vw,20px)}.story-intro nav,.story-intro-choices{display:flex;gap:9px;flex-wrap:wrap}.story-intro button{min-height:44px;padding:10px 16px;border:1px solid #4ce6d05c;border-radius:11px;background:#0a2731;color:#fff;font-weight:800}.story-intro [data-next],.story-intro-choices button{background:linear-gradient(135deg,#e99737,#bd482f)}.story-intro [data-progress]{display:block;height:4px;margin:16px 0;background:#54e6d2;transition:width .3s}.story-intro-choices button{flex:1;min-width:180px}@media(max-width:600px){.story-intro-visual{padding:8px}.story-intro-copy{padding:18px;border-radius:18px}.story-intro-choices{display:grid}.story-intro-choices button{width:100%}}@media(prefers-reduced-motion:reduce){.story-intro-visual:before,.story-intro [data-progress]{transition:none}}`; document.head.append(style);
  const title = root.querySelector("[data-title]"), text = root.querySelector("[data-text]"), choicesBox = root.querySelector("[data-choices]"), progress = root.querySelector("[data-progress]"), next = root.querySelector("[data-next]");
  let sequence, timer;
  const clear = () => { if (timer) clearTimeout(timer); timer = null; };
  const finish = skipped => { clear(); root.hidden = true; root.classList.remove("is-playing"); runtime.completeIntro({ skipped }); };
  const render = () => {
    clear(); const scene = sequence?.current; if (!scene) return finish(false);
    runtime.updateIntro(scene.id); title.textContent = titleOf(scene); text.textContent = textOf(scene); choicesBox.replaceChildren();
    progress.style.width = `${Math.round((sequence.index + 1) / Math.max(1, sequence.length) * 100)}%`; next.hidden = Boolean(scene.choices?.length);
    for (const choice of scene.choices || []) { const button = document.createElement("button"); button.textContent = choice.label; button.onclick = () => { runtime.choose(scene.id, choice.id); eventLog?.record("career", "cinematic:decision", { origin:runtime.snapshot.origin, sceneId:scene.id, choiceId:choice.id }); sequence = createStoryIntroSequence({ origin:runtime.snapshot.origin, choices:runtime.snapshot.choices }); if (choice.next) sequence.jumpTo(choice.next); else sequence.next(); render(); }; choicesBox.append(button); }
    eventLog?.record("career", "cinematic:scene", { origin:runtime.snapshot.origin, sceneId:scene.id });
    if (!scene.choices?.length && !reducedMotion) timer = setTimeout(() => { sequence.next(); render(); }, Math.max(2200, Math.min(7000, Number(scene.duration || 4) * 700)));
  };
  next.onclick = () => { sequence?.next(); render(); }; root.querySelector("[data-skip]").onclick = () => finish(true);
  return { root, play({ restart = false } = {}) { const state = runtime.snapshot; if (!state.origin) return false; sequence = createStoryIntroSequence({ origin:state.origin, choices:state.choices }); if (!restart && state.intro?.sceneId && !state.intro.completed) sequence.jumpTo(state.intro.sceneId); root.hidden = false; root.classList.add("is-playing"); render(); return true; }, skip:() => finish(true) };
}

export default createStoryIntro;
