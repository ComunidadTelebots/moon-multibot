import assert from "node:assert/strict";
import test from "node:test";
import {
  createDigitalTachograph,
  TACHOGRAPH_CONSTANTS
} from "./transport-digital-tachograph.js";

test("los limites de tacografo cumplen la normativa europea UE 561/2006", () => {
  assert.equal(TACHOGRAPH_CONSTANTS.MAX_CONTINUOUS_DRIVE_MINUTES, 270); // 4h 30m
  assert.equal(TACHOGRAPH_CONSTANTS.BREAK_REQUIRED_MINUTES, 45);
  assert.equal(TACHOGRAPH_CONSTANTS.MAX_DAILY_DRIVE_MINUTES, 540);     // 9h
  assert.equal(TACHOGRAPH_CONSTANTS.EXTENDED_DAILY_DRIVE_MINUTES, 600);// 10h
});

test("el tacografo registra tiempos de conduccion continua y emite aviso previo a la pausa", () => {
  const taco = createDigitalTachograph({ driverName: "Adrián Conductor" });
  assert.equal(taco.state.cardInserted, true);
  assert.equal(taco.state.currentMode, "REST");

  // Conducir 260 minutos (4h 20m)
  taco.setMode("DRIVE");
  taco.advanceTime(260);

  assert.equal(taco.state.continuousDriveMinutes, 260);
  assert.equal(taco.state.alert, "WARNING_BREAK_SOON"); // Aviso a falta de < 15 min

  // Conducir 15 minutos más (275 min > 270 min) -> Infracción por exceso de conducción
  taco.advanceTime(15);
  assert.equal(taco.state.alert, "INFRACTION_OVERDRIVE");
  assert.equal(taco.state.infractions.length, 1);
});

test("tomar una pausa reglamentaria de 45 minutos resetea la conduccion continua", () => {
  const taco = createDigitalTachograph({ driverName: "Adrián Conductor" });
  taco.setMode("DRIVE");
  taco.advanceTime(240); // 4h de conducción

  taco.setMode("BREAK");
  taco.advanceTime(45);  // Pausa de 45 min

  assert.equal(taco.state.continuousDriveMinutes, 0); // Reseteado a cero
  assert.equal(taco.state.alert, null);
});
