/**
 * Original, lightweight world data for Rutas del Continente.
 * Coordinates are stylised game-space positions rather than map projections.
 * The module intentionally contains no third-party game data or assets.
 */

export const EUROPE_MAP_BOUNDS = Object.freeze({
  minX: -100,
  maxX: 100,
  minZ: -82,
  maxZ: 82,
});

export const LANDSCAPE_TYPES = Object.freeze({
  ATLANTIC: "atlantic",
  MEDITERRANEAN: "mediterranean",
  ALPINE: "alpine",
  CENTRAL_PLAINS: "central-plains",
  NORDIC: "nordic",
  BALTIC: "baltic",
  CARPATHIAN: "carpathian",
  URBAN: "urban",
});

export const EUROPE_CITIES = Object.freeze([
  { id: "lisbon", name: "Lisboa", country: "Portugal", countryCode: "PT", x: -90, z: 51, elevationM: 45, landscape: "atlantic" },
  { id: "madrid", name: "Madrid", country: "España", countryCode: "ES", x: -67, z: 44, elevationM: 657, landscape: "central-plains" },
  { id: "barcelona", name: "Barcelona", country: "España", countryCode: "ES", x: -43, z: 48, elevationM: 12, landscape: "mediterranean" },
  { id: "paris", name: "París", country: "Francia", countryCode: "FR", x: -36, z: 12, elevationM: 35, landscape: "central-plains" },
  { id: "lyon", name: "Lyon", country: "Francia", countryCode: "FR", x: -25, z: 32, elevationM: 173, landscape: "alpine" },
  { id: "london", name: "Londres", country: "Reino Unido", countryCode: "GB", x: -49, z: -4, elevationM: 11, landscape: "atlantic" },
  { id: "dublin", name: "Dublín", country: "Irlanda", countryCode: "IE", x: -71, z: -16, elevationM: 20, landscape: "atlantic" },
  { id: "brussels", name: "Bruselas", country: "Bélgica", countryCode: "BE", x: -22, z: 1, elevationM: 13, landscape: "urban" },
  { id: "amsterdam", name: "Ámsterdam", country: "Países Bajos", countryCode: "NL", x: -18, z: -10, elevationM: -2, landscape: "atlantic" },
  { id: "hamburg", name: "Hamburgo", country: "Alemania", countryCode: "DE", x: 3, z: -15, elevationM: 8, landscape: "central-plains" },
  { id: "berlin", name: "Berlín", country: "Alemania", countryCode: "DE", x: 25, z: -9, elevationM: 34, landscape: "central-plains" },
  { id: "munich", name: "Múnich", country: "Alemania", countryCode: "DE", x: 12, z: 27, elevationM: 520, landscape: "alpine" },
  { id: "zurich", name: "Zúrich", country: "Suiza", countryCode: "CH", x: -5, z: 31, elevationM: 408, landscape: "alpine" },
  { id: "milan", name: "Milán", country: "Italia", countryCode: "IT", x: 1, z: 43, elevationM: 122, landscape: "alpine" },
  { id: "rome", name: "Roma", country: "Italia", countryCode: "IT", x: 15, z: 67, elevationM: 21, landscape: "mediterranean" },
  { id: "vienna", name: "Viena", country: "Austria", countryCode: "AT", x: 32, z: 29, elevationM: 171, landscape: "alpine" },
  { id: "prague", name: "Praga", country: "Chequia", countryCode: "CZ", x: 28, z: 12, elevationM: 235, landscape: "central-plains" },
  { id: "warsaw", name: "Varsovia", country: "Polonia", countryCode: "PL", x: 53, z: -2, elevationM: 100, landscape: "central-plains" },
  { id: "copenhagen", name: "Copenhague", country: "Dinamarca", countryCode: "DK", x: 9, z: -34, elevationM: 6, landscape: "nordic" },
  { id: "oslo", name: "Oslo", country: "Noruega", countryCode: "NO", x: 9, z: -68, elevationM: 23, landscape: "nordic" },
  { id: "stockholm", name: "Estocolmo", country: "Suecia", countryCode: "SE", x: 39, z: -63, elevationM: 28, landscape: "nordic" },
  { id: "helsinki", name: "Helsinki", country: "Finlandia", countryCode: "FI", x: 67, z: -62, elevationM: 17, landscape: "baltic" },
  { id: "tallinn", name: "Tallin", country: "Estonia", countryCode: "EE", x: 68, z: -45, elevationM: 9, landscape: "baltic" },
  { id: "riga", name: "Riga", country: "Letonia", countryCode: "LV", x: 68, z: -27, elevationM: 7, landscape: "baltic" },
  { id: "budapest", name: "Budapest", country: "Hungría", countryCode: "HU", x: 45, z: 38, elevationM: 96, landscape: "carpathian" },
  { id: "zagreb", name: "Zagreb", country: "Croacia", countryCode: "HR", x: 33, z: 49, elevationM: 122, landscape: "carpathian" },
  { id: "bucharest", name: "Bucarest", country: "Rumanía", countryCode: "RO", x: 72, z: 46, elevationM: 70, landscape: "carpathian" },
  { id: "sofia", name: "Sofía", country: "Bulgaria", countryCode: "BG", x: 67, z: 61, elevationM: 550, landscape: "carpathian" },
  { id: "athens", name: "Atenas", country: "Grecia", countryCode: "GR", x: 70, z: 79, elevationM: 70, landscape: "mediterranean" },
  { id: "porto", name: "Oporto", country: "Portugal", countryCode: "PT", x: -91, z: 37, elevationM: 104, landscape: "atlantic" },
  { id: "seville", name: "Sevilla", country: "España", countryCode: "ES", x: -76, z: 66, elevationM: 7, landscape: "mediterranean" },
  { id: "marseille", name: "Marsella", country: "Francia", countryCode: "FR", x: -25, z: 48, elevationM: 12, landscape: "mediterranean" },
  { id: "venice", name: "Venecia", country: "Italia", countryCode: "IT", x: 14, z: 43, elevationM: 2, landscape: "mediterranean" },
  { id: "naples", name: "Nápoles", country: "Italia", countryCode: "IT", x: 23, z: 73, elevationM: 17, landscape: "mediterranean" },
  { id: "ljubljana", name: "Liubliana", country: "Eslovenia", countryCode: "SI", x: 27, z: 45, elevationM: 295, landscape: "alpine" },
  { id: "belgrade", name: "Belgrado", country: "Serbia", countryCode: "RS", x: 49, z: 52, elevationM: 117, landscape: "carpathian" },
  { id: "sarajevo", name: "Sarajevo", country: "Bosnia y Herzegovina", countryCode: "BA", x: 43, z: 59, elevationM: 518, landscape: "carpathian" },
  { id: "tirana", name: "Tirana", country: "Albania", countryCode: "AL", x: 48, z: 72, elevationM: 110, landscape: "mediterranean" },
  { id: "skopje", name: "Skopie", country: "Macedonia del Norte", countryCode: "MK", x: 58, z: 69, elevationM: 240, landscape: "carpathian" },
  { id: "bratislava", name: "Bratislava", country: "Eslovaquia", countryCode: "SK", x: 36, z: 28, elevationM: 134, landscape: "central-plains" },
  { id: "vilnius", name: "Vilna", country: "Lituania", countryCode: "LT", x: 64, z: -15, elevationM: 112, landscape: "baltic" },
]);

