const clamp = (v, min, max) => Math.max(min, Math.min(max, v));

/**
 * Lightweight deterministic truck dynamics for the WebGL transport scene.
 * Inputs are optional so older callers remain compatible. Distances are metres,
 * forces newtons, masses kilograms and speeds m/s internally.
 */
export function createTruckPhysics(options = {}) {
  const tractorMass = options.mass || 18000;
  const enginePower = options.enginePower || 390000;
  const maxSpeed = (options.maxSpeedKmh || 125) / 3.6;
  const gearRatios = options.gearRatios || [12.3, 9.1, 6.7, 5, 3.7, 2.75, 2.03, 1.5, 1.1, 0.81, 0.68, 0.57];
  const finalDrive = options.finalDrive || 2.85;
  const wheelRadius = options.wheelRadius || 0.51;
  const transmissionEfficiency = options.transmissionEfficiency || 0.9;
  const peakTorque = options.peakTorque || enginePower / ((options.powerPeakRpm || 1700) * Math.PI / 30);
  let velocity = 0;
  let yawRate = 0;
  let suspension = 0;
  let suspensionVelocity = 0;
  let gear = 1;
  let rpm = 600;
  let brakeTemperature = 85;
  let trailerAngle = 0;
  let trailerYawRate = 0;
  let filteredCrosswind = 0;

  function reset(speedKmh = 0) {
    velocity = Math.max(0, speedKmh / 3.6);
    yawRate = suspension = suspensionVelocity = trailerAngle = trailerYawRate = filteredCrosswind = 0;
    gear = 1;
    rpm = 600;
    brakeTemperature = 85;
  }

  function torqueAt(currentRpm, throttle, engineHealth) {
    const normalized = clamp((currentRpm - 600) / 1500, 0, 1);
    const curve = 0.58 + 0.52 * Math.sin(normalized * Math.PI * 0.72);
    const limiter = currentRpm > 2050 ? clamp((2300 - currentRpm) / 250, 0, 1) : 1;
    return peakTorque * curve * limiter * throttle * engineHealth;
  }

  function update(input = {}, dt) {
    dt = clamp(dt || 0, 0, 0.05);
    const throttle = clamp(input.throttle || 0, 0, 1);
    const brake = clamp(input.brake || 0, 0, 1);
    const steering = clamp(input.steering || 0, -1, 1);
    const wetness = clamp(input.wetness || 0, 0, 1);
    const offroad = Boolean(input.offroad);
    const damage = clamp(input.damage || 0, 0, 100);
    const cargoMass = clamp(input.cargoMass ?? options.cargoMass ?? 0, 0, 40000);
    const cargoHeight = clamp(input.cargoHeight ?? options.cargoHeight ?? 1.15, 0.4, 2.8);
    const mass = tractorMass + cargoMass;
    const loadRatio = cargoMass / Math.max(1, mass);
    const grip = (offroad ? 0.48 : 1) * (1 - wetness * 0.32);
    const engineHealth = clamp(1 - damage * 0.006, 0.25, 1);

    // Twelve-speed automated manual gearbox, including shift hysteresis.
    const wheelRpm = velocity / (2 * Math.PI * wheelRadius) * 60;
    rpm = Math.max(600, wheelRpm * gearRatios[gear - 1] * finalDrive);
    if (rpm > (throttle > 0.9 ? 2050 : 1850) && gear < gearRatios.length) gear += 1;
    else if (rpm < 950 && gear > 1) gear -= 1;
    const selectedRatio = gearRatios[gear - 1] * finalDrive;
    rpm = clamp(Math.max(600 + throttle * 90, wheelRpm * selectedRatio), 580, 2300);
    const engineTorque = torqueAt(rpm, throttle, engineHealth);
    const clutch = clamp(velocity / 1.8 + 0.22, 0.22, 1);
    const drivenForce = engineTorque * selectedRatio * transmissionEfficiency * clutch / wheelRadius;
    const tractionLimit = mass * 9.81 * grip * (0.38 + loadRatio * 0.12);
    const tractionForce = Math.min(drivenForce, tractionLimit);

    const rollingForce = mass * 9.81 * (offroad ? 0.042 : 0.009);
    const aeroForce = 0.5 * 1.225 * 0.72 * 10.5 * velocity * velocity;
    const ambientTemperature = input.ambientTemperature ?? 22;
    const brakeCooling = (8 + velocity * 1.15) * (brakeTemperature - ambientTemperature) / 100;
    brakeTemperature = clamp(brakeTemperature + brake * velocity * mass / 68000 * dt - brakeCooling * dt, ambientTemperature, 850);
    const brakeFade = clamp(1 - Math.max(0, brakeTemperature - 420) / 620, 0.42, 1);
    const brakeForce = brake * mass * 7.2 * grip * brakeFade;
    const acceleration = (tractionForce - rollingForce - aeroForce - brakeForce) / mass;
    velocity = clamp(velocity + acceleration * dt, 0, maxSpeed);
    if (input.parkingBrake) velocity = Math.max(0, velocity - 10 * dt);

    // Wind may be supplied as a signed crosswind or as speed and relative angle.
    const windSpeed = input.windSpeed || 0;
    const crosswind = input.crosswind ?? windSpeed * Math.sin(input.windAngle || 0);
    filteredCrosswind += (crosswind - filteredCrosswind) * Math.min(1, dt * 1.7);
    const windForce = 0.5 * 1.225 * 1.15 * 34 * filteredCrosswind * Math.abs(filteredCrosswind);
    const windYaw = windForce / mass * 0.014;
    const steerLimit = 0.52 * (1 - clamp(velocity / 42, 0, 0.72));
    const targetYaw = steering * steerLimit * velocity / 7.4 * grip + windYaw;
    yawRate += (targetYaw - yawRate) * Math.min(1, dt * (5.5 - loadRatio * 1.4));

    // The trailer follows with a delayed yaw response and resists extreme articulation.
    const trailerTarget = clamp(-yawRate * (0.72 + velocity * 0.018), -0.72, 0.72);
    trailerYawRate += (trailerTarget - trailerAngle) * 3.1 * dt;
    trailerYawRate *= Math.pow(0.18, dt);
    trailerAngle = clamp(trailerAngle + trailerYawRate * dt, -0.82, 0.82);

    const bump = Math.sin((input.distance || 0) * (offroad ? 5.5 : 1.7)) * (offroad ? 0.16 : 0.025);
    suspensionVelocity += (bump - suspension) * (28 - loadRatio * 7) * dt;
    suspensionVelocity *= Math.pow(0.08, dt);
    suspension += suspensionVelocity * dt;
    const lateralG = Math.abs(yawRate * velocity) / 9.81;
    const centreOfGravity = 1.05 + loadRatio * cargoHeight;
    const rolloverThreshold = clamp(0.82 / centreOfGravity * (1.15 - loadRatio * 0.18), 0.33, 0.82);
    const rolloverRisk = clamp(lateralG / rolloverThreshold, 0, 1.5);
    const bodyRoll = -Math.sign(yawRate || steering) * clamp(lateralG * centreOfGravity * 0.034, 0, 0.14);

    return {
      speedKmh: velocity * 3.6,
      forwardMeters: velocity * dt,
      yawRate,
      lateralMovement: (yawRate * velocity + windForce / mass) * dt * 0.34,
      bodyRoll,
      suspension,
      grip,
      lateralG,
      gear,
      rpm,
      engineTorque,
      brakeTemperature,
      brakeFade,
      totalMass: mass,
      cargoMass,
      centreOfGravity,
      crosswind: filteredCrosswind,
      trailerAngle,
      rolloverRisk,
      rolloverWarning: rolloverRisk >= 0.78,
    };
  }

  return {
    update,
    reset,
    get speedKmh() { return velocity * 3.6; },
    get gear() { return gear; },
    get rpm() { return rpm; },
    get brakeTemperature() { return brakeTemperature; },
    get trailerAngle() { return trailerAngle; },
  };
}
