import assert from "node:assert/strict";
import test from "node:test";
import { INFRASTRUCTURE_MODULES, REGIONAL_EXPANSIONS, createInfrastructureSystem } from "./transport-infrastructure-expansion.js";

test("los modulos de infraestructura cubren los 8 pilares de Canva", () => {
  const ids = INFRASTRUCTURE_MODULES.map(m => m.id);
  assert.equal(ids.includes("headquarters_builder"), true);
  assert.equal(ids.includes("garages_workshops"), true);
  assert.equal(ids.includes("cargo_terminals"), true);
  assert.equal(ids.includes("airports"), true);
  assert.equal(ids.includes("ports"), true);
  assert.equal(ids.includes("energy_stations"), true);
  assert.equal(ids.includes("roads_permits"), true);
  assert.equal(ids.includes("regional_expansion"), true);
});

test("las terminales y puertos tienen capacidades y ocupaciones de Canva", () => {
  const terminal = INFRASTRUCTURE_MODULES.find(m => m.id === "cargo_terminals");
  assert.equal(terminal.capacityTons, 20000);
  assert.equal(terminal.currentTons, 12750);
  assert.equal(terminal.occupancyPercent, 63);

  const port = INFRASTRUCTURE_MODULES.find(m => m.id === "ports");
  assert.equal(port.berthsTotal, 6);
  assert.equal(port.berthsOccupied, 3);
});

test("la estacion de energia incluye diesel y cargadores EV", () => {
  const energy = INFRASTRUCTURE_MODULES.find(m => m.id === "energy_stations");
  assert.equal(energy.fuelLiters, 180000);
  assert.equal(energy.evChargersTotal, 24);
  assert.equal(energy.evChargersActive, 16);
});

test("el sistema de infraestructura permite comprar parcelas y avanzar construccion", () => {
  const infra = createInfrastructureSystem({ initialBudget: 152430000 });
  assert.equal(infra.state.budget, 152430000);

  const phaseRes = infra.advanceHeadquartersPhase();
  assert.equal(phaseRes.currentPhase, 3);

  const buyRes = infra.buyRegionalExpansion("costa_azul");
  assert.equal(buyRes.success, true);
  assert.equal(infra.state.ownedRegions.includes("costa_azul"), true);
});