const road = (from, to, distanceKm, roadClass, landscape, options = {}) =>
  Object.freeze({ from, to, distanceKm, roadClass, landscape, toll: false, ferry: false, ...options });

export const EUROPE_ROADS = Object.freeze([
  road("lisbon", "madrid", 625, "motorway", "central-plains", { toll: true }),
  road("madrid", "barcelona", 620, "motorway", "central-plains", { toll: true }),
  road("madrid", "paris", 1270, "motorway", "central-plains"),
  road("barcelona", "lyon", 640, "motorway", "mediterranean", { toll: true }),
  road("lyon", "paris", 465, "motorway", "central-plains", { toll: true }),
  road("lyon", "zurich", 430, "mountain", "alpine", { toll: true }),
  road("lyon", "milan", 445, "mountain", "alpine", { toll: true }),
  road("paris", "brussels", 315, "motorway", "central-plains"),
  road("paris", "london", 455, "motorway", "atlantic", { ferry: true }),
  road("london", "dublin", 465, "regional", "atlantic", { ferry: true }),
  road("london", "amsterdam", 535, "motorway", "atlantic", { ferry: true }),
  road("brussels", "amsterdam", 210, "motorway", "atlantic"),
  road("brussels", "hamburg", 595, "motorway", "central-plains"),
  road("amsterdam", "hamburg", 465, "motorway", "central-plains"),
  road("hamburg", "berlin", 290, "motorway", "central-plains"),
  road("hamburg", "copenhagen", 335, "motorway", "nordic", { ferry: true }),
  road("berlin", "prague", 350, "motorway", "central-plains"),
  road("berlin", "warsaw", 575, "motorway", "central-plains", { toll: true }),
  road("munich", "prague", 385, "motorway", "central-plains"),
  road("munich", "zurich", 315, "motorway", "alpine"),
  road("munich", "vienna", 435, "motorway", "alpine", { toll: true }),
  road("zurich", "milan", 280, "mountain", "alpine", { toll: true }),
  road("milan", "rome", 575, "motorway", "mediterranean", { toll: true }),
  road("prague", "vienna", 335, "motorway", "central-plains"),
  road("prague", "warsaw", 680, "motorway", "central-plains"),
  road("vienna", "budapest", 245, "motorway", "central-plains", { toll: true }),
  road("vienna", "zagreb", 370, "motorway", "alpine", { toll: true }),
  road("warsaw", "riga", 660, "regional", "baltic"),
  road("copenhagen", "oslo", 600, "motorway", "nordic", { ferry: true }),
  road("copenhagen", "stockholm", 655, "motorway", "nordic", { toll: true }),
  road("oslo", "stockholm", 525, "regional", "nordic"),
  road("stockholm", "helsinki", 495, "regional", "baltic", { ferry: true }),
  road("helsinki", "tallinn", 85, "regional", "baltic", { ferry: true }),
  road("tallinn", "riga", 310, "regional", "baltic"),
  road("riga", "warsaw", 660, "regional", "baltic"),
  road("budapest", "zagreb", 345, "motorway", "carpathian", { toll: true }),
  road("budapest", "bucharest", 835, "motorway", "carpathian", { toll: true }),
  road("zagreb", "sofia", 790, "motorway", "carpathian", { toll: true }),
  road("bucharest", "sofia", 385, "regional", "carpathian"),
  road("sofia", "athens", 790, "motorway", "mediterranean", { toll: true }),
  road("lisbon", "porto", 315, "motorway", "atlantic", { toll: true }),
  road("lisbon", "seville", 465, "motorway", "mediterranean", { toll: true }),
  road("seville", "madrid", 535, "motorway", "central-plains"),
  road("barcelona", "marseille", 505, "motorway", "mediterranean", { toll: true }),
  road("marseille", "lyon", 315, "motorway", "mediterranean", { toll: true }),
  road("marseille", "milan", 520, "mountain", "alpine", { toll: true }),
  road("milan", "venice", 270, "motorway", "mediterranean", { toll: true }),
  road("rome", "naples", 225, "motorway", "mediterranean", { toll: true }),
  road("venice", "ljubljana", 240, "motorway", "alpine", { toll: true }),
  road("ljubljana", "zagreb", 140, "motorway", "alpine", { toll: true }),
  road("zagreb", "sarajevo", 405, "regional", "carpathian"),
  road("sarajevo", "belgrade", 295, "regional", "carpathian"),
  road("belgrade", "sofia", 395, "motorway", "carpathian", { toll: true }),
  road("belgrade", "skopje", 435, "motorway", "carpathian", { toll: true }),
  road("skopje", "tirana", 290, "mountain", "carpathian"),
  road("skopje", "athens", 700, "motorway", "mediterranean", { toll: true }),
  road("vienna", "bratislava", 80, "motorway", "central-plains"),
  road("bratislava", "budapest", 200, "motorway", "central-plains", { toll: true }),
  road("warsaw", "vilnius", 465, "regional", "baltic"),
  road("vilnius", "riga", 295, "regional", "baltic"),
]);

