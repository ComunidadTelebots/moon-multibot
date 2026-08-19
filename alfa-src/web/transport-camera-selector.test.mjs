import assert from "node:assert/strict";
import test from "node:test";
import { cameraViewsFor } from "./transport-camera-selector.js";

test("camera selector exposes nine numbered unique views", () => {
  const views = cameraViewsFor("truck");
  assert.equal(views.length, 9);
  assert.deepEqual(views.map(view => view.key), [1,2,3,4,5,6,7,8,9]);
  assert.equal(new Set(views.map(view => view.name)).size, 9);
});

test("camera selector adapts the interior position to each vehicle family", () => {
  assert.equal(cameraViewsFor("bus")[2].name, "Salón");
  assert.equal(cameraViewsFor("helicopter")[2].name, "Cabina vuelo");
  assert.equal(cameraViewsFor("container_ship")[2].name, "Puente");
  assert.equal(cameraViewsFor("truck")[2].name, "Interior");
});
