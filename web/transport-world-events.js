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

  function signFace(text, background = "#175d9b", foreground = "#fff") {
    if (typeof document === "undefined") return blue;
    const canvas = document.createElement("canvas");
    canvas.width = 256;
    canvas.height = 256;
    const context = canvas.getContext("2d");
    context.fillStyle = background;
    context.fillRect(0, 0, 256, 256);
    context.strokeStyle = foreground;
    context.lineWidth = 14;
    context.strokeRect(9, 9, 238, 238);
    context.fillStyle = foreground;
    context.font = "bold 92px system-ui, sans-serif";
    context.textAlign = "center";
    context.textBaseline = "middle";
    context.fillText(String(text), 128, 134);
    const texture = track(new T.CanvasTexture(canvas));
    if (T.SRGBColorSpace) texture.colorSpace = T.SRGBColorSpace;
    return track(new T.MeshStandardMaterial({ map: texture, roughness: 0.58 }));
  }

  function speedSign(x, z, limit) {
    const group = new T.Group();
    const pole = makeMesh(new T.CylinderGeometry(0.09, 0.12, 3.3, 9), steel);
    pole.position.y = 1.65;
    const face = makeMesh(new T.CylinderGeometry(0.75, 0.75, 0.1, 32), signFace(limit, "#fff", "#d42028"));
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
    const caseMesh = addBox(group, [0.85, 2.5, 0.7], [0, 4.6, 0], dark);
    const lamps = [];
    for (const [index, color] of [0xff2020, 0xffbd20, 0x20e06b].entries()) {
      const lampSurface = basic({ color, transparent: true, opacity: 0.18 });
      const lamp = makeMesh(new T.SphereGeometry(0.27, 16, 10), lampSurface, false);
      lamp.position.set(0, 5.35 - index * 0.76, -0.36);
      group.add(lamp);
      lamps.push(lamp);
    }
    group.add(pole, caseMesh);
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
    for (let i = -4; i <= 4; i += 1) {
      const side = i < 0 ? -1 : 1;
      const cone = makeMesh(new T.ConeGeometry(0.23, 0.75, 10), orange);
      cone.position.set(side * 3.3, 0.38, i * 2.7);
      group.add(cone);
    }
    addBox(group, [4.8, 0.22, 0.2], [0, 1.05, -10], yellow);
    addBox(group, [0.18, 1.4, 0.18], [-2, 0.7, -10], steel);
    addBox(group, [0.18, 1.4, 0.18], [2, 0.7, -10], steel);
    const excavator = new T.Group();
    addBox(excavator, [2.4, 0.65, 1.5], [0, 0.55, 0], yellow);
    addBox(excavator, [1.2, 1.1, 1.2], [-0.25, 1.35, 0], glass);
    const arm = addBox(excavator, [0.28, 0.28, 3.2], [0.6, 1.45, -1.35], yellow);
    arm.rotation.x = -0.45;
    excavator.position.set(1.2, 0, 1.5);
    group.add(excavator);
    group.position.set(x, 0.18, z);
    return register("roadworks", group, 65, { speedLimit: 40, laneBlocked: x < 0 ? "left" : "right" });
  }

  function accident(x, z) {
    const group = new T.Group();
    const car = new T.Group();
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
    group.position.set(x, 0.18, z);
    return register("accident", group, 75, { speedLimit: 30, laneBlocked: x < 0 ? "left" : "right" });
  }

  function police(x, z) {
    const group = new T.Group();
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
    addBox(group, [18, 4.2, 7], [0, 2.1, 10], white);
    addBox(group, [10, 2.4, 0.08], [0, 2.2, 6.46], glass);
    const sign = makeMesh(new T.BoxGeometry(3, 5.8, 0.42), signFace("FUEL", "#176a48", "#fff"));
    sign.position.set(-11, 2.9, -10);
    group.add(sign);
    group.position.set(x, 0.19, z);
    return register("fuel-station", group, 75, { price: 1.72, services: ["fuel", "rest", "repair"] });
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
