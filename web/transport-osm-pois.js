const CACHE_PREFIX = "moon.osm.route-pois.v1";
const CACHE_TTL = 7 * 24 * 60 * 60 * 1000;
const ENDPOINTS = ["https://overpass-api.de/api/interpreter", "https://overpass.kumi.systems/api/interpreter"];
const clamp = (value, min, max) => Math.max(min, Math.min(max, value));
const hash = value => { let result = 2166136261; for (const char of value) result = Math.imul(result ^ char.charCodeAt(0), 16777619); return result >>> 0; };

/** Loads real roadside POIs from OSM and projects them beside the rendered route. */
export function createOsmRoutePois({ THREE: T, scene, qualityLevel = 2, fetchImpl = globalThis.fetch, endpoint } = {}) {
  if (!T || !scene) throw new Error("THREE and scene are required");
  const root = new T.Group(); root.name = "osm-route-pois"; scene.add(root);
  const geometries = [new T.CylinderGeometry(.14, .2, 3.2, 8), new T.BoxGeometry(2.5, 1.25, .18)];
  const colors = { fuel: 0x43d9c2, charging: 0x58a9ff, rest: 0x8eb7ff, workshop: 0xf1ad45 };
  const materials = Object.fromEntries(Object.entries(colors).map(([type, color]) => [type, new T.MeshStandardMaterial({ color, emissive: color, emissiveIntensity: .22, roughness: .5 })]));
  let records = [], requestToken = 0, disposed = false;

  function clear() { while (root.children.length) root.remove(root.children[0]); records = []; }
  function normalizeGeo(route) { return (route?.coordinates || route || []).map(point => ({ lon: Number(point.lon ?? point.lng ?? point[0]), lat: Number(point.lat ?? point[1]) })).filter(point => Number.isFinite(point.lon) && Number.isFinite(point.lat)); }
  function normalizeWorld(route) { return (route || []).map(point => ({ x: Number(point.x ?? point[0]), y: Number(point.y ?? point[1] ?? 0), z: Number(point.z ?? point[2] ?? point[1]) })); }
  function classify(tags = {}) {
    if (tags.amenity === "fuel") return "fuel";
    if (tags.amenity === "charging_station") return "charging";
    if (tags.shop === "car_repair" || tags.shop === "truck_repair") return "workshop";
    if (tags.amenity === "parking" || tags.highway === "rest_area" || tags.highway === "services") return "rest";
    return null;
  }
  function samples(route) {
    const count = Math.min(qualityLevel > 1 ? 9 : 5, route.length), output = [];
    for (let index = 0; index < count; index += 1) output.push(route[Math.round(index * (route.length - 1) / Math.max(1, count - 1))]);
    return output;
  }
  function project(lat, lon, geo, world) {
    let best = null, elapsed = 0;
    for (let index = 0; index < geo.length - 1; index += 1) {
      const a = geo[index], b = geo[index + 1], latitude = (a.lat + b.lat) * Math.PI / 360;
      const gx = (b.lon - a.lon) * 111320 * Math.cos(latitude), gz = -(b.lat - a.lat) * 110540;
      const px = (lon - a.lon) * 111320 * Math.cos(latitude), pz = -(lat - a.lat) * 110540;
      const length = Math.hypot(gx, gz), length2 = length * length || 1, t = clamp((px * gx + pz * gz) / length2, 0, 1);
      const ox = px - gx * t, oz = pz - gz * t, distance = Math.hypot(ox, oz);
      if (!best || distance < best.offsetMeters) best = { index, t, gx, gz, ox, oz, offsetMeters: distance, routeMeters: elapsed + length * t };
      elapsed += length;
    }
    if (!best || best.offsetMeters > 650) return null;
    const a = world[best.index], b = world[best.index + 1]; if (!a || !b) return null;
    const dx = b.x - a.x, dz = b.z - a.z, worldLength = Math.hypot(dx, dz) || 1, geoLength = Math.hypot(best.gx, best.gz) || 1;
    const signed = (best.gx * best.oz - best.gz * best.ox) / geoLength, scale = clamp(worldLength / geoLength, .002, 1);
    return { x: a.x + dx * best.t - dz / worldLength * signed * scale, y: a.y + (b.y - a.y) * best.t, z: a.z + dz * best.t + dx / worldLength * signed * scale, distance: best.routeMeters, offsetMeters: best.offsetMeters, heading: Math.atan2(dx, dz) };
  }
  function build(data, geo, world) {
    clear(); const seen = new Set();
    for (const element of data?.elements || []) {
      const type = classify(element.tags), lat = Number(element.lat ?? element.center?.lat), lon = Number(element.lon ?? element.center?.lon);
      if (!type || !Number.isFinite(lat) || !Number.isFinite(lon) || seen.has(`${type}:${element.id}`)) continue;
      const pose = project(lat, lon, geo, world); if (!pose) continue; seen.add(`${type}:${element.id}`);
      const group = new T.Group(), mast = new T.Mesh(geometries[0], materials[type]), sign = new T.Mesh(geometries[1], materials[type]);
      mast.position.y = 1.6; sign.position.y = 3.55; group.add(mast, sign); group.position.set(pose.x, pose.y, pose.z); group.rotation.y = pose.heading; group.name = `osm_poi_${type}_${element.id}`; root.add(group);
      records.push({ id: `osm-${element.type}-${element.id}`, type, name: element.tags?.name || element.tags?.brand || null, pose, distance: pose.distance, offsetMeters: pose.offsetMeters, group, source: "OpenStreetMap" });
      if (records.length >= (qualityLevel > 1 ? 48 : 24)) break;
    }
    return records;
  }
  async function load(route, worldRoute) {
    const geo = normalizeGeo(route), world = normalizeWorld(worldRoute); clear();
    if (disposed || geo.length < 2 || geo.length !== world.length) return records;
    const token = ++requestToken, points = samples(geo), key = `${CACHE_PREFIX}.${hash(points.map(p => `${p.lat.toFixed(3)},${p.lon.toFixed(3)}`).join(";"))}`; let data;
    try { const cached = JSON.parse(localStorage.getItem(key) || "null"); if (cached && Date.now() - cached.at < CACHE_TTL) data = cached.data; } catch {}
    if (!data) {
      const clauses = points.map(p => `nwr(around:1800,${p.lat},${p.lon})[amenity~"^(fuel|charging_station|parking)$"];nwr(around:1800,${p.lat},${p.lon})[highway~"^(rest_area|services)$"];nwr(around:1800,${p.lat},${p.lon})[shop~"^(car_repair|truck_repair)$"];`).join("");
      const query = `[out:json][timeout:18][maxsize:8388608];(${clauses});out center tags qt;`; let failure;
      for (const url of endpoint ? [endpoint] : ENDPOINTS) { try { const response = await fetchImpl(`${url}?data=${encodeURIComponent(query)}`, { headers: { Accept: "application/json" } }); if (!response.ok) throw new Error(`Overpass ${response.status}`); data = await response.json(); break; } catch (error) { failure = error; } }
      if (!data) throw failure || new Error("Overpass unavailable");
      try { localStorage.setItem(key, JSON.stringify({ at: Date.now(), data })); } catch {}
    }
    return disposed || token !== requestToken ? records : build(data, geo, world);
  }
  function nearest(position) { return records.map(item => ({ ...item, distance: Math.hypot(position.x - item.pose.x, position.z - item.pose.z) })).sort((a, b) => a.distance - b.distance)[0] || null; }
  function dispose() { disposed = true; requestToken += 1; clear(); geometries.forEach(value => value.dispose()); Object.values(materials).forEach(value => value.dispose()); root.removeFromParent(); }
  return { root, load, nearest, dispose, get records() { return records; } };
}