const CITY_BY_ID = new Map(EUROPE_CITIES.map((city) => [city.id, city]));

export function getCityById(id) {
  return CITY_BY_ID.get(String(id).toLowerCase()) || null;
}

export function getRoadsForCity(cityId) {
  return EUROPE_ROADS.filter((route) => route.from === cityId || route.to === cityId);
}

export function getConnectedCities(cityId) {
  return getRoadsForCity(cityId)
    .map((route) => getCityById(route.from === cityId ? route.to : route.from))
    .filter(Boolean);
}

export function getCitiesByCountry(countryCode) {
  const code = String(countryCode).toUpperCase();
  return EUROPE_CITIES.filter((city) => city.countryCode === code);
}

export function mapToWorld(cityOrId, scale = 1) {
  const city = typeof cityOrId === "string" ? getCityById(cityOrId) : cityOrId;
  return city ? { x: city.x * scale, y: 0, z: city.z * scale } : null;
}

/** Returns the shortest known route using road distance as its cost. */
export function findShortestRoute(fromId, toId) {
  if (!getCityById(fromId) || !getCityById(toId)) return null;
  const distance = new Map(EUROPE_CITIES.map(({ id }) => [id, Infinity]));
  const previous = new Map();
  const pending = new Set(distance.keys());
  distance.set(fromId, 0);

  while (pending.size) {
    let current = null;
    for (const id of pending) {
      if (current === null || distance.get(id) < distance.get(current)) current = id;
    }
    if (current === toId || distance.get(current) === Infinity) break;
    pending.delete(current);
    for (const route of getRoadsForCity(current)) {
      const next = route.from === current ? route.to : route.from;
      if (!pending.has(next)) continue;
      const candidate = distance.get(current) + route.distanceKm;
      if (candidate < distance.get(next)) {
        distance.set(next, candidate);
        previous.set(next, { city: current, route });
      }
    }
  }

  if (!Number.isFinite(distance.get(toId))) return null;
  const cityIds = [toId];
  const roads = [];
  let cursor = toId;
  while (cursor !== fromId) {
    const step = previous.get(cursor);
    if (!step) return null;
    roads.unshift(step.route);
    cursor = step.city;
    cityIds.unshift(cursor);
  }
  return { cityIds, cities: cityIds.map(getCityById), roads, distanceKm: distance.get(toId) };
}

export default Object.freeze({
  bounds: EUROPE_MAP_BOUNDS,
  landscapes: LANDSCAPE_TYPES,
  cities: EUROPE_CITIES,
  roads: EUROPE_ROADS,
});
