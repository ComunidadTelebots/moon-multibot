/* Optimised procedural road-surface detail for Rutas 3D.
 * The road follows the Z axis. No imports or external assets are required.
 */

const clamp = (value, minimum, maximum) => Math.max(minimum, Math.min(maximum, value));

export function createRoadSurfaceEnhancements({
  THREE: T,
  scene,
  qualityLevel = 2,
  roadLength = 6000,
} = {}) {
  if (!T || !scene) throw new Error("THREE and scene are required");

  const quality = clamp(Math.round(Number(qualityLevel) || 0), 0, 3);
  const length = Math.max(200, Number(roadLength) || 6000);
  const root = new T.Group();
  root.name = "transport-road-surface-enhancements";
  scene.add(root);

  const resources = new Set();
  const surfaces = {};
  const track = (resource) => (resources.add(resource), resource);
  const standard = (parameters) => track(new T.MeshStandardMaterial(parameters));
  const geometry = (value) => track(value);
  const dummy = new T.Object3D();

  const createTexture = (size, draw) => {
    if (typeof document === "undefined") return null;
    const canvas = document.createElement("canvas");
    canvas.width = canvas.height = size;
    const context = canvas.getContext("2d");
    draw(context, size);
    const texture = track(new T.CanvasTexture(canvas));
    texture.wrapS = texture.wrapT = T.RepeatWrapping;
    texture.anisotropy = quality >= 2 ? 4 : 1;
    if (T.SRGBColorSpace) texture.colorSpace = T.SRGBColorSpace;
    return texture;
  };

  // Deterministic grain avoids a visibly flat road while keeping every load stable.
  const asphaltMap = createTexture(256, (context, size) => {
    context.fillStyle = "#34373a";
    context.fillRect(0, 0, size, size);
    let seed = 4173;
    for (let index = 0; index < 2400; index += 1) {
      seed = (seed * 16807) % 2147483647;
      const x = seed % size;
      seed = (seed * 16807) % 2147483647;
      const y = seed % size;
      const shade = 35 + (seed % 38);
      context.fillStyle = `rgba(${shade},${shade},${shade},${0.12 + (seed % 16) / 100})`;
      context.fillRect(x, y, 1 + (seed % 2), 1 + ((seed >> 2) % 2));
    }
  });
  if (asphaltMap) asphaltMap.repeat.set(5, Math.max(20, length / 18));

  surfaces.asphalt = standard({
    color: 0x4a4c4d,
    map: asphaltMap,
    roughness: 0.93,
    metalness: 0.02,
    polygonOffset: true,
    polygonOffsetFactor: -1,
  });
  surfaces.patch = standard({ color: 0x24272a, roughness: 0.88, polygonOffset: true, polygonOffsetFactor: -2 });
  surfaces.shoulder = standard({ color: 0x77756f, roughness: 0.98 });
  surfaces.marking = standard({
    color: 0xf4f4eb,
    roughness: 0.34,
    metalness: 0.04,
    emissive: 0xd9e0d8,
    emissiveIntensity: quality >= 2 ? 0.13 : 0.06,
  });
  surfaces.drain = standard({ color: 0x464b4d, roughness: 0.48, metalness: 0.72 });
  surfaces.joint = standard({ color: 0x17191b, roughness: 0.9 });
  surfaces.stud = standard({
    color: 0xf7f7ed,
    roughness: 0.18,
    metalness: 0.16,
    emissive: 0xffffff,
    emissiveIntensity: quality >= 2 ? 0.65 : 0.25,
  });

  const road = new T.Mesh(geometry(new T.PlaneGeometry(20, length)), surfaces.asphalt);
  road.name = "road-surface-relief";
  road.rotation.x = -Math.PI / 2;
  road.position.y = 0.012;
  road.receiveShadow = true;
  root.add(road);

  for (const side of [-1, 1]) {
    const shoulder = new T.Mesh(geometry(new T.PlaneGeometry(2.2, length)), surfaces.shoulder);
    shoulder.name = side < 0 ? "left-shoulder" : "right-shoulder";
    shoulder.rotation.x = -Math.PI / 2;
    shoulder.rotation.z = side * 0.025;
    shoulder.position.set(side * 11.05, -0.035, 0);
    shoulder.receiveShadow = true;
    root.add(shoulder);
  }

  const addInstances = (name, shape, surface, transforms, shadows = false) => {
    if (!transforms.length) return null;
    const mesh = new T.InstancedMesh(geometry(shape), surface, transforms.length);
    mesh.name = name;
    mesh.castShadow = shadows && quality > 1;
    mesh.receiveShadow = shadows;
    transforms.forEach((transform, index) => {
      dummy.position.set(...transform.position);
      dummy.rotation.set(...(transform.rotation || [0, 0, 0]));
      dummy.scale.set(...(transform.scale || [1, 1, 1]));
      dummy.updateMatrix();
      mesh.setMatrixAt(index, dummy.matrix);
    });
    mesh.instanceMatrix.needsUpdate = true;
    root.add(mesh);
    return mesh;
  };

  const dashes = [];
  const dashStep = quality === 0 ? 18 : 12;
  for (let z = -length / 2 + 5; z < length / 2; z += dashStep) {
    for (const x of [-3.35, 3.35]) dashes.push({ position: [x, 0.034, z], scale: [1, 1, 1] });
  }
  addInstances("reflective-lane-dashes", new T.BoxGeometry(0.14, 0.018, 4.2), surfaces.marking, dashes);

  const edgeLines = [];
  const edgeStep = quality === 0 ? 38 : 24;
  for (let z = -length / 2 + edgeStep / 2; z < length / 2; z += edgeStep) {
    for (const x of [-9.35, 9.35]) edgeLines.push({ position: [x, 0.033, z], scale: [1, 1, 1] });
  }
  addInstances("reflective-edge-lines", new T.BoxGeometry(0.18, 0.018, edgeStep - 0.2), surfaces.marking, edgeLines);

  const joints = [];
  for (let z = -length / 2 + 45; z < length / 2; z += 72) {
    joints.push({ position: [0, 0.029, z], rotation: [0, ((z / 72) % 3 - 1) * 0.025, 0] });
  }
  addInstances("sealed-expansion-joints", new T.BoxGeometry(18.5, 0.012, 0.1), surfaces.joint, joints);

  const patches = [];
  let patchSeed = 9137;
  const patchCount = Math.floor(length / (quality >= 2 ? 105 : 165));
  for (let index = 0; index < patchCount; index += 1) {
    patchSeed = (patchSeed * 48271) % 2147483647;
    const x = ((patchSeed % 1500) / 100 - 7.5);
    patchSeed = (patchSeed * 48271) % 2147483647;
    const z = -length / 2 + (patchSeed % Math.floor(length));
    patches.push({
      position: [x, 0.031, z],
      rotation: [-Math.PI / 2, 0, (patchSeed % 23) / 100],
      scale: [0.75 + (patchSeed % 90) / 100, 0.8 + (patchSeed % 180) / 100, 1],
    });
  }
  addInstances("asphalt-repair-patches", new T.PlaneGeometry(2.4, 4.8), surfaces.patch, patches);

  const drains = [];
  const drainSpacing = quality >= 2 ? 42 : 72;
  for (let z = -length / 2 + 24; z < length / 2; z += drainSpacing) {
    for (const x of [-10.05, 10.05]) drains.push({ position: [x, 0.005, z] });
  }
  addInstances("shoulder-drainage-grates", new T.BoxGeometry(0.62, 0.055, 1.35), surfaces.drain, drains);

  if (quality > 0) {
    const studs = [];
    const studSpacing = quality >= 2 ? 12 : 24;
    for (let z = -length / 2 + 6; z < length / 2; z += studSpacing) {
      for (const x of [-9.15, -3.35, 3.35, 9.15]) studs.push({ position: [x, 0.065, z] });
    }
    addInstances("retroreflective-road-studs", new T.BoxGeometry(0.16, 0.07, 0.11), surfaces.stud, studs);
  }

  function applyTextures(maps = {}) {
    const aliases = {
      asphalt: "asphalt",
      road: "asphalt",
      patch: "patch",
      shoulder: "shoulder",
      marking: "marking",
      markings: "marking",
      drainage: "drain",
      drain: "drain",
    };
    for (const [key, value] of Object.entries(maps || {})) {
      const surface = surfaces[aliases[key] || key];
      if (!surface || !value) continue;
      if (value.isTexture) surface.map = value;
      else {
        for (const property of ["map", "normalMap", "roughnessMap", "aoMap"]) {
          if (value[property]?.isTexture) surface[property] = value[property];
        }
        if (Number.isFinite(value.normalScale) && surface.normalScale) surface.normalScale.setScalar(value.normalScale);
        if (Number.isFinite(value.roughness)) surface.roughness = clamp(value.roughness, 0, 1);
      }
      surface.needsUpdate = true;
    }
    return api;
  }

  function dispose() {
    scene.remove(root);
    for (const resource of resources) resource?.dispose?.();
    root.clear();
  }

  const api = { root, surfaces, applyTextures, dispose };
  return api;
}
