/**
 * Rutas del Continente - sistema de carrera independiente.
 * No conoce Three.js ni el DOM: transport-3d.html puede escuchar cambios y
 * traducirlos a HUD, trayectos y eventos del mundo.
 */

export const CAREER_STORAGE_KEY = "moon.transport.career.v1";
export const CAREER_SCHEMA_VERSION = 1;

const GARAGES = Object.freeze({
  nova_liria: { id: "nova_liria", name: "Nova Liria", price: 0, slots: 2 },
  puerto_aurora: { id: "puerto_aurora", name: "Puerto Aurora", price: 92000, slots: 3 },
  valle_cobalto: { id: "valle_cobalto", name: "Valle Cobalto", price: 138000, slots: 4 },
  capital_verde: { id: "capital_verde", name: "Capital Verde", price: 215000, slots: 5 },
});

const CARGO = Object.freeze([
  { id: "alimentos", name: "Alimentos refrigerados", rate: 18, fragility: 0.35 },
  { id: "madera", name: "Madera certificada", rate: 12, fragility: 0.08 },
  { id: "maquinaria", name: "Maquinaria industrial", rate: 23, fragility: 0.25 },
  { id: "medicinas", name: "Suministros médicos", rate: 28, fragility: 0.55 },
  { id: "electronica", name: "Equipos electrónicos", rate: 31, fragility: 0.7 },
  { id: "reciclaje", name: "Material para reciclaje", rate: 10, fragility: 0.05 },
]);

const CITIES = Object.freeze([
  { id: "nova_liria", name: "Nova Liria", x: 0, z: 0 },
  { id: "puerto_aurora", name: "Puerto Aurora", x: -145, z: 310 },
  { id: "valle_cobalto", name: "Valle Cobalto", x: 220, z: 520 },
  { id: "capital_verde", name: "Capital Verde", x: 390, z: 80 },
  { id: "bahia_solar", name: "Bahía Solar", x: -360, z: 620 },
  { id: "monte_claro", name: "Monte Claro", x: 510, z: 760 },
]);

const DRIVER_NAMES = ["Alex Vega", "Noa Serra", "Dani Sol", "Iria Norte", "Leo Campos", "Mara Ríos"];

const clamp = (value, min, max) => Math.min(max, Math.max(min, Number(value) || 0));
const roundMoney = (value) => Math.round((Number(value) || 0) * 100) / 100;
const uid = (prefix = "id") => `${prefix}_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 8)}`;
const copy = (value) => JSON.parse(JSON.stringify(value));

function initialState(name = "Transportista") {
  const now = Date.now();
  return {
    schema: CAREER_SCHEMA_VERSION,
    profile: { name: String(name).slice(0, 32), company: "Rutas Moon", createdAt: now, lastPlayedAt: now },
    economy: { money: 35000, totalEarned: 0, totalSpent: 0, finesPaid: 0 },
    progress: { xp: 0, level: 1, completedJobs: 0, failedJobs: 0, distanceKm: 0 },
    truck: { fuel: 100, fuelCapacity: 100, condition: 100, odometerKm: 0 },
    garages: [{ ...GARAGES.nova_liria, purchasedAt: now }],
    drivers: [],
    loans: [],
    contracts: [],
    activeContractId: null,
    ledger: [],
    settings: { autosave: true },
  };
}

function normalize(raw) {
  const base = initialState(raw?.profile?.name);
  if (!raw || typeof raw !== "object") return base;
  const state = {
    ...base,
    ...raw,
    profile: { ...base.profile, ...raw.profile },
    economy: { ...base.economy, ...raw.economy },
    progress: { ...base.progress, ...raw.progress },
    truck: { ...base.truck, ...raw.truck },
    settings: { ...base.settings, ...raw.settings },
    garages: Array.isArray(raw.garages) ? raw.garages : base.garages,
    drivers: Array.isArray(raw.drivers) ? raw.drivers : [],
    loans: Array.isArray(raw.loans) ? raw.loans : [],
    contracts: Array.isArray(raw.contracts) ? raw.contracts : [],
    ledger: Array.isArray(raw.ledger) ? raw.ledger.slice(-100) : [],
  };
  state.truck.fuel = clamp(state.truck.fuel, 0, state.truck.fuelCapacity);
  state.truck.condition = clamp(state.truck.condition, 0, 100);
  return state;
}

