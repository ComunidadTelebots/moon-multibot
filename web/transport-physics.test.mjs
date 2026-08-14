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
