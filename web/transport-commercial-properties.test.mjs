import assert from "node:assert/strict";
import test from "node:test";
import {
  PROPERTY_TYPES,
  CITY_TAX_RATES,
  createCommercialPropertySystem
} from "./transport-commercial-properties.js";

test("los tipos de negocio cubren hoteles, restaurantes, bares, gasolineras y talleres con 3 Tiers", () => {
  const ids = Object.keys(PROPERTY_TYPES);
  assert.equal(ids.includes("hotel"), true);
  assert.equal(ids.includes("restaurante"), true);
  assert.equal(ids.includes("bar"), true);
  assert.equal(ids.includes("gasolinera"), true);
  assert.equal(ids.includes("taller"), true);

  // Verificar que cada tipo tiene Tier 1, Tier 2 y Tier 3
  for (const typeKey of ids) {
    const p = PROPERTY_TYPES[typeKey];
    assert.equal(p.tiers[1] !== undefined, true);
    assert.equal(p.tiers[2] !== undefined, true);
    assert.equal(p.tiers[3] !== undefined, true);
    assert.equal(p.tiers[3].purchaseCost > p.tiers[1].purchaseCost, true);
    assert.equal(p.tiers[3].dailyIncome > p.tiers[1].dailyIncome, true);
  }
});

test("las tasas de impuestos municipales cubren las ciudades del juego", () => {
  const cities = Object.keys(CITY_TAX_RATES);
  assert.equal(cities.includes("Nova Liria"), true);
  assert.equal(cities.includes("Puerto Alba"), true);
  assert.equal(cities.includes("Valleverde"), true);
  assert.equal(cities.includes("Madrid"), true);
});

test("un jugador puede comprar un negocio Tier 1, recaudar ingresos y pagar impuestos a la ciudad", () => {
  const sys = createCommercialPropertySystem({ initialPlayerMoney: 150000 });

  // Comprar un bar Tier 1 en Nova Liria
  const buyRes = sys.acquireProperty({ type: "bar", city: "Nova Liria", name: "Café Ruta Nova" });
  assert.equal(buyRes.success, true);
  assert.equal(sys.state.ownedProperties.length, 1);
  assert.equal(sys.state.ownedProperties[0].tier, 1);
  assert.equal(sys.state.playerMoney < 150000, true);

  // Avanzar ciclo diario (recaudar ingresos y generar impuestos municipales)
  const dayRes = sys.processDailyCycle();
  assert.equal(dayRes.grossRevenue > 0, true);
  assert.equal(dayRes.accruedTaxes > 0, true);
  assert.equal(sys.state.pendingCityTaxes > 0, true);

  // Pagar los impuestos a la ciudad
  const taxPay = sys.payCityTaxes();
  assert.equal(taxPay.success, true);
  assert.equal(sys.state.pendingCityTaxes, 0);
});

test("un jugador puede mejorar un negocio de Tier 1 a Tier 2 y a Tier 3 aumentando ingresos", () => {
  const sys = createCommercialPropertySystem({ initialPlayerMoney: 1200000 });
  const buyRes = sys.acquireProperty({ type: "hotel", city: "Madrid", name: "Gran Hotel Continental" });
  const propId = buyRes.property.id;

  const upg1 = sys.upgradeProperty(propId);
  assert.equal(upg1.success, true);
  assert.equal(upg1.property.tier, 2);

  const upg2 = sys.upgradeProperty(propId);
  assert.equal(upg2.success, true);
  assert.equal(upg2.property.tier, 3);
  assert.equal(upg2.property.dailyIncome >= 5500, true);
});
