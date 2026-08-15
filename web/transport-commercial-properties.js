/**
 * Sistema de Inmuebles Comerciales, Franquicias y Pago de Impuestos Municipales.
 * Permite a los jugadores adquirir Hoteles, Restaurantes, Bares, Gasolineras y Talleres,
 * mejorarlos a Tier 1, Tier 2 y Tier 3, y financiar los servicios públicos de cada ciudad.
 * Si no hay pagos de impuestos, los servicios municipales (policía, asfalto, farolas, bomberos) se cortan.
 */

export const PROPERTY_TYPES = Object.freeze({
  hotel: {
    id: "hotel",
    name: "Hotel & Descanso",
    icon: "🏨",
    tiers: {
      1: { tierName: "Motel de Carretera", purchaseCost: 120000, upgradeCost: 0, dailyIncome: 1450, municipalTaxDaily: 110, description: "12 habitaciones básicas para descanso de conductores." },
      2: { tierName: "Hotel Ejecutivo de Área", purchaseCost: 360000, upgradeCost: 240000, dailyIncome: 3800, municipalTaxDaily: 320, description: "36 habitaciones con gimnasio y tarifa reducida para tu flota." },
      3: { tierName: "Resort & Spa Gran Ruta", purchaseCost: 1010000, upgradeCost: 650000, dailyIncome: 9200, municipalTaxDaily: 840, description: "Complejo de 100 habitaciones con restauración y bonus de reputación (+5)." }
    }
  },
  restaurante: {
    id: "restaurante",
    name: "Restaurante de Ruta",
    icon: "🍽️",
    tiers: {
      1: { tierName: "Asador de Camioneros", purchaseCost: 65000, upgradeCost: 0, dailyIncome: 850, municipalTaxDaily: 65, description: "Menú del día tradicional y 40 comensales diarios." },
      2: { tierName: "Buffet Intermodal 24h", purchaseCost: 215000, upgradeCost: 150000, dailyIncome: 2400, municipalTaxDaily: 195, description: "Servicio continuo con 120 comensales y comida para llevar en cabina." },
      3: { tierName: "Restaurante Gourmet & Convenciones", purchaseCost: 595000, upgradeCost: 380000, dailyIncome: 6100, municipalTaxDaily: 520, description: "Salones para 300 personas y banquetes de empresas logísticas." }
    }
  },
  bar: {
    id: "bar",
    name: "Bar & Cafetería",
    icon: "☕",
    tiers: {
      1: { tierName: "Cafetería de Servicio", purchaseCost: 35000, upgradeCost: 0, dailyIncome: 480, municipalTaxDaily: 35, description: "Café exprés, bollería y aperitivos rápidos para transportistas." },
      2: { tierName: "Cervecería & Grill de Ruta", purchaseCost: 120000, upgradeCost: 85000, dailyIncome: 1350, municipalTaxDaily: 115, description: "Bocadillos calientes, punto de encuentro y radioemisora local." },
      3: { tierName: "Lounge Club de Transportistas", purchaseCost: 340000, upgradeCost: 220000, dailyIncome: 3600, municipalTaxDaily: 310, description: "Billar, sala de descanso VIP y alta rentabilidad nocturna." }
    }
  },
  gasolinera: {
    id: "gasolinera",
    name: "Estación de Servicio",
    icon: "⛽",
    tiers: {
      1: { tierName: "Surtidor Local (2 Islas)", purchaseCost: 95000, upgradeCost: 0, dailyIncome: 1200, municipalTaxDaily: 95, description: "Diésel y AdBlue con descuento del 5% para tus camiones." },
      2: { tierName: "Estación de Servicio (6 Islas + Tienda)", purchaseCost: 305000, upgradeCost: 210000, dailyIncome: 3100, municipalTaxDaily: 270, description: "Túnel de lavado y descuento del 12% en combustible propio." },
      3: { tierName: "Mega-Hub de Energía & Ultra-EV", purchaseCost: 825000, upgradeCost: 520000, dailyIncome: 8400, municipalTaxDaily: 760, description: "8 cargadores eléctricos de 350 kW, GNL y descuento del 25%." }
    }
  },
  taller: {
    id: "taller",
    name: "Taller Mecánico",
    icon: "🔧",
    tiers: {
      1: { tierName: "Taller Rápido y Neumáticos", purchaseCost: 80000, upgradeCost: 0, dailyIncome: 950, municipalTaxDaily: 75, description: "Mano de obra gratuita para las reparaciones de tu tractora." },
      2: { tierName: "Centro de Mantenimiento Integral", purchaseCost: 260000, upgradeCost: 180000, dailyIncome: 2700, municipalTaxDaily: 230, description: "Recambios a precio de coste y calibración de tacógrafos." },
      3: { tierName: "Factoría de Ingeniería de Convoyes", purchaseCost: 710000, upgradeCost: 450000, dailyIncome: 7200, municipalTaxDaily: 640, description: "Furgón taller móvil de asistencia inmediata sin coste." }
    }
  }
});

