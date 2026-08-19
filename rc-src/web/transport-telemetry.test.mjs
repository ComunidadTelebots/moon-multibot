import assert from "node:assert/strict";
import test from "node:test";

import { createCargoCondition } from "./transport-cargo-condition.js";
import {
  createTransportEventLog,
  TRANSPORT_EVENT_STORAGE_KEY,
} from "./transport-event-log.js";

function memoryStorage(seed = {}) {
  const values = new Map(Object.entries(seed));
  return {
    getItem(key) { return values.has(key) ? values.get(key) : null; },
    setItem(key, value) { values.set(key, String(value)); },
    read(key) { return values.get(key); },
  };
}

test("event log persists bounded, defensive event copies", () => {
  const storage = memoryStorage();
  const log = createTransportEventLog({ storage, limit: 100 });
  const detail = { contract: "ADR-42", nested: { score: 8 } };
  const event = log.record("contract", "contract:completed", detail, {
    severity: "critical",
    player: "A".repeat(300),
  });

  detail.nested.score = 0;
  event.detail.nested.score = -1;
  assert.equal(log.events[0].detail.nested.score, 8);
  assert.equal(log.events[0].player.length, 240);
  assert.equal(log.summary().completed, 1);
  assert.equal(log.summary().critical, 1);

  for (let index = 0; index < 110; index += 1) {
    log.record("technical", `tick:${index}`);
  }
  assert.equal(log.events.length, 100);
  assert.equal(JSON.parse(storage.read(TRANSPORT_EVENT_STORAGE_KEY)).length, 100);
});

test("event log recovers from corrupt storage and isolates subscribers", () => {
  const storage = memoryStorage({ [TRANSPORT_EVENT_STORAGE_KEY]: "not-json" });
  const log = createTransportEventLog({ storage });
  let received;
  const unsubscribe = log.subscribe(event => { received = event; });
  log.record("cargo", "cargo:loaded", { privateToken: undefined });
  unsubscribe();
  log.record("cargo", "cargo:delivered");

  assert.equal(received.type, "cargo:loaded");
  received.type = "tampered";
  assert.equal(log.events[0].type, "cargo:loaded");
  assert.equal(log.query({ search: "DELIVERED" })[0].type, "cargo:delivered");
});

test("cargo condition clamps damage and models cold-chain recovery", () => {
  const cargo = createCargoCondition({ type: "cold" });
  const overheated = cargo.update({
    ambientTemperature: 42,
    doorOpen: true,
    reeferPowered: false,
    longitudinalG: 500,
    lateralG: 500,
    vibration: 500,
  }, 60);

  assert.equal(overheated.integrity, 0);
  assert.equal(overheated.restraint, 0);
  assert.ok(overheated.alerts.includes("Temperatura fuera de rango"));
  assert.ok(overheated.alerts.includes("Carga dañada"));

  const beforeRecovery = overheated.temperature;
  const recovered = cargo.update({ ambientTemperature: 2.5, reeferPowered: true }, 10);
  assert.ok(Math.abs(recovered.temperature - 2.5) < Math.abs(beforeRecovery - 2.5));
});

test("cargo profiles switch safely and return defensive alert arrays", () => {
  const cargo = createCargoCondition({ type: "unknown" });
  assert.equal(cargo.snapshot().type, "standard");
  assert.deepEqual(cargo.profiles.map(profile => profile.id), [
    "standard", "adr", "cold", "livestock", "fragile",
  ]);

  const selected = cargo.select("livestock");
  assert.equal(selected.temperature, 20);
  selected.alerts.push("external mutation");
  assert.deepEqual(cargo.snapshot().alerts, []);
});

test("cargo operations warn about open doors and allow a stopped inspection", () => {
  const cargo = createCargoCondition({ type: "fragile" });
  const unsafe = cargo.update({ doorOpen: true, speed: 45, lateralG: 8 }, 10);
  assert.ok(unsafe.alerts.includes("Puertas de carga abiertas en marcha"));
  assert.ok(unsafe.restraint < 100);
  const secured = cargo.secure();
  assert.equal(secured.restraint, 100);
});
