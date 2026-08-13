/* Procedural traffic and roadside events for Rutas 3D.
 * No imports or external assets: pass the active THREE namespace in.
 */

const clamp = (value, min, max) => Math.max(min, Math.min(max, value));
const distance2D = (a, b) => Math.hypot((a?.x || 0) - b.x, (a?.z || 0) - b.z);

export function createWorldEvents({ THREE: T, scene, qualityLevel = 2 } = {}) {
  if (!T || !scene) throw new Error("THREE and scene are required");

  const root = new T.Group();
  root.name = "transport-world-events";
  scene.add(root);
  const resources = [];
  const entities = [];
  const trafficLights = [];
  const weatherZones = [];
  const proximity = [];
  const eventState = {
    time: 0,
    currentSpeedLimit: 90,
    localWeather: "clear",
    nearest: null,
    nearby: [],
    fine: 0,
    totalFines: 0,
    speeding: false,
    policeAlert: false,
    fuelStationNearby: false,
    activeEvents: [],
  };

  const track = (value) => (resources.push(value), value);
  const material = (params) => track(new T.MeshStandardMaterial(params));
  const basic = (params) => track(new T.MeshBasicMaterial(params));
  const makeMesh = (geometry, surface, shadows = true) => {
    track(geometry);
    const value = new T.Mesh(geometry, surface);
    value.castShadow = shadows && qualityLevel > 0;
    value.receiveShadow = shadows;
    return value;
  };
  const addBox = (parent, size, position, surface, rotationY = 0) => {
    const value = makeMesh(new T.BoxGeometry(...size), surface);
    value.position.set(...position);
    value.rotation.y = rotationY;
    parent.add(value);
    return value;
  };
  const register = (type, object, radius, data = {}) => {
    object.userData.worldEvent = { type, radius, ...data };
    entities.push(object);
    root.add(object);
    return object;
  };

  const asphalt = material({ color: 0x30343a, roughness: 0.96 });
  const steel = material({ color: 0x626c73, roughness: 0.4, metalness: 0.72 });
  const white = material({ color: 0xe9ece8, roughness: 0.72 });
  const orange = material({ color: 0xf26a21, roughness: 0.62 });
  const yellow = material({ color: 0xf5c542, roughness: 0.55 });
  const red = material({ color: 0xc52929, roughness: 0.52 });
  const blue = material({ color: 0x155fa3, roughness: 0.48, metalness: 0.08 });
  const dark = material({ color: 0x101318, roughness: 0.68 });
  const glass = material({ color: 0x9edfff, roughness: 0.08, metalness: 0.12, transparent: true, opacity: 0.58 });
  const grass = material({ color: 0x526d3d, roughness: 1 });
  yellow.userData.vehicleSurface = "machinery";

  function canvasMaterial(draw, width = 256, height = 256) {
    if (typeof document === "undefined") return white;
    const canvas = document.createElement("canvas");
    canvas.width = width;
    canvas.height = height;
    const context = canvas.getContext("2d");
    draw(context, width, height);
    const texture = track(new T.CanvasTexture(canvas));
    if (T.SRGBColorSpace) texture.colorSpace = T.SRGBColorSpace;
    texture.anisotropy = qualityLevel > 1 ? 4 : 1;
    return track(new T.MeshStandardMaterial({ map: texture, roughness: 0.56 }));
  }

  function signFace(text, background = "#175d9b", foreground = "#fff") {
    return canvasMaterial((context) => {
      context.fillStyle = background;
      context.fillRect(0, 0, 256, 256);
      context.strokeStyle = foreground;
      context.lineWidth = 14;
      context.strokeRect(9, 9, 238, 238);
      context.fillStyle = foreground;
      context.font = "bold 78px system-ui, sans-serif";
      context.textAlign = "center";
      context.textBaseline = "middle";
      context.fillText(String(text), 128, 132, 220);
    });
  }

  function regulatoryFace(limit) {
    return canvasMaterial((context) => {
      context.fillStyle = "#fff";
      context.beginPath();
      context.arc(128, 128, 112, 0, Math.PI * 2);
      context.fill();
      context.strokeStyle = "#d21f2b";
      context.lineWidth = 25;
      context.stroke();
      context.fillStyle = "#111";
      context.font = "700 94px Arial, sans-serif";
      context.textAlign = "center";
      context.textBaseline = "middle";
      context.fillText(String(limit), 128, 137);
    });
  }

  function worksFace() {
    return canvasMaterial((context) => {
      context.fillStyle = "#fff";
      context.beginPath();
      context.moveTo(128, 12);
      context.lineTo(244, 226);
      context.lineTo(12, 226);
      context.closePath();
      context.fill();
      context.strokeStyle = "#d21f2b";
      context.lineWidth = 18;
      context.stroke();
      context.fillStyle = "#171717";
      context.beginPath();
      context.arc(128, 102, 15, 0, Math.PI * 2);
      context.fill();
      context.lineWidth = 13;
      context.beginPath();
      context.moveTo(128, 119);
      context.lineTo(106, 166);
      context.moveTo(118, 138);
      context.lineTo(158, 151);
      context.moveTo(108, 163);
      context.lineTo(90, 205);
      context.moveTo(111, 163);
      context.lineTo(145, 203);
      context.stroke();
    });
  }

  function speedSign(x, z, limit) {
    const group = new T.Group();
    const pole = makeMesh(new T.CylinderGeometry(0.09, 0.12, 3.3, 9), steel);
    pole.position.y = 1.65;
    const face = makeMesh(new T.CylinderGeometry(0.75, 0.75, 0.1, 32), regulatoryFace(limit));
    face.rotation.x = Math.PI / 2;
    face.position.set(0, 3.3, 0);
    group.add(pole, face);
    group.position.set(x, 0, z);
    return register("speed-limit", group, 55, { limit });
  }

  function trafficLight(x, z, cycleOffset = 0) {
    const group = new T.Group();
    const pole = makeMesh(new T.CylinderGeometry(0.1, 0.14, 5, 10), steel);
    pole.position.y = 2.5;
    const backboard = addBox(group, [1.15, 2.78, 0.18], [0, 4.6, 0.18], dark);
    const caseMesh = addBox(group, [0.82, 2.45, 0.65], [0, 4.6, -0.08], dark);
    const lamps = [];
    for (const [index, color] of [0xff2020, 0xffbd20, 0x20e06b].entries()) {
      const lampSurface = basic({ color, transparent: true, opacity: 0.18 });
      const lamp = makeMesh(new T.SphereGeometry(0.27, 16, 10), lampSurface, false);
      lamp.position.set(0, 5.35 - index * 0.76, -0.36);
      group.add(lamp);
      const hood = makeMesh(new T.CylinderGeometry(0.31, 0.31, 0.38, 18, 1, false, 0, Math.PI), dark);
      hood.rotation.set(Math.PI / 2, 0, Math.PI);
      hood.position.set(0, 5.45 - index * 0.76, -0.57);
      group.add(hood);
      lamps.push(lamp);
    }
    group.add(pole, backboard, caseMesh);
    const stopLine = makeMesh(new T.PlaneGeometry(8.2, 0.42), white, false);
    stopLine.rotation.x = -Math.PI / 2;
    stopLine.position.set(x < 0 ? 4.1 : -4.1, 0.026, 3.2);
    group.add(stopLine);
    group.position.set(x, 0, z);
    group.userData.lamps = lamps;
    group.userData.cycleOffset = cycleOffset;
    trafficLights.push(group);
    return register("traffic-light", group, 42, { signal: "green" });
  }

  function roadworks(x, z) {
    const group = new T.Group();
    const patch = makeMesh(new T.PlaneGeometry(7.8, 26), asphalt);
    patch.rotation.x = -Math.PI / 2;
    patch.position.y = 0.025;
    group.add(patch);
    const coneStripe = material({ color: 0xf7f7f2, roughness: 0.6 });
    for (let i = 0; i < 10; i += 1) {
      const progress = i / 9;
      const cone = new T.Group();
      addBox(cone, [0.62, 0.08, 0.62], [0, 0.04, 0], dark);
      const body = makeMesh(new T.ConeGeometry(0.23, 0.72, 12), orange);
      body.position.y = 0.4;
      cone.add(body);
      const stripe = makeMesh(new T.CylinderGeometry(0.13, 0.17, 0.13, 12), coneStripe);
      stripe.position.y = 0.37;
      cone.add(stripe);
      cone.position.set(3.7 - progress * 2.4, 0, -17 + i * 3.3);
      group.add(cone);
    }
    const barrierFace = canvasMaterial((context) => {
      context.fillStyle = "#fff";
      context.fillRect(0, 0, 256, 256);
      context.strokeStyle = "#d62828";
      context.lineWidth = 42;
      for (let x = -180; x < 300; x += 110) {
        context.beginPath();
        context.moveTo(x, 256);
        context.lineTo(x + 160, 0);
        context.stroke();
      }
    });
    addBox(group, [4.8, 0.72, 0.2], [0, 1.05, -10], barrierFace);
    addBox(group, [0.18, 1.4, 0.18], [-2, 0.7, -10], steel);
    addBox(group, [0.18, 1.4, 0.18], [2, 0.7, -10], steel);
    const excavator = new T.Group();
    excavator.name = "roadwork_excavator";
    addBox(excavator, [2.4, 0.65, 1.5], [0, 0.55, 0], yellow);
    addBox(excavator, [1.2, 1.1, 1.2], [-0.25, 1.35, 0], glass);
    const arm = addBox(excavator, [0.28, 0.28, 3.2], [0.6, 1.45, -1.35], yellow);
    arm.rotation.x = -0.45;
    excavator.position.set(1.2, 0, 1.5);
    group.add(excavator);
    const warning = makeMesh(new T.CylinderGeometry(0.78, 0.78, 0.08, 3), worksFace());
    warning.rotation.set(Math.PI / 2, 0, Math.PI);
    warning.position.set(4.7, 2.45, -21);
    group.add(warning);
    group.position.set(x, 0.18, z);
    return register("roadworks", group, 65, { speedLimit: 40, laneBlocked: x < 0 ? "left" : "right" });
  }

  function accident(x, z) {
    const group = new T.Group();
    const car = new T.Group();
    car.name = "accident_vehicle";
    addBox(car, [2, 0.65, 4.2], [0, 0.65, 0], red, 0.13);
    addBox(car, [1.65, 0.72, 1.9], [0, 1.25, -0.2], glass, 0.13);
    car.rotation.y = 0.42;
    group.add(car);
    const warningSurface = basic({ color: 0xff7b24 });
    for (const side of [-1, 1]) {
      const beacon = makeMesh(new T.SphereGeometry(0.14, 10, 8), warningSurface, false);
      beacon.position.set(side * 1.4, 1.25, 2.5);
      group.add(beacon);
    }
    group.userData.beacons = group.children.filter((item) => item.material === warningSurface);
    for (let index = 0; index < 3; index += 1) {
      const triangle = makeMesh(new T.CylinderGeometry(0.42, 0.42, 0.06, 3), worksFace());
      triangle.rotation.set(Math.PI / 2, 0, Math.PI);
      triangle.position.set(-1.3, 0.48, 5.5 + index * 4.5);
      group.add(triangle);
    }
    group.position.set(x, 0.18, z);
    return register("accident", group, 75, { speedLimit: 30, laneBlocked: x < 0 ? "left" : "right" });
  }

  function police(x, z) {
    const group = new T.Group();
    group.name = "police_vehicle";
    addBox(group, [2.15, 0.7, 4.5], [0, 0.65, 0], white);
    addBox(group, [1.7, 0.7, 2], [0, 1.28, -0.25], glass);
    addBox(group, [2.18, 0.2, 2.2], [0, 0.72, 0.2], blue);
    const lampSurfaces = [basic({ color: 0x1976ff }), basic({ color: 0xff2020 })];
    for (const side of [-1, 1]) {
      const lamp = makeMesh(new T.BoxGeometry(0.55, 0.16, 0.22), lampSurfaces[side > 0 ? 1 : 0], false);
      lamp.position.set(side * 0.35, 1.78, -0.2);
      group.add(lamp);
    }
    group.userData.lampSurfaces = lampSurfaces;
    group.position.set(x, 0.18, z);
    return register("police", group, 95, { tolerance: 7 });
  }

  function namedBox(parent, name, size, position, surface, rotationY = 0) {
    const value = addBox(parent, size, position, surface, rotationY);
    value.name = name;
    return value;
  }

  function emergencyBeacon(parent, name, position, color) {
    const surface = material({ color, emissive: color, emissiveIntensity: 0.12, roughness: 0.22 });
    const lamp = makeMesh(new T.CylinderGeometry(0.16, 0.19, 0.18, 12), surface, false);
    lamp.name = name;
    lamp.position.set(...position);
    parent.add(lamp);
    (parent.userData.emergencyLights ||= []).push({ lamp, surface });
    return lamp;
  }

  function wheel(parent, name, x, z) {
    const value = makeMesh(new T.CylinderGeometry(0.42, 0.42, 0.3, 14), dark);
    value.name = name;
    value.rotation.z = Math.PI / 2;
    value.position.set(x, 0.48, z);
    parent.add(value);
  }

  function breakdownAssistance(x, z) {
    const group = new T.Group();
    group.name = "breakdown_assistance_scene";
    const disabled = new T.Group();
    disabled.name = "disabled_delivery_vehicle";
    namedBox(disabled, "disabled_vehicle_body", [2.2, 1.05, 4.8], [0, 0.95, 0], white);
    namedBox(disabled, "disabled_vehicle_cab", [2.05, 1.25, 1.7], [0, 1.58, -1.2], glass);
    for (const side of [-1, 1]) for (const wz of [-1.45, 1.35]) wheel(disabled, `disabled_wheel_${side}_${wz}`, side * 1.08, wz);
    disabled.position.set(-2.4, 0, -1.5);
    disabled.rotation.y = -0.06;
    group.add(disabled);

    const tow = new T.Group();
    tow.name = "roadside_recovery_truck";
    namedBox(tow, "recovery_chassis", [2.5, 0.55, 6.4], [0, 0.64, 0], steel);
    namedBox(tow, "recovery_cab", [2.35, 1.8, 2.1], [0, 1.45, -2], yellow);
    namedBox(tow, "recovery_windscreen", [1.85, 0.72, 0.08], [0, 1.72, -3.08], glass);
    const boom = namedBox(tow, "hydraulic_recovery_boom", [0.35, 0.35, 4.6], [0, 2.05, 0.35], yellow);
    boom.rotation.x = -0.28;
    namedBox(tow, "recovery_crossbar", [2.3, 0.18, 0.25], [0, 0.42, 3.12], steel);
    for (const side of [-1, 1]) for (const wz of [-2, 1.9]) wheel(tow, `recovery_wheel_${side}_${wz}`, side * 1.2, wz);
    emergencyBeacon(tow, "recovery_amber_left", [-0.65, 2.48, -2], 0xff8a16);
    emergencyBeacon(tow, "recovery_amber_right", [0.65, 2.48, -2], 0xff8a16);
    tow.position.set(2.6, 0, 4.2);
    group.add(tow);
    group.userData.emergencyLights = tow.userData.emergencyLights;
    group.position.set(x, 0.18, z);
    return register("breakdown-assistance", group, 95, { speedLimit: 40, laneBlocked: x < 0 ? "left" : "right", service: "recovery" });
  }

  function medicalResponse(x, z) {
    const group = new T.Group();
    group.name = "medical_response_scene";
    const ambulance = new T.Group();
    ambulance.name = "ambulance_vehicle";
    namedBox(ambulance, "ambulance_body", [2.45, 2.15, 5.5], [0, 1.35, 0], white);
    namedBox(ambulance, "ambulance_lower_stripe", [2.5, 0.34, 4.9], [0, 0.9, 0.2], yellow);
    namedBox(ambulance, "ambulance_windscreen", [2, 0.8, 0.08], [0, 1.85, -2.79], glass);
    namedBox(ambulance, "ambulance_rear_doors", [2.05, 1.72, 0.08], [0, 1.45, 2.79], white);
    for (const side of [-1, 1]) for (const wz of [-1.75, 1.65]) wheel(ambulance, `ambulance_wheel_${side}_${wz}`, side * 1.22, wz);
    emergencyBeacon(ambulance, "ambulance_blue_left", [-0.68, 2.52, -1.45], 0x287eff);
    emergencyBeacon(ambulance, "ambulance_blue_right", [0.68, 2.52, -1.45], 0x287eff);
    group.add(ambulance);
    group.userData.emergencyLights = ambulance.userData.emergencyLights;
    const stretcher = namedBox(group, "medical_stretcher", [0.72, 0.12, 2], [1.9, 0.75, 1.6], steel);
    stretcher.rotation.y = 0.18;
    for (const sx of [-0.29, 0.29]) for (const sz of [-0.72, 0.72]) {
      const caster = makeMesh(new T.SphereGeometry(0.1, 8, 6), dark);
      caster.name = "stretcher_caster";
      caster.position.set(1.9 + sx, 0.42, 1.6 + sz);
      group.add(caster);
    }
    group.position.set(x, 0.18, z);
    return register("medical-response", group, 105, { speedLimit: 30, laneBlocked: x < 0 ? "left" : "right", priorityVehicle: true });
  }

  function fireResponse(x, z) {
    const group = new T.Group();
    group.name = "fire_response_scene";
    const engine = new T.Group();
    engine.name = "fire_engine_vehicle";
    namedBox(engine, "fire_engine_body", [2.55, 2.35, 6.5], [0, 1.5, 0], red);
    namedBox(engine, "fire_engine_windscreen", [2.12, 0.76, 0.08], [0, 2, -3.27], glass);
    namedBox(engine, "fire_engine_equipment_shutter_left", [0.08, 1.25, 3.3], [-1.3, 1.42, 0.65], steel);
    namedBox(engine, "fire_engine_equipment_shutter_right", [0.08, 1.25, 3.3], [1.3, 1.42, 0.65], steel);
    const ladder = namedBox(engine, "fire_engine_roof_ladder", [0.42, 0.18, 5.2], [0, 2.78, 0.3], steel);
    ladder.rotation.x = -0.05;
    for (const side of [-1, 1]) for (const wz of [-2.15, 1.9]) wheel(engine, `fire_engine_wheel_${side}_${wz}`, side * 1.28, wz);
    emergencyBeacon(engine, "fire_blue_left", [-0.7, 2.82, -2.25], 0x287eff);
    emergencyBeacon(engine, "fire_blue_right", [0.7, 2.82, -2.25], 0x287eff);
    group.add(engine);
    group.userData.emergencyLights = engine.userData.emergencyLights;
    const smokeGeometry = track(new T.BufferGeometry());
    const count = qualityLevel > 1 ? 48 : 20;
    const positions = new Float32Array(count * 3);
    for (let index = 0; index < count; index += 1) {
      positions[index * 3] = 3.8 + (Math.random() - 0.5) * 2;
      positions[index * 3 + 1] = 1 + Math.random() * 5;
      positions[index * 3 + 2] = 2 + (Math.random() - 0.5) * 2;
    }
    smokeGeometry.setAttribute("position", new T.BufferAttribute(positions, 3));
    const smoke = new T.Points(smokeGeometry, basic({ color: 0x5b6064, size: 0.72, transparent: true, opacity: 0.42 }));
    smoke.name = "incident_smoke_particles";
    group.add(smoke);
    group.userData.smoke = smoke;
    group.position.set(x, 0.18, z);
    return register("fire-response", group, 120, { speedLimit: 20, laneBlocked: x < 0 ? "left" : "right", priorityVehicle: true });
  }

  function mobileLaneControl(x, z) {
    const group = new T.Group();
    group.name = "mobile_lane_control_scene";
    const van = new T.Group();
    van.name = "mobile_control_vehicle";
    namedBox(van, "control_van_body", [2.35, 1.8, 5], [0, 1.18, 0], yellow);
    namedBox(van, "control_van_windscreen", [1.95, 0.66, 0.08], [0, 1.68, -2.53], glass);
    for (const side of [-1, 1]) for (const wz of [-1.55, 1.45]) wheel(van, `control_van_wheel_${side}_${wz}`, side * 1.15, wz);
    emergencyBeacon(van, "control_amber_left", [-0.65, 2.18, -1.3], 0xff8a16);
    emergencyBeacon(van, "control_amber_right", [0.65, 2.18, -1.3], 0xff8a16);
    const boardSurface = signFace("←", "#171717", "#ffd328");
    namedBox(van, "variable_message_arrow_board", [2.05, 1.35, 0.18], [0, 2.5, 1.4], boardSurface);
    group.add(van);
    group.userData.emergencyLights = van.userData.emergencyLights;
    for (let index = 0; index < 8; index += 1) {
      const cone = makeMesh(new T.ConeGeometry(0.22, 0.72, 10), orange);
      cone.name = `lane_closure_cone_${index + 1}`;
      cone.position.set(-3.6 + index * 0.55, 0.36, 5 + index * 3.2);
      group.add(cone);
    }
    group.position.set(x, 0.18, z);
    return register("mobile-lane-control", group, 115, { speedLimit: 40, laneBlocked: x < 0 ? "left" : "right", mergeDirection: x < 0 ? "right" : "left" });
  }

  function fuelStation(x, z) {
    const group = new T.Group();
    const ground = makeMesh(new T.PlaneGeometry(26, 30), material({ color: 0x777b7e, roughness: 0.92 }));
    ground.rotation.x = -Math.PI / 2;
    group.add(ground);
    addBox(group, [24, 0.6, 11], [0, 5.2, 0], white);
    for (const px of [-9, 9]) addBox(group, [0.45, 5, 0.45], [px, 2.5, 0], steel);
    for (const px of [-5, 0, 5]) {
      addBox(group, [1.1, 1.9, 0.8], [px, 0.95, 1.4], blue);
      addBox(group, [0.72, 0.44, 0.05], [px, 1.35, 0.97], dark);
    }
    for (const px of [-7.5, 7.5]) {
      const charger = addBox(group, [0.8, 1.5, 0.55], [px, 0.75, 6], material({ color: 0xeff4f2, roughness: 0.58 }));
      addBox(charger, [0.5, 0.48, 0.03], [0, 0.28, -0.29], blue);
      const cable = makeMesh(new T.TorusGeometry(0.28, 0.035, 8, 18, Math.PI * 1.5), dark);
      cable.position.set(0.38, -0.12, -0.31);
      charger.add(cable);
    }
    addBox(group, [18, 4.2, 7], [0, 2.1, 10], white);
    addBox(group, [10, 2.4, 0.08], [0, 2.2, 6.46], glass);
    const sign = makeMesh(new T.BoxGeometry(3, 5.8, 0.42), signFace("24h", "#176a48", "#fff"));
    sign.position.set(-11, 2.9, -10);
    group.add(sign);
    group.position.set(x, 0.19, z);
    return register("fuel-station", group, 75, { price: 1.72, services: ["fuel", "rest", "repair", "ev-charge"] });
  }

  function weatherZone(x, z, weather, radius) {
    const group = new T.Group();
    group.position.set(x, 0, z);
    group.visible = qualityLevel > 0;
    const count = qualityLevel > 1 ? 90 : 36;
    const points = new Float32Array(count * 3);
    for (let i = 0; i < count; i += 1) {
      points[i * 3] = (Math.random() - 0.5) * radius * 1.6;
      points[i * 3 + 1] = 2 + Math.random() * 17;
      points[i * 3 + 2] = (Math.random() - 0.5) * radius * 1.6;
    }
    const geometry = track(new T.BufferGeometry());
    geometry.setAttribute("position", new T.BufferAttribute(points, 3));
    const surface = basic({ color: weather === "fog" ? 0xdbe4e8 : 0x9dc8e7, size: weather === "fog" ? 0.45 : 0.1, transparent: true, opacity: weather === "fog" ? 0.13 : 0.55 });
    const particles = new T.Points(geometry, surface);
    group.add(particles);
    group.userData.particles = particles;
    weatherZones.push({ group, weather, radius, positions: points });
    return register("weather", group, radius, { weather });
  }

  function buildWorld() {
    speedSign(13.5, 380, 90);
    speedSign(13.5, 115, 70);
    speedSign(13.5, -155, 50);
    trafficLight(-11.5, -205, 0);
    trafficLight(11.5, -205, 7);
    roadworks(5.7, 55);
    accident(-5.6, -318);
    police(17.5, 235);
    fuelStation(-29, -65);
    breakdownAssistance(6.2, 710);
    medicalResponse(-6, -735);
    fireResponse(6.4, 980);
    mobileLaneControl(-5.8, -1040);
    weatherZone(0, -410, "rain", 105);
    weatherZone(0, 465, "fog", 90);
  }
  buildWorld();

  function update(input = {}) {
    const dt = clamp(Number(input.dt || 1 / 60), 0, 0.1);
    eventState.time += dt;
    const position = input.position || input.vehicle?.position || { x: 0, z: 0 };
    const speed = Math.max(0, Number(input.speed || 0));
    let limit = Number(input.defaultSpeedLimit || 90);
    let localWeather = input.weather || "clear";
    proximity.length = 0;
    eventState.activeEvents = [];
    eventState.fuelStationNearby = false;
    eventState.policeAlert = false;

    for (const light of trafficLights) {
      const phase = (eventState.time + light.userData.cycleOffset) % 20;
      const index = phase < 10 ? 2 : phase < 13 ? 1 : 0;
      light.userData.worldEvent.signal = ["red", "yellow", "green"][index];
      light.userData.lamps.forEach((lamp, lampIndex) => {
        lamp.material.opacity = lampIndex === index ? 1 : 0.16;
      });
    }

    for (const zone of weatherZones) {
      const attribute = zone.group.userData.particles.geometry.attributes.position;
      if (zone.weather === "rain") {
        for (let i = 1; i < zone.positions.length; i += 3) {
          zone.positions[i] -= dt * 24;
          if (zone.positions[i] < 0.3) zone.positions[i] = 18;
        }
        attribute.needsUpdate = true;
      } else zone.group.rotation.y += dt * 0.012;
      if (distance2D(position, zone.group.position) < zone.radius) localWeather = zone.weather;
    }

    for (const object of entities) {
      const data = object.userData.worldEvent;
      const distance = distance2D(position, object.position);
      if (distance <= data.radius) {
        const entry = { type: data.type, distance, object, ...data };
        proximity.push(entry);
        eventState.activeEvents.push(data.type);
        if (data.limit) limit = Math.min(limit, data.limit);
        if (data.speedLimit) limit = Math.min(limit, data.speedLimit);
        if (data.type === "traffic-light" && data.signal === "yellow" && distance < 24) limit = Math.min(limit, 30);
        if (data.type === "traffic-light" && data.signal === "red" && distance < 28) limit = 0;
        if (data.type === "fuel-station") eventState.fuelStationNearby = true;
        if (data.type === "police") eventState.policeAlert = true;
      }
    }
    proximity.sort((a, b) => a.distance - b.distance);
    eventState.nearest = proximity[0] || null;
    eventState.nearby = proximity.slice(0, 6);
    eventState.currentSpeedLimit = limit;
    eventState.localWeather = localWeather;
    eventState.speeding = limit > 0 && speed > limit + 5;

    if (eventState.policeAlert && speed > limit + 7) {
      eventState.fine += dt * (speed - limit) * 0.18;
      eventState.totalFines = Math.floor(eventState.fine);
    }
    for (const object of entities) {
      const emergencyLights = object.userData.emergencyLights || [];
      for (let index = 0; index < emergencyLights.length; index += 1) {
        const { lamp, surface } = emergencyLights[index];
        const active = Math.sin(eventState.time * 12 + index * Math.PI) > 0.2;
        lamp.scale.setScalar(active ? 1.12 : 0.94);
        surface.emissiveIntensity = active ? 2.4 : 0.08;
      }
      if (object.userData.smoke) {
        const smoke = object.userData.smoke;
        smoke.rotation.y += dt * 0.14;
        smoke.position.y = Math.sin(eventState.time * 0.7) * 0.18;
        smoke.material.opacity = 0.34 + Math.sin(eventState.time * 1.1) * 0.08;
      }
      if (object.userData.worldEvent.type === "accident") {
        const pulse = Math.sin(eventState.time * 9) > 0;
        for (const beacon of object.userData.beacons || []) beacon.visible = pulse;
      }
      if (object.userData.worldEvent.type === "police") {
        const flip = Math.sin(eventState.time * 13) > 0;
        const [blueLamp, redLamp] = object.userData.lampSurfaces || [];
        if (blueLamp) blueLamp.emissive?.set(flip ? 0x174fcc : 0x000000);
        if (redLamp) redLamp.emissive?.set(flip ? 0x000000 : 0xcc1717);
      }
    }
    return eventState;
  }

  function reset() {
    eventState.time = 0;
    eventState.currentSpeedLimit = 90;
    eventState.localWeather = "clear";
    eventState.nearest = null;
    eventState.nearby = [];
    eventState.fine = 0;
    eventState.totalFines = 0;
    eventState.speeding = false;
    eventState.policeAlert = false;
    eventState.fuelStationNearby = false;
    eventState.activeEvents = [];
    proximity.length = 0;
  }

  function dispose() {
    scene.remove(root);
    for (const resource of new Set(resources)) resource?.dispose?.();
    entities.length = 0;
    trafficLights.length = 0;
    weatherZones.length = 0;
    proximity.length = 0;
  }

  return { root, state: eventState, entities, update, reset, dispose };
}
