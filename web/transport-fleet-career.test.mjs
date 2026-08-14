import assert from "node:assert/strict";
import test from "node:test";
import { TransportCareer, CAREER_SCHEMA_VERSION } from "./transport-career.js";

const storage = seed => ({ value: seed || null, getItem(){ return this.value; }, setItem(_, value){ this.value=value; } });
const memory = () => storage();

test("migra una partida anterior con el Aster inicial", () => {
  const old = { schema:2, profile:{name:"Mara"}, economy:{money:35000}, garages:[{id:"nova_liria",name:"Nova Liria",slots:2,price:0}], drivers:[] };
  const career = new TransportCareer({ storage:storage(JSON.stringify(old)) });
  assert.equal(career.snapshot.schema, CAREER_SCHEMA_VERSION);
  assert.equal(career.snapshot.fleet[0].modelId, "aster");
});

test("compra, asigna, mejora y mantiene un vehículo persistente", () => {
  const career = new TransportCareer({ autoload:false, storage:memory() });
  career.record(200000, "capital de prueba");
  const driver = career.hireDriver({ name:"Noa", skill:4 });
  const vehicle = career.buyFleetVehicle("aster");
  career.assignFleetVehicle(vehicle.id, driver.id);
  career.upgradeFleetVehicle(vehicle.id, "efficiency");
  career.state.fleet.find(v=>v.id===vehicle.id).condition=80;
  const service = career.serviceFleetVehicle(vehicle.id);
  const saved = career.snapshot;
  assert.equal(saved.drivers.find(d=>d.id===driver.id).vehicleId, vehicle.id);
  assert.equal(saved.fleet.find(v=>v.id===vehicle.id).upgrades.efficiency, 1);
  assert.equal(service.vehicle.condition, 100);
});

test("solo producen los conductores con vehículo operativo asignado", () => {
  const career = new TransportCareer({ autoload:false, storage:memory() });
  const driver = career.hireDriver({ name:"Iria", skill:5, salary:900 });
  assert.equal(career.runCompanyDay(), 0);
  career.assignFleetVehicle(career.snapshot.fleet[0].id, driver.id);
  const originalRandom=Math.random; Math.random=()=>0;
  try { assert.ok(career.runCompanyDay()>0); } finally { Math.random=originalRandom; }
  assert.ok(career.snapshot.fleet[0].odometerKm>0);
  assert.ok(career.snapshot.fleet[0].condition<100);
});
