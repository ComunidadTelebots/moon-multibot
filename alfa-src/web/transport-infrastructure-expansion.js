/**
 * Módulo de Infraestructuras, Sedes Modulares y Expansión Regional (Canal Alfa).
 * Basado fielmente en la página 028 de Canva.
 */

export const INFRASTRUCTURE_MODULES = Object.freeze([
  {
    id: "headquarters_builder",
    title: "Constructor de sedes",
    subtitle: "Diseña y construye tu sede central",
    phase: "2/5",
    phaseName: "Cimentación y estructura",
    progressPercent: 42,
    modules: ["Oficinas", "Sala de servidores", "Comedor", "Torre de control", "Helipuerto"]
  },
  {
    id: "garages_workshops",
    title: "Garajes y talleres",
    subtitle: "Gestiona flotas y mantenimiento",
    parkingOccupied: 28,
    parkingTotal: 40,
    status: "Operativo",
    workshopBays: 6
  },
  {
    id: "cargo_terminals",
    title: "Terminales de carga",
    subtitle: "Almacena y mueve mercancías",
    capacityTons: 20000,
    currentTons: 12750,
    occupancyPercent: 63,
    loadingDocks: 12
  },
  {
    id: "airports",
    title: "Aeropuertos",
    subtitle: "Conecta ciudades y personas",
    runwaysActive: 2,
    runwaysTotal: 4,
    gatesOccupied: 18,
    gatesTotal: 32
  },
  {
    id: "ports",
    title: "Puertos",
    subtitle: "Puertos y rutas marítimas",
    berthsOccupied: 3,
    berthsTotal: 6,
    capacityTons: 30000,
    currentTons: 18500,
    cranesActive: 5
  },
  {
    id: "energy_stations",
    title: "Estaciones y energía",
    subtitle: "Combustible, carga eléctrica y servicios",
    fuelLiters: 180000,
    evChargersActive: 16,
    evChargersTotal: 24,
    hourlyConsumptionMwh: 2.4,
    status: "Operativo"
  },
  {
    id: "roads_permits",
    title: "Carreteras y permisos",
    subtitle: "Construye carreteras y gestiona permisos",
    permitsActive: 8,
    permitsTotal: 12,
    tollRevenueMonth: 1250000,
    networkHealthPercent: 87
  },
  {
    id: "regional_expansion",
    title: "Expansión regional",
    subtitle: "Compra terreno y expande tu red",
    regionName: "Costa Azul",
    population: 3240000,
    areaKm2: 120,
    expansionCost: 24800000
  }
]);

export const REGIONAL_EXPANSIONS = Object.freeze([
  { id: "costa_azul",     name: "Costa Azul",     population: 3240000, areaKm2: 120, cost: 24800000 },
  { id: "valle_alpino",   name: "Valle Alpino",   population: 1850000, areaKm2: 240, cost: 18500000 },
  { id: "corredor_norte", name: "Corredor Norte", population: 4100000, areaKm2: 180, cost: 31200000 }
]);

export function createInfrastructureSystem({ initialBudget = 152430000, initialIncomeDay = 8245000, initialReputation = 82 } = {}) {
  const state = {
    budget: initialBudget,
    incomeDay: initialIncomeDay,
    reputation: initialReputation,
    hqPhase: 2,
    hqMaxPhases: 5,
    hqProgress: 42,
    ownedRegions: ["madrid_hub"],
    modules: JSON.parse(JSON.stringify(INFRASTRUCTURE_MODULES))
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
    advanceHeadquartersPhase() {
      if (state.hqPhase < state.hqMaxPhases) {
        state.hqPhase++;
        state.hqProgress = 0;
        state.budget -= 5000000;
        state.reputation += 3;
        return { success: true, currentPhase: state.hqPhase, state: emit() };
      }
      return { success: false, reason: "Sede al máximo nivel" };
    },
    buyRegionalExpansion(regionId) {
      const region = REGIONAL_EXPANSIONS.find(r => r.id === regionId);
      if (!region) return { success: false, reason: "Región no encontrada" };
      if (state.ownedRegions.includes(regionId)) return { success: false, reason: "Ya posees esta región" };
      if (state.budget < region.cost) return { success: false, reason: "Presupuesto insuficiente" };

      state.budget -= region.cost;
      state.ownedRegions.push(regionId);
      state.reputation += 5;
      state.incomeDay += Math.round(region.cost * 0.04);
      return { success: true, region, state: emit() };
    },
    upgradeEnergyStation(evChargersCount = 4) {
      const energy = state.modules.find(m => m.id === "energy_stations");
      if (energy) {
        energy.evChargersTotal += evChargersCount;
        state.budget -= evChargersCount * 45000;
        return emit();
      }
      return state;
    },
    subscribe(fn) {
      listeners.add(fn);
      return () => listeners.delete(fn);
    }
  };
}

export default { INFRASTRUCTURE_MODULES, REGIONAL_EXPANSIONS, createInfrastructureSystem };
