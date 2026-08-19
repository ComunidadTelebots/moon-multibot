/**
 * Enlace de Datos de Interfaz (UI Data-Binding).
 * Separa de manera estricta los Catálogos y Strings Fijas (Lore y Modelos de Canva)
 * de las Variables Dinámicas del Jugador (Dinero, XP, Kilometraje, Desgaste, Combustible).
 */

export const IMMUTABLE_CANVA_CONSTANTS = Object.freeze({
  vehicles: Object.freeze({
    truck: "Aster Viento 3D",
    bus: "Nortia Urbano X8",
    heavyTruck: "Titán 8x4 Heavy",
    oversizedLoad: "Tanque presurizado industrial",
    emergencyAmbulance: "SAMUR Soporte Vital Avanzado",
    emergencyFire: "Autobomba Forestal Pesada"
  }),
  cities: Object.freeze([
    "Nova Liria", "Puerto Alba", "Valleverde", "Bahía Solar",
    "Madrid", "Barcelona", "Zaragoza", "Lisboa", "Milán", "Berlín"
  ]),
  skills: Object.freeze([
    "Eficiencia Diésel",
    "Mercancía Frágil",
    "Larga Distancia",
    "ADR / Peligrosas",
    "Conducción Nocturna",
    "Liderazgo de Convoy",
    "Mecánica Preventiva"
  ]),
  drivers: Object.freeze([
    "Diego Ramírez",
    "Laura Méndez",
    "Iván López"
  ]),
  securityProviders: Object.freeze([
    "Seguridad Integral 24",
    "Protección Global",
    "Vigilant Services",
    "Guardian Elite"
  ]),
  globalEvents: Object.freeze([
    "Ruta Ártica Extrema",
    "Desafío del Desierto",
    "Entrega Nocturna Global"
  ]),
  storyItem: "Caja 07-A",
  workshopDiagnosticCode: "P0562"
});

export function createUIDataBinding({
  initialMoney = 15000,
  initialXp = 0,
  initialKm = 0,
  truckModel = IMMUTABLE_CANVA_CONSTANTS.vehicles.truck
} = {}) {
  const state = {
    // Modelos y strings fijas de Canva
    truckModel,
    storyItem: IMMUTABLE_CANVA_CONSTANTS.storyItem,

    // Variables dinámicas que crecen y se modifican con la partida
    money: initialMoney,
    xp: initialXp,
    level: 1,
    odometerKm: initialKm,
    fuelPercent: 100,
    damagePercent: 0,
    brakesPercent: 100,
    tiresTreadMm: 8.0,
    reputation: 10,
    hqPhase: 1,
    hqProgressPercent: 0,
    recentExpenses: []
  };

  const listeners = new Set();
  const emit = () => {
    // Calcular nivel automáticamente a partir de los puntos de XP acumulados
    let lvl = 1;
    let required = 1000;
    let accumulated = 0;
    while (state.xp >= accumulated + required) {
      accumulated += required;
      lvl++;
      required = Math.round(required * 1.22);
    }
    state.level = lvl;

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
    get formatted() {
      return {
        truckModel: state.truckModel, // Fijo
        storyItem: state.storyItem,   // Fijo
        money: `${Math.round(state.money).toLocaleString("es-ES")} €`,
        odometer: `${Math.round(state.odometerKm).toLocaleString("es-ES")} km`,
        level: `Nivel ${state.level}`,
        xp: `${state.xp.toLocaleString("es-ES")} XP`,
        fuel: `${Math.round(state.fuelPercent)}%`,
        damage: `${Math.round(state.damagePercent)}%`,
        brakes: `${Math.round(state.brakesPercent)}%`,
        tires: `${state.tiresTreadMm.toFixed(1)} mm`,
        hqProgress: `${state.hqProgressPercent}%`
      };
    },
    addEarnings(moneyReward, earnedXp, distanceKm = 0) {
      state.money += moneyReward;
      state.xp += earnedXp;
      state.odometerKm += distanceKm;
      return emit();
    },
    payExpense(amount, concept = "Gasto operativo") {
      state.money = Math.max(0, state.money - amount);
      state.recentExpenses.unshift({ time: new Date().toLocaleTimeString("es-ES"), amount, concept });
      if (state.recentExpenses.length > 20) state.recentExpenses.pop();
      return emit();
    },
    consumeFuel(percentAmount) {
      state.fuelPercent = Math.max(0, Number((state.fuelPercent - percentAmount).toFixed(2)));
      return emit();
    },
    refuel() {
      state.fuelPercent = 100;
      return emit();
    },
    repairTruck() {
      state.damagePercent = 0;
      state.brakesPercent = 100;
      state.tiresTreadMm = 8.0;
      return emit();
    },
    subscribe(fn) {
      listeners.add(fn);
      return () => listeners.delete(fn);
    }
  };
}

export default { IMMUTABLE_CANVA_CONSTANTS, createUIDataBinding };
