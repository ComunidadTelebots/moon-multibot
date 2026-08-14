import assert from "node:assert/strict";
import test from "node:test";
import { createStoryRuntime } from "./transport-story-runtime.js";

const memory = () => { const data = new Map(); return { getItem:key => data.get(key) ?? null, setItem:(key,value) => data.set(key,value) }; };

test("selecciona una campaña y conserva sus variables iniciales", () => {
  const runtime = createStoryRuntime({ storage:memory() });
  runtime.selectOrigin("aurora");
  assert.equal(runtime.snapshot.origin, "aurora");
  assert.equal(runtime.snapshot.variables.debt, 30000);
});

test("aplica y persiste una decisión del prólogo", () => {
  const storage = memory();
  const runtime = createStoryRuntime({ storage });
  runtime.selectOrigin("aurora");
  runtime.choose("player-choice", "family");
  assert.equal(runtime.snapshot.choices["player-choice"], "family");
  assert.equal(runtime.snapshot.variables.familyBond, 2);
  assert.equal(createStoryRuntime({ storage }).snapshot.choices["player-choice"], "family");
});

test("rechaza decisiones ajenas a la campaña elegida", () => {
  const runtime = createStoryRuntime({ storage:memory() });
  runtime.selectOrigin("aster");
  assert.throws(() => runtime.choose("player-choice", "family"), /Decisión no disponible/);
});
