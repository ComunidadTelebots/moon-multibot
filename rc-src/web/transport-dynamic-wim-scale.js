/**
 * Sistema de Pesaje Dinámico en Movimiento WIM (Weight-In-Motion) y Báscula de Inspección.
 * Evalúa en tiempo real el pesaje por ejes (directriz, motriz, tridem) y MMA total,
 * gestiona el semáforo en autovía (Verde, Ámbar, Rojo) y calcula sanciones e inmovilizaciones.
 */

export const AXLE_LIMITS_KG = Object.freeze({
  steerAxleMaxKg: 7500,
  driveAxleMaxKg: 11500,
  tridemAxleMaxKg: 24000,
  standardTotalMmaKg: 40000,
  intermodalTotalMmaKg: 44000
});

export function evaluateDynamicWIMScale({
  steerAxleKg = 6500,
  driveAxleKg = 10000,
  tridemKg = 20000,
  isIntermodal = false
} = {}) {
  const totalGrossWeightKg = steerAxleKg + driveAxleKg + tridemKg;
  const maxAllowedMmaKg = isIntermodal ? AXLE_LIMITS_KG.intermodalTotalMmaKg : AXLE_LIMITS_KG.standardTotalMmaKg;

  const steerOverloadKg = Math.max(0, steerAxleKg - AXLE_LIMITS_KG.steerAxleMaxKg);
  const driveOverloadKg = Math.max(0, driveAxleKg - AXLE_LIMITS_KG.driveAxleMaxKg);
  const tridemOverloadKg = Math.max(0, tridemKg - AXLE_LIMITS_KG.tridemAxleMaxKg);
  const totalOverloadKg = Math.max(0, totalGrossWeightKg - maxAllowedMmaKg);

  const hasAxleOverload = steerOverloadKg > 0 || driveOverloadKg > 0 || tridemOverloadKg > 0;
  const hasTotalOverload = totalOverloadKg > 0;
  const isCompliant = !hasAxleOverload && !hasTotalOverload;

  let signalLight = "GREEN";
  let fineEuros = 0;
  let immobilized = false;
  let inspectionRequired = false;

  if (!isCompliant) {
    inspectionRequired = true;
    signalLight = "RED";

    const maxExcessPercent = Math.max(
      (totalOverloadKg / maxAllowedMmaKg) * 100,
      (driveOverloadKg / AXLE_LIMITS_KG.driveAxleMaxKg) * 100,
      (tridemOverloadKg / AXLE_LIMITS_KG.tridemAxleMaxKg) * 100
    );

    if (maxExcessPercent > 25) {
      fineEuros = 3500;
      immobilized = true;
    } else if (maxExcessPercent > 15) {
      fineEuros = 1500;
    } else if (maxExcessPercent > 5) {
      fineEuros = 800;
    } else {
      fineEuros = 350;
    }
  } else if (totalGrossWeightKg >= maxAllowedMmaKg * 0.95) {
    signalLight = "AMBER";
  }

  const advice = [];
  if (steerOverloadKg > 0) advice.push(`Sobrecarga de ${steerOverloadKg} kg en eje directriz.`);
  if (driveOverloadKg > 0) advice.push(`Sobrecarga de ${driveOverloadKg} kg en eje motriz.`);
  if (tridemOverloadKg > 0) advice.push(`Sobrecarga de ${tridemOverloadKg} kg en tridem del semirremolque.`);
  if (totalOverloadKg > 0) advice.push(`Masa máxima total sobrepasada en ${totalOverloadKg} kg.`);

  return {
    isCompliant,
    signalLight,
    totalGrossWeightKg,
    maxAllowedMmaKg,
    steerOverloadKg,
    driveOverloadKg,
    tridemOverloadKg,
    totalOverloadKg,
    inspectionRequired,
    fineEuros,
    immobilized,
    advice: advice.length ? advice : ["Peso y distribución de carga en regla. Continúe la marcha."]
  };
}

export function createWIMScaleStation({ stationName = "Báscula WIM A-3 km 120" } = {}) {
  const state = {
    stationName,
    inspectionsConducted: 0,
    totalFinesCollected: 0,
    recentPasses: []
  };

  const listeners = new Set();
  const emit = () => {
    const snap = JSON.parse(JSON.stringify(state));
    listeners.forEach(fn => {
      try { fn(snap); } catch {}
    });
    return snap;
  };

  return {
    get state() {
      return JSON.parse(JSON.stringify(state));
    },
    processVehiclePass({
      steerAxleKg = 6500,
      driveAxleKg = 10000,
      tridemKg = 20000,
      vehiclePlate = "TRX-0001",
      isIntermodal = false
    } = {}) {
      const evaluation = evaluateDynamicWIMScale({ steerAxleKg, driveAxleKg, tridemKg, isIntermodal });
      if (evaluation.inspectionRequired) {
        state.inspectionsConducted += 1;
        state.totalFinesCollected += evaluation.fineEuros;
      }

      const record = {
        stationName: state.stationName,
        vehiclePlate,
        at: Date.now(),
        ...evaluation
      };

      state.recentPasses.unshift(record);
      if (state.recentPasses.length > 50) state.recentPasses.pop();

      emit();
      return record;
    },
    subscribe(fn) {
      listeners.add(fn);
      return () => listeners.delete(fn);
    }
  };
}

export default { AXLE_LIMITS_KG, evaluateDynamicWIMScale, createWIMScaleStation };
