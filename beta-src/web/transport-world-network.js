/**
 * Red logística mundial original para Rutas Moon.
 *
 * Los nodos usan coordenadas geográficas públicas aproximadas de ciudades y
 * terminales. Las conexiones no pretenden representar una licencia de juego ni
 * afirmar que exista carretera entre continentes: los saltos oceánicos siempre
 * se modelan como tramos marítimos o aéreos.
 */

export const WORLD_REGIONS = Object.freeze({
  europe: { id: "europe", name: "Europa", climate: "temperate", textureProfile: "europe-temperate" },
  northAmerica: { id: "northAmerica", name: "Norteamérica", climate: "continental", textureProfile: "north-america" },
  latinAmerica: { id: "latinAmerica", name: "Latinoamérica", climate: "tropical", textureProfile: "latin-america" },
  africa: { id: "africa", name: "África", climate: "mixed-arid", textureProfile: "africa-mixed" },
  middleEast: { id: "middleEast", name: "Oriente Medio", climate: "arid", textureProfile: "middle-east-arid" },
  asia: { id: "asia", name: "Asia", climate: "mixed", textureProfile: "asia-mixed" },
  oceania: { id: "oceania", name: "Oceanía", climate: "oceanic", textureProfile: "oceania" },
});

const hub = (id, name, countryCode, region, lon, lat, modes, textureProfile) =>
  Object.freeze({ id, name, countryCode, region, coordinates: Object.freeze([lon, lat]), modes: Object.freeze(modes), textureProfile });

export const WORLD_HUBS = Object.freeze([
  hub("madrid", "Madrid", "ES", "europe", -3.7038, 40.4168, ["road", "rail", "air"], "iberian-inland"),
  hub("rotterdam", "Róterdam", "NL", "europe", 4.4777, 51.9244, ["road", "sea", "air"], "north-sea-industrial"),
  hub("hamburg", "Hamburgo", "DE", "europe", 9.9937, 53.5511, ["road", "sea", "air"], "north-sea-industrial"),
  hub("valencia", "Valencia", "ES", "europe", -0.3763, 39.4699, ["road", "sea", "air"], "mediterranean-port"),
  hub("istanbul", "Estambul", "TR", "europe", 28.9784, 41.0082, ["road", "sea", "air"], "bosphorus"),
  hub("new_york", "Nueva York", "US", "northAmerica", -74.006, 40.7128, ["road", "sea", "air"], "atlantic-metropolis"),
  hub("los_angeles", "Los Ángeles", "US", "northAmerica", -118.2437, 34.0522, ["road", "sea", "air"], "pacific-metropolis"),
  hub("chicago", "Chicago", "US", "northAmerica", -87.6298, 41.8781, ["road", "air"], "great-lakes"),
  hub("vancouver", "Vancouver", "CA", "northAmerica", -123.1207, 49.2827, ["road", "sea", "air"], "pacific-northwest"),
  hub("mexico_city", "Ciudad de México", "MX", "northAmerica", -99.1332, 19.4326, ["road", "air"], "mexican-highland"),
  hub("santos", "Santos", "BR", "latinAmerica", -46.3289, -23.9608, ["road", "sea"], "atlantic-tropical-port"),
  hub("sao_paulo", "São Paulo", "BR", "latinAmerica", -46.6333, -23.5505, ["road", "air"], "brazil-urban"),
  hub("buenos_aires", "Buenos Aires", "AR", "latinAmerica", -58.3816, -34.6037, ["road", "sea", "air"], "pampas-port"),
  hub("panama", "Ciudad de Panamá", "PA", "latinAmerica", -79.5199, 8.9824, ["road", "sea", "air"], "tropical-canal"),
  hub("casablanca", "Casablanca", "MA", "africa", -7.5898, 33.5731, ["road", "sea", "air"], "maghreb-atlantic"),
  hub("cairo", "El Cairo", "EG", "africa", 31.2357, 30.0444, ["road", "air"], "nile-arid"),
  hub("durban", "Durban", "ZA", "africa", 31.0218, -29.8587, ["road", "sea", "air"], "south-africa-coast"),
  hub("nairobi", "Nairobi", "KE", "africa", 36.8219, -1.2921, ["road", "air"], "east-africa-highland"),
  hub("dubai", "Dubái", "AE", "middleEast", 55.2708, 25.2048, ["road", "sea", "air"], "gulf-arid"),
  hub("jeddah", "Yeda", "SA", "middleEast", 39.1925, 21.4858, ["road", "sea", "air"], "red-sea-arid"),
  hub("singapore", "Singapur", "SG", "asia", 103.8198, 1.3521, ["road", "sea", "air"], "equatorial-port"),
  hub("shanghai", "Shanghái", "CN", "asia", 121.4737, 31.2304, ["road", "sea", "air"], "east-asia-megacity"),
  hub("tokyo", "Tokio", "JP", "asia", 139.6917, 35.6895, ["road", "sea", "air"], "japan-urban"),
  hub("mumbai", "Bombay", "IN", "asia", 72.8777, 19.076, ["road", "sea", "air"], "monsoon-port"),
  hub("delhi", "Delhi", "IN", "asia", 77.1025, 28.7041, ["road", "air"], "north-india-urban"),
  hub("sydney", "Sídney", "AU", "oceania", 151.2093, -33.8688, ["road", "sea", "air"], "australia-east-coast"),
  hub("melbourne", "Melbourne", "AU", "oceania", 144.9631, -37.8136, ["road", "sea", "air"], "australia-south-coast"),
  hub("auckland", "Auckland", "NZ", "oceania", 174.7633, -36.8485, ["road", "sea", "air"], "new-zealand-oceanic"),
]);

