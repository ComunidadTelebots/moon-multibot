/**
 * Sistema de Inmuebles Comerciales, Franquicias, Embargos y Vado Municipal.
 * Gestiona Hoteles, Restaurantes, Bares, Gasolineras y Talleres (Tier 1-3).
 * Incluye:
 * 1. Suspensión de servicios públicos y clausura por impago de impuestos.
 * 2. Embargo forzoso municipal de inmuebles a final de mes si persiste la deuda tributaria.
 * 3. Tasa de Vado Permanente: si no se paga, retirada de placa y grúa municipal al depósito.
 */

export const PROPERTY_TYPES = Object.freeze({
  hotel: {
    id: "hotel",
    name: "Hotel & Descanso",
    icon: "🏨",
    tiers: {
      1: { tierName: "Motel de Carretera", purchaseCost: 120000, upgradeCost: 0, dailyIncome: 1450, municipalTaxDaily: 110, vadoMonthlyFee: 350, description: "12 habitaciones básicas para descanso de conductores." },
      2: { tierName: "Hotel Ejecutivo de Área", purchaseCost: 360000, upgradeCost: 240000, dailyIncome: 3800, municipalTaxDaily: 320, vadoMonthlyFee: 650, description: "36 habitaciones con gimnasio y tarifa reducida para tu flota." },
      3: { tierName: "Resort & Spa Gran Ruta", purchaseCost: 1010000, upgradeCost: 650000, dailyIncome: 9200, municipalTaxDaily: 840, vadoMonthlyFee: 1200, description: "Complejo de 100 habitaciones con restauración y bonus de reputación (+5)." }
    }
  },
  restaurante: {
    id: "restaurante",
    name: "Restaurante de Ruta",
    icon: "🍽️",
    tiers: {
      1: { tierName: "Asador de Camioneros", purchaseCost: 65000, upgradeCost: 0, dailyIncome: 850, municipalTaxDaily: 65, vadoMonthlyFee: 250, description: "Menú del día tradicional y 40 comensales diarios." },
      2: { tierName: "Buffet Intermodal 24h", purchaseCost: 215000, upgradeCost: 150000, dailyIncome: 2400, municipalTaxDaily: 195, vadoMonthlyFee: 450, description: "Servicio continuo con 120 comensales y comida para llevar en cabina." },
      3: { tierName: "Restaurante Gourmet & Convenciones", purchaseCost: 595000, upgradeCost: 380000, dailyIncome: 6100, municipalTaxDaily: 520, vadoMonthlyFee: 850, description: "Salones para 300 personas y banquetes de empresas logísticas." }
    }
  },
  bar: {
    id: "bar",
    name: "Bar & Cafetería",
    icon: "☕",
    tiers: {
      1: { tierName: "Cafetería de Servicio", purchaseCost: 35000, upgradeCost: 0, dailyIncome: 480, municipalTaxDaily: 35, vadoMonthlyFee: 180, description: "Café exprés, bollería y aperitivos rápidos para transportistas." },
      2: { tierName: "Cervecería & Grill de Ruta", purchaseCost: 120000, upgradeCost: 85000, dailyIncome: 1350, municipalTaxDaily: 115, vadoMonthlyFee: 320, description: "Bocadillos calientes, punto de encuentro y radioemisora local." },
      3: { tierName: "Lounge Club de Transportistas", purchaseCost: 340000, upgradeCost: 220000, dailyIncome: 3600, municipalTaxDaily: 310, vadoMonthlyFee: 550, description: "Billar, sala de descanso VIP y alta rentabilidad nocturna." }
    }
  },
  gasolinera: {
    id: "gasolinera",
    name: "Estación de Servicio",
    icon: "⛽",
    tiers: {
      1: { tierName: "Surtidor Local (2 Islas)", purchaseCost: 95000, upgradeCost: 0, dailyIncome: 1200, municipalTaxDaily: 95, vadoMonthlyFee: 400, description: "Diésel y AdBlue con descuento del 5% para tus camiones." },
      2: { tierName: "Estación de Servicio (6 Islas + Tienda)", purchaseCost: 305000, upgradeCost: 210000, dailyIncome: 3100, municipalTaxDaily: 270, vadoMonthlyFee: 750, description: "Túnel de lavado y descuento del 12% en combustible propio." },
      3: { tierName: "Mega-Hub de Energía & Ultra-EV", purchaseCost: 825000, upgradeCost: 520000, dailyIncome: 8400, municipalTaxDaily: 760, vadoMonthlyFee: 1400, description: "8 cargadores eléctricos de 350 kW, GNL y descuento del 25%." }
    }
  },
  taller: {
    id: "taller",
    name: "Taller Mecánico",
    icon: "🔧",
    tiers: {
      1: { tierName: "Taller Rápido y Neumáticos", purchaseCost: 80000, upgradeCost: 0, dailyIncome: 950, municipalTaxDaily: 75, vadoMonthlyFee: 380, description: "Mano de obra gratuita para las reparaciones de tu tractora." },
      2: { tierName: "Centro de Mantenimiento Integral", purchaseCost: 260000, upgradeCost: 180000, dailyIncome: 2700, municipalTaxDaily: 230, vadoMonthlyFee: 680, description: "Recambios a precio de coste y calibración de tacógrafos." },
      3: { tierName: "Factoría de Ingeniería de Convoyes", purchaseCost: 710000, upgradeCost: 450000, dailyIncome: 7200, municipalTaxDaily: 640, vadoMonthlyFee: 1100, description: "Furgón taller móvil de asistencia inmediata sin coste." }
    }
  }
});

