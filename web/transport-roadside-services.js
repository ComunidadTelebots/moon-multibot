const TYPES = ["workshop", "fuel", "rest", "inspection"];

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
    workshopFloor: new T.MeshStandardMaterial({ color: 0x30373b, roughness: .72, metalness: .08 }),
    safety: new T.MeshStandardMaterial({ color: 0xf0a429, roughness: .58, metalness: .12 }),
    tool: new T.MeshStandardMaterial({ color: 0x1d4254, roughness: .44, metalness: .42 }),
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
    const frontX = buildingX - side * 13.45, backX = buildingX + side * 13.25;
    mesh(new T.BoxGeometry(27, .3, 24), materials.workshopFloor, parent, buildingX, .28, 4, "workshop_epoxy_floor");
    mesh(new T.BoxGeometry(.45, 9.4, 24), materials.workshop, parent, backX, 4.9, 4, "workshop_back_wall");
    for (const z of [-7.8, 15.8]) mesh(new T.BoxGeometry(27, 9.4, .45), materials.workshop, parent, buildingX, 4.9, z, "workshop_side_wall");
    mesh(new T.BoxGeometry(27.6, .5, 24.6), materials.dark, parent, buildingX, 9.7, 4, "workshop_roof");
    for (const z of [-5, 3, 11]) {
      for (const edge of [-3.25, 3.25]) mesh(new T.BoxGeometry(.45, 7.1, .45), materials.dark, parent, frontX, 3.65, z + edge, "workshop_bay_frame");
      mesh(new T.BoxGeometry(.48, .5, 6.9), materials.dark, parent, frontX, 7.05, z, "workshop_bay_header");
      if (qualityLevel > 1) mesh(new T.BoxGeometry(.3, .18, 5.1), materials.accent, parent, frontX - side * .15, 6.55, z, "door_lamp");
    }
    const sign = mesh(new T.PlaneGeometry(12, 3.4), labelMaterial("TALLER 24H", "Mecánica · neumáticos"), parent, buildingX - side * 13.72, 8.3, 3, "workshop_sign"); sign.rotation.y = side > 0 ? -Math.PI / 2 : Math.PI / 2;
    for (const z of [-5, 5]) { const lift = mesh(new T.BoxGeometry(5, .28, 4), materials.accent, parent, side * 30, .45, z, "service_lift"); lift.rotation.z = side * .03; }
    for (const z of [-5, 3]) {
      const bayX = buildingX - side * 2;
      mesh(new T.BoxGeometry(7.2, .12, 5.8), materials.dark, parent, bayX, .5, z, "workshop_inspection_tray");
      for (const offset of [-3, 3]) {
        mesh(new T.BoxGeometry(.55, 6.7, .65), materials.tool, parent, bayX + side * offset, 3.65, z, "workshop_lift_column");
        mesh(new T.BoxGeometry(1.05, .18, 2.8), materials.safety, parent, bayX + side * (offset - Math.sign(offset) * 1.1), 1.05, z, "workshop_lift_arm");
      }
    }
    const receptionX = buildingX + side * 8.5;
    mesh(new T.BoxGeometry(5.5, 1.15, 5.2), materials.tool, parent, receptionX, 1, 11, "workshop_reception");
    mesh(new T.BoxGeometry(.18, 3.4, 6), materials.glass, parent, receptionX - side * 2.9, 3.3, 11, "workshop_reception_glass");
    for (const z of [-4, 0, 4, 8]) {
      mesh(new T.BoxGeometry(1.15, 2.2, 3.4), materials.tool, parent, backX - side * .8, 1.35, z, "workshop_tool_cabinet");
      if (qualityLevel > 1) for (let tyre = 0; tyre < 3; tyre++) { const wheel = mesh(new T.TorusGeometry(.48, .16, 8, 18), materials.dark, parent, backX - side * 1.25, 2 + tyre * 1.05, z + 1.25, "workshop_tyre_stock"); wheel.rotation.y = Math.PI / 2; }
    }
    if (qualityLevel > 0) for (const z of [-5, 3, 11]) {
      mesh(new T.BoxGeometry(7.5, .12, .38), materials.lamp, parent, buildingX, 8.9, z, "workshop_ceiling_light");
      for (const stripe of [-2.7, 2.7]) mesh(new T.BoxGeometry(7.5, .035, .12), materials.safety, parent, buildingX, .47, z + stripe, "workshop_safety_line");
    }
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
  function inspection(parent, side) {
    base(parent, side);
    const laneX = side * 31;
    mesh(new T.BoxGeometry(7.2, .18, 25), materials.dark, parent, laneX, .2, 1, "weighbridge_platform");
    for (const x of [-2.8, 2.8]) mesh(new T.BoxGeometry(.35, .12, 23), materials.accent, parent, laneX + x, .34, 1, "weighbridge_sensor");
    const officeX = side * 49;
    mesh(new T.BoxGeometry(14, 7, 15), materials.workshop, parent, officeX, 3.55, 5, "inspection_office");
    mesh(new T.BoxGeometry(.2, 2.6, 6), materials.glass, parent, officeX - side * 7.1, 4.1, 5, "inspection_window");
    const gantry = new T.Group(); gantry.name = "inspection_gantry"; parent.add(gantry);
    for (const x of [-4.4, 4.4]) mesh(new T.BoxGeometry(.32, 6.4, .32), materials.dark, gantry, laneX + x, 3.2, -9, "inspection_gantry_post");
    mesh(new T.BoxGeometry(9.2, .38, .38), materials.dark, gantry, laneX, 6.25, -9, "inspection_gantry_beam");
    const sign = mesh(new T.PlaneGeometry(8.4, 2.7), labelMaterial("CONTROL", "Peso · documentación"), parent, laneX, 5.1, -8.78, "inspection_sign");
    sign.rotation.y = Math.PI;
  }
  const spacing = qualityLevel > 0 ? 760 : 1100;
  let index = 0;
  for (let z = -roadLength / 2 + 380; z < roadLength / 2 - 260; z += spacing) {
    const type = TYPES[index % TYPES.length], side = index % 2 ? -1 : 1, group = new T.Group();
    group.name = `roadside_${type}`; group.position.z = z; root.add(group);
    ({ workshop, fuel, rest, inspection })[type](group, side);
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
