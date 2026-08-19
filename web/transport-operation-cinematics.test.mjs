import assert from "node:assert/strict";
import { createOperationCinematics } from "./transport-operation-cinematics.js";

const cinematic = createOperationCinematics({ duration: 1000 });
assert.equal(cinematic.snapshot(0).active, false);
assert.equal(cinematic.start({ now: 100, pallet: "p1" }).phase, "align");
assert.equal(cinematic.update(500).phase, "lift");
assert.equal(cinematic.update(900).phase, "secure");
const complete = cinematic.update(1100);
assert.equal(complete.phase, "complete");
assert.equal(complete.active, false);
assert.equal(cinematic.active, false);
assert.equal(cinematic.start({ now: 2000 }).active, true);
cinematic.cancel();
assert.equal(cinematic.active, false);

console.log("transport operation cinematics: ok");
