import assert from "node:assert/strict";
import test from "node:test";
import {
  AXLE_LIMITS_KG,
  evaluateDynamicWIMScale,
  createWIMScaleStation
} from "./transport-dynamic-wim-scale.js";

test("los limites de peso por eje cumplen la normativa tecnica de transportes", () => {
  assert.equal(AXLE_LIMITS_KG.steerAxleMaxKg, 7500);
  assert.equal(AXLE_LIMITS_KG.driveAxleMaxKg, 11500);
  assert.equal(AXLE_LIMITS_KG.tridemAxleMaxKg, 24000);
  assert.equal(AXLE_LIMITS_KG.standardTotalMmaKg, 40000);
  assert.equal(AXLE_LIMITS_KG.intermodalTotalMmaKg, 44000);
});

test("la bascula WIM evalua si un camion va en regla y activa semaforo verde", () => {
  const result = evaluateDynamicWIMScale({
    steerAxleKg: 6200,
    driveAxleKg: 9500,
    tridemKg: 19500,
    isIntermodal: false
  });

  assert.equal(result.isCompliant, true);
  assert.equal(result.signalLight, "GREEN");
  assert.equal(result.totalGrossWeightKg, 35200);
  assert.equal(result.inspectionRequired, false);
});

test("la bascula WIM detecta sobrecarga, activa semaforo rojo y desvia a inspeccion policial", () => {
  const result = evaluateDynamicWIMScale({
    steerAxleKg: 7900,
    driveAxleKg: 13200, // Sobrecarga en eje motriz (límite 11.500 kg)
    tridemKg: 25800,   // Sobrecarga en tridem (límite 24.000 kg)
    isIntermodal: false
  });

  assert.equal(result.isCompliant, false);
  assert.equal(result.signalLight, "RED");
  assert.equal(result.inspectionRequired, true);
  assert.equal(result.fineEuros >= 800, true);
});

test("la estacion de pesaje registra pasos e inmoviliza vehiculos con sobrecarga muy grave", () => {
  const station = createWIMScaleStation({ stationName: "Báscula WIM A-3 km 120" });

  const record = station.processVehiclePass({
    steerAxleKg: 8200,
    driveAxleKg: 14500,
    tridemKg: 29000,
    vehiclePlate: "TRX-9921"
  });

  assert.equal(record.signalLight, "RED");
  assert.equal(record.immobilized, true);
  assert.equal(station.state.inspectionsConducted, 1);
});
