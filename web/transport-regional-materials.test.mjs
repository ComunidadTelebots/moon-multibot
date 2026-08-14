import assert from "node:assert/strict";
import test from "node:test";
import {
  ENVIRONMENT_ATLAS_TILES,
  ENVIRONMENT_ATLAS_URL,
  ENVIRONMENT_TEXTURE_URLS,
  environmentAtlasTransform,
} from "./transport-regional-materials.js";

test("the authored environment atlas exposes sixteen unique tiles", () => {
  assert.match(ENVIRONMENT_ATLAS_URL, /world-environment-material-atlas-v1\.png$/);
  const coordinates = Object.values(ENVIRONMENT_ATLAS_TILES).map(value => value.join(","));
  assert.equal(coordinates.length, 16);
  assert.equal(new Set(coordinates).size, 16);
  assert.equal(Object.keys(ENVIRONMENT_TEXTURE_URLS).length, 16);
  for (const url of Object.values(ENVIRONMENT_TEXTURE_URLS)) assert.match(url, /^\.\/generated-textures\/environment-.+-v1\.png$/);
});

test("atlas transforms address tiles from top-left without bleeding outside", () => {
  assert.deepEqual(environmentAtlasTransform("terrain"), { repeat: [.25, .25], offset: [0, .75] });
  assert.deepEqual(environmentAtlasTransform("airport"), { repeat: [.25, .25], offset: [.75, 0] });
  assert.equal(environmentAtlasTransform("missing"), null);
  for (const name of Object.keys(ENVIRONMENT_ATLAS_TILES)) {
    const transform = environmentAtlasTransform(name);
    assert.ok(transform.offset.every(value => value >= 0 && value <= .75));
  }
});
