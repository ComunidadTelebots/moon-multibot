import assert from "node:assert/strict";
import { chaseCameraComposition } from "./transport-camera-composition.js";

const truck = chaseCameraComposition("truck", 0, 0);
const bus = chaseCameraComposition("bus", 0, 0);
const ambulance = chaseCameraComposition("ambulance", 0, 0);
assert.ok(truck.z > bus.z && bus.z > ambulance.z, "la cámara respeta la longitud del vehículo");
assert.ok(truck.y > bus.y, "el conjunto articulado necesita más altura de encuadre");

const moving = chaseCameraComposition("truck", 90, 0.5);
assert.ok(moving.z > truck.z, "la cámara se abre con la velocidad");
assert.ok(moving.lookZ < truck.lookZ, "la mirada anticipa más carretera con velocidad");
assert.ok(moving.x > 0 && moving.fov > truck.fov, "dirección y velocidad modifican la composición");

const fallback = chaseCameraComposition("unknown", 0, 0);
assert.deepEqual(fallback, truck, "los vehículos desconocidos conservan una composición segura");
console.log("transport-camera-composition: OK");
