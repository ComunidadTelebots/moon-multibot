import assert from "node:assert/strict";
import test from "node:test";
import { REGIONAL_MARKETS, VEHICLE_AUCTIONS, INSURANCE_POLICIES, createEconomySystem } from "./transport-economy-market.js";

test("los mercados regionales cubren las 5 áreas globales de Canva", () => {
  assert.equal(REGIONAL_MARKETS.length, 5);
  const we = REGIONAL_MARKETS.find(m => m.id === "europa_occidental");
  assert.equal(we.pricePerTon, 1248);
  assert.equal(we.demandPercent, 14);
});

test("las subastas de vehículos incluyen tractoras usadas con kilometraje y pujas", () => {
  assert.equal(VEHICLE_AUCTIONS.length >= 1, true);
  const auction = VEHICLE_AUCTIONS[0];
  assert.equal(auction.title.includes("Tractor"), true);
  assert.equal(auction.year, 2021);
  assert.equal(auction.mileageKm, 485000);
  assert.equal(auction.currentBid, 35800);
});

test("las pólizas de seguro cubren vehículos, carga y propiedades", () => {
  assert.equal(INSURANCE_POLICIES.vehicles.activeCount, 32);
  assert.equal(INSURANCE_POLICIES.cargo.activeCount, 18);
  assert.equal(INSURANCE_POLICIES.property.activeCount, 7);
});

test("el sistema de economía gestiona préstamos bancarios y pujas de subasta", () => {
  const econ = createEconomySystem({ initialCash: 2458750 });
  assert.equal(econ.state.cash, 2458750);

  const bidRes = econ.placeAuctionBid(VEHICLE_AUCTIONS[0].id, 36500);
  assert.equal(bidRes.success, true);
  assert.equal(econ.state.auctions[0].currentBid, 36500);

  econ.takeLoan(500000, 5.25);
  assert.equal(econ.state.activeLoanTotal >= 500000, true);
});
