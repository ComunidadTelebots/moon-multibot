/**
 * Rutas del Continente - sistema de carrera independiente.
 * No conoce Three.js ni el DOM: transport-3d.html puede escuchar cambios y
 * traducirlos a HUD, trayectos y eventos del mundo.
 */

export const CAREER_STORAGE_KEY = "moon.transport.career.v1";
export const CAREER_SCHEMA_VERSION = 3;

const FLEET_VEHICLES = Object.freeze({
  aster: { id: "aster", name: "Aster Viento", kind: "truck", price: 78000, capacityKg: 24000, baseYield: 1, requiredLevel: 1 },
  nortia: { id: "nortia", name: "Nortia Urbano X8", kind: "bus", price: 112000, capacityKg: 0, baseYield: 1.12, requiredLevel: 3 },
  atlas: { id: "atlas", name: "Atlas Carga 6x4", kind: "truck", price: 148000, capacityKg: 36000, baseYield: 1.28, requiredLevel: 5 },
  boreal: { id: "boreal", name: "Boreal Frío E", kind: "truck", price: 186000, capacityKg: 26000, baseYield: 1.42, requiredLevel: 7 },
});

const FLEET_UPGRADES = Object.freeze({
  engine: { id: "engine", name: "Cadena cinemática", costs: [9000, 22000, 48000], maxRank: 3 },
  efficiency: { id: "efficiency", name: "Eficiencia", costs: [7000, 18000, 39000], maxRank: 3 },
  safety: { id: "safety", name: "Seguridad activa", costs: [6500, 16000, 35000], maxRank: 3 },
});

const DRIVER_TALENTS = Object.freeze({
  efficiency: { id: "efficiency", name: "Eco-conducción", description: "Reduce costes operativos", maxRank: 3 },
  fragile: { id: "fragile", name: "Carga delicada", description: "Mejora ingresos especiales", maxRank: 3 },
  punctuality: { id: "punctuality", name: "Ruta exprés", description: "Aumenta entregas por jornada", maxRank: 3 },
});

