const TYPES = ["workshop", "fuel", "rest"];

export function createRoadsideServices({ THREE: T, scene, qualityLevel = 2, roadLength = 6000, atlasUrl }) {
  const root = new T.Group(); root.name = "roadside_service_network"; scene.add(root);
  const materials = {
    workshop: new T.MeshStandardMaterial({ color: 0xb9b8b2, roughness: .82 }),
    fuel: new T.MeshPhysicalMaterial({ color: 0xe8eeee, roughness: .32, metalness: .18, clearcoat: .45 }),
    paving: new T.MeshStandardMaterial({ color: 0x696863, roughness: .95 }),
    lodge: new T.MeshStandardMaterial({ color: 0x805735, roughness: .9 }),
    dark: new T.MeshStandardMaterial({ color: 0x192126, roughness: .55, metalness: .35 }),
    glass: new T.MeshPhysicalMaterial({ color: 0x4b8798, roughness: .12, transmission: .12, transparent: true, opacity: .82 }),
    accent: new T.MeshStandardMaterial({ color: 0x27cdb8, emissive: 0x0b5c55, emissiveIntensity: .7, roughness: .38 }),
    lamp: new T.MeshStandardMaterial({ color: 0xffedc2, emissive: 0xffd982, emissiveIntensity: 2.1 }),
  };
  const geometries = [];
  const mesh = (geometry, material, parent, x, y, z, name = "service_part") => {
    geometries.push(geometry); const item = new T.Mesh(geometry, material); item.name = name;
    item.position.set(x, y, z); item.castShadow = item.receiveShadow = true; parent.add(item); return item;
  };
  const labelMaterial = (title, subtitle) => {
    const canvas = document.createElement("canvas"); canvas.width = 768; canvas.height = 220;
    const x = canvas.getContext("2d"); x.fillStyle = "#083e42"; x.fillRect(0, 0, 768, 220);
    x.strokeStyle = "#54ebd6"; x.lineWidth = 10; x.strokeRect(8, 8, 752, 204);
    x.fillStyle = "#effffb"; x.textAlign = "center"; x.font = "800 72px system-ui"; x.fillText(title, 384, 98);
    x.fillStyle = "#a5ddd5"; x.font = "600 34px system-ui"; x.fillText(subtitle, 384, 160);
    const texture = new T.CanvasTexture(canvas); texture.colorSpace = T.SRGBColorSpace;
    return new T.MeshStandardMaterial({ map: texture, emissive: 0x0a3535, emissiveIntensity: .42, roughness: .4 });
  };
  const services = [];
  function base(parent, side) {
    const slab = mesh(new T.BoxGeometry(48, .24, 62), materials.paving, parent, side * 39, .02, 0, "heavy_vehicle_forecourt");
    for (const lane of [-12, 0, 12]) mesh(new T.BoxGeometry(.16, .035, 48), materials.lamp, parent, side * 39 + lane, .17, 0, "parking_bay_marking");
    return slab;
  }
  function workshop(parent, side) {
    base(parent, side);
    const buildingX = side * 48;
    mesh(new T.BoxGeometry(27, 10, 24), materials.workshop, parent, buildingX, 5, 4, "service_workshop");
    for (const z of [-5, 3, 11]) {
      mesh(new T.BoxGeometry(.18, 6.2, 6), materials.dark, parent, buildingX - side * 13.6, 3.25, z, "roller_door");
      if (qualityLevel > 1) mesh(new T.BoxGeometry(.3, .18, 5.1), materials.accent, parent, buildingX - side * 13.75, 6.1, z, "door_lamp");
    }
    const sign = mesh(new T.PlaneGeometry(12, 3.4), labelMaterial("TALLER 24H", "Mecánica · neumáticos"), parent, buildingX - side * 13.72, 8.3, 3, "workshop_sign"); sign.rotation.y = side > 0 ? -Math.PI / 2 : Math.PI / 2;
    for (const z of [-5, 5]) { const lift = mesh(new T.BoxGeometry(5, .28, 4), materials.accent, parent, side * 30, .45, z, "service_lift"); lift.rotation.z = side * .03; }
  }
  function fuel(parent, side) {
    base(parent, side);
    mesh(new T.BoxGeometry(36, 1.15, 25), materials.fuel, parent, side * 39, 7.6, 0, "fuel_canopy");
    for (const x of [-12, 0, 12]) for (const z of [-8, 8]) {
      mesh(new T.CylinderGeometry(.28, .34, 7, 12), materials.dark, parent, side * 39 + x, 3.55, z, "canopy_column");
      mesh(new T.BoxGeometry(2.1, 2.8, 1.15), materials.fuel, parent, side * 39 + x, 1.45, z, "fuel_pump");
      mesh(new T.BoxGeometry(1.25, .55, 1.18), materials.glass, parent, side * 39 + x, 1.85, z, "pump_display");
    }
    const pylon = mesh(new T.BoxGeometry(5.2, 10, 1), materials.accent, parent, side * 22, 5, -22, "fuel_service_pylon");
    const sign = mesh(new T.PlaneGeometry(4.7, 3.5), labelMaterial("ENERGÍA", "Diésel · carga EV"), parent, side * 21.48, 6, -22, "fuel_sign"); sign.rotation.y = side > 0 ? -Math.PI / 2 : Math.PI / 2;
    pylon.castShadow = true;
  }
  function rest(parent, side) {
    base(parent, side);
    mesh(new T.BoxGeometry(22, 7, 18), materials.lodge, parent, side * 49, 3.55, 7, "rest_lodge");
    const roof = mesh(new T.ConeGeometry(16, 5, 4), materials.dark, parent, side * 49, 9, 7, "rest_lodge_roof"); roof.rotation.y = Math.PI / 4;
    for (const z of [1, 7, 13]) mesh(new T.BoxGeometry(.2, 2.4, 3.4), materials.glass, parent, side * 37.9, 3.8, z, "rest_window");
    for (const z of [-17, -9, -1]) {
      mesh(new T.BoxGeometry(5.5, .32, 1.2), materials.lodge, parent, side * 31, 1.05, z, "rest_bench");
      for (const offset of [-2.2, 2.2]) mesh(new T.BoxGeometry(.25, 1, .25), materials.dark, parent, side * 31 + offset, .5, z, "bench_leg");
    }
    const sign = mesh(new T.PlaneGeometry(10, 3), labelMaterial("DESCANSO", "Parking · cafetería"), parent, side * 37.85, 6.1, 7, "rest_sign"); sign.rotation.y = side > 0 ? -Math.PI / 2 : Math.PI / 2;
  }
  const spacing = qualityLevel > 0 ? 760 : 1100;
  let index = 0;
  for (let z = -roadLength / 2 + 380; z < roadLength / 2 - 260; z += spacing) {
    const type = TYPES[index % TYPES.length], side = index % 2 ? -1 : 1, group = new T.Group();
    group.name = `roadside_${type}`; group.position.z = z; root.add(group);
    ({ workshop, fuel, rest })[type](group, side);
    services.push({ type, side, z, group }); index++;
  }
  const ready = atlasUrl ? new Promise((resolve, reject) => new T.TextureLoader().load(atlasUrl, source => {
    const size = Math.floor(Math.min(source.image.width, source.image.height) / 2);
    [["workshop",0,0],["fuel",1,0],["paving",0,1],["lodge",1,1]].forEach(([name,c,r]) => {
      const canvas = document.createElement("canvas"); canvas.width = canvas.height = size;
      canvas.getContext("2d").drawImage(source.image, c * size, r * size, size, size, 0, 0, size, size);
      const texture = new T.CanvasTexture(canvas); texture.colorSpace = T.SRGBColorSpace; texture.wrapS = texture.wrapT = T.RepeatWrapping; texture.repeat.set(2, 2); texture.anisotropy = qualityLevel >= 2 ? 8 : 2;
      materials[name].map = texture; materials[name].bumpMap = texture; materials[name].bumpScale = .045; materials[name].needsUpdate = true;
    }); source.dispose(); resolve();
  }, undefined, reject)) : Promise.resolve();
  function update(position) {
    let nearest = null;
    for (const service of services) {
      const distance = Math.hypot(position.x - service.side * 39, position.z - service.z);
      if (!nearest || distance < nearest.distance) nearest = { ...service, distance };
    }
    return nearest;
  }
  function dispose() { root.removeFromParent(); geometries.forEach(g => g.dispose()); Object.values(materials).forEach(m => { m.map?.dispose(); m.dispose(); }); }
  return { root, services, ready, update, dispose };
}
