const clamp = (v, min, max) => Math.max(min, Math.min(max, v));
const moveTowards = (value, target, maximumDelta) =>
  value + clamp(target - value, -maximumDelta, maximumDelta);

// Relative, original handling profiles. `truck` is exactly the legacy baseline.
const VEHICLE_PROFILES = Object.freeze({
  truck: Object.freeze({ mass: 1, power: 1, torque: 1, brake: 1, cg: 1, wheelbase: 1, steering: 1, stability: 1, drag: 1 }),
  bus: Object.freeze({ mass: 0.82, power: 0.78, torque: 0.82, brake: 1.03, cg: 1.16, wheelbase: 1.58, steering: 0.82, stability: 0.86, drag: 0.92 }),
  ambulance: Object.freeze({ mass: 0.23, power: 0.48, torque: 0.36, brake: 1.2, cg: 0.82, wheelbase: 0.93, steering: 1.2, stability: 1.2, drag: 0.32 }),
  fire: Object.freeze({ mass: 0.72, power: 0.76, torque: 0.82, brake: 1.12, cg: 1.2, wheelbase: 1.25, steering: 0.9, stability: 0.82, drag: 0.68 }),
  recovery: Object.freeze({ mass: 0.64, power: 0.68, torque: 0.74, brake: 1.08, cg: 1.08, wheelbase: 1.18, steering: 0.92, stability: 0.92, drag: 0.58 }),
});

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
  let suspensionPitch = 0;
  let suspensionPitchVelocity = 0;
  let suspensionRoll = 0;
  let suspensionRollVelocity = 0;
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
    suspensionPitch = suspensionPitchVelocity = suspensionRoll = suspensionRollVelocity = 0;
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
    const surface = offroad ? "offroad" : String(input.surface || "asphalt").toLowerCase();
    const roadGrade = clamp(input.roadGrade ?? input.slope ?? 0, -0.18, 0.18);
    const damage = clamp(input.damage || 0, 0, 100);
    const requestedVehicleType = String(input.vehicleType || options.vehicleType || "truck").toLowerCase();
    const vehicleType = VEHICLE_PROFILES[requestedVehicleType] ? requestedVehicleType : "truck";
    const profile = VEHICLE_PROFILES[vehicleType];
    const cargoMass = clamp(input.cargoMass ?? options.cargoMass ?? 0, 0, 40000);
    const cargoHeight = clamp(input.cargoHeight ?? options.cargoHeight ?? 1.15, 0.4, 2.8);
    const vehicleMass = tractorMass * profile.mass;
    const mass = vehicleMass + cargoMass;
    const loadRatio = cargoMass / Math.max(1, mass);
    // Original approximate surface coefficients; callers may add surfaces without breaking defaults.
    const surfaceGrip = {
      asphalt: 0.88,
      concrete: 0.92,
      cobblestone: 0.7,
      gravel: 0.55,
      dirt: 0.48,
      mud: 0.34,
      snow: 0.3,
      ice: 0.14,
      offroad: 0.48,
    }[surface] ?? 0.82;
    const waterDepth = clamp(input.waterDepth ?? wetness * 0.006, 0, 0.02);
    // Water-film lift grows smoothly with speed/depth; no sudden binary aquaplaning switch.
    const aquaplaningSpeed = 25.5 * Math.sqrt(0.006 / Math.max(0.001, waterDepth));
    const aquaplaning = wetness * clamp((velocity - aquaplaningSpeed) / 16, 0, 1);
    const wetGripLoss = wetness * (surface === "asphalt" || surface === "concrete" ? 0.22 : 0.3);
    const gripFactor = clamp((1 - wetGripLoss) * (1 - aquaplaning * 0.68), 0.18, 1);
    const grip = clamp(surfaceGrip * gripFactor, 0.08, 0.92);
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
    // Profiles scale both torque and usable power so unlike vehicles retain distinct response.
    const profilePowerLimit = enginePower * profile.power / Math.max(rpm * Math.PI / 30, 1);
    const engineTorque = Math.min(torqueAt(rpm, throttle, engineHealth) * profile.torque, profilePowerLimit);
    const clutch = clamp(velocity / 1.7 + 0.2, 0.2, 1);
    const shiftCut = shiftTimer > 0 ? 0.12 : 1;
    const drivenForce = engineTorque * selectedRatio * transmissionEfficiency * clutch * shiftCut / wheelRadius;
    // Approximate driven-axle normal load, including longitudinal load transfer.
    const drivenLoadShare = clamp(0.43 + loadRatio * 0.11 + Math.max(0, acceleration) * 0.012, 0.38, 0.58);
    const tractionLimit = mass * 9.81 * grip * drivenLoadShare;
    const tractionForce = Math.min(drivenForce, tractionLimit);

    const surfaceRolling = {
      asphalt: 0.0065, concrete: 0.006, cobblestone: 0.012, gravel: 0.026,
      dirt: 0.032, mud: 0.06, snow: 0.035, ice: 0.008, offroad: 0.04,
    }[surface] ?? 0.008;
    const rollingCoefficient = surfaceRolling + wetness * (surface === "mud" ? 0.018 : 0.001);
    const rollingForce = mass * 9.81 * rollingCoefficient;
    const aeroForce = 0.5 * airDensity * dragArea * profile.drag * velocity * velocity;
    const gradeForce = mass * 9.81 * roadGrade;
    const ambientTemperature = input.ambientTemperature ?? 22;
    const brakeFade = clamp(1 - Math.max(0, brakeTemperature - 430) / 520, 0.38, 1);
    const serviceBrakeLimit = mass * 9.81 * grip * clamp(0.72 * profile.brake, 0.58, 0.9);
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
    const effectiveWheelbase = wheelbase * profile.wheelbase;
    const maxRoadWheelAngle = 0.52 * profile.steering / (1 + velocity * velocity / (520 * profile.stability));
    steerAngle = moveTowards(steerAngle, steering * maxRoadWheelAngle, dt * 0.72);
    const geometricYaw = velocity / effectiveWheelbase * Math.tan(steerAngle);
    const requestedLateralAcceleration = geometricYaw * velocity + windForce / mass;
    const availableLateralAcceleration = grip * 9.81 * 0.82 * profile.stability;
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

    const roughness = {
      asphalt: 0.022, concrete: 0.018, cobblestone: 0.065, gravel: 0.09,
      dirt: 0.12, mud: 0.1, snow: 0.055, ice: 0.018, offroad: 0.16,
    }[surface] ?? 0.03;
    const bumpFrequency = surface === "cobblestone" ? 8.5 : offroad ? 5.5 : 1.7;
    const bump = Math.sin((input.distance || 0) * bumpFrequency) * roughness;
    suspensionVelocity += (bump - suspension) * (28 - loadRatio * 7) * dt;
    suspensionVelocity *= Math.pow(0.08, dt);
    suspension += suspensionVelocity * dt;
    const lateralG = Math.abs(lateralAcceleration) / 9.81;
    const centreOfGravity = (1.05 + loadRatio * cargoHeight) * profile.cg;
    // Damped cab/chassis response: braking pitches forward, cornering rolls outward.
    const pitchTarget = clamp(-acceleration / 9.81 * (0.11 + loadRatio * 0.035) - roadGrade * 0.16, -0.13, 0.11);
    suspensionPitchVelocity += (pitchTarget - suspensionPitch) * (18 - loadRatio * 3.5) * dt;
    suspensionPitchVelocity *= Math.pow(0.055, dt);
    suspensionPitch += suspensionPitchVelocity * dt;
    const signedLateralG = lateralAcceleration / 9.81;
    const rollTarget = clamp(-signedLateralG * centreOfGravity * 0.09, -0.17, 0.17);
    suspensionRollVelocity += (rollTarget - suspensionRoll) * (15 - loadRatio * 3) * dt;
    suspensionRollVelocity *= Math.pow(0.07, dt);
    suspensionRoll += suspensionRollVelocity * dt;
    // Static-stability-factor approximation, softened for suspension/compliance.
    const rolloverThreshold = clamp(trackWidth / (2 * centreOfGravity) * 0.78, 0.28, 0.78);
    const rolloverRisk = clamp(lateralG / rolloverThreshold, 0, 1.5);
    const bodyRoll = suspensionRoll;

    return {
      speedKmh: velocity * 3.6,
      forwardMeters: velocity * dt,
      yawRate,
      lateralMovement: lateralAcceleration * dt * 0.34,
      bodyRoll,
      suspension,
      suspensionPitch,
      suspensionRoll,
      grip,
      gripFactor,
      aquaplaning,
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
      vehicleType,
      vehicleMass,
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