export const CITY_TAX_RATES = Object.freeze({
  "Nova Liria":   { baseRatePercent: 8.5,  towFee: 850,  dailyImpoundFee: 75 },
  "Puerto Alba":  { baseRatePercent: 9.0,  towFee: 920,  dailyImpoundFee: 80 },
  "Valleverde":   { baseRatePercent: 7.0,  towFee: 700,  dailyImpoundFee: 60 },
  "Bahía Solar":  { baseRatePercent: 8.0,  towFee: 880,  dailyImpoundFee: 70 },
  "Madrid":       { baseRatePercent: 11.5, towFee: 1200, dailyImpoundFee: 110 },
  "Barcelona":    { baseRatePercent: 12.0, towFee: 1250, dailyImpoundFee: 115 },
  "Zaragoza":     { baseRatePercent: 9.5,  towFee: 950,  dailyImpoundFee: 85 },
  "Lisboa":       { baseRatePercent: 10.0, towFee: 1000, dailyImpoundFee: 90 },
  "Milán":        { baseRatePercent: 13.0, towFee: 1350, dailyImpoundFee: 125 },
  "Berlín":       { baseRatePercent: 12.5, towFee: 1300, dailyImpoundFee: 120 }
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
    unpaidCyclesPerCity: {},
    vadoPasses: {},
    impoundedVehicles: [],
    embargoedPropertiesHistory: []
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
      const propId = `prop_${type}_${Date.now()}_${counter++}`;
      const property = {
        id: propId,
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
      state.vadoPasses[propId] = {
        propertyId: propId,
        city,
        plateActive: true,
        monthlyFee: tier1.vadoMonthlyFee,
        debt: 0,
        assignedVehicle: null
      };

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

      if (state.vadoPasses[propertyId]) {
        state.vadoPasses[propertyId].monthlyFee = nextTier.vadoMonthlyFee;
      }

      return { success: true, property: prop, state: emit() };
    },
    assignVehicleToVado(propertyId, vehiclePlate) {
      const vado = state.vadoPasses[propertyId];
      if (vado) {
        vado.assignedVehicle = vehiclePlate;
        return emit();
      }
      return state;
    },
    simulateVadoDefault(propertyId) {
      const vado = state.vadoPasses[propertyId];
      if (vado) {
        vado.plateActive = false;
        vado.debt += vado.monthlyFee;

        if (vado.assignedVehicle && !state.impoundedVehicles.some(v => v.plate === vado.assignedVehicle)) {
          const cityRates = CITY_TAX_RATES[vado.city] || { towFee: 850, dailyImpoundFee: 75 };
          state.impoundedVehicles.push({
            plate: vado.assignedVehicle,
            propertyId,
            city: vado.city,
            towFee: cityRates.towFee,
            dailyImpoundFee: cityRates.dailyImpoundFee,
            impoundedAt: Date.now()
          });
        }
        return emit();
      }
      return state;
    },
    releaseImpoundedVehicle(vehiclePlate, propertyId) {
      const impIndex = state.impoundedVehicles.findIndex(v => v.plate === vehiclePlate);
      if (impIndex < 0) return { success: false, reason: "Vehículo no encontrado en el depósito municipal" };

      const imp = state.impoundedVehicles[impIndex];
      const vado = state.vadoPasses[propertyId];
      const totalCost = imp.towFee + (vado ? vado.debt : 0);

      if (state.playerMoney < totalCost) {
        return { success: false, reason: `Dinero insuficiente (${totalCost.toLocaleString("es-ES")} € requeridos para tasa de grúa y vado)` };
      }

      state.playerMoney -= totalCost;
      state.impoundedVehicles.splice(impIndex, 1);
      if (vado) {
        vado.debt = 0;
        vado.plateActive = true;
      }

      return { success: true, releasedPlate: vehiclePlate, state: emit() };
    },
    processDailyCycle() {
      let grossRevenue = 0;
      let accruedTaxes = 0;

      for (const prop of state.ownedProperties) {
        state.unpaidCyclesPerCity[prop.city] = (state.unpaidCyclesPerCity[prop.city] || 0) + 1;
        const debtCycles = state.unpaidCyclesPerCity[prop.city];
        if (debtCycles > 3) {
          // Closed due to tax default, no revenue generated
          continue;
        }

        const cityRate = CITY_TAX_RATES[prop.city]?.baseRatePercent || 10;
        const income = prop.dailyIncome;
        const tax = Math.round(income * (cityRate / 100) + prop.municipalTaxDaily);

        grossRevenue += income;
        accruedTaxes += tax;

        state.taxDebtPerCity[prop.city] = (state.taxDebtPerCity[prop.city] || 0) + tax;
      }

      state.playerMoney += grossRevenue;
      state.totalBusinessRevenue += grossRevenue;
      state.pendingCityTaxes += accruedTaxes;

      return { grossRevenue, accruedTaxes, state: emit() };
    },
    processEndOfMonthAudit() {
      const embargoed = [];
      const remainingProperties = [];

      for (const prop of state.ownedProperties) {
        const debtCycles = state.unpaidCyclesPerCity[prop.city] || 0;
        if (debtCycles >= 25) {
          embargoed.push(prop);
          state.embargoedPropertiesHistory.push({
            property: prop,
            city: prop.city,
            embargoDate: Date.now(),
            reason: "Embargo forzoso municipal por impago tributario continuado a final de mes"
          });
          state.taxDebtPerCity[prop.city] = 0;
          state.unpaidCyclesPerCity[prop.city] = 0;
        } else {
          remainingProperties.push(prop);
        }
      }

      state.ownedProperties = remainingProperties;
      state.pendingCityTaxes = Object.values(state.taxDebtPerCity).reduce((a, b) => a + b, 0);

      return { embargoedProperties: embargoed, remainingCount: remainingProperties.length, state: emit() };
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
          roadMaintenanceActive: false,
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
