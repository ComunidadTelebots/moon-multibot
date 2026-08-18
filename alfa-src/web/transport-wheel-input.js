const clamp = (value, min = 0, max = 1) => Math.min(max, Math.max(min, value));
const buttonValue = (pad, index) => pad?.buttons?.[index]?.value || 0;

const PROFILES = [
  { match: /g920/i, name: "Logitech G920", steering: 0, throttle: 2, brake: 1, clutch: 3 },
  { match: /g29/i, name: "Logitech G29", steering: 0, throttle: 2, brake: 3, clutch: 1 },
  { match: /g923/i, name: "Logitech G923", steering: 0, throttle: 2, brake: 1, clutch: 3 },
  { match: /(thrustmaster|t150|t248|t300|t500|tx racing|t-gt)/i, name: "Thrustmaster", steering: 0, throttle: 2, brake: 1, clutch: 3 },
  { match: /(fanatec|clubsport|csl elite|gran turismo dd)/i, name: "Fanatec", steering: 0, throttle: 2, brake: 1, clutch: 3 },
];

export function createWheelInput({ storageKey = "moon.transport.wheel.v1" } = {}) {
  let padIndex = -1, connected = false, previousButtons = [], calibrationUntil = 0;
  let calibration = { min: [], max: [] };
  try { calibration = { ...calibration, ...JSON.parse(localStorage.getItem(storageKey) || "{}") }; } catch {}

  const getPad = () => [...(navigator.getGamepads?.() || [])].find((pad) => pad && (pad.index === padIndex || padIndex < 0));
  const profileFor = (pad) => PROFILES.find((profile) => profile.match.test(pad?.id || "")) || {
    name: pad?.mapping === "standard" ? "Volante / mando estándar" : "Volante genérico",
    steering: 0, throttle: 2, brake: 1, clutch: 3,
  };
  const pedal = (pad, axis, trigger) => {
    if (pad.mapping === "standard" && buttonValue(pad, trigger) > 0.01) return buttonValue(pad, trigger);
    const raw = pad.axes?.[axis];
    if (!Number.isFinite(raw)) return 0;
    const min = calibration.min[axis] ?? -1, max = calibration.max[axis] ?? 1;
    return clamp(1 - ((raw - min) / Math.max(0.01, max - min)));
  };
  const pressedOnce = (pad, index) => {
    const pressed = Boolean(pad.buttons?.[index]?.pressed);
    const result = pressed && !previousButtons[index]; previousButtons[index] = pressed; return result;
  };
  const poll = () => {
    const pad = getPad();
    if (!pad) { connected = false; padIndex = -1; return { connected: false, steering: 0, throttle: 0, brake: 0, clutch: 0, actions: {} }; }
    connected = true; padIndex = pad.index;
    const profile = profileFor(pad);
    if (performance.now() < calibrationUntil) {
      pad.axes.forEach((value, index) => {
        calibration.min[index] = Math.min(calibration.min[index] ?? value, value);
        calibration.max[index] = Math.max(calibration.max[index] ?? value, value);
      });
      localStorage.setItem(storageKey, JSON.stringify(calibration));
    }
    let steering = pad.axes?.[profile.steering] || 0;
    if (Math.abs(steering) < 0.035) steering = 0;
    return {
      connected: true, id: pad.id, profile: profile.name, calibrating: performance.now() < calibrationUntil,
      steering: clamp(steering, -1, 1), throttle: pedal(pad, profile.throttle, 7),
      brake: pedal(pad, profile.brake, 6), clutch: pedal(pad, profile.clutch, 4),
      actions: { view: pressedOnce(pad, 3), cruise: pressedOnce(pad, 0), parking: pressedOnce(pad, 1), retarder: pressedOnce(pad, 5), horn: pad.buttons?.[2]?.pressed || false },
    };
  };
  const calibrate = (duration = 8000) => { calibration = { min: [], max: [] }; calibrationUntil = performance.now() + duration; };
  const pulse = (strength = 0.35, duration = 100) => {
    const actuator = getPad()?.vibrationActuator; if (!actuator?.playEffect) return false;
    actuator.playEffect("dual-rumble", { duration, strongMagnitude: strength, weakMagnitude: strength * 0.65 }).catch(() => {}); return true;
  };
  addEventListener("gamepadconnected", (event) => { padIndex = event.gamepad.index; connected = true; });
  addEventListener("gamepaddisconnected", (event) => { if (event.gamepad.index === padIndex) { padIndex = -1; connected = false; } });
  return { poll, calibrate, pulse, get connected() { return connected; } };
}

export { PROFILES as WHEEL_PROFILES };
