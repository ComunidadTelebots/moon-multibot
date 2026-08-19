import assert from "node:assert/strict";
import test from "node:test";
import {
  calculateEcoDrivingScore,
  DOPPLER_WEATHER_SYSTEM,
  COOPERATIVE_OPERATIONS,
  createConnectedSystemsEngine
} from "./transport-connected-systems.js";

test("el algoritmo Eco-Driving evalua consumo, suavidad, anticipacion e inercias", () => {
  // Conducción eficiente óptima
  const goodDrive = calculateEcoDrivingScore({
    avgFuelL100: 27.5,
    targetFuelL100: 28.4,
    harshAccels: 0,
    harshBrakes: 0,
    coastingPercent: 35,
    speedingSeconds: 0
  });

  assert.equal(goodDrive.score >= 90, true);
  assert.equal(goodDrive.grade, "A+");

  // Conducción agresiva con acelerones y frenazos
  const aggressiveDrive = calculateEcoDrivingScore({
    avgFuelL100: 38.2,
    targetFuelL100: 28.4,
    harshAccels: 8,
    harshBrakes: 6,
    coastingPercent: 5,
    speedingSeconds: 45
  });

  assert.equal(aggressiveDrive.score < 60, true);
  assert.equal(aggressiveDrive.grade === "D" || aggressiveDrive.grade === "F", true);
});

test("el radar meteorologico doppler cubre los frentes climaticos de Canva", () => {
  const ids = DOPPLER_WEATHER_SYSTEM.layers.map(l => l.id);
  assert.equal(ids.includes("rain_radar"), true);
  assert.equal(ids.includes("snow_passes"), true);
  assert.equal(ids.includes("crosswind_alert"), true);
  assert.equal(ids.includes("dense_fog"), true);
  assert.equal(ids.includes("wildfire_smoke"), true);
});

test("las operaciones cooperativas cubren corredor medico, incendios, puerto e intermodal", () => {
  const opIds = COOPERATIVE_OPERATIONS.map(op => op.id);
  assert.equal(opIds.includes("corredor_medico"), true);
  assert.equal(opIds.includes("respuesta_incendios"), true);
  assert.equal(opIds.includes("emergencia_portuaria"), true);
  assert.equal(opIds.includes("entrega_intermodal"), true);
});

test("el motor de sistemas conectados despacha misiones cooperativas y radar de trafico", () => {
  const engine = createConnectedSystemsEngine();

  const missionRes = engine.startCooperativeMission("corredor_medico", ["Player1", "Player2"]);
  assert.equal(missionRes.success, true);
  assert.equal(engine.state.activeMission.id, "corredor_medico");
  assert.equal(engine.state.activeMission.assignedPlayers.length, 2);

  const radarFeed = engine.sampleTrafficRadar();
  assert.equal(radarFeed.activeTrucks >= 1, true);
});
