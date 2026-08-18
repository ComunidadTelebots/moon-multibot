import assert from "node:assert/strict";
import test from "node:test";
import {
  ADR_CLASSES,
  TUNNEL_CATEGORIES,
  checkTunnelAccess,
  createADRRoutingEngine
} from "./transport-adr-tunnel-routing.js";

test("los catalogos ADR y categorias de tuneles cubren la normativa europea", () => {
  assert.equal(ADR_CLASSES["3"].name, "Líquidos inflamables");
  assert.equal(ADR_CLASSES["8"].name, "Sustancias corrosivas");
  assert.equal(TUNNEL_CATEGORIES.A.restrictionLevel, 0); // Sin restricción
  assert.equal(TUNNEL_CATEGORIES.E.restrictionLevel, 4); // Prohibido todo ADR
});

test("la comprobacion de acceso a tunel valida si una carga peligrosa puede cruzar", () => {
  // Gasolina (Clase 3, Código Kemler 33-1203)
  const gasolineAccessA = checkTunnelAccess({ adrClass: "3", kemler: "33-1203", tunnelCategory: "A" });
  assert.equal(gasolineAccessA.allowed, true);

  const gasolineAccessE = checkTunnelAccess({ adrClass: "3", kemler: "33-1203", tunnelCategory: "E" });
  assert.equal(gasolineAccessE.allowed, false);
  assert.equal(gasolineAccessE.requiresDetour, true);
});

test("el motor de enrutamiento ADR recalcula desvios y sanciona accesos no autorizados", () => {
  const engine = createADRRoutingEngine({ currentCargo: { name: "Gasolina Super 98", adrClass: "3", kemler: "33-1203" } });

  assert.equal(engine.state.adrPlateOrangeActive, true);
  assert.equal(engine.state.kemlerCode, "33-1203");

  // Intentar cruzar Túnel de Guadarrama (Categoría D) con gasolina
  const attempt = engine.attemptTunnelEntry({ tunnelName: "Túnel de Guadarrama", category: "D" });
  assert.equal(attempt.allowed, false);
  assert.equal(attempt.fined, true);
  assert.equal(engine.state.infractions.length, 1);
});