export class TransportCareer {
  constructor(options = {}) {
    this.storage = options.storage ?? globalThis.localStorage ?? null;
    this.storageKey = options.storageKey || CAREER_STORAGE_KEY;
    this.listeners = new Set();
    this.state = initialState(options.playerName);
    if (options.autoload !== false) this.load();
  }

  get snapshot() { return copy(this.state); }
  get level() { return this.state.progress.level; }
  get activeContract() { return this.state.contracts.find((job) => job.id === this.state.activeContractId) || null; }
  get catalog() { return { cities: copy(CITIES), cargo: copy(CARGO), garages: copy(Object.values(GARAGES)) }; }

  subscribe(listener) {
    if (typeof listener !== "function") throw new TypeError("listener debe ser una función");
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  emit(type, detail = {}) {
    const event = { type, detail: copy(detail), state: this.snapshot };
    this.listeners.forEach((listener) => listener(event));
    if (this.state.settings.autosave) this.save();
    return event;
  }

  save() {
    this.state.profile.lastPlayedAt = Date.now();
    if (this.storage) this.storage.setItem(this.storageKey, JSON.stringify(this.state));
    return this.snapshot;
  }

  load() {
    try {
      const stored = this.storage?.getItem(this.storageKey);
      if (stored) this.state = normalize(JSON.parse(stored));
    } catch (error) {
      console.warn("[transport-career] No se pudo cargar la partida", error);
    }
    return this.snapshot;
  }

  reset(playerName = this.state.profile.name) {
    this.state = initialState(playerName);
    this.save();
    this.emit("career:reset");
    return this.snapshot;
  }

  exportSave() { return JSON.stringify(this.state); }
  importSave(serialized) {
    const parsed = typeof serialized === "string" ? JSON.parse(serialized) : serialized;
    this.state = normalize(parsed);
    this.emit("career:imported");
    return this.snapshot;
  }

  record(amount, reason, meta = {}) {
    amount = roundMoney(amount);
    this.state.economy.money = roundMoney(this.state.economy.money + amount);
    if (amount >= 0) this.state.economy.totalEarned += amount;
    else this.state.economy.totalSpent += Math.abs(amount);
    this.state.ledger.push({ id: uid("tx"), at: Date.now(), amount, reason, ...meta });
    this.state.ledger = this.state.ledger.slice(-100);
    return amount;
  }

  addXp(amount) {
    this.state.progress.xp += Math.max(0, Math.round(amount));
    this.state.progress.level = Math.max(1, Math.floor(Math.sqrt(this.state.progress.xp / 250)) + 1);
    return this.state.progress.level;
  }

  generateContracts(count = 6) {
    const generated = [];
    for (let i = 0; i < clamp(count, 1, 20); i += 1) {
      const from = CITIES[Math.floor(Math.random() * CITIES.length)];
      let to = from;
      while (to.id === from.id) to = CITIES[Math.floor(Math.random() * CITIES.length)];
      const cargo = CARGO[Math.floor(Math.random() * CARGO.length)];
      const distanceKm = Math.max(45, Math.round(Math.hypot(to.x - from.x, to.z - from.z) * 0.82));
      const levelBonus = 1 + Math.min(0.45, this.level * 0.025);
      const reward = Math.round((650 + distanceKm * cargo.rate) * levelBonus / 10) * 10;
      generated.push({
        id: uid("job"), from: copy(from), to: copy(to), cargo: copy(cargo), distanceKm,
        reward, xp: Math.round(90 + distanceKm * 0.7), deadlineMinutes: Math.round(18 + distanceKm / 6),
        status: "available", generatedAt: Date.now(),
      });
    }
    this.state.contracts = [...this.state.contracts.filter((job) => job.status !== "available"), ...generated].slice(-30);
    this.emit("contracts:generated", { count: generated.length });
    return copy(generated);
  }

  acceptContract(id) {
    if (this.activeContract) throw new Error("Ya hay un contrato activo");
    const job = this.state.contracts.find((contract) => contract.id === id && contract.status === "available");
    if (!job) throw new Error("Contrato no disponible");
    job.status = "active";
    job.acceptedAt = Date.now();
    this.state.activeContractId = job.id;
    this.emit("contract:accepted", { contract: job });
    return copy(job);
  }

  completeContract({ damage = 0, lateMinutes = 0, cargoDamage = 0 } = {}) {
    const job = this.activeContract;
    if (!job) throw new Error("No hay un contrato activo");
    const penaltyRatio = clamp(damage / 140 + cargoDamage * job.cargo.fragility / 100 + lateMinutes / 300, 0, 0.8);
    const payout = Math.round(job.reward * (1 - penaltyRatio));
    job.status = "completed";
    job.completedAt = Date.now();
    job.payout = payout;
    this.record(payout, `Entrega: ${job.cargo.name}`, { contractId: job.id });
    this.addXp(Math.round(job.xp * (1 - penaltyRatio * 0.5)));
    this.state.progress.completedJobs += 1;
    this.addDistance(job.distanceKm);
    this.state.activeContractId = null;
    this.emit("contract:completed", { contract: job, payout, penaltyRatio });
    return { contract: copy(job), payout, penaltyRatio };
  }

  failContract(reason = "Entrega cancelada") {
    const job = this.activeContract;
    if (!job) return false;
    job.status = "failed";
    job.failureReason = reason;
    this.record(-Math.round(job.reward * 0.12), reason, { contractId: job.id });
    this.state.progress.failedJobs += 1;
    this.state.activeContractId = null;
    this.emit("contract:failed", { contract: job });
    return true;
  }

  addDistance(km, consumptionPer100Km = 28, wearPer1000Km = 1.8) {
    km = Math.max(0, Number(km) || 0);
    this.state.progress.distanceKm += km;
    this.state.truck.odometerKm += km;
    this.state.truck.fuel = clamp(this.state.truck.fuel - km * consumptionPer100Km / 100, 0, this.state.truck.fuelCapacity);
    this.state.truck.condition = clamp(this.state.truck.condition - km * wearPer1000Km / 1000, 0, 100);
    this.emit("truck:distance", { km });
    return copy(this.state.truck);
  }

  refuel(liters = this.state.truck.fuelCapacity, pricePerLiter = 1.72) {
    const available = this.state.truck.fuelCapacity - this.state.truck.fuel;
    const wanted = clamp(liters, 0, available);
    const affordable = Math.min(wanted, this.state.economy.money / pricePerLiter);
    const cost = roundMoney(affordable * pricePerLiter);
    this.state.truck.fuel += affordable;
    this.record(-cost, "Combustible");
    this.emit("truck:refueled", { liters: affordable, cost });
    return { liters: affordable, cost };
  }

  repair(percent = 100, pricePerPercent = 125) {
    const needed = clamp(percent, 0, 100 - this.state.truck.condition);
    const repaired = Math.min(needed, this.state.economy.money / pricePerPercent);
    const cost = roundMoney(repaired * pricePerPercent);
    this.state.truck.condition += repaired;
    this.record(-cost, "Mantenimiento del vehículo");
    this.emit("truck:repaired", { repaired, cost });
    return { repaired, cost };
  }

  applyFine({ amount = 250, reason = "Infracción de tráfico", points = 0 } = {}) {
    amount = Math.max(0, roundMoney(amount));
    this.record(-amount, reason, { kind: "fine", points });
    this.state.economy.finesPaid += amount;
    this.emit("fine:paid", { amount, reason, points });
    return amount;
  }

  takeLoan(amount, months = 12, annualRate = 0.08) {
    amount = clamp(amount, 1000, 500000);
    months = Math.round(clamp(months, 3, 60));
    const totalDue = roundMoney(amount * (1 + annualRate * months / 12));
    const loan = { id: uid("loan"), principal: amount, balance: totalDue, monthlyPayment: roundMoney(totalDue / months), monthsLeft: months, annualRate, createdAt: Date.now() };
    this.state.loans.push(loan);
    this.record(amount, "Préstamo recibido", { loanId: loan.id });
    this.emit("loan:taken", { loan });
    return copy(loan);
  }

  payLoan(id, amount) {
    const loan = this.state.loans.find((item) => item.id === id);
    if (!loan) throw new Error("Préstamo no encontrado");
    const paid = Math.min(clamp(amount || loan.monthlyPayment, 0, loan.balance), this.state.economy.money);
    loan.balance = roundMoney(loan.balance - paid);
    if (loan.balance <= 0) loan.closedAt = Date.now();
    else loan.monthsLeft = Math.max(0, loan.monthsLeft - 1);
    this.record(-paid, "Cuota de préstamo", { loanId: loan.id });
    this.emit("loan:paid", { loan, paid });
    return { loan: copy(loan), paid };
  }

  buyGarage(id) {
    const garage = GARAGES[id];
    if (!garage) throw new Error("Garaje desconocido");
    if (this.state.garages.some((item) => item.id === id)) throw new Error("El garaje ya pertenece a la empresa");
    if (this.state.economy.money < garage.price) throw new Error("Fondos insuficientes");
    const owned = { ...garage, purchasedAt: Date.now() };
    this.state.garages.push(owned);
    this.record(-garage.price, `Garaje: ${garage.name}`, { garageId: id });
    this.emit("garage:purchased", { garage: owned });
    return copy(owned);
  }

  hireDriver({ name, skill, salary } = {}) {
    const capacity = this.state.garages.reduce((sum, garage) => sum + garage.slots, 0);
    if (this.state.drivers.length >= capacity) throw new Error("No quedan plazas en los garajes");
    const driver = { id: uid("driver"), name: name || DRIVER_NAMES[this.state.drivers.length % DRIVER_NAMES.length], skill: clamp(skill ?? 1, 1, 10), salary: roundMoney(salary ?? 950), status: "idle", garageId: this.state.garages[0].id, hiredAt: Date.now(), earnings: 0 };
    this.state.drivers.push(driver);
    this.emit("driver:hired", { driver });
    return copy(driver);
  }

  assignDriver(driverId, garageId) {
    const driver = this.state.drivers.find((item) => item.id === driverId);
    const garage = this.state.garages.find((item) => item.id === garageId);
    if (!driver || !garage) throw new Error("Conductor o garaje no disponible");
    const occupied = this.state.drivers.filter((item) => item.garageId === garageId && item.id !== driverId).length;
    if (occupied >= garage.slots) throw new Error("El garaje está completo");
    driver.garageId = garageId;
    this.emit("driver:assigned", { driver, garage });
    return copy(driver);
  }

  runCompanyDay() {
    let net = 0;
    for (const driver of this.state.drivers) {
      const gross = Math.round(450 + driver.skill * 135 + Math.random() * 400);
      const profit = gross - driver.salary / 30;
      driver.earnings += profit;
      net += profit;
    }
    this.record(net, "Operaciones de conductores");
    this.emit("company:day", { net: roundMoney(net) });
    return roundMoney(net);
  }
}

export function createTransportCareer(options) {
  return new TransportCareer(options);
}

export default TransportCareer;
