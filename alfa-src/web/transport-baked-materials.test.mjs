import assert from "node:assert/strict";
import test from "node:test";
import { CABIN_TILES, EXTERIOR_TILES, INDEPENDENT_TEXTURES } from "./transport-baked-materials.js";

test("Aster uses one authored file per exterior and cabin material", () => {
  assert.deepEqual(Object.keys(INDEPENDENT_TEXTURES.exterior), Object.keys(EXTERIOR_TILES));
  assert.deepEqual(Object.keys(INDEPENDENT_TEXTURES.cabin), Object.keys(CABIN_TILES));
  const urls = Object.values(INDEPENDENT_TEXTURES).flatMap(Object.values);
  assert.equal(urls.length, 29);
  assert.equal(new Set(urls).size, 29);
  assert.ok(urls.every((url) => url.includes("/vehicle-parts/aster-viento/") && url.endsWith("-v1.png")));
  assert.ok(urls.every((url) => !url.includes("atlas")));
});
