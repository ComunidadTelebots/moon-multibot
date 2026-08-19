import assert from "node:assert/strict";
import { calculateInspection } from "./transport-weigh-station.js";
import { createMissionRuntime, TRANSPORT_MISSIONS } from "./transport-mission-runtime.js";

assert.deepEqual(calculateInspection({ vehicleMassKg:18000, cargoMassKg:15000, restraint:92 }), {
  grossKg:33000, limitKg:40000, overweightKg:0, restraintOk:true, passed:true, fine:0,
});
const overweight = calculateInspection({ vehicleMassKg:18000, cargoMassKg:24000, restraint:100 });
assert.equal(overweight.passed, false);
assert.equal(overweight.overweightKg, 2000);
assert.equal(overweight.fine, 440);
const unsafe = calculateInspection({ vehicleMassKg:18000, cargoMassKg:10000, restraint:60 });
assert.equal(unsafe.passed, false);
assert.equal(unsafe.fine, 240);
const mission = TRANSPORT_MISSIONS.find(item => item.id === "legal-weight-corridor");
const runtime = createMissionRuntime({ catalog:[mission], storage:null });
runtime.start(mission.id);
runtime.handleEvent({ type:"engine:started", detail:{ vehicle:"truck" } });
runtime.handleEvent({ type:"cargo:secured", detail:{} });
runtime.handleEvent({ type:"inspection:passed", detail:{ grossKg:33000 } });
assert.deepEqual(runtime.snapshot.completed, [mission.id]);
console.log("transport-weigh-station: ok");
