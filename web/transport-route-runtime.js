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
    const actors = { traffic: [], services: [], events: [] };

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
      Object.values(actors).forEach(list => {
        list.forEach(actor => adapter.remove?.(actor.handle, actor));
        list.length = 0;
      });
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
      const trafficCount = Math.min(settings.maxTraffic, Math.max(2, Math.floor(length / settings.trafficSpacing)));
      for (let index = 0; index < trafficCount; index += 1) {
        const direction = index % 2 ? -1 : 1;
        const lane = index % laneCount;
        const lateral = direction * (settings.laneWidth * (lane + 0.5));
        const distance = modulo((index + 0.35 + random() * 0.3) * length / trafficCount, length);
        const speed = (direction > 0 ? 18 : 16) + random() * 10;
        const pose = sampleAt(distance, lateral);
        if (direction < 0) pose.heading += Math.PI;
        addActor("traffic", { id: `traffic-${index}`, distance, lateral, direction, speed, lane, pose });
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
        const lateral = side * (roadHalfWidth + settings.roadShoulder + 1.5);
        addActor("events", { id: `event-${index}`, type: eventTypes[index % eventTypes.length], distance, lateral, side, active: true, pose: sampleAt(distance, lateral) });
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
      actors.traffic.forEach(actor => {
        actor.distance = modulo(actor.distance + actor.speed * actor.direction * dt, length);
        actor.pose = sampleAt(actor.distance, actor.lateral);
        if (actor.direction < 0) actor.pose.heading += Math.PI;
        adapter.move?.(actor.handle, actor.pose, actor, context);
      });
      const playerDistance = finite(context?.playerDistance);
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
