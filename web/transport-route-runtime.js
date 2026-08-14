(function (global) {
  "use strict";

  const DEFAULTS = {
    laneWidth: 3.6,
    lanesPerDirection: 1,
    trafficSpacing: 140,
    serviceSpacing: 2600,
    eventSpacing: 4200,
    roadShoulder: 2.2,
    seed: 7319,
    maxTraffic: 80,
    maxServices: 24,
    maxEvents: 12,
    trafficDensity: 1,
    quality: "high",
    minGap: 10,
    reactionTime: 1.35,
    maxAcceleration: 2.2,
    comfortableBrake: 4.5,
    laneChangeCooldown: 4,
  };

  const clamp = (value, min, max) => Math.max(min, Math.min(max, value));
  const modulo = (value, size) => size > 0 ? ((value % size) + size) % size : 0;
  const lerp = (a, b, t) => a + (b - a) * t;
  const finite = value => Number.isFinite(Number(value)) ? Number(value) : 0;

  function pointFrom(value) {
    if (Array.isArray(value)) return { x: finite(value[0]), y: finite(value.length > 2 ? value[1] : 0), z: finite(value.length > 2 ? value[2] : value[1]) };
    return { x: finite(value?.x ?? value?.lon ?? value?.lng), y: finite(value?.y), z: finite(value?.z ?? value?.lat) };
  }

  function seeded(seed) {
    let state = (seed >>> 0) || 1;
    return () => ((state = Math.imul(1664525, state) + 1013904223 >>> 0) / 4294967296);
  }

  function create(options) {
    const settings = Object.assign({}, DEFAULTS, options || {});
    const adapter = settings.adapter || {};
    let route = [], cumulative = [], length = 0, disposed = false;
    const actors = { traffic: [], services: [], events: [], threat: null, nearestTraffic: null, nearesTraffic: null };
    const vehicleProfiles = [
      { type: "car", speedMin: 23, speedMax: 34, length: 4.5, weight: 6 },
      { type: "van", speedMin: 20, speedMax: 29, length: 6, weight: 2 },
      { type: "truck", speedMin: 17, speedMax: 24, length: 16.5, weight: 2 },
      { type: "coach", speedMin: 18, speedMax: 25, length: 13, weight: 1 },
    ];

    function qualityDensity() {
      const quality = String(settings.quality || "high").toLowerCase();
      const factor = quality === "low" ? 0.4 : quality === "medium" ? 0.7 : quality === "ultra" ? 1.35 : 1;
      return clamp(finite(settings.trafficDensity) || 1, 0.1, 2) * factor;
    }

    function forwardGap(from, to, direction) {
      return direction > 0 ? modulo(to - from, length) : modulo(from - to, length);
    }

    function sampleAt(distance, lateralOffset) {
      if (!route.length) return null;
      if (route.length === 1 || length <= 0) return { ...route[0], distance: 0, heading: 0, tangent: { x: 0, z: 1 }, normal: { x: -1, z: 0 } };
      const target = clamp(finite(distance), 0, length);
      let low = 0, high = cumulative.length - 1;
      while (low + 1 < high) {
        const middle = (low + high) >> 1;
        cumulative[middle] <= target ? low = middle : high = middle;
      }
      const a = route[low], b = route[Math.min(low + 1, route.length - 1)];
      const span = Math.max(0.0001, cumulative[low + 1] - cumulative[low]);
      const t = clamp((target - cumulative[low]) / span, 0, 1);
      const dx = b.x - a.x, dz = b.z - a.z, magnitude = Math.hypot(dx, dz) || 1;
      const tangent = { x: dx / magnitude, z: dz / magnitude };
      const normal = { x: -tangent.z, z: tangent.x };
      const offset = finite(lateralOffset);
      return {
        x: lerp(a.x, b.x, t) + normal.x * offset,
        y: lerp(a.y, b.y, t),
        z: lerp(a.z, b.z, t) + normal.z * offset,
        distance: target,
        heading: Math.atan2(tangent.x, tangent.z),
        tangent, normal, segment: low, progress: target / length,
      };
    }

    function removeActors() {
      [actors.traffic, actors.services, actors.events].forEach(list => {
        list.forEach(actor => adapter.remove?.(actor.handle, actor));
        list.length = 0;
      });
      actors.threat = actors.nearestTraffic = actors.nearesTraffic = null;
    }

    function addActor(kind, data) {
      const actor = Object.assign({ kind, handle: null }, data);
      actor.handle = adapter.create?.(kind, actor) ?? null;
      actors[kind].push(actor);
      adapter.move?.(actor.handle, actor.pose, actor);
      return actor;
    }

    function populate() {
      removeActors();
      if (length < 20) return;
      const random = seeded(settings.seed + Math.round(length));
      const laneCount = Math.max(1, Math.floor(settings.lanesPerDirection));
      const trafficCount = Math.min(settings.maxTraffic, Math.max(2, Math.floor(length / settings.trafficSpacing * qualityDensity())));
      for (let index = 0; index < trafficCount; index += 1) {
        const direction = index % 2 ? -1 : 1;
        const lane = index % laneCount;
        const lateral = direction * (settings.laneWidth * (lane + 0.5));
        const distance = modulo((index + 0.35 + random() * 0.3) * length / trafficCount, length);
        let roll = random() * 11, profile = vehicleProfiles[0];
        for (const candidate of vehicleProfiles) { roll -= candidate.weight; if (roll <= 0) { profile = candidate; break; } }
        const targetSpeed = lerp(profile.speedMin, profile.speedMax, random()) * (direction > 0 ? 1 : 0.96);
        const pose = sampleAt(distance, lateral);
        if (direction < 0) pose.heading += Math.PI;
        addActor("traffic", { id: `traffic-${index}`, distance, lateral, direction, speed: targetSpeed * 0.85, targetSpeed, lane, vehicleType: profile.type, vehicleLength: profile.length, acceleration: 0, changingLane: false, laneChangeTimer: random() * settings.laneChangeCooldown, pose });
      }

      const serviceTypes = ["fuel", "rest", "workshop", "charging"];
      const serviceCount = Math.min(settings.maxServices, Math.floor(length / settings.serviceSpacing));
      const roadHalfWidth = laneCount * settings.laneWidth;
      for (let index = 0; index < serviceCount; index += 1) {
        const side = index % 2 ? -1 : 1;
        const distance = clamp((index + 0.7) * length / Math.max(1, serviceCount), 0, length);
        const lateral = side * (roadHalfWidth + settings.roadShoulder + 8 + random() * 8);
        addActor("services", { id: `service-${index}`, type: serviceTypes[index % serviceTypes.length], distance, lateral, side, pose: sampleAt(distance, lateral) });
      }

      const eventTypes = ["roadworks", "lane-closure", "broken-vehicle", "emergency"];
      const eventCount = Math.min(settings.maxEvents, Math.floor(length / settings.eventSpacing));
      for (let index = 0; index < eventCount; index += 1) {
        const side = index % 2 ? -1 : 1;
        const distance = clamp((index + 0.45) * length / Math.max(1, eventCount), 0, length);
        const type = eventTypes[index % eventTypes.length];
        const closesLane = type === "roadworks" || type === "lane-closure" || type === "broken-vehicle";
        const lane = closesLane ? index % laneCount : -1;
        const direction = side;
        const lateral = closesLane ? direction * settings.laneWidth * (lane + 0.5) : side * (roadHalfWidth + settings.roadShoulder + 1.5);
        addActor("events", { id: `event-${index}`, type, distance, lateral, side, direction, lane, closesLane, active: true, pose: sampleAt(distance, lateral) });
      }
    }

    function setRoute(points, metadata) {
      if (disposed) throw new Error("TransportRouteRuntime has been disposed");
      route = Array.isArray(points) ? points.map(pointFrom).filter((point, index, list) => !index || Math.hypot(point.x - list[index - 1].x, point.z - list[index - 1].z) > 0.001) : [];
      cumulative = route.map(() => 0);
      length = 0;
      for (let index = 1; index < route.length; index += 1) {
        length += Math.hypot(route[index].x - route[index - 1].x, route[index].y - route[index - 1].y, route[index].z - route[index - 1].z);
        cumulative[index] = length;
      }
      if (metadata) Object.assign(settings, metadata);
      populate();
      return { length, points: route.length, actors };
    }

    function update(deltaSeconds, context) {
      if (disposed || length <= 0) return actors;
      const dt = clamp(finite(deltaSeconds), 0, 0.1);
      const laneCount = Math.max(1, Math.floor(settings.lanesPerDirection));
      const occupied = actors.traffic;
      const playerDistance = finite(context?.playerDistance);
      const playerSpeed = Math.max(0, finite(context?.playerSpeed));
      const playerDirection = finite(context?.playerDirection) < 0 ? -1 : 1;
      const playerLateral = finite(context?.playerLateral);
      const playerLength = Math.max(4, finite(context?.playerLength) || 16.5);
      const playerLane = Array.from({ length: laneCount }, (_, lane) => lane)
        .map(lane => ({ lane, offset: Math.abs(playerLateral - playerDirection * settings.laneWidth * (lane + 0.5)) }))
        .sort((a, b) => a.offset - b.offset)[0];
      const playerOnLane = playerLane && playerLane.offset <= settings.laneWidth * 0.68 ? playerLane.lane : -1;
      const laneSafe = (actor, lane) => {
        const trafficClear = !occupied.some(other => other !== actor && other.direction === actor.direction && other.lane === lane && Math.min(forwardGap(actor.distance, other.distance, actor.direction), forwardGap(other.distance, actor.distance, actor.direction)) < Math.max(18, actor.speed * 1.6));
        if (!trafficClear || playerOnLane !== lane || playerDirection !== actor.direction) return trafficClear;
        const separation = Math.min(forwardGap(actor.distance, playerDistance, actor.direction), forwardGap(playerDistance, actor.distance, actor.direction));
        return separation > Math.max(22, actor.speed * 1.8, playerSpeed * 1.5);
      };
      actors.traffic.forEach(actor => {
        actor.laneChangeTimer = Math.max(0, actor.laneChangeTimer - dt);
        let obstacleGap = Infinity;
        let leadSpeed = actor.targetSpeed;
        occupied.forEach(other => {
          if (other === actor || other.direction !== actor.direction || other.lane !== actor.lane) return;
          const gap = forwardGap(actor.distance, other.distance, actor.direction) - (other.vehicleLength || 5);
          if (gap < obstacleGap) { obstacleGap = gap; leadSpeed = other.speed; }
        });
        actors.events.forEach(event => {
          if (!event.active || !event.closesLane || event.direction !== actor.direction || event.lane !== actor.lane) return;
          const gap = forwardGap(actor.distance, event.distance, actor.direction) - 4;
          if (gap < obstacleGap) { obstacleGap = gap; leadSpeed = 0; }
        });
        if (actor.direction === playerDirection && actor.lane === playerOnLane) {
          const gap = forwardGap(actor.distance, playerDistance, actor.direction) - playerLength * 0.5;
          if (gap < obstacleGap) { obstacleGap = gap; leadSpeed = playerSpeed; }
        }
        const desiredGap = settings.minGap + actor.speed * settings.reactionTime;
        if (obstacleGap < desiredGap * 1.8 && actor.laneChangeTimer <= 0) {
          const candidates = [actor.lane + 1, actor.lane - 1].filter(lane => lane >= 0 && lane < laneCount);
          const nextLane = candidates.find(lane => laneSafe(actor, lane));
          if (nextLane !== undefined) { actor.lane = nextLane; actor.changingLane = true; actor.laneChangeTimer = settings.laneChangeCooldown; }
        }
        let desiredSpeed = actor.targetSpeed;
        if (obstacleGap < desiredGap * 2.5) desiredSpeed = Math.min(desiredSpeed, leadSpeed, actor.targetSpeed * clamp((obstacleGap - settings.minGap) / Math.max(1, desiredGap), 0, 1));
        const speedError = desiredSpeed - actor.speed;
        actor.acceleration = clamp(speedError * 0.8, -settings.comfortableBrake, settings.maxAcceleration);
        actor.speed = clamp(actor.speed + actor.acceleration * dt, 0, actor.targetSpeed);
        const targetLateral = actor.direction * settings.laneWidth * (actor.lane + 0.5);
        actor.lateral = lerp(actor.lateral, targetLateral, clamp(dt * 1.8, 0, 1));
        actor.changingLane = Math.abs(actor.lateral - targetLateral) > 0.05;
        actor.distance = modulo(actor.distance + actor.speed * actor.direction * dt, length);
        actor.pose = sampleAt(actor.distance, actor.lateral);
        if (actor.direction < 0) actor.pose.heading += Math.PI;
        adapter.move?.(actor.handle, actor.pose, actor, context);
      });
      let nearest = null;
      actors.traffic.forEach(actor => {
        const gap = Math.min(forwardGap(playerDistance, actor.distance, playerDirection), forwardGap(actor.distance, playerDistance, playerDirection));
        if (!nearest || gap < nearest.distance) nearest = { id: actor.id, distance: gap, speed: actor.speed, lane: actor.lane, direction: actor.direction, vehicleType: actor.vehicleType };
      });
      actors.nearestTraffic = actors.nearesTraffic = nearest;
      actors.threat = nearest && nearest.distance < Math.max(12, finite(context?.playerSpeed) * 1.5) ? Object.assign({ level: nearest.distance < 6 ? "critical" : "warning" }, nearest) : null;
      actors.events.forEach(actor => {
        actor.distanceToPlayer = Math.min(Math.abs(actor.distance - playerDistance), length - Math.abs(actor.distance - playerDistance));
        adapter.update?.(actor.handle, actor, context);
      });
      return actors;
    }

    function dispose() {
      if (disposed) return;
      removeActors();
      route = []; cumulative = []; length = 0; disposed = true;
      adapter.dispose?.();
    }

    return { setRoute, update, sampleAt, dispose, actors, get length() { return length; } };
  }

  const runtime = create();
  global.MoonTransportRouteRuntime = {
    create,
    setRoute: runtime.setRoute,
    update: runtime.update,
    sampleAt: runtime.sampleAt,
    dispose: runtime.dispose,
    actors: runtime.actors,
    get length() { return runtime.length; },
  };
})(window);