const link = (from, to, mode, options = {}) => Object.freeze({ from, to, mode, bidirectional: true, ...options });

// Los enlaces road son corredores terrestres plausibles que deben resolverse
// contra OSRM. Los enlaces sea/air son abstracciones logísticas, no carreteras.
export const WORLD_LINKS = Object.freeze([
  link("madrid", "valencia", "road"), link("madrid", "rotterdam", "road"), link("rotterdam", "hamburg", "road"),
  link("madrid", "valencia", "rail"), link("madrid", "rotterdam", "rail"), link("rotterdam", "hamburg", "rail"), link("hamburg", "istanbul", "rail"),
  link("hamburg", "istanbul", "road"), link("valencia", "istanbul", "sea"),
  link("new_york", "chicago", "road"), link("chicago", "los_angeles", "road"), link("los_angeles", "vancouver", "road"),
  link("los_angeles", "mexico_city", "road"), link("santos", "sao_paulo", "road"), link("sao_paulo", "buenos_aires", "road"),
  link("casablanca", "cairo", "road"), link("cairo", "nairobi", "road"), link("nairobi", "durban", "road"),
  link("istanbul", "dubai", "road"), link("dubai", "jeddah", "road"), link("mumbai", "delhi", "road"),
  link("singapore", "shanghai", "sea"), link("shanghai", "tokyo", "sea"), link("sydney", "melbourne", "road"),
  link("rotterdam", "new_york", "sea"), link("valencia", "casablanca", "sea"), link("casablanca", "santos", "sea"),
  link("new_york", "panama", "sea"), link("panama", "los_angeles", "sea"), link("panama", "santos", "sea"),
  link("hamburg", "dubai", "sea"), link("dubai", "mumbai", "sea"), link("mumbai", "singapore", "sea"),
  link("singapore", "sydney", "sea"), link("sydney", "auckland", "sea"), link("los_angeles", "tokyo", "sea"),
  link("new_york", "madrid", "air"), link("madrid", "dubai", "air"), link("dubai", "singapore", "air"),
  link("singapore", "tokyo", "air"), link("tokyo", "los_angeles", "air"), link("los_angeles", "sydney", "air"),
  link("sydney", "auckland", "air"), link("sao_paulo", "madrid", "air"), link("nairobi", "dubai", "air"),
  link("delhi", "singapore", "air"), link("cairo", "madrid", "air"), link("chicago", "new_york", "air"),
]);

const HUB_BY_ID = new Map(WORLD_HUBS.map((item) => [item.id, item]));
const SPEED_KMH = Object.freeze({ road: 72, rail: 82, sea: 32, air: 760 });
const MODE_PENALTY_KM = Object.freeze({ road: 0, rail: 80, sea: 350, air: 900 });

export const getWorldHub = (id) => HUB_BY_ID.get(String(id || "").toLowerCase()) || null;
export const getHubsByRegion = (region) => WORLD_HUBS.filter((item) => item.region === region);
export const getHubsByMode = (mode) => WORLD_HUBS.filter((item) => item.modes.includes(mode));

export function greatCircleDistanceKm(from, to) {
  const a = Array.isArray(from) ? from : getWorldHub(from)?.coordinates;
  const b = Array.isArray(to) ? to : getWorldHub(to)?.coordinates;
  if (!a || !b) return NaN;
  const rad = Math.PI / 180, dLat = (b[1] - a[1]) * rad, dLon = (b[0] - a[0]) * rad;
  const value = Math.sin(dLat / 2) ** 2 + Math.cos(a[1] * rad) * Math.cos(b[1] * rad) * Math.sin(dLon / 2) ** 2;
  return 6371.0088 * 2 * Math.asin(Math.min(1, Math.sqrt(value)));
}

