/**
 * Motor de Mercancías Peligrosas ADR y Restricción de Túneles Europeos.
 * Gestiona códigos Kemler, paneles naranja reflectantes, categorías de túnel (A, B, C, D, E),
 * cálculo de rutas alternativas seguras y sanciones por incumplimiento.
 */

export const ADR_CLASSES = Object.freeze({
  "1": { code: "1", name: "Materias y objetos explosivos", icon: "💥", riskLevel: "HIGH" },
  "2": { code: "2", name: "Gases comprimidos y licuados",  icon: "🛢️", riskLevel: "HIGH" },
  "3": { code: "3", name: "Líquidos inflamables",          icon: "🔥", riskLevel: "HIGH" },
  "4": { code: "4", name: "Materias sólidas inflamables",  icon: "📦", riskLevel: "MEDIUM" },
  "5": { code: "5", name: "Sustancias comburentes",        icon: "⚡", riskLevel: "MEDIUM" },
  "6": { code: "6", name: "Sustancias tóxicas",           icon: "☣️", riskLevel: "HIGH" },
  "7": { code: "7", name: "Materiales radiactivos",        icon: "☢️", riskLevel: "CRITICAL" },
  "8": { code: "8", name: "Sustancias corrosivas",         icon: "🧪", riskLevel: "MEDIUM" },
  "9": { code: "9", name: "Materias peligrosas diversas",  icon: "⚠️", riskLevel: "LOW" }
});

export const TUNNEL_CATEGORIES = Object.freeze({
  A: { id: "A", name: "Túnel Categoría A", restrictionLevel: 0, description: "Sin restricciones para mercancías peligrosas." },
  B: { id: "B", name: "Túnel Categoría B", restrictionLevel: 1, description: "Restricción para materias susceptibles de provocar explosión muy grave." },
  C: { id: "C", name: "Túnel Categoría C", restrictionLevel: 2, description: "Restricción para explosión muy grave o fuga tóxica masiva." },
  D: { id: "D", name: "Túnel Categoría D", restrictionLevel: 3, description: "Restricción para explosión, fuga tóxica o incendio grave a granel." },
  E: { id: "E", name: "Túnel Categoría E", restrictionLevel: 4, description: "Restricción total para todas las mercancías peligrosas." }
});

export function checkTunnelAccess({ adrClass = null, kemler = "", tunnelCategory = "A" } = {}) {
  if (!adrClass) return { allowed: true, requiresDetour: false, reason: "Carga general sin ADR" };

  const cat = tunnelCategory.toUpperCase();
  if (cat === "A") {
    return { allowed: true, requiresDetour: false, reason: "Paso permitido por túnel Categoría A" };
  }

  if (cat === "E") {
    return {
      allowed: false,
      requiresDetour: true,
      reason: "Túnel Categoría E: Prohibido todo transporte de mercancías peligrosas ADR."
    };
  }

  if (cat === "D") {
    // Prohibido líquidos inflamables (Clase 3), gases (Clase 2) y explosivos (Clase 1)
    if (["1", "2", "3", "7"].includes(String(adrClass))) {
      return {
        allowed: false,
        requiresDetour: true,
        reason: `Túnel Categoría D: Prohibido paso para Clase ADR ${adrClass} (${kemler}).`
      };
    }
  }

  if (cat === "C" && ["1", "2", "7"].includes(String(adrClass))) {
    return {
      allowed: false,
      requiresDetour: true,
      reason: `Túnel Categoría C: Prohibido paso para materias de alto riesgo explosivo/tóxico.`
    };
  }

  if (cat === "B" && String(adrClass) === "1") {
    return {
      allowed: false,
      requiresDetour: true,
      reason: "Túnel Categoría B: Prohibido transporte de explosivos Clase 1."
    };
  }

  return { allowed: true, requiresDetour: false, reason: "Paso autorizado bajo normativa ADR" };
}

export function createADRRoutingEngine({ currentCargo = null } = {}) {
  const state = {
    cargo: currentCargo,
    adrClass: currentCargo?.adrClass || null,
    kemlerCode: currentCargo?.kemler || null,
    adrPlateOrangeActive: Boolean(currentCargo?.adrClass),
    infractions: []
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
    setCargo(cargo) {
      state.cargo = cargo;
      state.adrClass = cargo?.adrClass || null;
      state.kemlerCode = cargo?.kemler || null;
      state.adrPlateOrangeActive = Boolean(cargo?.adrClass);
      return emit();
    },
    attemptTunnelEntry({ tunnelName = "Túnel", category = "A" } = {}) {
      const access = checkTunnelAccess({
        adrClass: state.adrClass,
        kemler: state.kemlerCode,
        tunnelCategory: category
      });

      if (!access.allowed) {
        state.infractions.push({
          tunnelName,
          category,
          at: Date.now(),
          fineEuros: 1500,
          reason: `Acceso no autorizado con ADR a túnel ${category} (${tunnelName})`
        });
        emit();
        return { allowed: false, fined: true, fineEuros: 1500, reason: access.reason };
      }

      return { allowed: true, fined: false, reason: access.reason };
    },
    subscribe(fn) {
      listeners.add(fn);
      return () => listeners.delete(fn);
    }
  };
}

export default { ADR_CLASSES, TUNNEL_CATEGORIES, checkTunnelAccess, createADRRoutingEngine };
