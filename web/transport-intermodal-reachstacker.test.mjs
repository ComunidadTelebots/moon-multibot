import assert from "node:assert/strict";
import test from "node:test";
import {
  CONTAINER_TYPES,
  createReachStackerOperation,
  calculateContainerWeightBalance
} from "./transport-intermodal-reachstacker.js";

test("los tipos de contenedores ISO cubren standard, high cube, reefer e iso-tank", () => {
  const ids = Object.keys(CONTAINER_TYPES);
  assert.equal(ids.includes("20ST"), true);
  assert.equal(ids.includes("40ST"), true);
  assert.equal(ids.includes("40HC"), true);
  assert.equal(ids.includes("40RF"), true);
  assert.equal(ids.includes("20TK"), true);

  assert.equal(CONTAINER_TYPES["40RF"].isRefrigerated, true);
  assert.equal(CONTAINER_TYPES["20TK"].isTank, true);
});

test("el calculo de balance de masa detecta desequilibrios en la estiba del contenedor", () => {
  // Carga centrada
  const balanced = calculateContainerWeightBalance({
    containerType: "40ST",
    cargoMassKg: 20000,
    centerOfGravityOffsetX: 0.05,
    centerOfGravityOffsetZ: 0.1
  });

  assert.equal(balanced.isStable, true);
  assert.equal(balanced.rolloverRiskScore < 20, true);

  // Carga severamente descentrada lateralmente
  const unbalanced = calculateContainerWeightBalance({
    containerType: "40ST",
    cargoMassKg: 24000,
    centerOfGravityOffsetX: 0.95,
    centerOfGravityOffsetZ: 1.5
  });

  assert.equal(unbalanced.isStable, false);
  assert.equal(unbalanced.rolloverRiskScore >= 60, true);
});

test("la operacion de grua Reach Stacker engancha twistlocks y monta en semirremolque", () => {
  const op = createReachStackerOperation({ containerType: "40HC", cargoMassKg: 22000 });

  assert.equal(op.state.twistlocksEngaged, false);
  assert.equal(op.state.loadedOnChassis, false);

  // Alinear spreader y enganchar 4 twistlocks
  const engageRes = op.engageTwistlocks();
  assert.equal(engageRes.success, true);
  assert.equal(op.state.twistlocksEngaged, true);

  // Depositar y bloquear sobre el chasis portacontenedor
  const loadRes = op.mountOnChassis("CHASSIS-40-01");
  assert.equal(loadRes.success, true);
  assert.equal(op.state.loadedOnChassis, true);
  assert.equal(op.state.totalMmaKg, 22000 + CONTAINER_TYPES["40HC"].tareMassKg);
});
