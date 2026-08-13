export function createWorldDetail({ THREE: T, qualityLevel = 2, textureMaps = {} }) {
  const mats = {
    concrete: new T.MeshStandardMaterial({ color: 0x89949a, roughness: .86, bumpMap: textureMaps.concrete?.bumpMap, bumpScale: .08 }),
    dark: new T.MeshStandardMaterial({ color: 0x171c20, roughness: .64, metalness: .18 }),
    glass: new T.MeshPhysicalMaterial({ color: 0x234b62, roughness: .08, metalness: .08, transmission: .16, transparent: true, opacity: .83, clearcoat: 1 }),
    window: new T.MeshStandardMaterial({ color: 0x83b7cb, emissive: 0x183b4b, emissiveIntensity: .65, roughness: .16, metalness: .35 }),
    trunk: new T.MeshStandardMaterial({ color: 0x654126, roughness: .98, bumpMap: textureMaps.ground?.bumpMap, bumpScale: .12 }),
    tyre: new T.MeshStandardMaterial({ color: 0x111315, roughness: .96, bumpMap: textureMaps.tyre?.bumpMap, bumpScale: .08 }),
    chrome: new T.MeshStandardMaterial({ color: 0xa8b2b7, roughness: .2, metalness: .86 }),
    soil: new T.MeshStandardMaterial({ color: 0x443426, roughness: 1 }),
    barkDark: new T.MeshStandardMaterial({ color: 0x402a1d, roughness: 1 }),
  };
  mats.tyre.userData.vehicleSurface = "tyre";
  mats.leaves = [0x245f39, 0x2d7042, 0x397d48, 0x1e5134].map(color => new T.MeshStandardMaterial({ color, roughness: .94 }));
  const mesh = (geometry, material, name, position, parent) => { const item = new T.Mesh(geometry, material); item.name = name; item.position.set(...position); item.castShadow = item.receiveShadow = true; parent.add(item); return item; };
  function createBuilding({ width, height, depth, color, roadSide = 1, seed = 0 }) {
    const root = new T.Group(); root.name = "detailed_city_building";
    const facade = new T.MeshPhysicalMaterial({ color, roughness: .72, metalness: .04, clearcoat: .06, bumpMap: textureMaps.concrete?.bumpMap, bumpScale: .07 });
    mesh(new T.BoxGeometry(width, height, depth, 2, Math.max(2, Math.round(height / 7)), 2), facade, "facade_shell", [0, height / 2, 0], root);
    mesh(new T.BoxGeometry(width + .35, .55, depth + .35), mats.concrete, "stone_plinth", [0, .28, 0], root);
    mesh(new T.BoxGeometry(width + .45, .32, depth + .45), mats.dark, "roof_parapet", [0, height + .16, 0], root);
    const floors = Math.max(2, Math.floor((height - 2) / 4.2)), columns = Math.max(2, Math.floor(depth / 3));
    const windowGeometry = new T.BoxGeometry(.09, 1.65, Math.min(1.55, depth / (columns + 1)));
    const frontX = -roadSide * (width / 2 + .055);
    for (let floor = 0; floor < floors; floor++) for (let column = 0; column < columns; column++) {
      const pz = -depth / 2 + (column + 1) * depth / (columns + 1), py = 2.6 + floor * 4.15;
      mesh(windowGeometry, mats.window, "recessed_window", [frontX, py, pz], root);
      if (qualityLevel > 0) {
        mesh(new T.BoxGeometry(.14, 1.92, .06), mats.dark, "window_mullion", [frontX - roadSide * .07, py, pz], root);
        mesh(new T.BoxGeometry(.14, .12, Math.min(1.82, depth / columns)), mats.dark, "window_lintel", [frontX - roadSide * .07, py + .94, pz], root);
      }
      if (qualityLevel > 1 && floor > 0 && (floor + column + seed) % 3 === 0) {
        mesh(new T.BoxGeometry(.75, .12, Math.min(2.2, depth / columns)), mats.concrete, "balcony_slab", [frontX - roadSide * .38, py - .9, pz], root);
        mesh(new T.BoxGeometry(.045, .58, Math.min(2.05, depth / columns)), mats.glass, "balcony_glass", [frontX - roadSide * .75, py - .62, pz], root);
      }
    }
    if (qualityLevel > 1) {
      const facadeBand = new T.BoxGeometry(.12, .2, depth + .08);
      for (let floor = 1; floor < floors; floor++) {
        mesh(facadeBand, mats.concrete, "facade_floor_band", [frontX - roadSide * .04, floor * 4.15 + .45, 0], root);
      }
      const entrance = mesh(new T.BoxGeometry(.16, 2.45, 1.65), mats.glass, "street_entrance", [frontX - roadSide * .1, 1.35, depth * .27], root);
      entrance.material = mats.glass;
      mesh(new T.BoxGeometry(.4, .22, 2.15), mats.dark, "entrance_canopy", [frontX - roadSide * .42, 2.68, depth * .27], root);
    }
    for (const side of [-1, 1]) {
      mesh(new T.CylinderGeometry(.07, .09, height - 1, 10), mats.chrome, "rain_downpipe", [frontX, height / 2, side * (depth / 2 - .22)], root);
    }
    if (qualityLevel > 0) {
      mesh(new T.BoxGeometry(2.1, .8, 1.55), mats.dark, "roof_hvac", [width * .18, height + .55, 0], root);
      const antenna = mesh(new T.CylinderGeometry(.035, .05, 2.2, 8), mats.chrome, "roof_antenna", [-width * .22, height + 1.2, 0], root); antenna.rotation.z = -.05;
    }
    return root;
  }
  function createTree({ seed = 0, height = 10 }) {
    const root = new T.Group(); root.name = "detailed_roadside_tree";
    const treeScale = Math.max(.65, height / 10);
    if (qualityLevel > 0) {
      const soil = mesh(new T.CylinderGeometry(1.15 * treeScale, 1.28 * treeScale, .08, 14), mats.soil, "tree_soil", [0, .035, 0], root);
      soil.receiveShadow = true; soil.castShadow = false;
      for (let rootIndex = 0; rootIndex < (qualityLevel > 1 ? 6 : 3); rootIndex++) {
        const angle = seed + rootIndex * 2.399;
        const rootMesh = mesh(new T.CylinderGeometry(.055, .16, 1.8 * treeScale, 7), mats.barkDark, "visible_root", [Math.cos(angle) * .6 * treeScale, .11, Math.sin(angle) * .6 * treeScale], root);
        rootMesh.rotation.set(Math.PI / 2, 0, -angle); rootMesh.scale.y = 1 + (rootIndex % 2) * .18;
      }
    }
    const trunk = mesh(new T.CylinderGeometry(.34, .52, height * .48, qualityLevel > 1 ? 14 : 8), mats.trunk, "tapered_trunk", [0, height * .24, 0], root);
    for (let branch = 0; branch < (qualityLevel > 1 ? 5 : 3); branch++) {
      const angle = branch * 2.399 + seed, limb = mesh(new T.CylinderGeometry(.08, .18, height * .34, 8), mats.trunk, "branch", [Math.cos(angle) * .45, height * (.48 + branch * .025), Math.sin(angle) * .45], root);
      limb.rotation.set(Math.sin(angle) * .62, 0, Math.cos(angle) * .62);
      if (qualityLevel > 1) {
        const twig = mesh(new T.CylinderGeometry(.035, .075, height * .2, 6), mats.barkDark, "secondary_branch", [Math.cos(angle) * height * .09, height * (.62 + branch * .02), Math.sin(angle) * height * .09], root);
        twig.rotation.set(Math.sin(angle + .7) * .92, angle, Math.cos(angle + .7) * .92);
      }
    }
    for (let crown = 0; crown < (qualityLevel > 1 ? 7 : 4); crown++) {
      const angle = crown * 2.399 + seed, radius = height * (.19 + (crown % 3) * .018);
      const leaves = new T.Mesh(new T.IcosahedronGeometry(radius, qualityLevel > 2 ? 2 : 1), mats.leaves[Math.abs((crown + seed) | 0) % mats.leaves.length]);
      leaves.name = "irregular_leaf_canopy"; leaves.scale.set(1, .86 + (crown % 2) * .13, 1); leaves.position.set(Math.cos(angle) * height * .14, height * (.68 + (crown % 3) * .09), Math.sin(angle) * height * .14); leaves.castShadow = true; root.add(leaves);
    }
    root.rotation.y = seed * 1.37;
    return root;
  }
  function carWheel(parent, x, z) {
    const wheel = new T.Group(); wheel.name = "traffic_wheel"; wheel.position.set(x, .43, z); wheel.userData.isWheel = true;
    const tyre = mesh(new T.CylinderGeometry(.39, .39, .28, qualityLevel > 1 ? 20 : 12), mats.tyre, "tyre", [0, 0, 0], wheel); tyre.rotation.z = Math.PI / 2;
    const rim = mesh(new T.CylinderGeometry(.21, .21, .3, qualityLevel > 1 ? 16 : 10), mats.chrome, "alloy_rim", [0, 0, 0], wheel); rim.rotation.z = Math.PI / 2;
    parent.add(wheel);
  }
  function createTrafficVehicle({ index = 0, color = 0x547ee8 }) {
    const root = new T.Group(); root.name = "detailed_traffic_vehicle";
    const type = ["sedan", "suv", "van"][index % 3], length = type === "van" ? 5.6 : type === "suv" ? 4.9 : 4.65, height = type === "van" ? 2.25 : type === "suv" ? 1.72 : 1.42;
    const paint = new T.MeshPhysicalMaterial({ color, roughness: .24, metalness: .38, clearcoat: .92, clearcoatRoughness: .13 });
    paint.userData.vehicleSurface = type === "sedan" ? "paint" : "commercial";
    const lower = mesh(new T.BoxGeometry(2.22, .76, length - .45, 2, 2, qualityLevel > 1 ? 5 : 2), paint, "sculpted_body", [0, .78, 0], root);
    const hoodLength = type === "van" ? .72 : 1.28;
    const hood = mesh(new T.BoxGeometry(2.12, .48, hoodLength, 2, 2, 2), paint, "bonnet", [0, 1.12, -length / 2 + hoodLength * .55], root);
    hood.rotation.x = -.035;
    const cabinLength = type === "van" ? 3.4 : 2.5;
    const cabin = mesh(new T.CapsuleGeometry(.62, cabinLength - 1.24, 8, qualityLevel > 1 ? 18 : 10), mats.glass, "glazed_cabin", [0, 1.25 + height * .2, type === "van" ? .25 : .08], root); cabin.rotation.x = Math.PI / 2; cabin.scale.x = 1.25; cabin.scale.y = type === "van" ? 1.25 : .82;
    const roof = mesh(new T.BoxGeometry(1.96, .15, cabinLength - .25), paint, "painted_roof", [0, height + .45, type === "van" ? .2 : .22], root);
    roof.rotation.x = type === "sedan" ? -.018 : 0;
    mesh(new T.BoxGeometry(2.35, .24, .18), mats.dark, "front_bumper", [0, .54, -length / 2 + .04], root);
    mesh(new T.BoxGeometry(2.35, .24, .18), mats.dark, "rear_bumper", [0, .54, length / 2 - .04], root);
    const frontLamp = new T.MeshStandardMaterial({ color: 0xfff4ce, emissive: 0xffe2a3, emissiveIntensity: 2.2 });
    const rearLamp = new T.MeshStandardMaterial({ color: 0xc91f2d, emissive: 0x8c0711, emissiveIntensity: 1.8 });
    for (const x of [-.82, .82]) { mesh(new T.BoxGeometry(.48, .2, .08), frontLamp, "headlamp", [x, .84, -length / 2 - .05], root); mesh(new T.BoxGeometry(.42, .23, .08), rearLamp, "tail_lamp", [x, .84, length / 2 + .05], root); }
    if (qualityLevel > 0) {
      mesh(new T.BoxGeometry(1.05, .3, .07), mats.dark, "front_grille", [0, .72, -length / 2 - .055], root);
      mesh(new T.BoxGeometry(.62, .2, .045), mats.concrete, "front_plate", [0, .48, -length / 2 - .09], root);
      mesh(new T.BoxGeometry(.62, .2, .045), mats.concrete, "rear_plate", [0, .48, length / 2 + .09], root);
      for (const x of [-1.115, 1.115]) mesh(new T.BoxGeometry(.045, .08, length * .46), mats.dark, "door_sill", [x, .68, .25], root);
    }
    if (qualityLevel > 1) {
      for (const side of [-1, 1]) {
        mesh(new T.BoxGeometry(.035, .68, 1.28), mats.dark, "door_seam", [side * 1.116, 1.21, .35], root);
        const handle = mesh(new T.BoxGeometry(.045, .075, .38), mats.chrome, "door_handle", [side * 1.14, 1.38, .52], root); handle.castShadow = false;
      }
      const exhaust = mesh(new T.CylinderGeometry(.055, .07, .52, 10), mats.chrome, "exhaust_tip", [.7, .52, length / 2 - .18], root); exhaust.rotation.x = Math.PI / 2;
    }
    for (const x of [-1.16, 1.16]) { const mirror = mesh(new T.SphereGeometry(.12, 12, 8), mats.dark, "door_mirror", [x, 1.45, -.55], root); mirror.scale.set(1.25, .7, .72); }
    for (const z of [-length * .31, length * .31]) for (const x of [-1.08, 1.08]) carWheel(root, x, z);
    root.userData.vehicleLength = length; root.userData.vehicleType = type; return root;
  }
  function applyPhotorealTextures(maps) {
    const apply = (material, source, repeatX = 1, repeatY = 1) => {
      if (!source) return;
      const texture = source.clone(); texture.needsUpdate = true; texture.repeat.set(repeatX, repeatY);
      material.map = texture; material.bumpMap = texture; material.bumpScale = .045; material.needsUpdate = true;
    };
    apply(mats.concrete, maps.stone, 2, 2);
    mats.leaves.forEach((material, index) => apply(material, maps.foliage, 1 + index * .15, 1 + index * .15));
  }
  return { createBuilding, createTree, createTrafficVehicle, applyPhotorealTextures };
}
