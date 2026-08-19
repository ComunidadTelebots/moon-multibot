/**
 * Gestor de HUD Adaptativo y Distribución Contextual de Mandos y Botones.
 * Organiza los controles de forma inteligente según la situación de juego,
 * el dispositivo del usuario (móvil, teclado, volante) y la orientación de pantalla.
 */

export const CONTEXT_MODES = Object.freeze([
  "driving_exterior",
  "driving_interior",
  "warehouse_foot",
  "special_convoy",
  "diagnostics_workshop",
  "company_hq"
]);

export function detectDeviceEnvironment() {
  if (typeof window === "undefined" || typeof navigator === "undefined") {
    return { device: "desktop_keyboard", isTouch: false, isTelegram: false };
  }

  const isTouch = Boolean("ontouchstart" in window || navigator.maxTouchPoints > 0);
  const isMobile = isTouch && (window.innerWidth < 820 || /Android|iPhone|iPad|iPod/i.test(navigator.userAgent));
  const isTelegram = Boolean(window.Telegram?.WebApp);

  return {
    device: isMobile ? (window.innerWidth > window.innerHeight ? "mobile_landscape" : "mobile_portrait") : "desktop_keyboard",
    isTouch,
    isTelegram,
    orientation: window.innerWidth > window.innerHeight ? "landscape" : "portrait"
  };
}

export function resolveControlLayout({ context = "driving_exterior", device = "desktop_keyboard" } = {}) {
  const isMobile = device.startsWith("mobile");

  switch (context) {
    case "driving_interior":
      return {
        context,
        device,
        steeringType: isMobile ? "touch_steering_wheel" : "keyboard_wheel_analog",
        thumbZonePosition: isMobile ? "bottom_corners" : "cockpit_dashboard_cluster",
        showInteractiveDashboard: true,
        showCircularTachometer: true,
        showTransmissionSelector: true,
        showWalkJoystick: false,
        showOversizedControls: false,
        showDiagnosticTablet: true,
        hotkeysEnabled: !isMobile,
        primaryActions: ["engine_start", "lights", "wipers", "parking_brake", "retarder", "horn", "hazards", "view_cycle"],
        hotkeys: {
          W: "Acelerar", S: "Frenar", A: "Giro Izq", D: "Giro Der",
          C: "Control Crucero", P: "Freno Parking", H: "Bocina",
          M: "Mapa GPS", V: "Cambiar Cámara", R: "Rescate"
        }
      };

    case "warehouse_foot":
      return {
        context,
        device,
        steeringType: "walk_direction_joystick",
        thumbZonePosition: isMobile ? "bottom_corners" : "split_keyboard_mouse",
        showInteractiveDashboard: false,
        showCircularTachometer: false,
        showTransmissionSelector: false,
        showWalkJoystick: true,
        showOversizedControls: false,
        showDiagnosticTablet: false,
        hotkeysEnabled: !isMobile,
        primaryActions: ["walk_move", "interact_cargo", "switch_tool_forklift", "cargo_manifest", "exit_to_truck"],
        hotkeys: {
          W: "Avanzar a pie", S: "Retroceder", A: "Girar Izq", D: "Girar Der",
          E: "Cargar / Dejar Palé", T: "Cambiar Herramienta", ESC: "Subir al Camión"
        }
      };

    case "special_convoy":
      return {
        context,
        device,
        steeringType: isMobile ? "touch_pedals_or_swipe" : "keyboard_wheel_analog",
        thumbZonePosition: isMobile ? "bottom_corners" : "cockpit_dashboard_cluster",
        showInteractiveDashboard: true,
        showCircularTachometer: true,
        showTransmissionSelector: true,
        showWalkJoystick: false,
        showOversizedControls: true,
        showDiagnosticTablet: false,
        hotkeysEnabled: !isMobile,
        primaryActions: ["throttle_brake", "v21_pilot_lights", "siren_beacons", "hydraulic_neck_adjust", "convoy_radio"],
        hotkeys: {
          W: "Acelerar", S: "Frenar", K: "Rotativos V-21", B: "Sirena", J: "Hidráulica"
        }
      };

    case "diagnostics_workshop":
      return {
        context,
        device,
        steeringType: "3d_orbit_inspection",
        thumbZonePosition: "full_overlay_tablet",
        showInteractiveDashboard: false,
        showCircularTachometer: false,
        showTransmissionSelector: false,
        showWalkJoystick: false,
        showOversizedControls: false,
        showDiagnosticTablet: true,
        hotkeysEnabled: !isMobile,
        primaryActions: ["inspect_wheels", "inspect_brakes", "replace_filters", "test_engine_start", "dispatch_mobile_van"],
        hotkeys: {
          1: "Ver Neumáticos", 2: "Ver Frenos", 3: "Ver Motor", 4: "Prueba de Arranque"
        }
      };

    case "company_hq":
      return {
        context,
        device,
        steeringType: "management_pointer",
        thumbZonePosition: "modal_tabbed_view",
        showInteractiveDashboard: false,
        showCircularTachometer: false,
        showTransmissionSelector: false,
        showWalkJoystick: false,
        showOversizedControls: false,
        showDiagnosticTablet: false,
        hotkeysEnabled: !isMobile,
        primaryActions: ["talent_tree_upgrade", "hire_driver", "cctv_monitoring", "expand_warehouse", "invest_hq_blueprint"],
        hotkeys: {}
      };

    case "driving_exterior":
    default:
      return {
        context: "driving_exterior",
        device,
        steeringType: isMobile ? "touch_pedals_or_swipe" : "keyboard_wheel_analog",
        thumbZonePosition: isMobile ? "bottom_corners" : "compact_bottom_bar",
        showInteractiveDashboard: false,
        showCircularTachometer: true,
        showTransmissionSelector: true,
        showWalkJoystick: false,
        showOversizedControls: false,
        showDiagnosticTablet: false,
        hotkeysEnabled: !isMobile,
        primaryActions: ["throttle_brake", "cruise_control", "parking_brake", "view_cycle", "gps_toggle", "work_mode_switch"],
        hotkeys: {
          W: "Acelerar", S: "Frenar", A: "Izquierda", D: "Derecha",
          C: "Crucero", P: "Parking", V: "Cámara", M: "GPS", E: "Modo Trabajo"
        }
      };
  }
}

