const EARTH_RADIUS_M = 6371008.8;
const DEG = Math.PI / 180;

const clamp = (value, min, max) => Math.max(min, Math.min(max, value));
const finite = (value, fallback = 0) => Number.isFinite(Number(value)) ? Number(value) : fallback;

function coordinateOf(value) {
  if (Array.isArray(value) && value.length >= 2) return [finite(value[0]), finite(value[1])];
  if (value && typeof value === "object") {
    const lon = value.lon ?? value.lng ?? value.longitude ?? value.x;
    const lat = value.lat ?? value.latitude ?? value.y;
    if (Number.isFinite(Number(lon)) && Number.isFinite(Number(lat))) return [Number(lon), Number(lat)];
  }
  return null;
}

function project([lon, lat], origin) {
  const cosLat = Math.cos(origin[1] * DEG);
  return {
    x: (lon - origin[0]) * DEG * EARTH_RADIUS_M * cosLat,
    y: (lat - origin[1]) * DEG * EARTH_RADIUS_M,
  };
}

function nearestOnSegment(point, a, b) {
  const dx = b.x - a.x, dy = b.y - a.y;
  const length2 = dx * dx + dy * dy;
  const t = length2 ? clamp(((point.x - a.x) * dx + (point.y - a.y) * dy) / length2, 0, 1) : 0;
  const x = a.x + dx * t, y = a.y + dy * t;
  return { t, x, y, distance: Math.hypot(point.x - x, point.y - y) };
}

function instructionFor(step) {
  if (!step) return "Continúa por la ruta";
  if (step.instruction) return String(step.instruction);
  const road = step.name && step.name !== "Carretera sin nombre" ? ` hacia ${step.name}` : "";
  const modifier = String(step.modifier || "straight").replaceAll("_", " ");
  const type = String(step.maneuver || step.type || "continue");
  const labels = {
    depart: "Inicia la marcha", arrive: "Has llegado al destino", merge: "Incorpórate",
    fork: "Toma la bifurcación", roundabout: "Entra en la rotonda", rotary: "Entra en la rotonda",
    "roundabout turn": "Gira en la rotonda", "end of road": "Al final de la vía gira",
    "new name": "Continúa", continue: "Continúa", turn: "Gira", exit: "Toma la salida",
    notification: "Atención", "off ramp": "Toma la salida", "on ramp": "Toma el acceso",
  };
  const directions = {
    straight: "recto", right: "a la derecha", left: "a la izquierda", uturn: "para cambiar de sentido",
    "slight right": "ligeramente a la derecha", "slight left": "ligeramente a la izquierda",
    "sharp right": "pronunciadamente a la derecha", "sharp left": "pronunciadamente a la izquierda",
  };
  return `${labels[type] || "Continúa"} ${directions[modifier] || modifier}${road}`.replace(/\s+/g, " ").trim();
}

function normalizedSteps(route, origin, segments, totalDistance) {
  const raw = route?.steps || route?.legs?.flatMap(leg => leg.steps || []) || [];
  let running = 0;
  return raw.map((step, index) => {
    const location = coordinateOf(step.location || step.maneuver?.location);
    let progress = running;
    if (location) {
      const point = project(location, origin);
      let nearest = { distance: Infinity, progress: running };
      for (const segment of segments) {
        const match = nearestOnSegment(point, segment.a, segment.b);
        if (match.distance < nearest.distance) nearest = { distance: match.distance, progress: segment.start + segment.length * match.t };
      }
      progress = nearest.progress;
    }
    const distance = finite(step.distance, finite(step.distanceKm) * 1000);
    const result = {
      index, progress: clamp(progress, 0, totalDistance), distance,
      name: String(step.name || ""), type: step.maneuver?.type || step.maneuver || step.type || "continue",
      modifier: step.maneuver?.modifier || step.modifier || "straight",
      location, raw: step,
    };
    result.instruction = instructionFor(result);
    running = Math.max(running, result.progress + distance);
    return result;
  }).sort((a, b) => a.progress - b.progress);
}

