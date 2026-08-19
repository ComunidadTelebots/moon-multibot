const CACHE_PREFIX = "moon.osm.cargo-hubs.v1";
const CACHE_TTL = 7 * 24 * 60 * 60 * 1000;
const ENDPOINTS = ["https://overpass-api.de/api/interpreter", "https://overpass.kumi.systems/api/interpreter"];
const clamp = (value, min, max) => Math.max(min, Math.min(max, value));
const finite = value => Number.isFinite(Number(value)) ? Number(value) : 0;
const hash = value => { let output = 2166136261; for (const char of value) output = Math.imul(output ^ char.charCodeAt(0), 16777619); return output >>> 0; };

/** OSM-backed, route-projected cargo ports, airports and inland freight terminals. */
export function createCargoHubs({ THREE: T, scene, qualityLevel = 2, fetchImpl = globalThis.fetch, endpoint } = {}) {
  if (!T || !scene) throw new Error("THREE and scene are required");
  const root = new T.Group(); root.name = "osm-cargo-hubs"; scene.add(root);
  const geometries = new Set(), materials = new Set();
  let geoRoute = [], worldRoute = [], records = [], requestToken = 0, disposed = false, visibilityTick = 0;
  const limit = qualityLevel <= 0 ? 4 : qualityLevel === 1 ? 8 : 14;

  function material(color, options = {}) { const value = new T.MeshStandardMaterial({ color, roughness: .72, metalness: .08, ...options }); materials.add(value); return value; }
  const palette = {
    asphalt: material(0x30363b), concrete: material(0xaaa89e), steel: material(0x516878, { metalness: .55, roughness: .38 }),
    warehouse: material(0xd4d8d5), glass: material(0x69bcd0, { transparent: true, opacity: .58, roughness: .15 }),
    marking: material(0xf0d852, { emissive: 0x665400, emissiveIntensity: .15 }), water: material(0x267899, { roughness: .24, metalness: .16 }),
  };
  function box(parent, size, mat, position, name) { const geometry = new T.BoxGeometry(...size); geometries.add(geometry); const mesh = new T.Mesh(geometry, mat); mesh.position.set(...position); mesh.name = name; mesh.castShadow = qualityLevel > 0; mesh.receiveShadow = true; parent.add(mesh); return mesh; }
  function cylinder(parent, radius, height, mat, position, name) { const geometry = new T.CylinderGeometry(radius, radius, height, qualityLevel > 1 ? 16 : 8); geometries.add(geometry); const mesh = new T.Mesh(geometry, mat); mesh.position.set(...position); mesh.name = name; mesh.castShadow = qualityLevel > 0; parent.add(mesh); return mesh; }
  function clear() { while (root.children.length) root.remove(root.children[0]); records = []; }
  function normalizeGeo(route) { return (route?.coordinates || route || []).map(point => ({ lon: finite(point.lon ?? point.lng ?? point[0]), lat: finite(point.lat ?? point[1]) })).filter(point => Math.abs(point.lat) <= 90 && Math.abs(point.lon) <= 180); }
  function normalizeWorld(route) { return (route || []).map(point => ({ x: finite(point.x ?? point[0]), y: finite(point.y ?? (point.length > 2 ? point[1] : 0)), z: finite(point.z ?? (point.length > 2 ? point[2] : point[1])) })); }
  function setRoute(geo, world) {
    if (geo && !Array.isArray(geo) && (geo.geoRoute || geo.worldRoute || geo.coordinates)) { world = geo.worldRoute || world; geo = geo.geoRoute || geo.coordinates; }
    geoRoute = normalizeGeo(geo); worldRoute = normalizeWorld(world);
    if (geoRoute.length > 1 && worldRoute.length > 1 && geoRoute.length !== worldRoute.length) worldRoute = geoRoute.map((_, index) => worldRoute[Math.round(index * (worldRoute.length - 1) / (geoRoute.length - 1))]);
    requestToken += 1; clear(); root.visible = geoRoute.length > 1 && worldRoute.length > 1; return root.visible;
  }
  function project(lat, lon) {
    let best = null, elapsed = 0;
    for (let index = 0; index < geoRoute.length - 1; index += 1) {
      const a = geoRoute[index], b = geoRoute[index + 1], latitude = (a.lat + b.lat) * Math.PI / 360;
      const gx = (b.lon - a.lon) * 111320 * Math.cos(latitude), gz = -(b.lat - a.lat) * 110540, px = (lon - a.lon) * 111320 * Math.cos(latitude), pz = -(lat - a.lat) * 110540;
      const length = Math.hypot(gx, gz), t = clamp((px * gx + pz * gz) / (length * length || 1), 0, 1), ox = px - gx * t, oz = pz - gz * t;
      const distance = Math.hypot(ox, oz); if (!best || distance < best.offsetMeters) best = { index, t, gx, gz, ox, oz, offsetMeters: distance, routeMeters: elapsed + length * t }; elapsed += length;
    }
    if (!best || best.offsetMeters > 12000) return null;
    const a = worldRoute[best.index], b = worldRoute[best.index + 1]; if (!a || !b) return null;
    const dx = b.x - a.x, dz = b.z - a.z, worldLength = Math.hypot(dx, dz) || 1, geoLength = Math.hypot(best.gx, best.gz) || 1;
    const side = (best.gx * best.oz - best.gz * best.ox) >= 0 ? 1 : -1, offset = side * clamp(18 + best.offsetMeters * worldLength / geoLength, 18, 54);
    return { x: a.x + dx * best.t - dz / worldLength * offset, y: a.y + (b.y - a.y) * best.t, z: a.z + dz * best.t + dx / worldLength * offset, heading: Math.atan2(dx, dz), routeMeters: best.routeMeters, offsetMeters: best.offsetMeters };
  }
  function classify(tags = {}) {
    if (tags.aeroway === "aerodrome" || tags.aeroway === "terminal" || tags.aerodrome) return "airport";
    if (tags.harbour === "yes" || tags.industrial === "port" || tags.landuse === "port" || tags.seamark?.startsWith?.("harbour")) return "seaport";
    if (tags.railway === "terminal" || tags.railway === "yard" || tags.industrial === "logistics" || tags.landuse === "industrial" && /cargo|freight|logistic/i.test(`${tags.name || ""} ${tags.operator || ""}`)) return "terminal";
    return null;
  }
  function regionalStyle(lat, lon) {
    if (Math.abs(lat) < 24) return { region: "tropical", roof: 0xe6ded0, accent: 0x28b99a };
    if (Math.abs(lat) > 55) return { region: "nordic", roof: 0xa9bcc6, accent: 0x4b8bc4 };
    if (lon > 60 && lat > 20) return { region: "asian", roof: 0xd5d8dc, accent: 0xd84e43 };
    if (lon < -30) return { region: "american", roof: 0xc8c3b8, accent: 0xe39a34 };
    return { region: "temperate", roof: 0xcfc8b7, accent: 0x3ea77a };
  }
  function createWarehouse(parent, style, z = 0) { const wall = material(style.roof), accent = material(style.accent); box(parent, [17, 6, 10], wall, [0, 3.05, z], "freight_warehouse"); for (const x of [-5.6, 0, 5.6]) box(parent, [3.6, 3.4, .16], accent, [x, 1.75, z + 5.08], "loading_bay"); }
  function buildModel(type, style) {
    const group = new T.Group(); group.name = `cargo-hub-${type}`; box(group, [46, .28, 34], palette.concrete, [0, .02, 0], "freight_apron"); createWarehouse(group, style, -7);
    if (type === "airport") { box(group, [8, .12, 46], palette.asphalt, [14, .16, 0], "cargo_runway"); for (let z = -18; z <= 18; z += 6) box(group, [.22, .03, 2.8], palette.marking, [14, .24, z], "runway_marking"); box(group, [10, 4.5, 8], palette.glass, [-13, 2.3, -6], "cargo_terminal"); cylinder(group, .55, 10, palette.steel, [-15, 5, 7], "control_tower"); }
    else if (type === "seaport") { box(group, [13, .12, 34], palette.water, [16, .14, 0], "harbour_basin"); for (const x of [-13, -7, -1, 5]) box(group, [3.6, 2.7, 2.3], material([0xd34b43, 0x3f78bd, 0xe2a83b][Math.abs(x) % 3]), [x, 1.5, 7], "shipping_container"); for (const z of [-10, 2]) { box(group, [.6, 9, .6], palette.steel, [9, 4.6, z], "gantry_crane"); box(group, [8, .45, .45], palette.steel, [12.5, 8.7, z], "crane_boom"); } }
    else { for (const x of [-14, -9, 9, 14]) box(group, [.18, .08, 32], palette.steel, [x, .22, 0], "freight_rail"); for (const x of [-11.5, 11.5]) box(group, [4.2, 2.8, 12], material(style.accent), [x, 1.6, 5], "freight_wagon"); }
    const zoneMat = material(style.accent, { transparent: true, opacity: .38, emissive: style.accent, emissiveIntensity: .18 }); box(group, [8, .08, 8], zoneMat, [0, .23, 11], "cargo_interaction_zone"); return group;
  }
  function addRecord(item, index) {
    const pose = project(item.lat, item.lon); if (!pose) return;
    const style = regionalStyle(item.lat, item.lon), group = buildModel(item.type, style); group.position.set(pose.x, pose.y, pose.z); group.rotation.y = pose.heading; group.userData.streamCenter = { x: pose.x, z: pose.z }; root.add(group);
    records.push({ id: item.id || `hub-${item.type}-${index}`, type: item.type, name: item.name || ({ airport: "Terminal aérea de carga", seaport: "Puerto de carga", terminal: "Terminal intermodal" })[item.type], country: item.country || null, region: style.region, source: item.source || "OpenStreetMap", pose, interactionRadius: 11, group, active: false });
  }
  function fallback() {
    const indexes = [0, Math.floor((geoRoute.length - 1) / 2), geoRoute.length - 1], types = ["terminal", "airport", "seaport"];
    return indexes.map((index, order) => ({ id: `fallback-${types[order]}-${index}`, type: types[order], name: `Centro logístico ${order + 1}`, lat: geoRoute[index].lat, lon: geoRoute[index].lon, source: "procedural-fallback" }));
  }
  function build(data) {
    clear(); const found = [], seen = new Set();
    for (const element of data?.elements || []) { const type = classify(element.tags), lat = Number(element.lat ?? element.center?.lat), lon = Number(element.lon ?? element.center?.lon), id = `${element.type}-${element.id}`; if (!type || !Number.isFinite(lat) || !Number.isFinite(lon) || seen.has(id)) continue; seen.add(id); found.push({ id: `osm-${id}`, type, lat, lon, name: element.tags?.name, country: element.tags?.["addr:country"] || element.tags?.["ISO3166-1"] || null }); }
    (found.length ? found : fallback()).slice(0, limit).forEach(addRecord); root.visible = true; return records;
  }
  function samples() { const count = Math.min(qualityLevel > 1 ? 9 : 5, geoRoute.length); return Array.from({ length: count }, (_, index) => geoRoute[Math.round(index * (geoRoute.length - 1) / Math.max(1, count - 1))]); }
  async function load(geo, world) {
    if (geo) setRoute(geo, world); if (disposed || geoRoute.length < 2 || worldRoute.length < 2) return records;
    const token = ++requestToken, points = samples(), key = `${CACHE_PREFIX}.${hash(points.map(point => `${point.lat.toFixed(2)},${point.lon.toFixed(2)}`).join(";"))}`; let data;
    try { const cached = JSON.parse(globalThis.localStorage?.getItem(key) || "null"); if (cached && Date.now() - cached.at < CACHE_TTL) data = cached.data; } catch {}
    if (!data) { const clauses = points.map(point => `nwr(around:12000,${point.lat},${point.lon})[aeroway=aerodrome];nwr(around:12000,${point.lat},${point.lon})[aeroway=terminal];nwr(around:12000,${point.lat},${point.lon})[harbour=yes];nwr(around:12000,${point.lat},${point.lon})[industrial~"^(port|logistics)$"];nwr(around:12000,${point.lat},${point.lon})[railway~"^(terminal|yard)$"];`).join(""); const query = `[out:json][timeout:22][maxsize:12582912];(${clauses});out center tags qt;`; let failure;
      for (const url of endpoint ? [endpoint] : ENDPOINTS) try { const response = await fetchImpl(`${url}?data=${encodeURIComponent(query)}`, { headers: { Accept: "application/json" } }); if (!response.ok) throw new Error(`Overpass ${response.status}`); data = await response.json(); break; } catch (error) { failure = error; }
      if (!data) data = { elements: [] , fallbackReason: String(failure || "Overpass unavailable") }; else try { globalThis.localStorage?.setItem(key, JSON.stringify({ at: Date.now(), data })); } catch {}
    }
    return disposed || token !== requestToken ? records : build(data);
  }
  function nearest(position, maxDistance = Infinity) { const item = records.map(record => ({ record, distance: Math.hypot(finite(position?.x) - record.pose.x, finite(position?.z) - record.pose.z) })).sort((a, b) => a.distance - b.distance)[0]; return item && item.distance <= maxDistance ? { ...item.record, distance: item.distance } : null; }
  function update(deltaSeconds, context = {}) { visibilityTick -= Math.max(0, finite(deltaSeconds)); if (visibilityTick > 0) return nearest(context.playerPosition || context.camera?.position || {}); visibilityTick = .2; const position = context.playerPosition || context.camera?.position; records.forEach(record => { const distance = position ? Math.hypot(position.x - record.pose.x, position.z - record.pose.z) : 0; record.group.visible = !position || distance < (record.group.visible ? 2400 : 2100); record.active = Boolean(position && distance <= record.interactionRadius); }); return position ? nearest(position) : null; }
  function dispose() { if (disposed) return; disposed = true; requestToken += 1; clear(); geometries.forEach(value => value.dispose()); materials.forEach(value => value.dispose()); geometries.clear(); materials.clear(); root.removeFromParent(); geoRoute = []; worldRoute = []; }
  return { root, setRoute, load, update, nearest, dispose, get records() { return records; } };
}
