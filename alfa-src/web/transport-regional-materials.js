const clamp = (value, min, max) => Math.max(min, Math.min(max, value));
const finite = (value, fallback = 0) => Number.isFinite(Number(value)) ? Number(value) : fallback;
const hash = (value) => {
  let state = 2166136261;
  for (const character of String(value)) state = Math.imul(state ^ character.charCodeAt(0), 16777619);
  return state >>> 0;
};
const randomFactory = (seed) => {
  let state = seed >>> 0;
  return () => ((state = (Math.imul(state, 1664525) + 1013904223) >>> 0) / 4294967296);
};

export const REGIONAL_PROFILES = Object.freeze({
  northern_europe: { terrain: ["#355c37", "#66834d", "#273f31"], vegetation: ["#17472d", "#32633c", "#789052"], facade: "#aeb7b6", roof: "#4f5960", shoulder: "#b4b0a4", sign: "#1765a0", port: "#406d7d", airport: "#727b80" },
  western_europe: { terrain: ["#4d7338", "#7d8e4c", "#4b5633"], vegetation: ["#245b32", "#46753c", "#829653"], facade: "#c0b5a2", roof: "#785b4c", shoulder: "#c3bdb0", sign: "#185f9b", port: "#3c7181", airport: "#777d7e" },
  mediterranean: { terrain: ["#858044", "#9b8b56", "#765b37"], vegetation: ["#486534", "#75834a", "#9b985c"], facade: "#d1b991", roof: "#a45136", shoulder: "#d6c9ad", sign: "#176ca5", port: "#357b91", airport: "#8b8376" },
  eastern_europe: { terrain: ["#557341", "#79844b", "#554c35"], vegetation: ["#285536", "#416b3c", "#77874c"], facade: "#b1a99d", roof: "#64544c", shoulder: "#bbb5a7", sign: "#23669a", port: "#426f7c", airport: "#777b78" },
  north_america: { terrain: ["#6b7640", "#9a854f", "#6a5237"], vegetation: ["#265d35", "#52743a", "#87904d"], facade: "#a8a49b", roof: "#555a5d", shoulder: "#c5bca8", sign: "#257044", port: "#39758a", airport: "#73797a" },
  latin_america: { terrain: ["#657541", "#8b814b", "#704b31"], vegetation: ["#155b34", "#327746", "#6d944c"], facade: "#c9a978", roof: "#9c4f34", shoulder: "#c7b28d", sign: "#247249", port: "#327d91", airport: "#81786d" },
  north_africa_middle_east: { terrain: ["#a78c55", "#c2a567", "#745b3b"], vegetation: ["#45623b", "#76804b", "#9a9558"], facade: "#c9aa78", roof: "#9b835f", shoulder: "#d2b987", sign: "#267953", port: "#397b8c", airport: "#958879" },
  sub_saharan_africa: { terrain: ["#835e36", "#a47b42", "#59482e"], vegetation: ["#315d32", "#63783d", "#8f8d46"], facade: "#b88f63", roof: "#755f4c", shoulder: "#b99d72", sign: "#28724a", port: "#36788a", airport: "#806f60" },
  south_asia: { terrain: ["#766d3d", "#9b854b", "#5c4d32"], vegetation: ["#215c32", "#3b7b40", "#779248"], facade: "#c3a87f", roof: "#7b4e3e", shoulder: "#c3ad87", sign: "#26744c", port: "#397b8d", airport: "#81776b" },
  east_asia: { terrain: ["#526a3d", "#748348", "#554936"], vegetation: ["#1e5531", "#3d733b", "#78904d"], facade: "#b5b1a8", roof: "#555a60", shoulder: "#b9b5aa", sign: "#2671a2", port: "#38758a", airport: "#747b7d" },
  southeast_asia: { terrain: ["#3f7040", "#668e4b", "#55472e"], vegetation: ["#0e5b34", "#267a43", "#65964b"], facade: "#b7a27e", roof: "#76523f", shoulder: "#bcae8c", sign: "#237552", port: "#327c90", airport: "#77766d" },
  oceania: { terrain: ["#6d793f", "#9a8549", "#9a653b"], vegetation: ["#285d38", "#4f7541", "#83904e"], facade: "#b4aa98", roof: "#696563", shoulder: "#c7b89b", sign: "#287047", port: "#39778a", airport: "#807a70" },
  polar: { terrain: ["#bdc8ca", "#e0e5e4", "#87999e"], vegetation: ["#526b60", "#71877a", "#9aa79c"], facade: "#aeb9bc", roof: "#59666c", shoulder: "#d8dddd", sign: "#276e9b", port: "#47788a", airport: "#7e898c" },
});

