import assert from "node:assert/strict";
import test from "node:test";
import { createPlayerProfile, calculateLevelFromXp, calculateTireWear, calculateBrakeWear } from "./transport-player-progression.js";

test("un nuevo jugador empieza con nivel 1, dinero inicial y progreso en 0%", () => {
  const profile = createPlayerProfile({ uid: 12345, name: "Novato" });
  assert.equal(profile.state.level, 1);
  assert.equal(profile.state.xp, 0);
  assert.equal(profile.state.money, 15000);
  assert.equal(profile.state.distanceKm, 0);
  assert.equal(profile.state.hqPhase, 1);
  assert.equal(profile.state.hqProgressPercent, 0);
});

test("el cálculo de niveles y XP es dinámico y proporcional", () => {
  const lvl1 = calculateLevelFromXp(0);
  assert.equal(lvl1.level, 1);
  assert.equal(lvl1.percentToNextLevel, 0);

  const lvl2 = calculateLevelFromXp(1200);
  assert.equal(lvl2.level, 2);
  assert.equal(lvl2.percentToNextLevel > 0, true);
});

test("al ganar XP y dinero por entregas el perfil sube de nivel y desbloquea recompensas", () => {
  const profile = createPlayerProfile({ uid: 999 });
  profile.completeDelivery({ distanceKm: 450, rewardMoney: 3500, earnedXp: 850, damagePercent: 0 });

  assert.equal(profile.state.distanceKm, 450);
  assert.equal(profile.state.money, 18500);
  assert.equal(profile.state.xp, 850);
  assert.equal(profile.state.totalDeliveries, 1);
});

test("el desgaste mecánico de neumáticos y frenos se calcula según los km recorridos", () => {
  const initialTread = 8.0;
  const wornTread = calculateTireWear(initialTread, 15000, 24000); // 15.000 km con 24t de carga
  assert.equal(wornTread < initialTread, true);
  assert.equal(wornTread > 0, true);

  const initialPads = 100;
  const wornPads = calculateBrakeWear(initialPads, 20000, 50); // 20.000 km con 50 frenadas bruscas
  assert.equal(wornPads < 100, true);
});

test("el jugador puede invertir en la construcción de su sede y ver su porcentaje real de obra", () => {
  const profile = createPlayerProfile({ uid: 555, initialMoney: 100000 });
  const buildStep = profile.investInHQ(25000);

  assert.equal(buildStep.success, true);
  assert.equal(profile.state.hqInvestedMoney, 25000);
  assert.equal(profile.state.hqProgressPercent, 25);
  assert.equal(profile.state.money, 75000);
});