export const CITY_TAX_RATES = Object.freeze({
  "Nova Liria":   { baseRatePercent: 8.5,  licenseFeeYear: 1200 },
  "Puerto Alba":  { baseRatePercent: 9.0,  licenseFeeYear: 1400 },
  "Valleverde":   { baseRatePercent: 7.0,  licenseFeeYear: 950 },
  "Bahía Solar":  { baseRatePercent: 8.0,  licenseFeeYear: 1100 },
  "Madrid":       { baseRatePercent: 11.5, licenseFeeYear: 2800 },
  "Barcelona":    { baseRatePercent: 12.0, licenseFeeYear: 3100 },
  "Zaragoza":     { baseRatePercent: 9.5,  licenseFeeYear: 1600 },
  "Lisboa":       { baseRatePercent: 10.0, licenseFeeYear: 1900 },
  "Milán":        { baseRatePercent: 13.0, licenseFeeYear: 3500 },
  "Berlín":       { baseRatePercent: 12.5, licenseFeeYear: 3300 }
});

export function createCommercialPropertySystem({ initialPlayerMoney = 150000 } = {}) {
  let counter = 1;
  const state = {
    playerMoney: initialPlayerMoney,
    ownedProperties: [],
    pendingCityTaxes: 0,
    paidCityTaxesTotal: 0,
    totalBusinessRevenue: 0,
    taxDebtPerCity: {},
    unpaidCyclesPerCity: {}
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
    acquireProperty({ type, city = "Nova Liria", name } = {}) {
      const typeDef = PROPERTY_TYPES[type];
      if (!typeDef) return { success: false, reason: "Tipo de negocio desconocido" };

      const tier1 = typeDef.tiers[1];
      if (state.playerMoney < tier1.purchaseCost) {
        return { success: false, reason: `Dinero insuficiente (${tier1.purchaseCost.toLocaleString("es-ES")} € requeridos)` };
      }

      state.playerMoney -= tier1.purchaseCost;
      const property = {
        id: `prop_${type}_${Date.now()}_${counter++}`,
        type,
        typeName: typeDef.name,
        name: name || `${typeDef.name} ${city}`,
        city,
        tier: 1,
        tierName: tier1.tierName,
        dailyIncome: tier1.dailyIncome,
        municipalTaxDaily: tier1.municipalTaxDaily,
        acquiredAt: Date.now()
      };

      state.ownedProperties.push(property);
      return { success: true, property, state: emit() };
    },
    upgradeProperty(propertyId) {
      const prop = state.ownedProperties.find(p => p.id === propertyId);
      if (!prop) return { success: false, reason: "Inmueble no encontrado" };
      if (prop.tier >= 3) return { success: false, reason: "El negocio ya está en el Tier 3 máximo" };

      const nextTierNumber = prop.tier + 1;
      const nextTier = PROPERTY_TYPES[prop.type].tiers[nextTierNumber];
      if (state.playerMoney < nextTier.upgradeCost) {
        return { success: false, reason: `Dinero insuficiente (${nextTier.upgradeCost.toLocaleString("es-ES")} € requeridos)` };
      }

      state.playerMoney -= nextTier.upgradeCost;
      prop.tier = nextTierNumber;
      prop.tierName = nextTier.tierName;
      prop.dailyIncome = nextTier.dailyIncome;
      prop.municipalTaxDaily = nextTier.municipalTaxDaily;

      return { success: true, property: prop, state: emit() };
    },
    processDailyCycle() {
      let grossRevenue = 0;
      let accruedTaxes = 0;

      for (const prop of state.ownedProperties) {
        const debtCycles = state.unpaidCyclesPerCity[prop.city] || 0;
        // Si la ciudad tiene 3+ ciclos de impago, los negocios se clausuran preventivamente y no generan ingresos
        if (debtCycles >= 3) {
          continue;
        }

        const cityRate = CITY_TAX_RATES[prop.city]?.baseRatePercent || 10;
        const income = prop.dailyIncome;
        const tax = Math.round(income * (cityRate / 100) + prop.municipalTaxDaily);

        grossRevenue += income;
        accruedTaxes += tax;

        state.taxDebtPerCity[prop.city] = (state.taxDebtPerCity[prop.city] || 0) + tax;
        state.unpaidCyclesPerCity[prop.city] = (state.unpaidCyclesPerCity[prop.city] || 0) + 1;
      }

      state.playerMoney += grossRevenue;
      state.totalBusinessRevenue += grossRevenue;
      state.pendingCityTaxes += accruedTaxes;

      return { grossRevenue, accruedTaxes, state: emit() };
    },
    getCityServiceStatus(cityName = "Nova Liria") {
      const debt = state.taxDebtPerCity[cityName] || 0;
      const unpaidCycles = state.unpaidCyclesPerCity[cityName] || 0;

      if (debt <= 0 || unpaidCycles === 0) {
        return {
          city: cityName,
          status: "OPERATIVO",
          serviceHealthPercent: 100,
          policeActive: true,
          roadMaintenanceActive: true,
          streetLightingActive: true,
          fireRescueActive: true,
          businessClosedDueToDebt: false,
          description: "Todos los servicios municipales están completamente operativos y financiados."
        };
      }

      if (unpaidCycles < 3) {
        return {
          city: cityName,
          status: "DEGRADADO",
          serviceHealthPercent: 55,
          policeActive: true,
          roadMaintenanceActive: false, // Se suspende el bacheo y limpieza de carreteras
          streetLightingActive: true,
          fireRescueActive: true,
          businessClosedDueToDebt: false,
          description: `Alerta de impago (${debt.toLocaleString("es-ES")} € pendientes). Mantenimiento de asfalto suspendido.`
        };
      }

      return {
        city: cityName,
        status: "SUSPENDIDO",
        serviceHealthPercent: 0,
        policeActive: false,
        roadMaintenanceActive: false,
        streetLightingActive: false,
        fireRescueActive: false,
        businessClosedDueToDebt: true,
        description: `Servicios municipales cortados por impago tributario de ${unpaidCycles} ciclos. Negocios clausurados.`
      };
    },
    payCityTaxes(city = "all") {
      let amountToPay = 0;
      if (city === "all") {
        amountToPay = state.pendingCityTaxes;
        if (state.playerMoney < amountToPay) {
          return { success: false, reason: "Saldo insuficiente para abonar todos los impuestos" };
        }
        state.playerMoney -= amountToPay;
        state.paidCityTaxesTotal += amountToPay;
        state.pendingCityTaxes = 0;
        state.taxDebtPerCity = {};
        state.unpaidCyclesPerCity = {};
      } else {
        amountToPay = state.taxDebtPerCity[city] || 0;
        if (state.playerMoney < amountToPay) {
          return { success: false, reason: `Saldo insuficiente para abonar los impuestos de ${city}` };
        }
        state.playerMoney -= amountToPay;
        state.paidCityTaxesTotal += amountToPay;
        state.pendingCityTaxes = Math.max(0, state.pendingCityTaxes - amountToPay);
        state.taxDebtPerCity[city] = 0;
        state.unpaidCyclesPerCity[city] = 0;
      }

      return { success: true, paidAmount: amountToPay, state: emit() };
    },
    subscribe(fn) {
      listeners.add(fn);
      return () => listeners.delete(fn);
    }
  };
}

export default { PROPERTY_TYPES, CITY_TAX_RATES, createCommercialPropertySystem };
