const FLEET_TILES = { paint: [0, 0], commercial: [1, 0], escort: [0, 1], tyre: [1, 1] };
const WORK_TILES = { machinery: [0, 0], chevron: [1, 0], heavySteel: [0, 1], utility: [1, 1] };

function loadAtlas(T, url, tiles, qualityLevel) {
  const output = {};
  return new Promise((resolve, reject) => new T.TextureLoader().load(url, source => {
    const size = Math.floor(Math.min(source.image.width, source.image.height) / 2);
    for (const [name, [column, row]] of Object.entries(tiles)) {
      const canvas = document.createElement("canvas"); canvas.width = canvas.height = size;
      canvas.getContext("2d", { alpha: false }).drawImage(source.image, column * size, row * size, size, size, 0, 0, size, size);
      const texture = new T.CanvasTexture(canvas); texture.name = `vehicle_${name}`; texture.colorSpace = T.SRGBColorSpace;
      texture.wrapS = texture.wrapT = T.RepeatWrapping; texture.repeat.set(1.4, 1.4); texture.anisotropy = qualityLevel >= 3 ? 16 : qualityLevel >= 2 ? 8 : 2;
      output[name] = texture;
    }
    source.dispose(); resolve(output);
  }, undefined, reject));
}

export function createVehicleTextureSystem({ THREE: T, qualityLevel = 2, fleetAtlasUrl, maintenanceAtlasUrl }) {
  const textures = {};
  const ready = Promise.all([
    loadAtlas(T, fleetAtlasUrl, FLEET_TILES, qualityLevel),
    loadAtlas(T, maintenanceAtlasUrl, WORK_TILES, qualityLevel),
  ]).then(([fleet, work]) => Object.assign(textures, fleet, work));
  const applied = new WeakMap();
  const ancestor = (object, predicate) => { for (let node = object; node; node = node.parent) if (predicate(node)) return node; return null; };
  const textureFor = object => {
    const name = String(object.name || "").toLowerCase();
    const semantic = object.material?.userData?.vehicleSurface;
    if (semantic && textures[semantic]) return textures[semantic];
    if (/tyre|wheel/.test(name) && !/steering/.test(name)) return textures.tyre;
    if (/crawler|track_pad|hydraulic_hose/.test(name)) return textures.heavySteel;
    if (/excavator|mining_machine|operator_body|boom/.test(name)) return textures.machinery;
    if (/escort_vehicle|wide_load_banner|warning_edge/.test(name)) return textures.escort;
    if (/hydraulic|platform|gooseneck|generator|transformer|pressure_chamber/.test(name)) return textures.utility;
    if (ancestor(object, node => node.name === "roadwork_excavator")) return object.material?.transparent ? null : object.material?.color?.getHex() === 0xf5c542 ? textures.machinery : textures.heavySteel;
    if (ancestor(object, node => node.name === "police_vehicle")) return object.material?.transparent ? null : textures.escort;
    if (ancestor(object, node => node.name === "accident_vehicle")) return object.material?.transparent ? null : textures.paint;
    if (ancestor(object, node => node.name === "roadside_recovery_truck" || node.name === "mobile_control_vehicle")) return /wheel|tyre/.test(name) ? textures.tyre : textures.machinery;
    if (ancestor(object, node => node.name === "ambulance_vehicle")) return /wheel|tyre/.test(name) ? textures.tyre : textures.commercial;
    if (ancestor(object, node => node.name === "fire_engine_vehicle")) return /wheel|tyre/.test(name) ? textures.tyre : textures.utility;
    const traffic = ancestor(object, node => node.name === "detailed_traffic_vehicle");
    if (traffic && /body|hood|roof|bumper/.test(name)) return traffic.userData.vehicleType === "sedan" ? textures.paint : textures.commercial;
    return null;
  };
  function apply(root) {
    if (!root || !Object.keys(textures).length) return;
    root.traverse(object => {
      if (!object.isMesh || !object.material || object.material.transparent || object.material.isMeshBasicMaterial) return;
      const texture = textureFor(object); if (!texture) return;
      const previous = applied.get(object); if (previous === texture) return;
      object.material = object.material.clone(); object.material.map = texture;
      object.material.bumpMap = texture; object.material.bumpScale = /tyre|heavySteel/.test(texture.name) ? .065 : .025;
      object.material.color?.set(0xffffff); object.material.needsUpdate = true; applied.set(object, texture);
    });
  }
  function dispose() { Object.values(textures).forEach(texture => texture.dispose()); }
  return { textures, ready, apply, dispose };
}