export const WEATHER_MATERIAL_STATES = Object.freeze({
  clear: { roughnessDelta: 0, metalnessDelta: 0, colorScale: 1, envMapIntensity: 0.8 },
  rain: { roughnessDelta: -0.3, metalnessDelta: 0.03, colorScale: 0.72, envMapIntensity: 1.35 },
  storm: { roughnessDelta: -0.38, metalnessDelta: 0.04, colorScale: 0.58, envMapIntensity: 1.55 },
  fog: { roughnessDelta: 0.08, metalnessDelta: -0.02, colorScale: 0.86, envMapIntensity: 0.45 },
  snow: { roughnessDelta: 0.1, metalnessDelta: -0.03, colorScale: 1.18, envMapIntensity: 1.05 },
  heat: { roughnessDelta: 0.04, metalnessDelta: 0, colorScale: 1.08, envMapIntensity: 0.7 },
});

export function resolveRegion(position = {}) {
  if (typeof position === "string" && REGIONAL_PROFILES[position]) return position;
  const lat = finite(position.lat ?? position.latitude), lon = finite(position.lon ?? position.lng ?? position.longitude);
  if (Math.abs(lat) >= 66) return "polar";
  if (lat >= 15 && lat <= 72 && lon >= -170 && lon <= -50) return "north_america";
  if (lat < 15 && lat > -60 && lon >= -120 && lon <= -30) return "latin_america";
  if (lat >= 35 && lat <= 72 && lon >= -12 && lon <= 45) {
    if (lat >= 56) return "northern_europe";
    if (lat <= 44 && lon <= 30) return "mediterranean";
    return lon >= 15 ? "eastern_europe" : "western_europe";
  }
  if (lat >= 12 && lat <= 38 && lon >= -18 && lon <= 62) return "north_africa_middle_east";
  if (lat < 15 && lat > -38 && lon >= -20 && lon <= 55) return "sub_saharan_africa";
  if (lat >= 5 && lat <= 38 && lon > 62 && lon <= 92) return "south_asia";
  if (lat >= 18 && lat <= 55 && lon > 92 && lon <= 150) return "east_asia";
  if (lat > -12 && lat < 25 && lon > 92 && lon <= 150) return "southeast_asia";
  if (lat <= -10 && lon >= 105 && lon <= 180) return "oceania";
  return lat >= 0 ? "north_america" : "oceania";
}

export const ENVIRONMENT_ATLAS_URL = "./generated-textures/world-environment-material-atlas-v1.png";
export const ENVIRONMENT_TEXTURE_URLS = Object.freeze(Object.fromEntries([
  "terrain", "soil", "rock", "snow", "sand", "shoulder", "concrete", "brick",
  "architecture", "masonry", "roof", "timber", "vegetation", "industrial-floor", "port", "airport",
  "cobblestone", "cracked-asphalt", "tropical-mud", "forest-floor", "autumn-leaves", "crop-field",
  "dry-grass", "volcanic-rock", "rail-ballast", "platform-paving", "corrugated-metal", "painted-plaster",
  "glass-facade", "ceramic-roof", "water", "ice",
  "adobe", "sandstone", "limestone", "granite-masonry", "timber-siding", "bamboo", "breeze-block",
  "painted-metal", "asphalt-shingles", "thatch-roof", "zinc-roof", "copper-roof", "tunnel-concrete",
  "drainage-grate", "winter-slush", "red-clay",
].map(name => [name === "industrial-floor" ? "industrialFloor" : name, `./generated-textures/environment-${name}-v1.png`])));
export const ENVIRONMENT_ATLAS_TILES = Object.freeze({
  terrain: [0, 0], soil: [1, 0], rock: [2, 0], snow: [3, 0],
  sand: [0, 1], shoulder: [1, 1], concrete: [2, 1], brick: [3, 1],
  architecture: [0, 2], masonry: [1, 2], roof: [2, 2], timber: [3, 2],
  vegetation: [0, 3], industrialFloor: [1, 3], port: [2, 3], airport: [3, 3],
});

