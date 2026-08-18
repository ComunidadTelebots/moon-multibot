export function createRouteScenery({ THREE: T, scene, qualityLevel = 2 }) {
  const root = new T.Group();
  root.name = "dense_european_route_scenery";
  scene.add(root);
  const materials = {
    field: new T.MeshStandardMaterial({ color: 0x738b32, roughness: .98 }),
    soil: new T.MeshStandardMaterial({ color: 0x64503a, roughness: 1 }),
    stone: new T.MeshStandardMaterial({ color: 0x777b78, roughness: .94 }),
    hedge: new T.MeshStandardMaterial({ color: 0x315d2d, roughness: .96 }),
    rail: new T.MeshStandardMaterial({ color: 0xb7c0c2, roughness: .3, metalness: .76 }),
    reflector: new T.MeshStandardMaterial({ color: 0xf8f5df, emissive: 0xcac39b, emissiveIntensity: .25, roughness: .45 }),
  };
  const fieldCount = qualityLevel >= 2 ? 34 : 18;
  for (let i = 0; i < fieldCount; i++) {
    const side = i % 2 ? -1 : 1;
    const field = new T.Mesh(new T.PlaneGeometry(75 + (i % 4) * 18, 145, 1, 1), i % 5 === 0 ? materials.soil : materials.field);
    field.rotation.x = -Math.PI / 2;
    field.rotation.z = ((i % 3) - 1) * .055;
    field.position.set(side * (72 + (i % 3) * 36), -.12 + (i % 2) * .04, -2750 + i * 168);
    field.receiveShadow = true;
    root.add(field);
    if (qualityLevel >= 2) {
      for (let row = -3; row <= 3; row++) {
        const crop = new T.Mesh(new T.BoxGeometry(.18, .14, 132), materials.hedge);
        crop.position.set(field.position.x + row * 7.5, .02, field.position.z);
        crop.rotation.y = field.rotation.z;
        root.add(crop);
      }
    }
  }
  for (const side of [-1, 1]) {
    for (let z = -2700; z < 2700; z += qualityLevel >= 2 ? 95 : 150) {
      if (Math.abs(z) % 400 < 170) {
        const wall = new T.Mesh(new T.BoxGeometry(1.05, 1.7, 76), materials.stone);
        wall.position.set(side * 24.2, .7, z); wall.castShadow = wall.receiveShadow = true; root.add(wall);
      } else {
        const hedge = new T.Mesh(new T.BoxGeometry(3.2, 2.2 + Math.abs(z % 3) * .25, 68), materials.hedge);
        hedge.position.set(side * 26.5, 1, z); hedge.castShadow = hedge.receiveShadow = true; root.add(hedge);
      }
    }
    for (let z = -2900; z < 2900; z += 48) {
      const post = new T.Mesh(new T.BoxGeometry(.18, 1.15, .18), materials.reflector);
      post.position.set(side * 17.35, .56, z); post.castShadow = true; root.add(post);
      const marker = new T.Mesh(new T.BoxGeometry(.23, .18, .04), materials.reflector);
      marker.position.set(side * 17.24, .82, z); root.add(marker);
    }
  }
  function applyTextures(maps) {
    const setup = (material, texture, rx, ry, bump = false) => {
      if (!texture) return;
      const map = texture.clone(); map.needsUpdate = true; map.repeat.set(rx, ry);
      material.map = map;
      if (bump) { material.bumpMap = map; material.bumpScale = .08; }
      material.needsUpdate = true;
    };
    setup(materials.field, maps.ground, 5, 11);
    setup(materials.soil, maps.ground, 6, 12);
    setup(materials.stone, maps.stone, 1, 13, true);
    setup(materials.hedge, maps.foliage, 1.5, 12, true);
  }
  function dispose() {
    root.traverse(node => node.geometry?.dispose());
    Object.values(materials).forEach(material => { material.map?.dispose(); material.dispose(); });
    root.removeFromParent();
  }
  return { root, materials, applyTextures, dispose };
}
