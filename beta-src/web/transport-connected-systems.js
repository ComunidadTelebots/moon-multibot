/**
 * Motor de Sistemas Conectados, Evaluación Eco-Driving, Radar Doppler y Operaciones Cooperativas.
 * Basado fielmente en las especificaciones de la página 024 de Canva.
 */

export function calculateEcoDrivingScore({
  avgFuelL100 = 28.4,
  targetFuelL100 = 28.4,
  harshAccels = 0,
  harshBrakes = 0,
  coastingPercent = 25,
  speedingSeconds = 0
} = {}) {
  // 1. Puntuación de Consumo de Combustible (máx 35 pts)
  const fuelDiffRatio = (targetFuelL100 - avgFuelL100) / targetFuelL100;
  const fuelScore = Math.max(0, Math.min(35, 25 + fuelDiffRatio * 30));

  // 2. Puntuación de Suavidad y G-Force (máx 25 pts)
  const penaltyAccels = harshAccels * 3.5;
  const penaltyBrakes = harshBrakes * 3.0;
  const smoothnessScore = Math.max(0, 25 - penaltyAccels - penaltyBrakes);

  // 3. Anticipación y Respeto de Límites (máx 20 pts)
  const speedingPenalty = (speedingSeconds / 10) * 4.0;
  const anticipationScore = Math.max(0, 20 - speedingPenalty);

  // 4. Aprovechamiento de Inercias y Retarder (máx 20 pts)
  const inertiaScore = Math.min(20, (coastingPercent / 30) * 20);

  const totalScore = Math.max(0, Math.min(100, Math.round(fuelScore + smoothnessScore + anticipationScore + inertiaScore)));

  let grade = "C";
  if (totalScore >= 90) grade = "A+";
  else if (totalScore >= 80) grade = "A";
  else if (totalScore >= 70) grade = "B";
  else if (totalScore >= 55) grade = "C";
  else if (totalScore >= 40) grade = "D";
  else grade = "F";

  const advice = [];
  if (harshAccels > 2) advice.push("Acelera de forma progresiva manteniendo el motor en la zona verde.");
  if (harshBrakes > 2) advice.push("Usa el freno retarder y reduce marchas con antelación.");
  if (coastingPercent < 15) advice.push("Aprovecha la inercia del convoy en pendientes descendentes.");
  if (speedingSeconds > 10) advice.push("Respeta los límites de velocidad para reducir la resistencia aerodinámica.");

  return {
    score: totalScore,
    grade,
    metrics: {
      fuelScore: Math.round(fuelScore),
      smoothnessScore: Math.round(smoothnessScore),
      anticipationScore: Math.round(anticipationScore),
      inertiaScore: Math.round(inertiaScore)
    },
    coastingPercent,
    advice: advice.length ? advice : ["¡Conducción Eco-Driving impecable! Sigue manteniendo este ritmo."]
  };
}

export const DOPPLER_WEATHER_SYSTEM = Object.freeze({
  layers: [
    { id: "rain_radar",       name: "Radar de Precipitación", unit: "dBZ",  warningThreshold: 45, icon: "🌧️" },
    { id: "snow_passes",      name: "Nieve en Puertos",       unit: "cm/h", warningThreshold: 5,  icon: "❄️" },
    { id: "crosswind_alert",  name: "Rachas de Viento",       unit: "km/h", warningThreshold: 65, icon: "💨" },
    { id: "dense_fog",        name: "Niebla y Visibilidad",   unit: "m",    warningThreshold: 100,icon: "🌫️" },
    { id: "wildfire_smoke",   name: "Humo e Incendios",       unit: "AQI",  warningThreshold: 150,icon: "🔥" }
  ]
});

export const COOPERATIVE_OPERATIONS = Object.freeze([
  {
    id: "corredor_medico",
    title: "Corredor Médico de Emergencia",
    icon: "🚑",
    description: "Transporte urgente de órganos y vacunas con escolta coordinada y prioridad de paso.",
    requiredRoles: ["Líder de Convoy", "Coche Piloto", "Transporte Frigorífico Crítico"],
    timeLimitSeconds: 600,
    rewardCredits: 45000,
    reputationGain: 350
  },
  {
    id: "respuesta_incendios",
    title: "Respuesta a Incendios Forestales",
    icon: "🚒",
    description: "Despliegue de generadores industriales de alta potencia y cisternas de agua pesadas.",
    requiredRoles: ["Cisterna Nodriza", "Transporte de Maquinaria Pesada", "Vehículo de Mando"],
    timeLimitSeconds: 720,
    rewardCredits: 52000,
    reputationGain: 400
  },
  {
    id: "emergencia_portuaria",
    title: "Descongestión Portuaria y Logística",
    icon: "⚓",
    description: "Evacuación masiva de contenedores marítimos con grúas y camiones plataforma.",
    requiredRoles: ["Operador de Grúa Pórtico", "Tractora Portacontenedor", "Coordinador de Atraque"],
    timeLimitSeconds: 900,
    rewardCredits: 68000,
    reputationGain: 500
  },
  {
    id: "entrega_intermodal",
    title: "Red Multimodal Sincronizada",
    icon: "🚂",
    description: "Transbordo coordinado de mercancías entre carretera, ferrocarril y buque de carga.",
    requiredRoles: ["Transporte Carretera", "Logística Ferroviaria", "Carga Marítima"],
    timeLimitSeconds: 1200,
    rewardCredits: 85000,
    reputationGain: 650
  }
]);

export function createConnectedSystemsEngine() {
  const state = {
    activeMission: null,
    missionStage: 0,
    missionTimeRemaining: 0,
    trafficFeed: [
      { id: "TRK-01", type: "truck", model: "Aster Viento", x: 12.5, z: -450.0, speedKmh: 84, heading: 0.12 },
      { id: "TRK-02", type: "truck", model: "Titán 8x4",    x: -8.0, z: 230.0,  speedKmh: 72, heading: 3.14 },
      { id: "AIR-01", type: "plane", model: "Cargo Jet 700",x: 350.0,z: -1200.0,altitude: 2400, speedKmh: 420 },
      { id: "SEA-01", type: "ship",  model: "Atlas Express",x: -850.0,z: 1400.0, speedKmh: 35 }
    ]
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
    startCooperativeMission(missionId, assignedPlayers = ["Player1"]) {
      const op = COOPERATIVE_OPERATIONS.find(o => o.id === missionId);
      if (!op) return { success: false, reason: "Operación no encontrada" };

      state.activeMission = {
        ...op,
        assignedPlayers,
        startedAt: Date.now(),
        status: "EN CURSO"
      };
      state.missionStage = 1;
      state.missionTimeRemaining = op.timeLimitSeconds;

      return { success: true, mission: state.activeMission, state: emit() };
    },
    sampleTrafficRadar() {
      return {
        timestamp: Date.now(),
        activeTrucks: state.trafficFeed.filter(t => t.type === "truck").length,
        activeAircraft: state.trafficFeed.filter(t => t.type === "plane").length,
        activeShips: state.trafficFeed.filter(t => t.type === "ship").length,
        feed: state.trafficFeed
      };
    },
    subscribe(fn) {
      listeners.add(fn);
      return () => listeners.delete(fn);
    }
  };
}

export default { calculateEcoDrivingScore, DOPPLER_WEATHER_SYSTEM, COOPERATIVE_OPERATIONS, createConnectedSystemsEngine };
