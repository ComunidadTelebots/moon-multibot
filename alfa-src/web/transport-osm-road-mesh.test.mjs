import assert from "node:assert/strict";
import test from "node:test";
import { buildRoadSignPlan, roadSignLabel } from "./transport-osm-road-mesh.js";

test("normaliza destinos y limita textos largos", () => {
  assert.equal(roadSignLabel({ name: "  A-6   Madrid  " }), "A-6 Madrid");
  assert.equal(roadSignLabel({ name: "Carretera sin nombre" }), "Siguiente salida");
  assert.ok(roadSignLabel({ name: "Una carretera con un nombre extraordinariamente largo hacia el norte" }).length <= 34);
});

test("proyecta los pasos OSRM sobre la distancia real de la ruta", () => {
  const route = Array.from({ length: 11 }, (_, index) => ({ x: 0, z: -index * 10, distanceKm: index }));
  const plan = buildRoadSignPlan(route, [
    { name: "A-6 Madrid", distanceKm: 2.2, maneuver: "turn right" },
    { name: "AP-9 A Coruña", distanceKm: 4.7, maneuver: "turn left" },
  ]);
  assert.deepEqual(plan.map(sign => sign.index), [2, 7]);
  assert.equal(plan[0].label, "A-6 Madrid");
  assert.equal(plan[1].maneuver, "turn left");
});

test("no crea carteles sin ruta o pasos", () => {
  assert.deepEqual(buildRoadSignPlan([], [{ name: "A-1" }]), []);
  assert.deepEqual(buildRoadSignPlan([{ x: 0, z: 0 }, { x: 0, z: 1 }], []), []);
});
