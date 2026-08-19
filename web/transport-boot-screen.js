(function (root) {
  const PHASES = ["DOM", "Modulos", "Render", "Mundo"];

  function normalizePhase(value) {
    const index = typeof value === "number" ? value : PHASES.findIndex(item => item.toLowerCase() === String(value || "").toLowerCase());
    return Math.max(0, Math.min(PHASES.length - 1, index < 0 ? 0 : index));
  }

  function phaseProgress(value) {
    return [12, 38, 68, 92][normalizePhase(value)];
  }

  function mountTransportBoot({ document = root.document, reload = () => root.location.reload() } = {}) {
    if (!document) return null;
    document.querySelector("#transportBoot")?.remove();
    const style = document.createElement("style");
    style.id = "transportBootStyle";
    style.textContent = `
      .transport-boot{position:fixed;z-index:99999;inset:0;display:grid;place-items:center;padding:max(18px,env(safe-area-inset-top)) max(18px,env(safe-area-inset-right)) max(18px,env(safe-area-inset-bottom)) max(18px,env(safe-area-inset-left));background:radial-gradient(circle at 50% 18%,#15333d 0,#08151e 42%,#03080d 100%);color:#eefcfb;font:14px/1.45 system-ui,sans-serif;transition:.35s opacity}.transport-boot.is-closing{opacity:0;pointer-events:none}.transport-boot-card{width:min(620px,100%);padding:clamp(22px,5vw,48px);border:1px solid #55e6d03d;border-radius:28px;background:linear-gradient(145deg,#102631ed,#07131bed);box-shadow:0 28px 100px #000c,inset 0 1px #ffffff18}.transport-boot-brand{color:#66ebd8;font-size:10px;font-weight:800;letter-spacing:.2em;text-transform:uppercase}.transport-boot h1{margin:8px 0 5px;font-size:clamp(30px,7vw,58px);line-height:.95;letter-spacing:-.055em}.transport-boot-sub{margin:0 0 28px;color:#91abb5}.transport-boot-track{height:7px;border-radius:99px;background:#172a32;overflow:hidden}.transport-boot-track i{display:block;width:12%;height:100%;border-radius:inherit;background:linear-gradient(90deg,#47dbc5,#ff9637);box-shadow:0 0 22px #55e6d070;transition:.35s width}.transport-boot-meta{display:flex;justify-content:space-between;gap:14px;margin:10px 0 20px;color:#91abb5;font-size:11px}.transport-boot-meta b{color:#e9f8f6}.transport-boot-phases{display:grid;grid-template-columns:repeat(4,1fr);gap:6px}.transport-boot-phase{padding:8px 4px;border:1px solid #ffffff12;border-radius:9px;color:#657c86;text-align:center;font-size:10px}.transport-boot-phase.done{border-color:#4ce6d04d;background:#123a36;color:#70efdc}.transport-boot-phase.active{color:#fff;box-shadow:inset 0 -2px #ff9637}.transport-boot-actions{display:flex;gap:9px;margin-top:20px}.transport-boot-actions button{flex:1;min-height:48px;border:1px solid #4ce6d054;border-radius:12px;background:#102934;color:#eaf9f8;font-weight:800}.transport-boot-actions .enter{border-color:#ffad58;background:linear-gradient(135deg,#f19a35,#c44e32);color:#fff}.transport-boot-error{margin-top:16px;padding:12px;border:1px solid #ff725f;border-radius:12px;background:#351216;color:#ffd9d4;white-space:pre-wrap;overflow-wrap:anywhere}.transport-boot[aria-busy=true] .transport-boot-card::before{content:"";display:block;width:34px;height:34px;margin:0 0 22px;border:3px solid #ffffff20;border-top-color:#4ce6d0;border-radius:50%;animation:transportBootSpin .9s linear infinite}@keyframes transportBootSpin{to{transform:rotate(360deg)}}@media(max-width:520px){.transport-boot-card{padding:22px;border-radius:20px}.transport-boot-phases{grid-template-columns:repeat(2,1fr)}.transport-boot-meta{align-items:flex-start;flex-direction:column;gap:3px}}@media(prefers-reduced-motion:reduce){.transport-boot,.transport-boot-track i{transition:none}.transport-boot[aria-busy=true] .transport-boot-card::before{animation:none;border-color:#4ce6d0}}
    `;
    document.head.append(style);
    const screen = document.createElement("section");
    screen.id = "transportBoot";
    screen.className = "transport-boot";
    screen.setAttribute("role", "dialog");
    screen.setAttribute("aria-modal", "true");
    screen.setAttribute("aria-busy", "true");
    screen.setAttribute("aria-label", "Cargando Rutas del Continente");
    screen.innerHTML = `<div class="transport-boot-card"><div class="transport-boot-brand">TodoSobreAllTech Studios</div><h1>Rutas del<br>Continente</h1><p class="transport-boot-sub" data-status>Preparando la experiencia de conduccion</p><div class="transport-boot-track" aria-hidden="true"><i></i></div><div class="transport-boot-meta"><span data-percent>12% completado</span><span>Graficos <b data-profile>Detectando...</b></span></div><div class="transport-boot-phases">${PHASES.map((phase,index)=>`<span class="transport-boot-phase${index===0?" active":""}">${phase}</span>`).join("")}</div><div class="transport-boot-error" data-error hidden></div><div class="transport-boot-actions"><button type="button" data-retry hidden>Reintentar</button><button type="button" class="enter" data-enter hidden>Entrar al simulador</button></div></div>`;
    document.body.append(screen);
    const bar = screen.querySelector(".transport-boot-track i"), status = screen.querySelector("[data-status]"), percent = screen.querySelector("[data-percent]"), profile = screen.querySelector("[data-profile]"), errorBox = screen.querySelector("[data-error]"), retry = screen.querySelector("[data-retry]"), enter = screen.querySelector("[data-enter]");
    let closed = false;
    const api = {
      phase(value, label) {
        const index = normalizePhase(value), progress = phaseProgress(index);
        bar.style.width = `${progress}%`; percent.textContent = `${progress}% completado`; if (label) status.textContent = label;
        screen.querySelectorAll(".transport-boot-phase").forEach((node,i)=>{node.classList.toggle("done",i<index);node.classList.toggle("active",i===index)});
        return api;
      },
      profile(value) { profile.textContent = String(value || "AUTO").toUpperCase(); return api; },
      fail(error, source, line) {
        const message = error?.stack || error?.message || String(error || "Error desconocido");
        screen.setAttribute("aria-busy", "false"); status.textContent = "No se pudo completar el arranque"; errorBox.hidden = false; retry.hidden = false; enter.hidden = true;
        errorBox.textContent = `${message}${source ? `\n${source}${line ? `:${line}` : ""}` : ""}`; retry.focus(); return api;
      },
      ready() {
        api.phase("Mundo", "Vehiculo y mundo preparados"); bar.style.width = "100%"; percent.textContent = "100% completado"; screen.setAttribute("aria-busy", "false"); enter.hidden = false; enter.focus(); return api;
      },
      close() {
        if (closed) return; closed = true; screen.classList.add("is-closing"); root.setTimeout(()=>{screen.remove();style.remove()},360);
      }
    };
    retry.onclick = reload; enter.onclick = api.close;
    return api;
  }

  root.TransportBoot = { PHASES, normalizePhase, phaseProgress, mount: mountTransportBoot };
  if (typeof module !== "undefined" && module.exports) module.exports = root.TransportBoot;
})(typeof window !== "undefined" ? window : globalThis);