function makeLeg(edge, fromId) {
  const from = getWorldHub(fromId), to = getWorldHub(edge.from === fromId ? edge.to : edge.from);
  const directKm = greatCircleDistanceKm(from.coordinates, to.coordinates);
  const distanceKm = Math.round(directKm * (edge.mode === "road" ? 1.22 : edge.mode === "sea" ? 1.12 : 1));
  return { from, to, mode: edge.mode, distanceKm, durationHours: distanceKm / SPEED_KMH[edge.mode], source: edge.mode === "road" ? "road-estimate-awaiting-osrm" : "world-network", requiresExternalRouting: edge.mode === "road" };
}

export function findMultimodalRoute(fromId, toId, { allowedModes = ["road", "rail", "sea", "air"] } = {}) {
  if (!getWorldHub(fromId) || !getWorldHub(toId)) return null;
  const allowed = new Set(allowedModes), distances = new Map(WORLD_HUBS.map(({ id }) => [id, Infinity]));
  const previous = new Map(), pending = new Set(distances.keys());
  distances.set(fromId, 0);
  while (pending.size) {
    let current = null;
    for (const id of pending) if (current === null || distances.get(id) < distances.get(current)) current = id;
    if (current === toId || !Number.isFinite(distances.get(current))) break;
    pending.delete(current);
    for (const edge of WORLD_LINKS) {
      if (!allowed.has(edge.mode) || (edge.from !== current && edge.to !== current)) continue;
      const next = edge.from === current ? edge.to : edge.from;
      if (!pending.has(next)) continue;
      const leg = makeLeg(edge, current), candidate = distances.get(current) + leg.distanceKm + MODE_PENALTY_KM[edge.mode];
      if (candidate < distances.get(next)) { distances.set(next, candidate); previous.set(next, { at: current, edge }); }
    }
  }
  if (!Number.isFinite(distances.get(toId))) return null;
  const legs = []; let cursor = toId;
  while (cursor !== fromId) { const step = previous.get(cursor); if (!step) return null; legs.unshift(makeLeg(step.edge, step.at)); cursor = step.at; }
  return {
    from: getWorldHub(fromId), to: getWorldHub(toId), legs,
    distanceKm: legs.reduce((sum, leg) => sum + leg.distanceKm, 0),
    durationHours: legs.reduce((sum, leg) => sum + leg.durationHours, 0),
    modes: [...new Set(legs.map((leg) => leg.mode))],
  };
}

export function createOsrmRequest(leg, endpoint = "https://router.project-osrm.org") {
  if (!leg || leg.mode !== "road") return null;
  const coordinates = `${leg.from.coordinates.join(",")};${leg.to.coordinates.join(",")}`;
  return `${endpoint.replace(/\/$/, "")}/route/v1/driving/${coordinates}?overview=full&geometries=geojson&steps=true&annotations=false`;
}

export async function resolveRoadLeg(leg, { fetchImpl = globalThis.fetch, endpoint } = {}) {
  const url = createOsrmRequest(leg, endpoint);
  if (!url) return leg;
  if (typeof fetchImpl !== "function") throw new Error("No hay cliente HTTP para consultar OSRM");
  const response = await fetchImpl(url, { headers: { Accept: "application/json" } });
  if (!response.ok) throw new Error(`OSRM ${response.status}`);
  const payload = await response.json(), route = payload.routes?.[0];
  if (payload.code !== "Ok" || !route?.geometry?.coordinates?.length) throw new Error(payload.message || "Ruta terrestre no encontrada");
  return { ...leg, distanceKm: route.distance / 1000, durationHours: route.duration / 3600, coordinates: route.geometry.coordinates, source: "osrm-openstreetmap", requiresExternalRouting: false };
}

export async function resolveMultimodalRoads(plan, options = {}) {
  if (!plan) return null;
  const legs = [];
  for (const leg of plan.legs) legs.push(leg.mode === "road" ? await resolveRoadLeg(leg, options) : leg);
  return { ...plan, legs, distanceKm: legs.reduce((sum, leg) => sum + leg.distanceKm, 0), durationHours: legs.reduce((sum, leg) => sum + leg.durationHours, 0) };
}

export default Object.freeze({ regions: WORLD_REGIONS, hubs: WORLD_HUBS, links: WORLD_LINKS });