export function createAdaptiveHUD({ initialContext = "driving_exterior", deviceOverride = null } = {}) {
  const env = detectDeviceEnvironment();
  const state = {
    activeContext: initialContext,
    device: deviceOverride || env.device,
    isTouch: env.isTouch,
    hapticsEnabled: true
  };

  const listeners = new Set();
  const emit = () => {
    const layout = resolveControlLayout({ context: state.activeContext, device: state.device });
    const snap = { ...state, layout };
    listeners.forEach(fn => {
      try { fn(snap); } catch {}
    });
    return snap;
  };

  return {
    get state() {
      return JSON.parse(JSON.stringify(state));
    },
    get currentLayout() {
      return resolveControlLayout({ context: state.activeContext, device: state.device });
    },
    setContext(nextContext) {
      if (CONTEXT_MODES.includes(nextContext)) {
        state.activeContext = nextContext;
        return emit();
      }
      return state;
    },
    setDevice(nextDevice) {
      state.device = nextDevice;
      return emit();
    },
    triggerHaptic(durationMs = 25) {
      if (state.hapticsEnabled && typeof navigator !== "undefined" && navigator.vibrate) {
        try { navigator.vibrate(durationMs); } catch {}
      }
    },
    subscribe(fn) {
      listeners.add(fn);
      return () => listeners.delete(fn);
    }
  };
}

export default { CONTEXT_MODES, detectDeviceEnvironment, resolveControlLayout, createAdaptiveHUD };
