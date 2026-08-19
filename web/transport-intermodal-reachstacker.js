/**
 * Sistema de Terminal Intermodal, Contenedores ISO y Operaciones de Grúa Reach Stacker.
 * Gestiona tipos de contenedores (20ST, 40ST, 40HC, 40RF, 20TK), enganche de twistlocks,
 * equilibrado de centro de gravedad y estiba sobre chasis portacontenedores.
 */

export const CONTAINER_TYPES = Object.freeze({
  "20ST": {
    code: "20ST",
    name: "Contenedor 20ft Estándar Dry",
    lengthMeters: 6.06,
    widthMeters: 2.44,
    heightMeters: 2.59,
    tareMassKg: 2230,
    maxPayloadKg: 28250,
    volumeM3: 33.2,
    isRefrigerated: false,
    isTank: false
  },
  "40ST": {
    code: "40ST",
    name: "Contenedor 40ft Estándar Dry",
    lengthMeters: 12.19,
    widthMeters: 2.44,
    heightMeters: 2.59,
    tareMassKg: 3700,
    maxPayloadKg: 26780,
    volumeM3: 67.7,
    isRefrigerated: false,
    isTank: false
  },
  "40HC": {
    code: "40HC",
    name: "Contenedor 40ft High Cube",
    lengthMeters: 12.19,
    widthMeters: 2.44,
    heightMeters: 2.89,
    tareMassKg: 3900,
    maxPayloadKg: 26580,
    volumeM3: 76.2,
    isRefrigerated: false,
    isTank: false
  },
  "40RF": {
    code: "40RF",
    name: "Contenedor 40ft Reefer Frigorífico",
    lengthMeters: 12.19,
    widthMeters: 2.44,
    heightMeters: 2.89,
    tareMassKg: 4800,
    maxPayloadKg: 25680,
    volumeM3: 67.0,
    isRefrigerated: true,
    isTank: false,
    tempRangeCelsius: [-25, 25]
  },
  "20TK": {
    code: "20TK",
    name: "Contenedor Cisterna ISO Tank",
    lengthMeters: 6.06,
    widthMeters: 2.44,
    heightMeters: 2.59,
    tareMassKg: 3600,
    maxPayloadKg: 32400,
    volumeM3: 26.0,
    isRefrigerated: false,
    isTank: true,
    capacityLiters: 26000
  }
});

export function calculateContainerWeightBalance({
  containerType = "40ST",
  cargoMassKg = 18000,
  centerOfGravityOffsetX = 0, // Desplazamiento lateral en metros (-1.0 a +1.0)
  centerOfGravityOffsetZ = 0  // Desplazamiento longitudinal en metros (-3.0 a +3.0)
} = {}) {
  const cDef = CONTAINER_TYPES[containerType] || CONTAINER_TYPES["40ST"];
  const halfWidth = cDef.widthMeters / 2;
  const halfLength = cDef.lengthMeters / 2;

  const lateralPercent = Math.abs(centerOfGravityOffsetX) / halfWidth;
  const longitudinalPercent = Math.abs(centerOfGravityOffsetZ) / halfLength;

  // El riesgo de vuelco aumenta drásticamente si el peso está descentrado lateralmente
  const rolloverRiskScore = Math.min(100, Math.round(lateralPercent * 75 + longitudinalPercent * 25));
  const isStable = rolloverRiskScore < 45 && lateralPercent < 0.4;

  const recommendations = [];
  if (lateralPercent >= 0.4) recommendations.push("⚠️ Desplazamiento lateral excesivo: Riesgo alto de vuelco en rotondas y curvas.");
  if (longitudinalPercent >= 0.5) recommendations.push("⚠️ Desplazamiento longitudinal: Sobrecarga en el eje motriz o tridem trasero.");
  if (cargoMassKg > cDef.maxPayloadKg) recommendations.push("🚨 ¡Sobrecarga estructural! La mercancía supera la carga útil máxima.");

  return {
    isStable,
    rolloverRiskScore,
    centerOfGravityOffsetX,
    centerOfGravityOffsetZ,
    stabilityRating: isStable ? (rolloverRiskScore < 15 ? "EXCELENTE" : "ESTABLE") : "PELIGROSO",
    recommendations: recommendations.length ? recommendations : ["Estiba equilibrada conforme a la norma ISO."]
  };
}

export function createReachStackerOperation({
  containerType = "40ST",
  cargoMassKg = 18000,
  containerNumber = "MSKU-982410-2"
} = {}) {
  const cDef = CONTAINER_TYPES[containerType] || CONTAINER_TYPES["40ST"];
  const state = {
    containerType,
    cargoMassKg,
    containerNumber,
    twistlocksEngaged: false,
    spreaderHeightMeters: 4.5,
    loadedOnChassis: false,
    chassisId: null,
    totalMmaKg: cargoMassKg + cDef.tareMassKg
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
    engageTwistlocks() {
      state.twistlocksEngaged = true;
      return { success: true, message: "Twistlocks de 4 esquinas bloqueados con seguridad", state: emit() };
    },
    disengageTwistlocks() {
      if (!state.loadedOnChassis && state.spreaderHeightMeters > 0.5) {
        return { success: false, reason: "No se pueden soltar los twistlocks con el contenedor en el aire" };
      }
      state.twistlocksEngaged = false;
      return { success: true, message: "Twistlocks liberados", state: emit() };
    },
    mountOnChassis(chassisId = "CHASSIS-01") {
      if (!state.twistlocksEngaged) {
        return { success: false, reason: "Primero debes asegurar los twistlocks con el spreader de la grúa" };
      }
      state.loadedOnChassis = true;
      state.chassisId = chassisId;
      state.spreaderHeightMeters = 1.4;
      return { success: true, message: `Contenedor ${state.containerNumber} fijado sobre el chasis ${chassisId}`, state: emit() };
    },
    unloadFromChassis() {
      state.loadedOnChassis = false;
      state.chassisId = null;
      state.spreaderHeightMeters = 4.0;
      return { success: true, message: "Contenedor izado y retirado del semirremolque", state: emit() };
    },
    subscribe(fn) {
      listeners.add(fn);
      return () => listeners.delete(fn);
    }
  };
}

export default { CONTAINER_TYPES, calculateContainerWeightBalance, createReachStackerOperation };