export function environmentAtlasTransform(name) {
  const tile = ENVIRONMENT_ATLAS_TILES[name];
  if (!tile) return null;
  return { repeat: [.25, .25], offset: [tile[0] * .25, .75 - tile[1] * .25] };
}

export function createMaterials({ THREE: T, region, coordinates, qualityLevel = 2, seed = "moon-world" } = {}) {
  if (!T) throw new Error("THREE is required");
  const regionId = resolveRegion(region || coordinates || {}), profile = REGIONAL_PROFILES[regionId];
  const quality = clamp(Math.floor(finite(qualityLevel, 2)), 0, 3), size = [128, 256, 512, 1024][quality];
  const textures = [], materials = {}, authored = quality >= 2;
  const texture = (name, palette, pattern = "noise", { color = true, repeat = null } = {}) => {
    const canvas = document.createElement("canvas"); canvas.width = canvas.height = size;
    const context = canvas.getContext("2d", { alpha: false }), random = randomFactory(hash(`${seed}:${regionId}:${name}`));
    context.fillStyle = palette[0]; context.fillRect(0, 0, size, size);
    const count = size * (quality + 3);
    for (let index = 0; index < count; index += 1) {
      context.globalAlpha = .12 + random() * .28; context.fillStyle = palette[1 + ((random() * (palette.length - 1)) | 0)] || palette[0];
      const x = random() * size, y = random() * size;
      if (pattern === "facade") context.fillRect(x, y, 1 + random() * 4, 2 + random() * 8);
      else if (pattern === "roof") context.fillRect(x, y, 5 + random() * 15, 1 + random() * 3);
      else if (pattern === "marking") context.fillRect(x, y, 1 + random() * 2, 12 + random() * 30);
      else context.fillRect(x, y, .5 + random() * 2.5, .5 + random() * 2.5);
    }
    context.globalAlpha = 1;
    const output = new T.CanvasTexture(canvas); output.name = `regional_${regionId}_${name}`;
    output.wrapS = output.wrapT = T.RepeatWrapping;
    const repetitions = repeat || (name === "terrain" ? [16, 16] : [3, 3]); output.repeat.set(...repetitions);
    if (color && T.SRGBColorSpace) output.colorSpace = T.SRGBColorSpace;
    else if (!color && T.NoColorSpace) output.colorSpace = T.NoColorSpace;
    output.anisotropy = [1, 2, 8, 16][quality]; output.generateMipmaps = quality > 0; textures.push(output); return output;
  };
  const detail = (name, repeat) => texture(`${name}_detail`, ["#777", "#999", "#555"], "noise", { color: false, repeat });
  const make = (name, color, map, options = {}) => {
    const { detailMap, bumpScale = .025, ...parameters } = options;
    materials[name] = new T.MeshStandardMaterial({ color, map, roughness: parameters.roughness ?? .88, metalness: parameters.metalness ?? .02, ...parameters });
    if (detailMap) { materials[name].roughnessMap = detailMap; materials[name].bumpMap = detailMap; materials[name].bumpScale = bumpScale; }
    return materials[name];
  };
  const generated = (name, palette, pattern, options) => authored ? null : texture(name, palette, pattern, options);
  const generatedDetail = (name, repeat) => authored ? null : detail(name, repeat);
  make("asphalt", "#34373a", generated("asphalt", ["#34373a", "#202326", "#62605a"], "noise", { repeat: [3, 48] }), { roughness: .93, detailMap: generatedDetail("asphalt", [3, 48]), bumpScale: .035 });
  make("terrain", profile.terrain[0], generated("terrain", profile.terrain), { roughness: .98, detailMap: generatedDetail("terrain", [16, 16]), bumpScale: .07 });
  make("vegetation", profile.vegetation[0], generated("vegetation", profile.vegetation), { roughness: .96, detailMap: generatedDetail("vegetation", [4, 4]), bumpScale: .045 });
  make("architecture", profile.facade, generated("architecture", [profile.facade, "#766f65", "#e1d7c5"], "facade"), { detailMap: generatedDetail("architecture", [3, 3]), bumpScale: .035 });
  make("roof", profile.roof, generated("roof", [profile.roof, "#3d4142", "#a27c5c"], "roof"), { roughness: .92, detailMap: generatedDetail("roof", [4, 4]), bumpScale: .045 });
  make("shoulder", profile.shoulder, generated("shoulder", [profile.shoulder, "#77736b", "#ddd7c9"], "marking", { repeat: [5, 32] }), { roughness: .96, detailMap: generatedDetail("shoulder", [5, 32]), bumpScale: .025 });
  make("soil", profile.terrain[2], generated("soil", [profile.terrain[2], profile.terrain[1], "#43372b"], "noise", { repeat: [12, 12] }), { roughness: 1, detailMap: generatedDetail("soil", [12, 12]), bumpScale: .09 });
  make("sand", "#b99b68", generated("sand", ["#b99b68", "#d2b77f", "#806a49"], "noise", { repeat: [12, 12] }), { roughness: 1, detailMap: generatedDetail("sand", [12, 12]), bumpScale: .06 });
  make("rock", profile.shoulder, generated("rock", [profile.shoulder, "#686761", "#a7a49a"], "noise", { repeat: [8, 8] }), { roughness: .97, detailMap: generatedDetail("rock", [8, 8]), bumpScale: .11 });
  make("concrete", "#8c8b84", generated("concrete", ["#8c8b84", "#5e605e", "#b5b2aa"], "noise", { repeat: [6, 6] }), { roughness: .94, detailMap: generatedDetail("concrete", [6, 6]), bumpScale: .035 });
  make("brick", "#8f4f3c", generated("brick", ["#8f4f3c", "#5e332b", "#c28b71"], "roof", { repeat: [6, 6] }), { roughness: .93, detailMap: generatedDetail("brick", [6, 6]), bumpScale: .055 });
  make("sign", profile.sign, generated("sign", [profile.sign, "#f2f5ee", "#123b55"], "marking"), { roughness: .45, metalness: .12 });
  make("port", profile.port, generated("port", [profile.port, "#263a41", "#b6c0c0"], "facade"), { roughness: .64, metalness: .28 });
  make("airport", profile.airport, generated("airport", [profile.airport, "#2f3538", "#d8d8cf"], "marking"), { roughness: .7, metalness: .08 });
  // Verified gaps: operational interiors, exposed timber/masonry and regional fleet
  // finishes were previously forced through the generic facade/port materials.
  make("industrialFloor", "#747a7b", generated("industrial_floor", ["#747a7b", "#3e4548", "#a5a6a0"], "marking", { repeat: [8, 20] }), { roughness: .82, metalness: .05, detailMap: generatedDetail("industrial_floor", [8, 20]), bumpScale: .028 });
  make("masonry", profile.facade, generated("masonry", [profile.facade, profile.roof, "#d8cdbb"], "roof", { repeat: [5, 5] }), { roughness: .94, detailMap: generatedDetail("masonry", [5, 5]), bumpScale: .075 });
  make("timber", "#76583e", generated("timber", ["#76583e", "#3f3025", "#aa8058"], "roof", { repeat: [2, 7] }), { roughness: .84, detailMap: generatedDetail("timber", [2, 7]), bumpScale: .045 });
  make("vehicleBody", profile.sign, generated("vehicle_body", [profile.sign, "#e6eceb", "#28343a"], "noise", { repeat: [1, 1] }), { roughness: .34, metalness: .22, detailMap: generatedDetail("vehicle_body", [1, 1]), bumpScale: .008 });
  make("snow", "#dce5e6", generated("snow", ["#dce5e6", "#f4f6f3", "#aebfc2"], "noise", { repeat: [10, 10] }), { roughness: .98, detailMap: generatedDetail("snow", [10, 10]), bumpScale: .12 });
  const authoredOnly = (name, color, roughness, metalness = .01, options = {}) => make(name, color, null, { roughness, metalness, ...options });
  authoredOnly("cobblestone", "#777873", .94);
  authoredOnly("cracked-asphalt", "#303235", .95);
  authoredOnly("tropical-mud", "#59483c", .72);
  authoredOnly("forest-floor", "#514536", .98);
  authoredOnly("autumn-leaves", "#76543a", .96);
  authoredOnly("crop-field", "#587342", .97);
  authoredOnly("dry-grass", "#938363", .98);
  authoredOnly("volcanic-rock", "#303337", .91);
  authoredOnly("rail-ballast", "#777977", .97);
  authoredOnly("platform-paving", "#92928d", .91);
  authoredOnly("corrugated-metal", "#7f898c", .58, .38);
  authoredOnly("painted-plaster", "#d1c8b6", .89);
  authoredOnly("glass-facade", "#7899a8", .16, .2, { envMapIntensity: 1.35 });
  authoredOnly("ceramic-roof", "#a95336", .84);
  authoredOnly("water", "#285d6a", .12, .04, { transparent: true, opacity: .9, envMapIntensity: 1.5 });
  authoredOnly("ice", "#b7ced7", .24, .02, { transparent: true, opacity: .92, envMapIntensity: 1.3 });
  authoredOnly("adobe", "#b99161", .97);
  authoredOnly("sandstone", "#b88e5a", .92);
  authoredOnly("limestone", "#c9c2ad", .91);
  authoredOnly("granite-masonry", "#777a78", .94);
  authoredOnly("timber-siding", "#75604d", .87);
  authoredOnly("bamboo", "#a88955", .83);
  authoredOnly("breeze-block", "#878781", .96);
  authoredOnly("painted-metal", "#82958d", .52, .28);
  authoredOnly("asphalt-shingles", "#3d4145", .91);
  authoredOnly("thatch-roof", "#9b835b", .98);
  authoredOnly("zinc-roof", "#858c8e", .56, .42);
  authoredOnly("copper-roof", "#628b82", .48, .45);
  authoredOnly("tunnel-concrete", "#676762", .96);
  authoredOnly("drainage-grate", "#555957", .6, .65);
  authoredOnly("winter-slush", "#a6aaa6", .76);
  authoredOnly("red-clay", "#9d5837", .98);

  let disposed = false;
  const authoredRepeats = { terrain: [16, 16], vegetation: [5, 5], architecture: [3, 3], roof: [5, 5], shoulder: [5, 32], soil: [12, 12], sand: [12, 12], rock: [8, 8], concrete: [6, 6], brick: [6, 6], port: [4, 4], airport: [6, 18], industrialFloor: [8, 20], masonry: [5, 5], timber: [3, 8], snow: [10, 10], cobblestone: [10, 10], "cracked-asphalt": [4, 32], "tropical-mud": [12, 12], "forest-floor": [12, 12], "autumn-leaves": [10, 10], "crop-field": [10, 10], "dry-grass": [14, 14], "volcanic-rock": [9, 9], "rail-ballast": [8, 24], "platform-paving": [8, 18], "corrugated-metal": [5, 8], "painted-plaster": [4, 4], "glass-facade": [3, 5], "ceramic-roof": [5, 8], water: [8, 18], ice: [10, 10], adobe: [5, 5], sandstone: [5, 5], limestone: [5, 5], "granite-masonry": [5, 5], "timber-siding": [4, 6], bamboo: [4, 6], "breeze-block": [5, 5], "painted-metal": [5, 7], "asphalt-shingles": [5, 8], "thatch-roof": [5, 7], "zinc-roof": [5, 8], "copper-roof": [5, 8], "tunnel-concrete": [6, 12], "drainage-grate": [4, 10], "winter-slush": [5, 24], "red-clay": [12, 12] };
  const ready = authored ? Promise.all(Object.entries(authoredRepeats).map(([name, repetitions]) => new Promise((resolve) => {
    const url = ENVIRONMENT_TEXTURE_URLS[name];
    if (!url || !materials[name]) { resolve(false); return; }
    new T.TextureLoader().load(url, (map) => {
      if (disposed) { map.dispose(); resolve(false); return; }
      map.name = `authored_environment_${name}`; map.wrapS = map.wrapT = T.RepeatWrapping;
      map.repeat.set(...repetitions); map.anisotropy = [1, 2, 8, 16][quality];
      if (T.SRGBColorSpace) map.colorSpace = T.SRGBColorSpace;
      map.needsUpdate = true; textures.push(map); materials[name].map = map; materials[name].needsUpdate = true; resolve(true);
    }, undefined, () => resolve(false));
  }))).then(results => results.every(Boolean)) : Promise.resolve(true);

  function materialFor(object) {
    const label = `${object.name || ""} ${object.userData?.surface || ""} ${object.userData?.regionalSurface || ""}`.toLowerCase();
    if (/vehicle_body|fleet_body|regional_vehicle|service_vehicle_body/.test(label)) return materials.vehicleBody;
    if (/slush|salted_snow|winter_road/.test(label)) return materials["winter-slush"];
    if (/snow|ice_bank|snowbank/.test(label)) return materials.snow;
    if (/frozen_lake|ice_sheet|glacier|black_ice/.test(label)) return materials.ice;
    if (/water|river|lake|canal|ocean|sea_surface/.test(label)) return materials.water;
    if (/glass_facade|curtain_wall|office_glass/.test(label)) return materials["glass-facade"];
    if (/ceramic_roof|terracotta|roof_tile/.test(label)) return materials["ceramic-roof"];
    if (/corrugated|sheet_metal|metal_cladding/.test(label)) return materials["corrugated-metal"];
    if (/painted_plaster|rendered_wall|stucco/.test(label)) return materials["painted-plaster"];
    if (/rail_ballast|railway_bed|track_bed/.test(label)) return materials["rail-ballast"];
    if (/platform_paving|station_platform/.test(label)) return materials["platform-paving"];
    if (/cobble|sett_paving|historic_paving/.test(label)) return materials.cobblestone;
    if (/cracked_asphalt|patched_asphalt|worn_tarmac/.test(label)) return materials["cracked-asphalt"];
    if (/tropical_mud|mud_track|muddy_ground/.test(label)) return materials["tropical-mud"];
    if (/forest_floor|woodland_ground|pine_needles/.test(label)) return materials["forest-floor"];
    if (/autumn_leaves|leaf_litter/.test(label)) return materials["autumn-leaves"];
    if (/crop_field|cropland|plantation|cultivated/.test(label)) return materials["crop-field"];
    if (/dry_grass|savanna|steppe/.test(label)) return materials["dry-grass"];
    if (/volcanic|basalt|lava_field/.test(label)) return materials["volcanic-rock"];
    if (/adobe|mud_brick|earthen_wall/.test(label)) return materials.adobe;
    if (/sandstone/.test(label)) return materials.sandstone;
    if (/limestone/.test(label)) return materials.limestone;
    if (/granite_masonry|granite_wall/.test(label)) return materials["granite-masonry"];
    if (/timber_siding|wood_cladding|weatherboard/.test(label)) return materials["timber-siding"];
    if (/bamboo|cane_wall/.test(label)) return materials.bamboo;
    if (/breeze_block|vent_block/.test(label)) return materials["breeze-block"];
    if (/painted_metal|metal_panel|industrial_cladding/.test(label)) return materials["painted-metal"];
    if (/asphalt_shingle/.test(label)) return materials["asphalt-shingles"];
    if (/thatch|thatched/.test(label)) return materials["thatch-roof"];
    if (/zinc_roof|galvanized_roof/.test(label)) return materials["zinc-roof"];
    if (/copper_roof|verdigris/.test(label)) return materials["copper-roof"];
    if (/tunnel_concrete|tunnel_lining|underpass_wall/.test(label)) return materials["tunnel-concrete"];
    if (/drain|grate|gully/.test(label)) return materials["drainage-grate"];
    if (/red_clay|laterite|clay_road/.test(label)) return materials["red-clay"];
    if (/hangar_floor|warehouse_floor|station_floor|garage_floor|industrial_floor/.test(label)) return materials.industrialFloor;
    if (/brick/.test(label)) return materials.brick;
    if (/masonry|stone_wall/.test(label)) return materials.masonry;
    if (/timber|wood|wooden/.test(label)) return materials.timber;
    if (/airport|runway|taxiway|hangar|apron/.test(label)) return materials.airport;
    if (/port|harbour|harbor|dock|quay|terminal|crane/.test(label)) return materials.port;
    if (/sign|gantry|bollard/.test(label)) return materials.sign;
    if (/road|asphalt|tarmac/.test(label)) return materials.asphalt;
    if (/concrete|cement|retaining_wall/.test(label)) return materials.concrete;
    if (/shoulder|kerb|curb|pavement|sidewalk|footway/.test(label)) return materials.shoulder;
    if (/mountain|rock|cliff|stone/.test(label)) return materials.rock;
    if (/sand|dune|beach|desert/.test(label)) return materials.sand;
    if (/soil|earth|dirt/.test(label)) return materials.soil;
    if (/roof|parapet/.test(label)) return materials.roof;
    if (/building|facade|architecture|warehouse/.test(label)) return materials.architecture;
    if (/tree|leaf|leaves|forest|hedge|vegetation/.test(label)) return materials.vegetation;
    if (/terrain|ground|grass|field|farmland|park|garden/.test(label)) return materials.terrain;
    return null;
  }
  const weatherBase = new Map(Object.values(materials).map(material => [material, {
    color: material.color.clone(), roughness: material.roughness, metalness: material.metalness,
    envMapIntensity: material.envMapIntensity ?? 1,
  }]));
  function applyWeather(state = "clear", intensity = 1) {
    const preset = WEATHER_MATERIAL_STATES[state] || WEATHER_MATERIAL_STATES.clear;
    const amount = clamp(finite(intensity, 1), 0, 1);
    for (const material of Object.values(materials)) {
      const base = weatherBase.get(material); if (!base) continue;
      material.color.copy(base.color).multiplyScalar(1 + (preset.colorScale - 1) * amount);
      material.roughness = clamp(base.roughness + preset.roughnessDelta * amount, .08, 1);
      material.metalness = clamp(base.metalness + preset.metalnessDelta * amount, 0, 1);
      material.envMapIntensity = base.envMapIntensity + (preset.envMapIntensity - base.envMapIntensity) * amount;
      material.needsUpdate = true;
    }
    return { state: WEATHER_MATERIAL_STATES[state] ? state : "clear", intensity: amount };
  }
  function applyTo(target, { clone = false } = {}) {
    let applied = 0;
    target?.traverse?.((object) => {
      if (!object.isMesh) return;
      if (Array.isArray(object.material) && /building/.test(`${object.name} ${object.userData?.regionalSurface || ""}`.toLowerCase())) {
        object.material = object.material.map((_, index) => index === 1 ? materials.roof : materials.architecture); applied += 1; return;
      }
      const selected = materialFor(object); if (!selected) return;
      object.material = clone ? selected.clone() : selected; object.material.needsUpdate = true; applied += 1;
    });
    return applied;
  }
  function dispose() { disposed = true; textures.forEach(value => value.dispose()); Object.values(materials).forEach(value => value.dispose()); }
  return { region: regionId, profile, qualityLevel: quality, authored, ready, materials, maps: { asphalt: materials.asphalt, shoulder: materials.shoulder, ground: materials.terrain, sand: materials.sand, concrete: materials.concrete, brick: materials.brick, industrialFloor: materials.industrialFloor, masonry: materials.masonry, timber: materials.timber, vehicleBody: materials.vehicleBody, snow: materials.snow, water: materials.water, ice: materials.ice, railBallast: materials["rail-ballast"], cobblestone: materials.cobblestone }, applyTo, applyWeather, dispose };
}

export default { REGIONAL_PROFILES, WEATHER_MATERIAL_STATES, ENVIRONMENT_ATLAS_URL, ENVIRONMENT_TEXTURE_URLS, ENVIRONMENT_ATLAS_TILES, environmentAtlasTransform, resolveRegion, createMaterials };
