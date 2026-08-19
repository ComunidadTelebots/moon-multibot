import assert from "node:assert/strict";
import test from "node:test";
import { AIR_FLEET, AIR_SKINS, SEA_FLEET, SEA_SKINS } from "./transport-air-sea-fleet.js";

test("every aircraft and vessel has an authored exterior", () => {
  assert.deepEqual(AIR_FLEET.filter(item => !AIR_SKINS[item.id]), []);
  assert.deepEqual(SEA_FLEET.filter(item => !SEA_SKINS[item.id]), []);
  for (const name of [...Object.values(AIR_SKINS), ...Object.values(SEA_SKINS)]) {
    assert.match(name, /^(air|sea)-[a-z-]+-exterior$/);
  }
});

test("the simulator exposes all requested transport families", () => {
  assert.equal(AIR_FLEET.length, 8);
  assert.equal(SEA_FLEET.length, 5);
  assert.ok(AIR_FLEET.some(item => item.kind === "helicopter"));
  assert.ok(SEA_FLEET.some(item => item.kind === "container"));
});
