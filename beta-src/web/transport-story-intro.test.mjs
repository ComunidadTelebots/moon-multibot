import assert from "node:assert/strict";
import test from "node:test";
import { createStoryIntroSequence } from "./transport-story-intro.js";

test("Aurora reutiliza su prólogo sin repetir el selector de camión", () => {
  const sequence = createStoryIntroSequence({ origin:"aurora", choices:{ "truck-origin":"aurora" } });
  const ids = []; while (sequence.current) { ids.push(sequence.current.id); sequence.next(); }
  assert.equal(ids.includes("truck-origin"), false); assert.equal(ids.includes("aurora-reveal"), true); assert.equal(ids.includes("frontier-reveal"), false);
});

test("veterano y Aster conservan sus decisiones cinematográficas", () => {
  const veteran = createStoryIntroSequence({ origin:"frontier" }); assert.equal(veteran.current.id, "final-shift");
  while (veteran.current && veteran.current.id !== "purchase-choice") veteran.next(); assert.equal(veteran.current.choices.length, 3);
  assert.equal(createStoryIntroSequence({ origin:"aster" }).current.id, "terminal-awakens");
});
