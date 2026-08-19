import test from "node:test";
import assert from "node:assert/strict";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const { PHASES, normalizePhase, phaseProgress } = require("./transport-boot-screen.js");

test("boot exposes the four real startup phases", () => {
  assert.deepEqual(PHASES, ["DOM", "Modulos", "Render", "Mundo"]);
  assert.equal(normalizePhase("render"), 2);
  assert.equal(normalizePhase("unknown"), 0);
});

test("boot progress is monotonic and bounded", () => {
  const values = PHASES.map(phaseProgress);
  assert.deepEqual(values, [12, 38, 68, 92]);
  assert.equal(phaseProgress(-99), 12);
  assert.equal(phaseProgress(99), 92);
});
