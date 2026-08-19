/**
 * Módulo de Comunidad, Temporadas, Eventos Globales y Misiones Cooperativas (Canal Alfa).
 * Basado fielmente en la página 029 de Canva.
 */

export const SEASON_PASS_HORIZONS = Object.freeze({
  seasonName: "Temporada 8: Horizontes",
  currentLevel: 27,
  currentXp: 7450,
  targetXp: 10000,
  timeLeft: "28d 09h",
  rewards: [
    { level: 25, name: "Créditos", type: "currency", value: "10.000" },
    { level: 26, name: "Llantas personalizadas", type: "cosmetic", value: "Cromadas R22.5" },
    { level: 27, name: "Tractora Nova Liria", type: "vehicle", value: "Aster Viento Especial" },
    { level: 28, name: "Caja de suministros", type: "lootbox", value: "Piezas premium" },
    { level: 29, name: "Skin reflectante", type: "skin", value: "Hexagonal Teal" },
    { level: 30, name: "Tractora Pesada Titán", type: "vehicle", value: "Titán 8x4 Heavy" }
  ]
});

export const GLOBAL_CHALLENGES = Object.freeze([
  { id: "ruta_artica",      name: "Ruta Ártica Extrema",     cargoType: "Carga pesada",  distanceKm: 15000, rewardCredits: 25000, schedule: "7 JUN · 18:00" },
  { id: "desafio_desierto",  name: "Desafío del Desierto",    cargoType: "Carga frágil",   distanceKm: 9800,  rewardCredits: 20000, schedule: "8 JUN · 20:00" },
  { id: "nocturna_global",   name: "Entrega Nocturna Global", cargoType: "Carga urgente",  distanceKm: 4200,  rewardCredits: 15000, schedule: "10 JUN · 11:00" }
]);

export const COMMUNITY_MISSIONS = Object.freeze({
  id: "ayuda_humanitaria",
  title: "Ayuda humanitaria: Zonas afectadas",
  subtitle: "Comunidad, unámonos para entregar suministros esenciales.",
  deliveriesDone: 28450,
  deliveriesTotal: 40000,
  progressPercent: 71,
  rewardGlobalCredits: 500000,
  timeLeft: "05d 21h"
});

export const PLAYER_LEADERBOARD = Object.freeze([
  { rank: 1, driverName: "ViajeroLunar", distanceKm: 265768, onTimePercent: 99.4, ecoScore: 96 },
  { rank: 2, driverName: "RutaMaestra",  distanceKm: 231450, onTimePercent: 98.8, ecoScore: 94 },
  { rank: 3, driverName: "CaminoSeguro", distanceKm: 217982, onTimePercent: 99.1, ecoScore: 92 },
  { rank: 4, driverName: "EstrellaPolar",distanceKm: 205311, onTimePercent: 97.5, ecoScore: 95 },
  { rank: 5, driverName: "ToroNegro",    distanceKm: 198774, onTimePercent: 98.2, ecoScore: 91 }
]);

export function createCommunitySystem({ initialCredits = 0 } = {}) {
  const state = {
    userCredits: initialCredits,
    claimedRewards: [],
    communityDeliveries: COMMUNITY_MISSIONS.deliveriesDone,
    communityGoal: COMMUNITY_MISSIONS.deliveriesTotal,
    seasonLevel: SEASON_PASS_HORIZONS.currentLevel,
    seasonXp: SEASON_PASS_HORIZONS.currentXp
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
    claimSeasonReward(level) {
      if (level > state.seasonLevel) return { success: false, reason: "Nivel no alcanzado" };
      if (state.claimedRewards.includes(level)) return { success: false, reason: "Recompensa ya reclamada" };

      const reward = SEASON_PASS_HORIZONS.rewards.find(r => r.level === level);
      if (reward) {
        state.claimedRewards.push(level);
        if (reward.type === "currency") state.userCredits += Number(reward.value.replace(".", ""));
        return { success: true, reward, state: emit() };
      }
      return { success: false, reason: "Recompensa no encontrada" };
    },
    contributeCommunityMission(deliveriesCount = 1) {
      state.communityDeliveries += deliveriesCount;
      return emit();
    },
    subscribe(fn) {
      listeners.add(fn);
      return () => listeners.delete(fn);
    }
  };
}

export default { SEASON_PASS_HORIZONS, GLOBAL_CHALLENGES, COMMUNITY_MISSIONS, PLAYER_LEADERBOARD, createCommunitySystem };
