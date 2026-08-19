/**
 * Motor de Progresión Dinámica del Jugador, Niveles, Desgaste Mecánico y Sede Modular.
 * Cada jugador gestiona su propio avance orgánico según sus horas de juego y decisiones.
 */

export function calculateLevelFromXp(totalXp = 0) {
  let level = 1;
  let accumulatedXp = 0;

  while (true) {
    const xpForThisLevel = Math.round(1000 * Math.pow(1.22, level - 1));
    if (totalXp < accumulatedXp + xpForThisLevel) {
      const currentLevelXp = Math.max(0, totalXp - accumulatedXp);
      const percentToNextLevel = Math.min(100, Math.round((currentLevelXp / xpForThisLevel) * 100));
      return {
        level,
        currentLevelXp,
        nextLevelRequiredXp: xpForThisLevel,
        percentToNextLevel
      };
    }
    accumulatedXp += xpForThisLevel;
    level++;
  }
}

export function calculateTireWear(currentTreadMm = 8.0, kmDriven = 0, cargoMassKg = 12000) {
  const loadFactor = 1 + Math.max(0, cargoMassKg - 10000) / 30000;
  const wearMm = (kmDriven / 1000) * 0.065 * loadFactor;
  return Math.max(1.6, Number((currentTreadMm - wearMm).toFixed(2)));
}

export function calculateBrakeWear(currentPercent = 100, kmDriven = 0, harshBrakingCount = 0) {
  const distanceWear = (kmDriven / 1000) * 1.8;
  const stressWear = harshBrakingCount * 0.25;
  return Math.max(0, Math.round(currentPercent - distanceWear - stressWear));
}

