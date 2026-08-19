import assert from "node:assert/strict";
import test from "node:test";
import { IMMUTABLE_CANVA_CONSTANTS, createUIDataBinding } from "./transport-ui-data-binding.js";

test("los catálogos fijos de vehículos, ciudades y strings de Canva son inmutables", () => {
  assert.equal(IMMUTABLE_CANVA_CONSTANTS.vehicles.truck, "Aster Viento 3D");
  assert.equal(IMMUTABLE_CANVA_CONSTANTS.vehicles.bus, "Nortia Urbano X8");
  assert.equal(IMMUTABLE_CANVA_CONSTANTS.cities.includes("Nova Liria"), true);
  assert.equal(IMMUTABLE_CANVA_CONSTANTS.skills.includes("Eficiencia Diésel"), true);
  assert.equal(IMMUTABLE_CANVA_CONSTANTS.storyItem, "Caja 07-A");
});

test("el dinero, nivel, km y desgaste son reactivos y se actualizan dinámicamente en la UI", () => {
  const binding = createUIDataBinding({
    initialMoney: 12500,
    initialXp: 0,
    initialKm: 0,
    truckModel: IMMUTABLE_CANVA_CONSTANTS.vehicles.truck
  });

  assert.equal(binding.formatted.money, "12.500 €");
  assert.equal(binding.formatted.truckModel, "Aster Viento 3D"); // El modelo permanece fijo

  // Simular entrega: el dinero y XP crecen dinámicamente
  binding.addEarnings(4500, 320, 180);

  assert.equal(binding.state.money, 17000);
  assert.equal(binding.formatted.money, "17.000 €");
  assert.equal(binding.state.odometerKm, 180);
  assert.equal(binding.formatted.odometer, "180 km");
  assert.equal(binding.formatted.truckModel, "Aster Viento 3D"); // El string fijo nunca cambia
});

test("el combustible y desgaste de piezas disminuyen con el uso y se formatean para la UI", () => {
  const binding = createUIDataBinding({ initialMoney: 50000 });

  binding.consumeFuel(14.5);
  assert.equal(binding.state.fuelPercent, 85.5);
  assert.equal(binding.formatted.fuel, "86%");

  binding.payExpense(350, "Peaje de autopista");
  assert.equal(binding.state.money, 49650);
  assert.equal(binding.formatted.money, "49.650 €");
});
