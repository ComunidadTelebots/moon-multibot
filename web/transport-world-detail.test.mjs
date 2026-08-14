import assert from "node:assert/strict";
import { deriveBuildingVariant } from "./transport-world-detail.js";

assert.deepEqual(deriveBuildingVariant({ seed: 0, qualityLevel: 0, height: 18 }), {
  family: "residential", roof: "flat", groundFloor: "simple", awnings: 0, rooftopProps: 0,
});
assert.equal(deriveBuildingVariant({ seed: 1, qualityLevel: 2, height: 18 }).family, "commercial");
assert.equal(deriveBuildingVariant({ seed: 1, qualityLevel: 2, height: 18 }).groundFloor, "shops");
assert.ok(deriveBuildingVariant({ seed: 1, qualityLevel: 2, height: 18 }).awnings >= 2);
assert.equal(deriveBuildingVariant({ seed: 2, qualityLevel: 2, height: 18 }).roof, "gable");
assert.equal(deriveBuildingVariant({ seed: 3, qualityLevel: 3, height: 18 }).rooftopProps, 3);
assert.equal(deriveBuildingVariant({ seed: 5, qualityLevel: 9, height: 42 }).roof, "flat");

console.log("transport-world-detail tests passed");