export function createPlayerProfile({
  uid = "guest_player",
  name = "Conductor Autónomo",
  initialMoney = 15000,
  initialXp = 0,
  storageKey = "moon_truck_save_v1"
} = {}) {
  let state = {
    uid: String(uid),
    name,
    level: 1,
    xp: initialXp,
    money: initialMoney,
    distanceKm: 0,
    totalDeliveries: 0,
    ecoDrivingAvgScore: 85,
    reputation: 10,
    truck: {
      model: "Aster Viento 3D",
      odometerKm: 0,
      tires: [
        { id: "fl", label: "Del. Izq.", treadMm: 8.0, pressureBar: 8.2 },
        { id: "fr", label: "Del. Der.", treadMm: 8.0, pressureBar: 8.2 },
        { id: "rl1", label: "Tras. Izq. Ext.", treadMm: 8.0, pressureBar: 8.0 },
        { id: "rl2", label: "Tras. Izq. Int.", treadMm: 8.0, pressureBar: 8.0 },
        { id: "rr1", label: "Tras. Der. Int.", treadMm: 8.0, pressureBar: 8.0 },
        { id: "rr2", label: "Tras. Der. Ext.", treadMm: 8.0, pressureBar: 8.0 }
      ],
      brakesPercent: 100,
      enginePercent: 100,
      transmissionPercent: 100,
      fuelPercent: 100
    },
    hqPhase: 1,
    hqMaxPhase: 5,
    hqInvestedMoney: 0,
    hqCostPerPhase: 100000,
    hqProgressPercent: 0,
    unlockedSkills: {
      eficiencia: 0,
      fragil: 0,
      larga_distancia: 0,
      adr_peligrosas: 0,
      nocturna: 0,
      liderazgo: 0,
      mecanica: 0
    },
    hiredDrivers: [],
    claimedSeasonTiers: [],
    unlockedGarages: ["madrid_central"]
  };

  // Cargar perfil existente de localStorage si estamos en el navegador
  try {
    if (typeof localStorage !== "undefined") {
      const saved = localStorage.getItem(`${storageKey}_${uid}`);
      if (saved) {
        state = { ...state, ...JSON.parse(saved) };
      }
    }
  } catch {}

  const listeners = new Set();
  const emit = () => {
    const levelInfo = calculateLevelFromXp(state.xp);
    state.level = levelInfo.level;

    try {
      if (typeof localStorage !== "undefined") {
        localStorage.setItem(`${storageKey}_${uid}`, JSON.stringify(state));
      }
    } catch {}

    const snapshot = JSON.parse(JSON.stringify(state));
    snapshot.levelInfo = levelInfo;
    listeners.forEach(fn => {
      try { fn(snapshot); } catch {}
    });
    return snapshot;
  };

  return {
    get state() {
      const snap = JSON.parse(JSON.stringify(state));
      snap.levelInfo = calculateLevelFromXp(state.xp);
      return snap;
    },
    completeDelivery({ distanceKm = 100, rewardMoney = 1200, earnedXp = 250, damagePercent = 0, harshBraking = 0, cargoMassKg = 12000 } = {}) {
      state.distanceKm += distanceKm;
      state.totalDeliveries++;
      state.xp += earnedXp;

      const penaltyMultiplier = Math.max(0.2, 1 - (damagePercent / 100) * 1.5);
      const netReward = Math.round(rewardMoney * penaltyMultiplier);
      state.money += netReward;

      // Actualizar desgaste real de ruedas y frenos del camión
      state.truck.odometerKm += distanceKm;
      state.truck.tires.forEach(tire => {
        tire.treadMm = calculateTireWear(tire.treadMm, distanceKm, cargoMassKg);
      });
      state.truck.brakesPercent = calculateBrakeWear(state.truck.brakesPercent, distanceKm, harshBraking);
      state.truck.enginePercent = Math.max(0, Math.round(state.truck.enginePercent - (distanceKm / 1000) * 0.4));

      return emit();
    },
    investInHQ(amount) {
      if (amount <= 0 || state.money < amount) {
        return { success: false, reason: "Saldo insuficiente" };
      }
      if (state.hqPhase >= state.hqMaxPhase && state.hqProgressPercent >= 100) {
        return { success: false, reason: "Sede central completada al 100%" };
      }

      state.money -= amount;
      state.hqInvestedMoney += amount;

      const totalTarget = state.hqCostPerPhase;
      const currentPhaseInvested = state.hqInvestedMoney % totalTarget;
      state.hqProgressPercent = Math.min(100, Math.round((currentPhaseInvested / totalTarget) * 100));

      if (state.hqInvestedMoney >= state.hqPhase * totalTarget && state.hqPhase < state.hqMaxPhase) {
        state.hqPhase++;
        state.hqProgressPercent = 0;
        state.reputation += 10;
      }

      return { success: true, state: emit() };
    },
    repairTruck(systemKey = "all") {
      if (systemKey === "all" || systemKey === "tires") {
        state.truck.tires.forEach(t => { t.treadMm = 8.0; t.pressureBar = 8.2; });
      }
      if (systemKey === "all" || systemKey === "brakes") {
        state.truck.brakesPercent = 100;
      }
      if (systemKey === "all" || systemKey === "engine") {
        state.truck.enginePercent = 100;
      }
      return emit();
    },
    upgradeSkill(skillId) {
      if (state.unlockedSkills[skillId] !== undefined && state.unlockedSkills[skillId] < 5) {
        state.unlockedSkills[skillId]++;
        return emit();
      }
      return state;
    },
    claimSeasonTier(tierNumber, rewardData) {
      if (state.claimedSeasonTiers.includes(tierNumber)) {
        return { success: false, reason: "Recompensa ya reclamada" };
      }
      state.claimedSeasonTiers.push(tierNumber);
      if (rewardData?.type === "money") {
        state.money += rewardData.amount;
      }
      return { success: true, state: emit() };
    },
    subscribe(fn) {
      listeners.add(fn);
      return () => listeners.delete(fn);
    }
  };
}

export default { calculateLevelFromXp, calculateTireWear, calculateBrakeWear, createPlayerProfile };