export function createRouteNavigation(options = {}) {
  const settings = {
    offRouteThreshold: finite(options.offRouteThreshold, 35),
    laneDepartureThreshold: finite(options.laneDepartureThreshold, 2.25),
    searchWindow: Math.max(4, Math.round(finite(options.searchWindow, 60))),
    maxBackwardMeters: finite(options.maxBackwardMeters, 12),
    recenterAfterMs: finite(options.recenterAfterMs, 1800),
    arrivalThreshold: finite(options.arrivalThreshold, 18),
  };
  let model = null;
  let state = emptyState();

  function emptyState() {
    return {
      ready: false, progressMeters: 0, progressRatio: 0, distanceRemainingMeters: 0,
      distanceToRouteMeters: Infinity, snappedPosition: null, segmentIndex: -1,
      nextManeuver: null, nextInstruction: "Sin ruta activa", distanceToManeuverMeters: null,
      offRoute: false, laneDeparture: false, arrived: false, recentering: false, updatedAt: 0,
    };
  }

  function setRoute(route) {
    const coordinates = (route?.coordinates || route?.geometry?.coordinates || []).map(coordinateOf).filter(Boolean);
    if (coordinates.length < 2) throw new TypeError("La ruta necesita al menos dos coordenadas [lon, lat]");
    const origin = coordinates[0], points = coordinates.map(value => project(value, origin));
    let total = 0;
    const segments = points.slice(0, -1).map((a, index) => {
      const b = points[index + 1], length = Math.hypot(b.x - a.x, b.y - a.y);
      const segment = { index, a, b, start: total, length };
      total += length;
      return segment;
    }).filter(segment => segment.length > 0.01);
    if (!segments.length) throw new TypeError("La geometría de ruta no contiene distancia utilizable");
    model = { route, coordinates, origin, points, segments, total, steps: normalizedSteps(route, origin, segments, total) };
    state = { ...emptyState(), ready: true, distanceRemainingMeters: total };
    return getState();
  }

  function findMatch(point, forceGlobal = false) {
    const center = state.segmentIndex < 0 ? 0 : state.segmentIndex;
    const start = forceGlobal ? 0 : Math.max(0, center - settings.searchWindow);
    const end = forceGlobal ? model.segments.length : Math.min(model.segments.length, center + settings.searchWindow + 1);
    let best = null;
    for (let index = start; index < end; index++) {
      const segment = model.segments[index], hit = nearestOnSegment(point, segment.a, segment.b);
      const progress = segment.start + segment.length * hit.t;
      // Prefer continuity when parallel roads or carriageways are very close.
      const continuityPenalty = state.segmentIndex < 0 ? 0 : Math.min(25, Math.abs(index - center) * 0.12);
      const score = hit.distance + continuityPenalty;
      if (!best || score < best.score) best = { ...hit, score, segment, index, progress };
    }
    return best;
  }

  function update(position, updateOptions = {}) {
    if (!model) return getState();
    const coordinate = coordinateOf(position);
    if (!coordinate) throw new TypeError("update necesita una posición {lon, lat} o [lon, lat]");
    const now = finite(updateOptions.timestamp, Date.now()), point = project(coordinate, model.origin);
    let match = findMatch(point);
    if (!match || match.distance > settings.offRouteThreshold * 2) match = findMatch(point, true);
    const wasOffRoute = state.offRoute;
    const offRoute = match.distance > finite(updateOptions.offRouteThreshold, settings.offRouteThreshold);
    const deltaMs = state.updatedAt ? Math.max(0, now - state.updatedAt) : 0;
    const speedMps = Math.max(0, finite(updateOptions.speedMps, finite(updateOptions.speedKmh) / 3.6));
    let progress = match.progress;
    if (!offRoute && state.segmentIndex >= 0) {
      const backwardLimit = settings.maxBackwardMeters + speedMps * Math.min(deltaMs / 1000, 2);
      progress = Math.max(progress, state.progressMeters - backwardLimit);
    }
    const recentering = wasOffRoute && !offRoute;
    if (recentering && deltaMs < settings.recenterAfterMs) {
      const blend = clamp(deltaMs / settings.recenterAfterMs, 0.12, 1);
      progress = state.progressMeters + (progress - state.progressMeters) * blend;
    }
    progress = clamp(progress, 0, model.total);
    const next = model.steps.find(step => step.progress > progress + 3) || null;
    const remaining = Math.max(0, model.total - progress);
    state = {
      ready: true, progressMeters: progress, progressRatio: model.total ? progress / model.total : 1,
      distanceRemainingMeters: remaining, distanceToRouteMeters: match.distance,
      snappedPosition: { lon: coordinate[0], lat: coordinate[1], x: match.x, y: match.y },
      segmentIndex: match.index, nextManeuver: next,
      nextInstruction: next?.instruction || (remaining <= settings.arrivalThreshold ? "Has llegado al destino" : "Continúa por la ruta"),
      distanceToManeuverMeters: next ? Math.max(0, next.progress - progress) : null,
      offRoute, laneDeparture: !offRoute && match.distance > finite(updateOptions.laneDepartureThreshold, settings.laneDepartureThreshold),
      arrived: remaining <= settings.arrivalThreshold && !offRoute, recentering, updatedAt: now,
    };
    return getState();
  }

  function getState() {
    return { ...state, snappedPosition: state.snappedPosition && { ...state.snappedPosition }, nextManeuver: state.nextManeuver && { ...state.nextManeuver } };
  }

  function reset() {
    model = null;
    state = emptyState();
    return getState();
  }

  return { setRoute, update, getState, reset };
}

export default createRouteNavigation;
