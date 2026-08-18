const LIMIT_KG = 40000;

export function calculateInspection({ vehicleMassKg = 18000, cargoMassKg = 0, restraint = 100 } = {}) {
  const grossKg = Math.max(0, Number(vehicleMassKg) || 0) + Math.max(0, Number(cargoMassKg) || 0);
  const overweightKg = Math.max(0, grossKg - LIMIT_KG);
  const restraintOk = Number(restraint) >= 75;
  return {
    grossKg, limitKg: LIMIT_KG, overweightKg, restraintOk,
    passed: overweightKg === 0 && restraintOk,
    fine: overweightKg ? Math.max(180, Math.round(overweightKg * .22)) : restraintOk ? 0 : 240,
  };
}

export function createWeighStation({ controls, eventLog, career } = {}) {
  let context = { nearby: false, stopped: false, cargoMassKg: 0, restraint: 100 };
  const button = document.createElement("button");
  button.id = "weighStationButton"; button.textContent = "Control de peso"; button.hidden = true;
  controls?.append(button);
  const panel = document.createElement("aside"); panel.className = "mission-panel"; panel.hidden = true; document.body.append(panel);
  const render = result => {
    panel.innerHTML = `<header><div><small>Inspección de carretera</small><h3>Báscula para vehículos pesados</h3></div><button data-close>×</button></header>
      <p>${result ? (result.passed ? "✓ Peso y sujeción conformes. Puedes continuar." : `Inspección desfavorable · sanción ${result.fine} €`) : "Detén el camión sobre la plataforma para pesar el conjunto y revisar la carga."}</p>
      ${result ? `<ol class="mission-objectives"><li>Masa total: ${(result.grossKg / 1000).toFixed(1)} t / ${(result.limitKg / 1000).toFixed(0)} t</li><li class="${result.restraintOk ? "done" : "current"}">Sujeción: ${result.restraintOk ? "correcta" : "requiere ajuste"}</li></ol>` : ""}
      <footer><button data-inspect ${context.stopped ? "" : "disabled"}>Iniciar inspección</button></footer>`;
    panel.querySelector("[data-close]").onclick = () => panel.hidden = true;
    const inspect = panel.querySelector("[data-inspect]"); if (inspect) inspect.onclick = run;
  };
  const run = () => {
    if (!context.nearby || !context.stopped) return null;
    const result = calculateInspection(context);
    if (result.fine) career?.record?.(-result.fine, "Control de peso", { kind:"inspection", ...result });
    eventLog?.record?.("operations", result.passed ? "inspection:passed" : "inspection:failed", result, { severity:result.passed ? "info" : "warning" });
    render(result); return result;
  };
  button.onclick = () => { panel.hidden = false; render(); };
  return {
    update({ service, speed = 0, cargoMassKg = 0, restraint = 100 } = {}) {
      context = { nearby: service?.type === "inspection" && service.distance < 34, stopped: Math.abs(speed) < .5, cargoMassKg, restraint };
      button.hidden = !context.nearby; if (!context.nearby) panel.hidden = true;
    },
    run,
  };
}
