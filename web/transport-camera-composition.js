const CHASE_PROFILES = Object.freeze({
  truck: { distance: 31, height: 8.2, lookAhead: -7, fov: 60 },
  bus: { distance: 24, height: 7.4, lookAhead: -8, fov: 59 },
  ambulance: { distance: 17.5, height: 5.7, lookAhead: -10, fov: 58 },
  fire: { distance: 21, height: 6.5, lookAhead: -9, fov: 59 },
  recovery: { distance: 21, height: 6.5, lookAhead: -9, fov: 59 },
});

export function chaseCameraComposition(kind = "truck", speed = 0, steering = 0) {
  const profile = CHASE_PROFILES[kind] || CHASE_PROFILES.truck;
  const velocity = Math.max(0, Number(speed) || 0);
  const steer = Math.max(-1, Math.min(1, Number(steering) || 0));
  return {
    x: steer * Math.min(1.15, 0.45 + velocity * 0.005),
    y: profile.height + Math.min(1.8, velocity * 0.012),
    z: profile.distance + Math.min(7, velocity * 0.032),
    lookX: steer * 1.35,
    lookY: 2.55,
    lookZ: profile.lookAhead - Math.min(7, velocity * 0.025),
    fov: profile.fov + Math.min(6, velocity * 0.035),
  };
}
