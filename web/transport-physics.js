const clamp = (v, min, max) => Math.max(min, Math.min(max, v));

export function createTruckPhysics(options = {}) {
  const mass = options.mass || 18000;
  const enginePower = options.enginePower || 390000;
  let velocity = 0;
  let yawRate = 0;
  let suspension = 0;
  let suspensionVelocity = 0;

  function reset(speedKmh = 0) {
    velocity = Math.max(0, speedKmh / 3.6);
    yawRate = suspension = suspensionVelocity = 0;
  }

  function update(input, dt) {
    dt = clamp(dt, 0, 0.05);
    const throttle = clamp(input.throttle || 0, 0, 1);
    const brake = clamp(input.brake || 0, 0, 1);
    const steering = clamp(input.steering || 0, -1, 1);
    const wetness = clamp(input.wetness || 0, 0, 1);
    const offroad = Boolean(input.offroad);
    const damage = clamp(input.damage || 0, 0, 100);
    const grip = (offroad ? 0.48 : 1) * (1 - wetness * 0.32);
    const engineHealth = 1 - damage * 0.006;
    const tractionForce = throttle * enginePower * engineHealth / Math.max(7, velocity);
    const rollingForce = mass * 9.81 * (offroad ? 0.042 : 0.009);
    const aeroForce = 0.5 * 1.225 * 0.72 * 10.5 * velocity * velocity;
    const brakeForce = brake * mass * 7.2 * grip;
    const acceleration = (tractionForce - rollingForce - aeroForce - brakeForce) / mass;
    velocity = clamp(velocity + acceleration * dt, 0, (options.maxSpeedKmh || 125) / 3.6);
    if (input.parkingBrake) velocity = Math.max(0, velocity - 10 * dt);

    const steerLimit = 0.52 * (1 - clamp(velocity / 42, 0, 0.72));
    const targetYaw = steering * steerLimit * velocity / 7.4 * grip;
    yawRate += (targetYaw - yawRate) * Math.min(1, dt * 5.5);
    const bump = Math.sin((input.distance || 0) * (offroad ? 5.5 : 1.7)) * (offroad ? 0.16 : 0.025);
    suspensionVelocity += (bump - suspension) * 28 * dt;
    suspensionVelocity *= Math.pow(0.08, dt);
    suspension += suspensionVelocity * dt;
    const lateralG = Math.abs(yawRate * velocity) / 9.81;
    return {
      speedKmh: velocity * 3.6,
      forwardMeters: velocity * dt,
      yawRate,
      lateralMovement: yawRate * velocity * dt * 0.34,
      bodyRoll: -steering * clamp(lateralG * 0.035, 0, 0.09),
      suspension,
      grip,
      lateralG,
    };
  }
  return { update, reset, get speedKmh() { return velocity * 3.6; } };
}
