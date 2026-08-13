const CACHE_PREFIX = "moon.osm.corridor.v1";
const CACHE_TTL = 7 * 24 * 60 * 60 * 1000;
const OVERPASS_ENDPOINTS = [
  "https://overpass-api.de/api/interpreter",
  "https://overpass.kumi.systems/api/interpreter",
];

const clamp = (value, min, max) => Math.max(min, Math.min(max, value));
const finite = value => Number.isFinite(Number(value)) ? Number(value) : 0;
const hash = value => { let output = 2166136261; for (const char of value) output = Math.imul(output ^ char.charCodeAt(0), 16777619); return output >>> 0; };

/** Generates a bounded Three.js scenery corridor from OpenStreetMap data. */
export function createOsmCorridor({ THREE: T, scene, qualityLevel = 2, endpoint, fetchImpl = globalThis.fetch } = {}) {
  if (!T || !scene) throw new Error("THREE and scene are required");
  const root = new T.Group(); root.name = "osm-route-corridor"; scene.add(root);
  const geometry = new Set(), material = new Set();
  const mats = {
    building: new T.MeshStandardMaterial({ color: 0xb8afa2, roughness: .91, metalness: .01 }),
    roof: new T.MeshStandardMaterial({ color: 0x726b65, roughness: .94 }),
    grass: new T.MeshStandardMaterial({ color: 0x477a3d, roughness: 1 }),
    forest: new T.MeshStandardMaterial({ color: 0x285a32, roughness: 1 }),
    farmland: new T.MeshStandardMaterial({ color: 0x829252, roughness: 1 }),
    water: new T.MeshStandardMaterial({ color: 0x347fa1, roughness: .3, metalness: .05, transparent: true, opacity: .86 }),
    trunk: new T.MeshStandardMaterial({ color: 0x60432c, roughness: 1 }),
    leaves: new T.MeshStandardMaterial({ color: 0x2e6839, roughness: .96 }),
  };
  Object.values(mats).forEach(value => material.add(value));
  let geoRoute = [], worldRoute = [], requestToken = 0, disposed = false, lastData = null, visibilityTick = 0;
  const entities = { buildings: 0, areas: 0, trees: 0 };
  const limits = qualityLevel <= 0
    ? { samples: 3, radius: 450, buildings: 45, areas: 24, trees: 70 }
    : qualityLevel === 1
      ? { samples: 5, radius: 600, buildings: 90, areas: 40, trees: 140 }
      : { samples: 7, radius: 750, buildings: 180, areas: 70, trees: 280 };

  function clear() {
    while (root.children.length) root.remove(root.children[0]);
    geometry.forEach(value => value.dispose()); geometry.clear();
    entities.buildings = entities.areas = entities.trees = 0;
  }

  function normalizeGeo(route) {
    const source = route?.coordinates || route || [];
    return source.map(point => Array.isArray(point)
      ? { lon: finite(point[0]), lat: finite(point[1]) }
      : { lon: finite(point.lon ?? point.lng ?? point.x), lat: finite(point.lat ?? point.y) })
      .filter((point, index, list) => Math.abs(point.lat) <= 90 && Math.abs(point.lon) <= 180 && (!index || point.lat !== list[index - 1].lat || point.lon !== list[index - 1].lon));
  }
  function normalizeWorld(route) {
    return (route || []).map(point => Array.isArray(point)
      ? { x: finite(point[0]), y: finite(point.length > 2 ? point[1] : 0), z: finite(point.length > 2 ? point[2] : point[1]) }
      : { x: finite(point.x), y: finite(point.y), z: finite(point.z) });
  }
  function setRoute(geo, world) {
    if (geo && !Array.isArray(geo) && (geo.geoRoute || geo.worldRoute || geo.coordinates)) {
      world = geo.worldRoute || world; geo = geo.geoRoute || geo.coordinates;
    }
    geoRoute = normalizeGeo(geo); worldRoute = normalizeWorld(world);
    if (geoRoute.length !== worldRoute.length && geoRoute.length > 1 && worldRoute.length > 1) {
      const resized = geoRoute.map((_, index) => worldRoute[Math.round(index * (worldRoute.length - 1) / (geoRoute.length - 1))]);
      worldRoute = resized;
    }
    requestToken += 1; clear(); root.visible = geoRoute.length > 1 && worldRoute.length > 1;
    return root.visible;
  }

  // Projects a nearby OSM coordinate onto the closest geographic route segment,
  // then preserves its lateral metric offset in the matching world segment.
  function project(lat, lon) {
    let best = null;
    for (let index = 0; index < geoRoute.length - 1; index += 1) {
      const a = geoRoute[index], b = geoRoute[index + 1], latitude = (a.lat + b.lat) * Math.PI / 360;
      const gx = (b.lon - a.lon) * 111320 * Math.cos(latitude), gz = -(b.lat - a.lat) * 110540;
      const px = (lon - a.lon) * 111320 * Math.cos(latitude), pz = -(lat - a.lat) * 110540;
      const length2 = gx * gx + gz * gz || 1, t = clamp((px * gx + pz * gz) / length2, 0, 1);
      const ox = px - gx * t, oz = pz - gz * t, distance2 = ox * ox + oz * oz;
      if (!best || distance2 < best.distance2) best = { index, t, ox, oz, gx, gz, distance2 };
    }
    if (!best) return null;
    const wa = worldRoute[best.index], wb = worldRoute[best.index + 1]; if (!wa || !wb) return null;
    const wdx = wb.x - wa.x, wdz = wb.z - wa.z, worldLength = Math.hypot(wdx, wdz) || 1;
    const geoLength = Math.hypot(best.gx, best.gz) || 1, scale = clamp(worldLength / geoLength, .002, 1);
    const signed = (best.gx * best.oz - best.gz * best.ox) / geoLength;
    return { x: wa.x + wdx * best.t - wdz / worldLength * signed * scale, y: wa.y + (wb.y - wa.y) * best.t, z: wa.z + wdz * best.t + wdx / worldLength * signed * scale };
  }

  function shapeFrom(element) {
    const points = (element.geometry || []).map(point => project(point.lat, point.lon)).filter(Boolean);
    if (points.length < 3) return null;
    const shape = new T.Shape(); shape.moveTo(points[0].x, -points[0].z);
    for (let index = 1; index < points.length; index += 1) shape.lineTo(points[index].x, -points[index].z);
    shape.closePath(); return {
      shape,
      y: points.reduce((sum, point) => sum + point.y, 0) / points.length,
      center: points.reduce((sum, point) => ({ x: sum.x + point.x / points.length, z: sum.z + point.z / points.length }), { x: 0, z: 0 }),
    };
  }
  function markStreamable(object, center) {
    object.userData.streamCenter = new T.Vector3(center.x, 0, center.z);
    return object;
  }
  function addArea(element) {
    const result = shapeFrom(element); if (!result) return;
    const type = element.tags?.natural === "water" || element.tags?.water ? "water" : element.tags?.landuse;
    const selected = type === "forest" ? mats.forest : type === "farmland" ? mats.farmland : type === "water" ? mats.water : mats.grass;
    const geo = new T.ShapeGeometry(result.shape); geometry.add(geo);
    const mesh = markStreamable(new T.Mesh(geo, selected), result.center); mesh.rotation.x = -Math.PI / 2; mesh.position.y = result.y + (type === "water" ? .04 : -.04); mesh.receiveShadow = true; root.add(mesh); entities.areas += 1;
  }
  function addBuilding(element, index) {
    const result = shapeFrom(element); if (!result) return;
    const levels = clamp(parseInt(element.tags?.["building:levels"], 10) || (2 + hash(String(element.id)) % 5), 1, 16);
    const height = clamp(parseFloat(element.tags?.height) || levels * 3.05, 2.6, 52);
    const geo = new T.ExtrudeGeometry(result.shape, { depth: height, bevelEnabled: qualityLevel > 1, bevelSize: .08, bevelThickness: .08, bevelSegments: 1 }); geometry.add(geo);
    const mesh = markStreamable(new T.Mesh(geo, [mats.building, mats.roof]), result.center); mesh.rotation.x = -Math.PI / 2; mesh.position.y = result.y; mesh.castShadow = qualityLevel > 0 && index < 70; mesh.receiveShadow = true; root.add(mesh); entities.buildings += 1;
  }
  function addTrees(elements) {
    const points = elements.map(item => project(item.lat, item.lon)).filter(Boolean).slice(0, limits.trees); if (!points.length) return;
    const trunkGeo = new T.CylinderGeometry(.18, .3, 3.2, qualityLevel > 1 ? 7 : 5), crownGeo = new T.IcosahedronGeometry(1.65, qualityLevel > 1 ? 1 : 0); geometry.add(trunkGeo); geometry.add(crownGeo);
    const sectors = new Map(), sectorSize = Math.max(220, limits.radius * .65);
    points.forEach(point => { const key = `${Math.floor(point.x / sectorSize)}:${Math.floor(point.z / sectorSize)}`; if (!sectors.has(key)) sectors.set(key, []); sectors.get(key).push(point); });
    let offset = 0;
    sectors.forEach(sectorPoints => {
      const center = sectorPoints.reduce((sum, point) => ({ x: sum.x + point.x / sectorPoints.length, z: sum.z + point.z / sectorPoints.length }), { x: 0, z: 0 });
      const trunks = markStreamable(new T.InstancedMesh(trunkGeo, mats.trunk, sectorPoints.length), center), crowns = markStreamable(new T.InstancedMesh(crownGeo, mats.leaves, sectorPoints.length), center), dummy = new T.Object3D();
      sectorPoints.forEach((point, index) => { const size = .75 + (hash(String(index + offset)) % 45) / 100; dummy.position.set(point.x, point.y + 1.6 * size, point.z); dummy.scale.set(size, size, size); dummy.rotation.y = (index + offset) * 2.399; dummy.updateMatrix(); trunks.setMatrixAt(index, dummy.matrix); dummy.position.y = point.y + 4.25 * size; dummy.updateMatrix(); crowns.setMatrixAt(index, dummy.matrix); });
      trunks.castShadow = crowns.castShadow = qualityLevel > 1; trunks.receiveShadow = crowns.receiveShadow = true; root.add(trunks, crowns); offset += sectorPoints.length;
    });
    entities.trees = points.length;
  }
  function build(data) {
    clear(); lastData = data;
    const buildings = [], areas = [], trees = [];
    for (const element of data?.elements || []) {
      if (element.type === "node" && element.tags?.natural === "tree") trees.push(element);
      else if (element.type === "way" && element.tags?.building) buildings.push(element);
      else if (element.type === "way" && (element.tags?.landuse || element.tags?.natural === "water" || element.tags?.water)) areas.push(element);
    }
    areas.slice(0, limits.areas).forEach(addArea); buildings.slice(0, limits.buildings).forEach(addBuilding); addTrees(trees);
    root.visible = true; return { ...entities };
  }
  function sampledRoute() {
    const count = Math.min(limits.samples, geoRoute.length), output = [];
    for (let index = 0; index < count; index += 1) output.push(geoRoute[Math.round(index * (geoRoute.length - 1) / Math.max(1, count - 1))]);
    return output;
  }
  function cacheKey(samples) { return `${CACHE_PREFIX}.${hash(samples.map(point => `${point.lat.toFixed(3)},${point.lon.toFixed(3)}`).join(";"))}.${limits.radius}`; }
  async function load() {
    if (disposed || geoRoute.length < 2 || worldRoute.length < 2) return { ...entities };
    const token = ++requestToken, samples = sampledRoute(), key = cacheKey(samples); let data;
    try { const cached = JSON.parse(localStorage.getItem(key) || "null"); if (cached && Date.now() - cached.at < CACHE_TTL) data = cached.data; } catch {}
    if (!data) {
      const around = samples.map(point => `nwr(around:${limits.radius},${point.lat},${point.lon})[building];way(around:${limits.radius},${point.lat},${point.lon})[landuse];way(around:${limits.radius},${point.lat},${point.lon})[natural~"^(wood|water)$"];node(around:${limits.radius},${point.lat},${point.lon})[natural=tree];`).join("");
      const query = `[out:json][timeout:20][maxsize:16777216];(${around});out body geom qt;`;
      let failure;
      for (const url of endpoint ? [endpoint] : OVERPASS_ENDPOINTS) {
        try { const response = await fetchImpl(`${url}?data=${encodeURIComponent(query)}`, { headers: { Accept: "application/json" } }); if (!response.ok) throw new Error(`Overpass ${response.status}`); data = await response.json(); break; } catch (error) { failure = error; }
      }
      if (!data) throw failure || new Error("Overpass unavailable");
      try { localStorage.setItem(key, JSON.stringify({ at: Date.now(), data })); } catch {}
    }
    if (disposed || token !== requestToken) return { ...entities };
    return build(data);
  }
  function update(_deltaSeconds, context = {}) {
    if (Number.isFinite(context.visibilityDistance)) {
      const camera = context.camera?.position || context.playerPosition;
      visibilityTick -= Math.max(0, finite(_deltaSeconds));
      if (camera && visibilityTick <= 0) {
        visibilityTick = .2;
        const enterDistance = context.visibilityDistance, exitDistance = enterDistance * 1.12;
        root.children.forEach(child => {
          const center = child.userData.streamCenter;
          if (!center) return;
          const distance = Math.hypot(center.x - camera.x, center.z - camera.z);
          child.visible = distance <= (child.visible ? exitDistance : enterDistance);
        });
      }
    }
    return entities;
  }
  function dispose() {
    if (disposed) return; disposed = true; requestToken += 1; clear(); material.forEach(value => value.dispose()); material.clear(); root.removeFromParent(); geoRoute = []; worldRoute = []; lastData = null;
  }
  return { root, entities, setRoute, load, update, dispose, get data() { return lastData; } };
}