const DELIVERY_BOTS = Object.freeze({
  rover: { id: "rover", name: "Rover urbano", price: 12500, capacity: 3, yield: 460 },
  courier: { id: "courier", name: "Courier eléctrico", price: 28500, capacity: 6, yield: 920 },
  cargo: { id: "cargo", name: "Cargo autónomo", price: 64000, capacity: 12, yield: 1880 },
});

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
    fleet: [{ id: "vehicle_aster_1", modelId: "aster", name: "Aster Viento 01", garageId: "nova_liria", driverId: null, condition: 100, odometerKm: 0, upgrades: {}, purchasedAt: now }],
    garages: [{ ...GARAGES.nova_liria, purchasedAt: now }],
    drivers: [],
    deliveryBots: [],
    loans: [],
    contracts: [],
    activeContractId: null,
    security: { guards: [], alarms: { nova_liria: 0 }, incidents: [], totalLosses: 0, preventedLosses: 0 },
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
    drivers: Array.isArray(raw.drivers) ? raw.drivers.map(driver => ({ trainingXp: 0, talentPoints: 0, talents: {}, deliveries: 0, vehicleId: null, ...driver })) : [],
    fleet: Array.isArray(raw.fleet) && raw.fleet.length ? raw.fleet.map(vehicle => ({ driverId: null, condition: 100, odometerKm: 0, upgrades: {}, ...vehicle })) : base.fleet,
    deliveryBots: Array.isArray(raw.deliveryBots) ? raw.deliveryBots : [],
    loans: Array.isArray(raw.loans) ? raw.loans : [],
    contracts: Array.isArray(raw.contracts) ? raw.contracts : [],
    security: {
      ...base.security, ...(raw.security && typeof raw.security === "object" ? raw.security : {}),
      guards: Array.isArray(raw.security?.guards) ? raw.security.guards.slice(-30) : [],
      alarms: raw.security?.alarms && typeof raw.security.alarms === "object" ? raw.security.alarms : base.security.alarms,
      incidents: Array.isArray(raw.security?.incidents) ? raw.security.incidents.slice(-50) : [],
    },
    ledger: Array.isArray(raw.ledger) ? raw.ledger.slice(-100) : [],
  };
  state.truck.fuel = clamp(state.truck.fuel, 0, state.truck.fuelCapacity);
  state.truck.condition = clamp(state.truck.condition, 0, 100);
  const vehicleIds = new Set(state.fleet.map(vehicle => vehicle.id));
  const driverIds = new Set(state.drivers.map(driver => driver.id));
  state.fleet.forEach(vehicle => {
    vehicle.condition = clamp(vehicle.condition, 0, 100);
    vehicle.odometerKm = Math.max(0, Number(vehicle.odometerKm) || 0);
    vehicle.upgrades = vehicle.upgrades && typeof vehicle.upgrades === "object" ? vehicle.upgrades : {};
    if (!driverIds.has(vehicle.driverId)) vehicle.driverId = null;
  });
  state.drivers.forEach(driver => { if (!vehicleIds.has(driver.vehicleId)) driver.vehicleId = null; });
  state.schema = CAREER_SCHEMA_VERSION;
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
  get catalog() { return { cities: copy(CITIES), cargo: copy(CARGO), garages: copy(Object.values(GARAGES)), talents: copy(Object.values(DRIVER_TALENTS)), deliveryBots: copy(Object.values(DELIVERY_BOTS)), fleetVehicles: copy(Object.values(FLEET_VEHICLES)), fleetUpgrades: copy(Object.values(FLEET_UPGRADES)) }; }

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

  buyFleetVehicle(modelId, garageId = this.state.garages[0]?.id) {
    const model = FLEET_VEHICLES[modelId];
    const garage = this.state.garages.find(item => item.id === garageId);
    if (!model || !garage) throw new Error("Vehículo o garaje no disponible");
    if (this.level < model.requiredLevel) throw new Error(`Nivel ${model.requiredLevel} necesario`);
    const parked = this.state.fleet.filter(item => item.garageId === garageId).length;
    if (parked >= garage.slots) throw new Error("No quedan plazas para vehículos en el garaje");
    if (this.state.economy.money < model.price) throw new Error("Fondos insuficientes");
    const vehicle = { id: uid("vehicle"), modelId, name: `${model.name} ${this.state.fleet.length + 1}`, garageId, driverId: null, condition: 100, odometerKm: 0, upgrades: {}, purchasedAt: Date.now() };
    this.state.fleet.push(vehicle);
    this.record(-model.price, `Vehículo: ${model.name}`, { vehicleId: vehicle.id, modelId, garageId });
    this.emit("fleet:vehicle_purchased", { vehicle, model });
    return copy(vehicle);
  }

  assignFleetVehicle(vehicleId, driverId = null) {
    const vehicle = this.state.fleet.find(item => item.id === vehicleId);
    if (!vehicle) throw new Error("Vehículo no disponible");
    const driver = driverId ? this.state.drivers.find(item => item.id === driverId) : null;
    if (driverId && !driver) throw new Error("Conductor no disponible");
    if (driver && driver.garageId !== vehicle.garageId) throw new Error("Vehículo y conductor deben estar en el mismo garaje");
    const previousDriver = this.state.drivers.find(item => item.id === vehicle.driverId);
    if (previousDriver) previousDriver.vehicleId = null;
    if (driver?.vehicleId) {
      const previousVehicle = this.state.fleet.find(item => item.id === driver.vehicleId);
      if (previousVehicle) previousVehicle.driverId = null;
    }
    vehicle.driverId = driver?.id || null;
    if (driver) driver.vehicleId = vehicle.id;
    this.emit("fleet:vehicle_assigned", { vehicle, driver });
    return copy(vehicle);
  }

  serviceFleetVehicle(vehicleId, targetCondition = 100) {
    const vehicle = this.state.fleet.find(item => item.id === vehicleId);
    if (!vehicle) throw new Error("Vehículo no disponible");
    const restored = clamp(targetCondition, vehicle.condition, 100) - vehicle.condition;
    const cost = roundMoney(restored * 165);
    if (!restored) throw new Error("El vehículo no necesita mantenimiento");
    if (this.state.economy.money < cost) throw new Error("Fondos insuficientes");
    vehicle.condition = clamp(vehicle.condition + restored, 0, 100);
    this.record(-cost, `Mantenimiento de flota: ${vehicle.name}`, { vehicleId });
    this.emit("fleet:vehicle_serviced", { vehicle, restored, cost });
    return { vehicle: copy(vehicle), restored, cost };
  }

  upgradeFleetVehicle(vehicleId, upgradeId) {
    const vehicle = this.state.fleet.find(item => item.id === vehicleId);
    const upgrade = FLEET_UPGRADES[upgradeId];
    if (!vehicle || !upgrade) throw new Error("Mejora no disponible");
    const rank = clamp(vehicle.upgrades?.[upgradeId], 0, upgrade.maxRank);
    if (rank >= upgrade.maxRank) throw new Error("Mejora al nivel máximo");
    const cost = upgrade.costs[rank];
    if (this.state.economy.money < cost) throw new Error("Fondos insuficientes");
    vehicle.upgrades = { ...vehicle.upgrades, [upgradeId]: rank + 1 };
    this.record(-cost, `${upgrade.name}: ${vehicle.name}`, { vehicleId, upgradeId, rank: rank + 1 });
    this.emit("fleet:vehicle_upgraded", { vehicle, upgradeId, rank: rank + 1, cost });
    return copy(vehicle);
  }

  hireDriver({ name, skill, salary } = {}) {
    const capacity = this.state.garages.reduce((sum, garage) => sum + garage.slots, 0);
    if (this.state.drivers.length >= capacity) throw new Error("No quedan plazas en los garajes");
    const driver = { id: uid("driver"), name: name || DRIVER_NAMES[this.state.drivers.length % DRIVER_NAMES.length], skill: clamp(skill ?? 1, 1, 10), salary: roundMoney(salary ?? 950), status: "idle", garageId: this.state.garages[0].id, hiredAt: Date.now(), earnings: 0, trainingXp: 0, talentPoints: 1, talents: {}, deliveries: 0 };
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
    if (driver.vehicleId) this.assignFleetVehicle(driver.vehicleId, null);
    driver.garageId = garageId;
    this.emit("driver:assigned", { driver, garage });
    return copy(driver);
  }

  trainDriver(driverId) {
    const driver = this.state.drivers.find(item => item.id === driverId);
    if (!driver) throw new Error("Conductor no disponible");
    if (driver.skill >= 10) throw new Error("El conductor ya tiene nivel máximo");
    const cost = Math.round(1100 + driver.skill * 650);
    if (this.state.economy.money < cost) throw new Error("Fondos insuficientes para la formación");
    this.record(-cost, `Formación: ${driver.name}`, { driverId });
    driver.skill += 1; driver.trainingXp += 100; driver.talentPoints += 1;
    this.emit("driver:trained", { driver, cost });
    return copy(driver);
  }

  unlockDriverTalent(driverId, talentId) {
    const driver = this.state.drivers.find(item => item.id === driverId);
    const talent = DRIVER_TALENTS[talentId];
    if (!driver || !talent) throw new Error("Talento no disponible");
    const rank = Number(driver.talents?.[talentId]) || 0;
    if (rank >= talent.maxRank) throw new Error("Talento al máximo");
    if ((driver.talentPoints || 0) < 1) throw new Error("Faltan puntos de talento");
    driver.talentPoints -= 1;
    driver.talents = { ...driver.talents, [talentId]: rank + 1 };
    this.emit("driver:talent", { driver, talentId, rank: rank + 1 });
    return copy(driver);
  }

  buyDeliveryBot(modelId) {
    const model = DELIVERY_BOTS[modelId];
    if (!model) throw new Error("Modelo de bot desconocido");
    if (this.state.economy.money < model.price) throw new Error("Fondos insuficientes");
    const bot = { id: uid("bot"), modelId, name: `${model.name} ${this.state.deliveryBots.length + 1}`, status: "active", deliveries: 0, earnings: 0, condition: 100, purchasedAt: Date.now() };
    this.state.deliveryBots.push(bot);
    this.record(-model.price, `Bot de reparto: ${model.name}`, { botId: bot.id });
    this.emit("delivery-bot:purchased", { bot });
    return copy(bot);
  }

  toggleDeliveryBot(botId) {
    const bot = this.state.deliveryBots.find(item => item.id === botId);
    if (!bot) throw new Error("Bot no disponible");
    bot.status = bot.status === "active" ? "paused" : "active";
    this.emit("delivery-bot:status", { bot });
    return copy(bot);
  }

  runCompanyDay() {
    let net = 0;
    for (const driver of this.state.drivers) {
      const vehicle = this.state.fleet.find(item => item.id === driver.vehicleId);
      if (!vehicle || vehicle.condition < 20) continue;
      const model = FLEET_VEHICLES[vehicle.modelId] || FLEET_VEHICLES.aster;
      const efficiency = Number(driver.talents?.efficiency) || 0;
      const fragile = Number(driver.talents?.fragile) || 0;
      const punctuality = Number(driver.talents?.punctuality) || 0;
      const upgradeEfficiency = Number(vehicle.upgrades?.efficiency) || 0;
      const gross = Math.round((450 + driver.skill * 135 + Math.random() * 400) * model.baseYield * (1 + fragile * .05 + punctuality * .04));
      const profit = gross - driver.salary / 30 * (1 - efficiency * .06);
      driver.earnings += profit;
      driver.deliveries = (driver.deliveries || 0) + 1 + (punctuality >= 3 ? 1 : 0);
      const tripKm = 90 + driver.skill * 12;
      vehicle.odometerKm += tripKm;
      vehicle.condition = clamp(vehicle.condition - Math.max(.15, .8 - upgradeEfficiency * .12), 0, 100);
      net += profit;
    }
    for (const bot of this.state.deliveryBots.filter(item => item.status === "active" && item.condition > 0)) {
      const model = DELIVERY_BOTS[bot.modelId];
      const gross = Math.round(model.yield * (.82 + Math.random() * .36));
      const profit = gross - Math.round(model.yield * .12);
      bot.deliveries += model.capacity; bot.earnings += profit; bot.condition = clamp(bot.condition - .5, 0, 100);
      net += profit;
    }
    this.record(net, "Operaciones de conductores");
    this.emit("company:day", { net: roundMoney(net) });
    return roundMoney(net);
  }

  upgradeAlarm(garageId) {
    const garage = this.state.garages.find((item) => item.id === garageId);
    if (!garage) throw new Error("Sede no disponible");
    const level = clamp(this.state.security.alarms[garageId], 0, 3);
    if (level >= 3) throw new Error("La alarma ya está al nivel máximo");
    const cost = [4500, 11000, 24000][level];
    if (this.state.economy.money < cost) throw new Error("Fondos insuficientes");
    this.state.security.alarms[garageId] = level + 1;
    this.record(-cost, `Alarma nivel ${level + 1}: ${garage.name}`, { garageId, kind: "security" });
    this.emit("security:alarm_upgraded", { garageId, garage: garage.name, level: level + 1, cost });
    return level + 1;
  }

  hireGuard(garageId) {
    const garage = this.state.garages.find((item) => item.id === garageId);
    if (!garage) throw new Error("Sede no disponible");
    if (this.state.security.guards.some((item) => item.garageId === garageId)) throw new Error("La sede ya tiene vigilancia");
    const setupCost = 1800;
    if (this.state.economy.money < setupCost) throw new Error("Fondos insuficientes");
    const guard = { id: uid("guard"), garageId, name: `Equipo ${garage.name}`, dailyCost: 160, hiredAt: Date.now() };
    this.state.security.guards.push(guard);
    this.record(-setupCost, `Alta de vigilancia: ${garage.name}`, { garageId, kind: "security" });
    this.emit("security:guard_hired", { guard, garage: garage.name, setupCost });
    return copy(guard);
  }

  dismissGuard(garageId) {
    const index = this.state.security.guards.findIndex((item) => item.garageId === garageId);
    if (index < 0) throw new Error("La sede no tiene vigilancia");
    const [guard] = this.state.security.guards.splice(index, 1);
    this.emit("security:guard_dismissed", { guard });
    return copy(guard);
  }

  runSecurityShift(garageId, threatRoll = Math.random()) {
    const garage = this.state.garages.find((item) => item.id === garageId);
    if (!garage) throw new Error("Sede no disponible");
    const alarmLevel = clamp(this.state.security.alarms[garageId], 0, 3);
    const guard = this.state.security.guards.find((item) => item.garageId === garageId);
    if (guard) this.record(-guard.dailyCost, `Vigilancia diaria: ${garage.name}`, { garageId, kind: "security" });
    const attempted = clamp(threatRoll, 0, 1) < 0.38;
    if (!attempted) {
      this.emit("security:shift_clear", { garageId, garage: garage.name, cost: guard?.dailyCost || 0 });
      return { attempted: false, cost: guard?.dailyCost || 0 };
    }
    const prevention = clamp(alarmLevel * 0.2 + (guard ? 0.42 : 0), 0, 0.95);
    const prevented = clamp(Number(threatRoll) * 2.17, 0, 1) < prevention;
    const exposure = Math.round(3500 + garage.slots * 2100 + Math.random() * 6000);
    const loss = prevented ? 0 : Math.min(exposure, Math.max(0, this.state.economy.money));
    if (loss) this.record(-loss, `Robo en ${garage.name}`, { garageId, kind: "security" });
    const incident = { id: uid("incident"), at: Date.now(), garageId, garage: garage.name, type: "intrusion", status: prevented ? "prevented" : "robbery", loss, exposure, alarmLevel, guard: Boolean(guard) };
    this.state.security.incidents.push(incident);
    this.state.security.incidents = this.state.security.incidents.slice(-50);
    this.state.security.totalLosses = roundMoney(this.state.security.totalLosses + loss);
    if (prevented) this.state.security.preventedLosses = roundMoney(this.state.security.preventedLosses + exposure);
    this.emit(prevented ? "security:incident_prevented" : "security:robbery", { incident });
    return copy(incident);
  }
}

export function createTransportCareer(options) {
  return new TransportCareer(options);
}

export default TransportCareer;
