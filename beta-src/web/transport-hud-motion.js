const STYLE_ID = "moon-hud-motion";

export function createHudMotion({ hud, controls, cockpit } = {}) {
  const reduceMotion = matchMedia?.("(prefers-reduced-motion: reduce)")?.matches;
  const style = document.createElement("style");
  style.id = STYLE_ID;
  style.textContent = `
    .pill{position:relative;overflow:hidden;transition:.22s transform,.22s border-color,.22s background}
    .pill:after{content:"";position:absolute;inset:0;pointer-events:none;background:linear-gradient(105deg,transparent 20%,#ffffff18 48%,transparent 72%);transform:translateX(-130%)}
    .pill.moon-value-changed{border-color:#55e6d066!important;transform:translateY(-2px)}
    .pill.moon-value-changed:after{animation:moonHudSweep .55s ease-out}
    .moon-driving .hud{transform:translateY(0);opacity:.96}.moon-stopped .hud{opacity:1}
    .moon-driving .controls:not(.drive){opacity:.76;transform:translateX(-50%) translateY(3px)}
    .moon-control-pressed{transform:translateY(1px) scale(.96)!important;filter:brightness(1.18)}
    .dash-speed{font-variant-numeric:tabular-nums;transition:.15s color,.15s text-shadow}
    .moon-speeding .dash-speed{color:#ffd166!important;text-shadow:0 0 20px #f5b83a66}
    .moon-critical .dash-screen{animation:moonCriticalEdge .7s alternate infinite}
    .dash-alert{transition:.18s color,.18s transform,.18s opacity}.dash-alert.moon-alert-changed{animation:moonAlertIn .28s ease-out}
    @keyframes moonHudSweep{to{transform:translateX(130%)}}@keyframes moonAlertIn{from{opacity:.25;transform:translateY(5px)}to{opacity:1;transform:none}}@keyframes moonCriticalEdge{to{box-shadow:inset 0 0 34px #ff706534,0 0 0 1px #ff7065}}
    @media(max-width:700px){.moon-driving .controls:not(.drive){opacity:.55}.moon-driving .controls.drive{opacity:1}.controls.drive button{transition:.1s transform,.15s filter}.pill.moon-value-changed{transform:none}}
    @media(prefers-reduced-motion:reduce){.pill:after{display:none}.moon-critical .dash-screen{animation:none}.dash-alert.moon-alert-changed{animation:none}}
  `;
  document.head.append(style);
  const observers = [];
  const watch = (root, selector, callback) => root?.querySelectorAll(selector).forEach(node => {
    let previous = node.textContent;
    const observer = new MutationObserver(() => {
      const next = node.textContent;
      if (next === previous) return;
      const old = previous; previous = next; callback(node, next, old);
    });
    observer.observe(node, { childList:true, subtree:true, characterData:true }); observers.push(observer);
  });
  watch(hud, ".pill b", node => {
    const pill = node.closest(".pill"); pill?.classList.remove("moon-value-changed");
    if (!reduceMotion) requestAnimationFrame(() => pill?.classList.add("moon-value-changed"));
    clearTimeout(pill?._moonTimer); if (pill) pill._moonTimer=setTimeout(()=>pill.classList.remove("moon-value-changed"),620);
  });
  watch(cockpit, ".dash-alert", node => {
    node.classList.remove("moon-alert-changed"); requestAnimationFrame(()=>node.classList.add("moon-alert-changed"));
  });
  const press = event => {
    const button=event.target.closest("button"); if(!button)return; button.classList.add("moon-control-pressed");
    if(event.type==="pointerdown" && event.pointerType!=="mouse") navigator.vibrate?.(10);
  };
  const release = event => event.target.closest("button")?.classList.remove("moon-control-pressed");
  controls?.addEventListener("pointerdown",press); controls?.addEventListener("pointerup",release); controls?.addEventListener("pointercancel",release); controls?.addEventListener("pointerleave",release,true);
  let driving=false, speeding=false, critical=false;
  function update({ speed=0, limit=90, alertLevel="info" }={}) {
    const nextDriving=speed>2, nextSpeeding=speed>limit+2, nextCritical=alertLevel==="critical";
    if(nextDriving!==driving){driving=nextDriving;document.body.classList.toggle("moon-driving",driving);document.body.classList.toggle("moon-stopped",!driving)}
    if(nextSpeeding!==speeding){speeding=nextSpeeding;document.body.classList.toggle("moon-speeding",speeding)}
    if(nextCritical!==critical){critical=nextCritical;document.body.classList.toggle("moon-critical",critical);if(critical)navigator.vibrate?.([45,35,45])}
  }
  document.body.classList.add("moon-stopped");
  return { update, dispose(){observers.forEach(observer=>observer.disconnect());controls?.removeEventListener("pointerdown",press);controls?.removeEventListener("pointerup",release);controls?.removeEventListener("pointercancel",release);style.remove();document.body.classList.remove("moon-driving","moon-stopped","moon-speeding","moon-critical")} };
}

export default createHudMotion;
