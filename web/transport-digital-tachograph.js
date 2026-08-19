/**
 * Tacógrafo Digital Inteligente VDO (Reglamento Europeo UE 561/2006).
 * Supervisa tiempos de conducción continua, descansos obligatorios de 45 minutos,
 * límites diarios de 9h/10h y genera alertas e infracciones viales.
 */

export const TACHOGRAPH_CONSTANTS = Object.freeze({
  MAX_CONTINUOUS_DRIVE_MINUTES: 270,    // 4h 30m
  BREAK_REQUIRED_MINUTES: 45,          // 45m pausa
  MAX_DAILY_DRIVE_MINUTES: 540,        // 9h
  EXTENDED_DAILY_DRIVE_MINUTES: 600,   // 10h
  DAILY_REST_REQUIRED_HOURS: 11
});

export function createDigitalTachograph({ driverName = "Conductor", driverId = "DRV-001" } = {}) {
  const state = {
    cardInserted: true,
    driverName,
    driverId,
    currentMode: "REST", // DRIVE, WORK, AVAILABILITY, REST, BREAK
    continuousDriveMinutes: 0,
    dailyDriveMinutes: 0,
    weeklyDriveMinutes: 0,
    currentBreakMinutes: 0,
    extendedDaysUsedThisWeek: 0,
    alert: null,
    infractions: [],
    activityLog: []
  };

  const listeners = new Set();
  const emit = () => {
    const snap = JSON.parse(JSON.stringify(state));
    listeners.forEach(fn => {
      try { fn(snap); } catch {}
    });
    return snap;
  };

  function checkLimits() {
    if (state.currentMode === "DRIVE") {
      if (state.continuousDriveMinutes > TACHOGRAPH_CONSTANTS.MAX_CONTINUOUS_DRIVE_MINUTES) {
        state.alert = "INFRACTION_OVERDRIVE";
        const exists = state.infractions.some(i => i.type === "OVERDRIVE_CONTINUOUS" && i.minuteMark === state.continuousDriveMinutes);
        if (!exists) {
          state.infractions.push({
            type: "OVERDRIVE_CONTINUOUS",
            fineEuros: 500,
            minuteMark: state.continuousDriveMinutes,
            at: Date.now(),
            description: `Exceso de conducción continua: ${Math.floor(state.continuousDriveMinutes / 60)}h ${state.continuousDriveMinutes % 60}m (límite 4h 30m).`
          });
        }
      } else if (state.continuousDriveMinutes >= 255) { // A falta de 15 minutos
        state.alert = "WARNING_BREAK_SOON";
      } else {
        state.alert = null;
      }
    } else if (state.currentMode === "BREAK" || state.currentMode === "REST") {
      if (state.currentBreakMinutes >= TACHOGRAPH_CONSTANTS.BREAK_REQUIRED_MINUTES) {
        state.continuousDriveMinutes = 0;
        state.alert = null;
      }
    }
  }

  return {
    get state() {
      return JSON.parse(JSON.stringify(state));
    },
    get formatted() {
      const driveH = Math.floor(state.continuousDriveMinutes / 60);
      const driveM = Math.round(state.continuousDriveMinutes % 60);
      const dailyH = Math.floor(state.dailyDriveMinutes / 60);
      const dailyM = Math.round(state.dailyDriveMinutes % 60);

      return {
        continuousDrive: `${driveH.toString().padStart(2, "0")}:${driveM.toString().padStart(2, "0")}`,
        dailyDrive: `${dailyH.toString().padStart(2, "0")}:${dailyM.toString().padStart(2, "0")}`,
        mode: state.currentMode,
        driver: state.driverName,
        cardInserted: state.cardInserted,
        alertText: state.alert === "INFRACTION_OVERDRIVE"
          ? "🚨 ¡INFRACCIÓN! Pausa obligatoria sobrepasada"
          : state.alert === "WARNING_BREAK_SOON"
          ? "⚠️ Pausa de 45m requerida en menos de 15 min"
          : "OK · Tiempos en regla"
      };
    },
    setMode(newMode) {
      const valid = ["DRIVE", "WORK", "AVAILABILITY", "REST", "BREAK"];
      if (valid.includes(newMode)) {
        state.currentMode = newMode;
        if (newMode !== "BREAK" && newMode !== "REST") {
          state.currentBreakMinutes = 0;
        }
        checkLimits();
        return emit();
      }
      return state;
    },
    advanceTime(minutes) {
      if (state.currentMode === "DRIVE") {
        state.continuousDriveMinutes += minutes;
        state.dailyDriveMinutes += minutes;
        state.weeklyDriveMinutes += minutes;
      } else if (state.currentMode === "BREAK" || state.currentMode === "REST") {
        state.currentBreakMinutes += minutes;
      }
      checkLimits();
      return emit();
    },
    takeBreak(minutes = 45) {
      state.currentMode = "BREAK";
      state.currentBreakMinutes += minutes;
      if (state.currentBreakMinutes >= TACHOGRAPH_CONSTANTS.BREAK_REQUIRED_MINUTES) {
        state.continuousDriveMinutes = 0;
        state.alert = null;
      }
      return emit();
    },
    insertCard(driver = "Conductor") {
      state.cardInserted = true;
      state.driverName = driver;
      return emit();
    },
    ejectCard() {
      if (state.currentMode === "DRIVE") return { success: false, reason: "No se puede extraer la tarjeta con el vehículo en marcha" };
      state.cardInserted = false;
      return { success: true, state: emit() };
    },
    subscribe(fn) {
      listeners.add(fn);
      return () => listeners.delete(fn);
    }
  };
}

export default { TACHOGRAPH_CONSTANTS, createDigitalTachograph };
