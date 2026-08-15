import assert from "node:assert/strict";
import test from "node:test";
import { createAdaptiveHUD, resolveControlLayout, CONTEXT_MODES } from "./transport-adaptive-hud.js";

test("los modos de contexto identifican las situaciones de juego", () => {
  assert.equal(CONTEXT_MODES.includes("driving_exterior"), true);
  assert.equal(CONTEXT_MODES.includes("driving_interior"), true);
  assert.equal(CONTEXT_MODES.includes("warehouse_foot"), true);
  assert.equal(CONTEXT_MODES.includes("special_convoy"), true);
  assert.equal(CONTEXT_MODES.includes("diagnostics_workshop"), true);
  assert.equal(CONTEXT_MODES.includes("company_hq"), true);
});

test("la resolución de layout adapta los mandos según el dispositivo y contexto", () => {
  const mobileDriving = resolveControlLayout({ context: "driving_exterior", device: "mobile_portrait" });
  assert.equal(mobileDriving.steeringType, "touch_pedals_or_swipe");
  assert.equal(mobileDriving.primaryActions.includes("throttle_brake"), true);
  assert.equal(mobileDriving.thumbZonePosition, "bottom_corners");

  const interiorLayout = resolveControlLayout({ context: "driving_interior", device: "desktop_keyboard" });
  assert.equal(interiorLayout.showInteractiveDashboard, true);
  assert.equal(interiorLayout.showCircularTachometer, true);
  assert.equal(interiorLayout.hotkeysEnabled, true);

  const footLayout = resolveControlLayout({ context: "warehouse_foot", device: "mobile_portrait" });
  assert.equal(footLayout.showWalkJoystick, true);
  assert.equal(footLayout.primaryActions.includes("interact_cargo"), true);
});

test("el gestor de HUD adaptativo reacciona a cambios de estado del juego", () => {
  const hud = createAdaptiveHUD();
  assert.equal(hud.state.activeContext, "driving_exterior");

  hud.setContext("warehouse_foot");
  assert.equal(hud.state.activeContext, "warehouse_foot");
  assert.equal(hud.currentLayout.showWalkJoystick, true);

  hud.setContext("driving_interior");
  assert.equal(hud.currentLayout.showInteractiveDashboard, true);
});
