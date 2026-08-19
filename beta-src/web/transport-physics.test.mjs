import assert from "node:assert/strict";
import test from "node:test";
import { createTruckPhysics } from "./transport-physics.js";

test("repeated service-brake applications consume reservoir air", () => {
  const physics = createTruckPhysics({ initialAirPressureBar: 8 });
  let frame;
  for (let cycle = 0; cycle < 12; cycle += 1) {
    frame = physics.update({ brake: 1, engineRunning: false }, 0.05);
    physics.update({ brake: 0, engineRunning: false }, 0.05);
  }
  assert.ok(frame.airPressureBar < 5.5);
  assert.equal(frame.lowAirPressure, true);
  assert.ok(frame.airBrakeFactor < 1);
});

test("running engine compressor restores usable air pressure", () => {
  const physics = createTruckPhysics({ initialAirPressureBar: 4.4 });
  let frame;
  for (let step = 0; step < 600; step += 1) {
    frame = physics.update({ engineRunning: true }, 0.05);
  }
  assert.ok(frame.airPressureBar > 9);
  assert.equal(frame.lowAirPressure, false);
  assert.equal(frame.airBrakeFactor, 1);
});

test("stopped engine does not recharge the reservoir", () => {
  const physics = createTruckPhysics({ initialAirPressureBar: 4.5 });
  let frame;
  for (let step = 0; step < 100; step += 1) frame = physics.update({ engineRunning: false }, 0.05);
  assert.equal(frame.airPressureBar, 4.5);
});

test("crosswind excites deterministic articulated-trailer sway", () => {
  const calm = createTruckPhysics();
  const windy = createTruckPhysics();
  calm.reset(80);
  windy.reset(80);
  let calmFrame, windyFrame;
  for (let step = 0; step < 240; step += 1) {
    calmFrame = calm.update({ throttle: 0.35, cargoMass: 24000 }, 0.025);
    windyFrame = windy.update({ throttle: 0.35, cargoMass: 24000, crosswind: 24 }, 0.025);
  }
  assert.ok(Math.abs(windyFrame.trailerSway) > Math.abs(calmFrame.trailerSway) + 0.002);
  assert.ok(windyFrame.jackknifeRisk >= calmFrame.jackknifeRisk);
});

test("trailer stability control intervenes and settles after a severe manoeuvre", () => {
  const physics = createTruckPhysics();
  physics.reset(92);
  let peakIntervention = 0;
  let peakRisk = 0;
  let frame;
  for (let step = 0; step < 180; step += 1) {
    frame = physics.update({ steering: step % 24 < 12 ? 1 : -1, crosswind: 28, wetness: 0.7, cargoMass: 28000, cargoHeight: 2.6 }, 0.03);
    peakIntervention = Math.max(peakIntervention, frame.stabilityIntervention);
    peakRisk = Math.max(peakRisk, frame.jackknifeRisk);
  }
  assert.ok(peakIntervention > 0.08);
  for (let step = 0; step < 320; step += 1) frame = physics.update({ cargoMass: 28000, cargoHeight: 2.6 }, 0.03);
  assert.ok(frame.jackknifeRisk < peakRisk * 0.5);
  assert.ok(frame.stabilityIntervention < peakIntervention);
});
