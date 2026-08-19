import assert from "node:assert/strict";
import test from "node:test";
import { SEASON_PASS_HORIZONS, GLOBAL_CHALLENGES, COMMUNITY_MISSIONS, PLAYER_LEADERBOARD, createCommunitySystem } from "./transport-community-events.js";

test("el pase de temporada incluye nivel 27 y recompensas de Canva", () => {
  assert.equal(SEASON_PASS_HORIZONS.currentLevel, 27);
  assert.equal(SEASON_PASS_HORIZONS.currentXp, 7450);
  assert.equal(SEASON_PASS_HORIZONS.targetXp, 10000);
  assert.equal(SEASON_PASS_HORIZONS.rewards.length >= 6, true);
});

test("los eventos globales cubren la ruta artica, desierto y nocturna", () => {
  const ids = GLOBAL_CHALLENGES.map(c => c.id);
  assert.equal(ids.includes("ruta_artica"), true);
  assert.equal(ids.includes("desafio_desierto"), true);
  assert.equal(ids.includes("nocturna_global"), true);

  const artica = GLOBAL_CHALLENGES.find(c => c.id === "ruta_artica");
  assert.equal(artica.rewardCredits, 25000);
  assert.equal(artica.distanceKm, 15000);
});

test("la mision comunitaria de ayuda humanitaria tiene 71% de progreso", () => {
  assert.equal(COMMUNITY_MISSIONS.id, "ayuda_humanitaria");
  assert.equal(COMMUNITY_MISSIONS.deliveriesDone, 28450);
  assert.equal(COMMUNITY_MISSIONS.deliveriesTotal, 40000);
  assert.equal(COMMUNITY_MISSIONS.progressPercent, 71);
});

test("la clasificacion de distancia lidera con ViajeroLunar", () => {
  assert.equal(PLAYER_LEADERBOARD[0].driverName, "ViajeroLunar");
  assert.equal(PLAYER_LEADERBOARD[0].distanceKm, 265768);
});

test("el sistema de comunidad suma entregas comunitarias y reclama recompensas de temporada", () => {
  const comm = createCommunitySystem();
  assert.equal(comm.state.userCredits, 0);

  const claimRes = comm.claimSeasonReward(27);
  assert.equal(claimRes.success, true);
  assert.equal(comm.state.claimedRewards.includes(27), true);

  comm.contributeCommunityMission(50);
  assert.equal(comm.state.communityDeliveries, 28500);
});
