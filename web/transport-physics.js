const clamp = (v, min, max) => Math.max(min, Math.min(max, v));
const moveTowards = (value, target, maximumDelta) =>
  value + clamp(target - value, -maximumDelta, maximumDelta);

/**
 * Deterministic articulated-truck dynamics for the WebGL transport scene.
 * Inputs remain optional for backwards compatibility. SI units are used inside.
 * Defaults describe an original 4x2 long-haul tractor, not a specific product.
 */
export function createTruckPhysics(options = {}) {
  const tractorMass = options.mass || 18000;
  const enginePower = options.enginePower || 390000;
  const maxSpeed = (options.maxSpeedKmh || 125) / 3.6;
  // Approximate wide-ratio 12-speed AMT: low launch gear and overdrive top gear.
  const gearRatios = options.gearRatios || [12.3, 9.1, 6.7, 5, 3.7, 2.75, 2.03, 1.5, 1.1, 0.81, 0.68, 0.57];
  const finalDrive = options.finalDrive || 2.85;
  const wheelRadius = options.wheelRadius || 0.51;
  const transmissionEfficiency = options.transmissionEfficiency || 0.9;
  const peakTorque = options.peakTorque || 2500;
  const wheelbase = options.wheelbase || 3.7;
  const trackWidth = options.trackWidth || 2.04;
  const trailerWheelbase = options.trailerWheelbase || 8.1;
  const airDensity = options.airDensity || 1.225;
  const dragArea = (options.dragCoefficient || 0.62) * (options.frontalArea || 10.2);

  let velocity = 0;
  let acceleration = 0;
  let yawRate = 0;
  let steerAngle = 0;
  let suspension = 0;
  let suspensionVelocity = 0;
  let gear = 1;
  let rpm = 600;
  let shiftTimer = 0;
  let brakeTemperature = 85;
  let trailerAngle = 0;
  let trailerYawRate = 0;
  let filteredCrosswind = 0;

  function reset(speedKmh = 0) {
    velocity = Math.max(0, speedKmh / 3.6);
    acceleration = yawRate = steerAngle = suspension = suspensionVelocity = 0;
    trailerAngle = trailerYawRate = filteredCrosswind = shiftTimer = 0;
    gear = 1;
    rpm = 600;
    brakeTemperature = 85;
  }

  // Broad low-rpm torque plateau, then power-limited falloff toward governed speed.
  function torqueAt(currentRpm, throttle, engineHealth) {
    let torqueFactor;
    if (currentRpm < 900) torqueFactor = 0.62 + (currentRpm - 600) / 300 * 0.34;
    else if (currentRpm <= 1400) torqueFactor = 0.96 + Math.sin((currentRpm - 900) / 500 * Math.PI) * 0.04;
    else torqueFactor = clamp(enginePower / (currentRpm * Math.PI / 30) / peakTorque, 0.48, 0.96);
    const governor = currentRpm > 2050 ? clamp((2250 - currentRpm) / 200, 0, 1) : 1;
    return peakTorque * torqueFactor * governor * throttle * engineHealth;
  }

  function update(input = {}, dt) {
    dt = clamp(dt || 0, 0, 0.05);
    const throttle = clamp(input.throttle || 0, 0, 1);
    const brake = clamp(input.brake || 0, 0, 1);
    const retarder = clamp(input.retarder ?? 0, 0, 1);
    const steering = clamp(input.steering || 0, -1, 1);
    const wetness = clamp(input.wetness || 0, 0, 1);
    const offroad = Boolean(input.offroad);
    const roadGrade = clamp(input.roadGrade ?? input.slope ?? 0, -0.18, 0.18);
    const damage = clamp(input.damage || 0, 0, 100);
    const cargoMass = clamp(input.cargoMass ?? options.cargoMass ?? 0, 0, 40000);
    const cargoHeight = clamp(input.cargoHeight ?? options.cargoHeight ?? 1.15, 0.4, 2.8);
    const mass = tractorMass + cargoMass;
    const loadRatio = cargoMass / Math.max(1, mass);
    // Approximate dry/wet/off-road friction, reduced progressively rather than abruptly.
    const grip = clamp((offroad ? 0.5 : 0.86) * (1 - wetness * 0.35), 0.24, 0.9);
    const engineHealth = clamp(1 - damage * 0.006, 0.25, 1);

    const wheelRpm = velocity / (2 * Math.PI * wheelRadius) * 60;
    const coupledRpm = wheelRpm * gearRatios[gear - 1] * finalDrive;
    rpm += (Math.max(600 + throttle * 80, coupledRpm) - rpm) * Math.min(1, dt * 8);
    shiftTimer = Math.max(0, shiftTimer - dt);
    // Shift hysteresis and a short torque interruption prevent instantaneous gear changes.
    if (!shiftTimer && rpm > (throttle > 0.82 ? 1950 : 1720) && gear < gearRatios.length) {
      gear += 1;
      shiftTimer = 0.42;
    } else if (!shiftTimer && rpm < (throttle > 0.65 ? 1050 : 850) && gear > 1) {
      gear -= 1;
      shiftTimer = 0.34;
    }
    const selectedRatio = gearRatios[gear - 1] * finalDrive;
    rpm = clamp(rpm, 580, 2250);
    const engineTorque = torqueAt(rpm, throttle, engineHealth);
    const clutch = clamp(velocity / 1.7 + 0.2, 0.2, 1);
    const shiftCut = shiftTimer > 0 ? 0.12 : 1;
    const drivenForce = engineTorque * selectedRatio * transmissionEfficiency * clutch * shiftCut / wheelRadius;
    // Approximate driven-axle normal load, including longitudinal load transfer.
    const drivenLoadShare = clamp(0.43 + loadRatio * 0.11 + Math.max(0, acceleration) * 0.012, 0.38, 0.58);
    const tractionLimit = mass * 9.81 * grip * drivenLoadShare;
    const tractionForce = Math.min(drivenForce, tractionLimit);

    const rollingCoefficient = offroad ? 0.04 : 0.0065 + wetness * 0.001;
    const rollingForce = mass * 9.81 * rollingCoefficient;
    const aeroForce = 0.5 * airDensity * dragArea * velocity * velocity;
    const gradeForce = mass * 9.81 * roadGrade;
    const ambientTemperature = input.ambientTemperature ?? 22;
    const brakeFade = clamp(1 - Math.max(0, brakeTemperature - 430) / 520, 0.38, 1);
    const serviceBrakeLimit = mass * 9.81 * grip * 0.72;
    const brakeForce = brake * serviceBrakeLimit * brakeFade;
    // Auxiliary braking is strongest at road speed and does not heat wheel brakes.
    const retarderForce = retarder * clamp(velocity / 8, 0, 1) * Math.min(105000, 430000 / Math.max(velocity, 3));
    const netForce = tractionForce - rollingForce - aeroForce - gradeForce - brakeForce - retarderForce;
    const targetAcceleration = netForce / mass;
    acceleration += (targetAcceleration - acceleration) * Math.min(1, dt * 7);
    velocity = clamp(velocity + acceleration * dt, 0, maxSpeed);
    if (input.parkingBrake) velocity = Math.max(0, velocity - 8.5 * dt);

    // Wheel-brake temperature follows dissipated energy; forced convection grows with speed.
    const brakePower = brakeForce * velocity;
    const effectiveBrakeThermalMass = 260000;
    const convectiveCooling = (10 + velocity * 2.2) * (brakeTemperature - ambientTemperature);
    brakeTemperature = clamp(
      brakeTemperature + (brakePower * 0.72 / effectiveBrakeThermalMass - convectiveCooling / 15000) * dt,
      ambientTemperature,
      900,
    );

    const windSpeed = input.windSpeed || 0;
    const crosswind = input.crosswind ?? windSpeed * Math.sin(input.windAngle || 0);
    filteredCrosswind += (crosswind - filteredCrosswind) * Math.min(1, dt * 1.6);
    const windForce = 0.5 * airDensity * 1.15 * 34 * filteredCrosswind * Math.abs(filteredCrosswind);

    // Speed-sensitive steering and a saturated bicycle model avoid unlimited lateral grip.
    const maxRoadWheelAngle = 0.52 / (1 + velocity * velocity / 520);
    steerAngle = moveTowards(steerAngle, steering * maxRoadWheelAngle, dt * 0.72);
    const geometricYaw = velocity / wheelbase * Math.tan(steerAngle);
    const requestedLateralAcceleration = geometricYaw * velocity + windForce / mass;
    const availableLateralAcceleration = grip * 9.81 * 0.82;
    const lateralAcceleration = clamp(requestedLateralAcceleration, -availableLateralAcceleration, availableLateralAcceleration);
    const targetYaw = velocity > 0.25 ? lateralAcceleration / velocity : 0;
    yawRate += (targetYaw - yawRate) * Math.min(1, dt * (4.4 - loadRatio * 1.15));

    // Single-track articulated response: trailer yaw lags and articulation self-centres.
    const hitchResponse = velocity / trailerWheelbase;
    const trailerTargetRate = yawRate - hitchResponse * Math.sin(trailerAngle);
    trailerYawRate += (trailerTargetRate - trailerYawRate) * Math.min(1, dt * 3.2);
    trailerAngle += (yawRate - trailerYawRate) * dt;
    trailerAngle -= trailerAngle * Math.min(1, dt * (0.22 + velocity * 0.018));
    trailerAngle = clamp(trailerAngle, -0.82, 0.82);

    const bump = Math.sin((input.distance || 0) * (offroad ? 5.5 : 1.7)) * (offroad ? 0.16 : 0.025);
    suspensionVelocity += (bump - suspension) * (28 - loadRatio * 7) * dt;
    suspensionVelocity *= Math.pow(0.08, dt);
    suspension += suspensionVelocity * dt;
    const lateralG = Math.abs(lateralAcceleration) / 9.81;
    const centreOfGravity = 1.05 + loadRatio * cargoHeight;
    // Static-stability-factor approximation, softened for suspension/compliance.
    const rolloverThreshold = clamp(trackWidth / (2 * centreOfGravity) * 0.78, 0.28, 0.78);
    const rolloverRisk = clamp(lateralG / rolloverThreshold, 0, 1.5);
    const bodyRoll = -Math.sign(yawRate || steering) * clamp(lateralG * centreOfGravity * 0.052, 0, 0.16);

    return {
      speedKmh: velocity * 3.6,
      forwardMeters: velocity * dt,
      yawRate,
      lateralMovement: lateralAcceleration * dt * 0.34,
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
      acceleration,
      roadGrade,
      retarderForce,
      tractionLimited: drivenForce > tractionLimit,
      shifting: shiftTimer > 0,
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
