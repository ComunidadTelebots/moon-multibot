/**
 * Módulo de Economía, Mercado Global, Subastas y Seguros (Canal Alfa).
 * Basado fielmente en la página 026 de Canva.
 */

export const REGIONAL_MARKETS = Object.freeze([
  { id: "europa_occidental", name: "Europa Occidental", demandPercent: 14, supplyPercent: 8,  pricePerTon: 1248, trend: "up" },
  { id: "europa_del_este",   name: "Europa del Este",   demandPercent: 9,  supplyPercent: 6,  pricePerTon: 1102, trend: "up" },
  { id: "norteamerica",      name: "Norteamérica",      demandPercent: 12, supplyPercent: 7,  pricePerTon: 1375, trend: "up" },
  { id: "sudamerica",        name: "Sudamérica",        demandPercent: 4,  supplyPercent: 9,  pricePerTon: 982,  trend: "down" },
  { id: "asia",              name: "Asia",              demandPercent: 15, supplyPercent: 10, pricePerTon: 1512, trend: "up" }
]);

export const VEHICLE_AUCTIONS = Object.freeze([
  {
    id: "auc-trx-6x4",
    title: "Camión Tractor 6x4",
    year: 2021,
    mileageKm: 485000,
    currentBid: 35800,
    minBidStep: 500,
    timeLeft: "01:35:42",
    seller: "Trans-Ibérica Flotas"
  },
  {
    id: "auc-trailer-lona",
    title: "Semirremolque Lona Tautliner 13.6m",
    year: 2022,
    mileageKm: 210000,
    currentBid: 18200,
    minBidStep: 300,
    timeLeft: "03:12:10",
    seller: "Logística Central"
  }
]);

export const INSURANCE_POLICIES = Object.freeze({
  vehicles: { label: "Vehículos", activeCount: 32, costMonth: 4800, status: "Activo" },
  cargo:    { label: "Carga",     activeCount: 18, costMonth: 2900, status: "Activo" },
  property: { label: "Propiedad", activeCount: 7,  costMonth: 1650, status: "Activo" }
});

export const CORPORATE_CONTRACTS = Object.freeze([
  { id: "CNT-2025-0021", route: "Madrid -> París",      marginPercent: 10.7, weeklyTrips: 5, rewardPerTrip: 3450 },
  { id: "CNT-2025-0018", route: "Milán -> Berlín",      marginPercent: 11.2, weeklyTrips: 4, rewardPerTrip: 2890 },
  { id: "CNT-2025-0012", route: "Barcelona -> Lyon",    marginPercent: 10.1, weeklyTrips: 6, rewardPerTrip: 2100 },
  { id: "CNT-2025-0009", route: "Hamburgo -> Praga",    marginPercent: 9.6,  weeklyTrips: 4, rewardPerTrip: 1850 },
  { id: "CNT-2025-0005", route: "Varsovia -> Viena",    marginPercent: 8.4,  weeklyTrips: 3, rewardPerTrip: 1600 }
]);

export function createEconomySystem({ initialCash = 2458750, initialLoan = 1250000 } = {}) {
  const state = {
    cash: initialCash,
    activeLoanTotal: initialLoan,
    loanInterestRate: 5.25,
    projectedTaxes6M: 128750,
    financialRiskPercent: 36,
    auctions: JSON.parse(JSON.stringify(VEHICLE_AUCTIONS)),
    contracts: JSON.parse(JSON.stringify(CORPORATE_CONTRACTS)),
    monthlyCashflow: {
      income: 350000,
      expenses: 215000,
      investments: 45000,
      netTotal: 115000
    }
  };

  const listeners = new Set();
  const emit = () => {
    const snap = JSON.parse(JSON.stringify(state));
    listeners.forEach(fn => {
      try { fn(snap); } catch {}
    });
    return snap;
  };

  return {
    get state() {
      return JSON.parse(JSON.stringify(state));
    },
    placeAuctionBid(auctionId, amount) {
      const auc = state.auctions.find(a => a.id === auctionId);
      if (!auc) return { success: false, reason: "Subasta no encontrada" };
      if (amount < auc.currentBid + auc.minBidStep) {
        return { success: false, reason: `Puja mínima: ${auc.currentBid + auc.minBidStep} €` };
      }
      if (state.cash < amount) {
        return { success: false, reason: "Saldo insuficiente" };
      }
      auc.currentBid = amount;
      auc.userIsHighestBidder = true;
      return { success: true, auction: auc, state: emit() };
    },
    takeLoan(amount, interestRate = 5.25) {
      state.cash += amount;
      state.activeLoanTotal += amount;
      state.loanInterestRate = interestRate;
      return emit();
    },
    repayLoan(amount) {
      const pay = Math.min(amount, state.activeLoanTotal, state.cash);
      state.cash -= pay;
      state.activeLoanTotal -= pay;
      return emit();
    },
    subscribe(fn) {
      listeners.add(fn);
      return () => listeners.delete(fn);
    }
  };
}

export default { REGIONAL_MARKETS, VEHICLE_AUCTIONS, INSURANCE_POLICIES, CORPORATE_CONTRACTS, createEconomySystem };
