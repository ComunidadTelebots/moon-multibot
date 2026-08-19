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

  for (const typeKey of ids) {
    const p = PROPERTY_TYPES[typeKey];
    assert.equal(p.tiers[1] !== undefined, true);
    assert.equal(p.tiers[2] !== undefined, true);
    assert.equal(p.tiers[3] !== undefined, true);
  }
});

test("si no se pagan los impuestos municipales se suspenden los servicios de la ciudad", () => {
  const sys = createCommercialPropertySystem({ initialPlayerMoney: 200000 });
  sys.acquireProperty({ type: "gasolinera", city: "Nova Liria" });

  for (let i = 0; i < 4; i++) {
    sys.processDailyCycle();
  }

  const cityServices = sys.getCityServiceStatus("Nova Liria");
  assert.equal(cityServices.status, "SUSPENDIDO");
  assert.equal(cityServices.businessClosedDueToDebt, true);

  sys.payCityTaxes("Nova Liria");
  const restoredServices = sys.getCityServiceStatus("Nova Liria");
  assert.equal(restoredServices.status, "OPERATIVO");
  assert.equal(restoredServices.businessClosedDueToDebt, false);
});

test("el ayuntamiento embarga el negocio a final de mes si persiste el impago tributario", () => {
  const sys = createCommercialPropertySystem({ initialPlayerMoney: 200000 });
  const buyRes = sys.acquireProperty({ type: "restaurante", city: "Puerto Alba", name: "Asador Alba" });
  assert.equal(sys.state.ownedProperties.length, 1);

  // Simular 30 días de ciclo mensual sin abonar impuestos
  for (let d = 0; d < 30; d++) {
    sys.processDailyCycle();
  }

  // Ejecutar auditoría de fin de mes del ayuntamiento
  const auditRes = sys.processEndOfMonthAudit();
  assert.equal(auditRes.embargoedProperties.length >= 1, true);
  assert.equal(sys.state.ownedProperties.length, 0); // Negocio embargado y perdido
  assert.equal(sys.state.embargoedPropertiesHistory.length, 1);
});

test("si no se paga la tasa de vado retiran la placa y la grúa se lleva el camión al depósito municipal", () => {
  const sys = createCommercialPropertySystem({ initialPlayerMoney: 200000 });
  const buyRes = sys.acquireProperty({ type: "taller", city: "Nova Liria" });
  const propId = buyRes.property.id;

  // Registrar camión asignado al vado
  sys.assignVehicleToVado(propId, "TRX-7781");
  assert.equal(sys.state.vadoPasses[propId].plateActive, true);
  assert.equal(sys.state.impoundedVehicles.length, 0);

  // Simular impago continuado de vado
  sys.simulateVadoDefault(propId);
  assert.equal(sys.state.vadoPasses[propId].plateActive, false); // Placa de vado retirada
  assert.equal(sys.state.impoundedVehicles.some(v => v.plate === "TRX-7781"), true); // Camión retirado por la grúa

  // Para recuperar el vehículo hay que pagar grúa + regularizar vado
  const releaseRes = sys.releaseImpoundedVehicle("TRX-7781", propId);
  assert.equal(releaseRes.success, true);
  assert.equal(sys.state.impoundedVehicles.length, 0);
  assert.equal(sys.state.vadoPasses[propId].plateActive, true);
});
