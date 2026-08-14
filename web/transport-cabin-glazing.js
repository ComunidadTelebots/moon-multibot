export function createCabinGlazing({ THREE: T, bus = false, qualityLevel = 2 }) {
  const root = new T.Group();
  root.name = "cabin_glazing_doors_and_mirrors";
  const frontZ = bus ? -5.93 : -5.79;
  const sideX = bus ? 2.35 : 2.18;

  let doorMap=null;
  if(qualityLevel<2){const doorCanvas=document.createElement("canvas");doorCanvas.width=doorCanvas.height=256;const doorContext=doorCanvas.getContext("2d");doorContext.fillStyle="#252b2e";doorContext.fillRect(0,0,doorCanvas.width,doorCanvas.height);for(let y=0;y<doorCanvas.height;y+=3){const shade=38+(y*17%13);doorContext.fillStyle=`rgba(${shade},${shade+4},${shade+5},.18)`;doorContext.fillRect(0,y,doorCanvas.width,1);}doorMap=new T.CanvasTexture(doorCanvas);doorMap.name="door_satin_micrograin";doorMap.colorSpace=T.SRGBColorSpace;doorMap.wrapS=doorMap.wrapT=T.RepeatWrapping;doorMap.repeat.set(7,5);doorMap.anisotropy=2;}
  const polymer = new T.MeshPhysicalMaterial({ name:"door_satin_polymer", color: 0xffffff, map:doorMap, bumpMap:doorMap, bumpScale:.009, roughness: .72, metalness: .025, clearcoat: .06, clearcoatRoughness:.68 });
  const rubber = new T.MeshStandardMaterial({ color: 0x070a0c, roughness: .96 });
  const alloy = new T.MeshPhysicalMaterial({ color: 0x9ca5a8, roughness: .25, metalness: .78, clearcoat: .28 });
  const glass = new T.MeshPhysicalMaterial({
    name: "laminated_clear_cabin_glass", color: 0xeafaff, roughness: .025,
    metalness: 0, transparent: true, opacity: .16, transmission: .96,
    thickness: .018, ior: 1.48, attenuationColor: new T.Color(0xd8f3f5), attenuationDistance: 5.5,
    clearcoat: 1, clearcoatRoughness: .035, envMapIntensity: .72,
    depthWrite: false, side: T.DoubleSide,
  });
  const mirrorGlass = new T.MeshPhysicalMaterial({
    name: "silvered_convex_mirror", color: 0xc8e0e8, roughness: .045,
    metalness: .94, clearcoat: 1, clearcoatRoughness: .02,
  });
  const accent = new T.MeshBasicMaterial({ color: 0x55e2d0, toneMapped: false });
  const speaker = new T.MeshStandardMaterial({ color: 0x101518, roughness: .84, metalness: .18 });
  const mirrorCaptures = [];

  const add = (geometry, material, name, position, rotation = [0, 0, 0], parent = root) => {
    const mesh = new T.Mesh(geometry, material); mesh.name = name;
    mesh.position.set(...position); mesh.rotation.set(...rotation);
    mesh.castShadow = material !== glass; mesh.receiveShadow = material !== glass;
    parent.add(mesh); return mesh;
  };
  const box = (name, size, position, material, rotation, parent) => add(new T.BoxGeometry(...size), material, name, position, rotation, parent);
  const rounded = (name, width, height, depth, radius, position, material, rotation = [0, 0, 0], parent = root) => {
    const shape = new T.Shape(), x = -width / 2, y = -height / 2;
    shape.moveTo(x + radius, y); shape.lineTo(-x - radius, y); shape.quadraticCurveTo(-x, y, -x, y + radius);
    shape.lineTo(-x, -y - radius); shape.quadraticCurveTo(-x, -y, -x - radius, -y);
    shape.lineTo(x + radius, -y); shape.quadraticCurveTo(x, -y, x, -y - radius);
    shape.lineTo(x, y + radius); shape.quadraticCurveTo(x, y, x + radius, y);
    const geometry = new T.ExtrudeGeometry(shape, { depth, bevelEnabled: true, bevelSegments: qualityLevel > 1 ? 3 : 1, bevelSize: .025, bevelThickness: .025, curveSegments: qualityLevel > 1 ? 10 : 5 });
    geometry.center(); return add(geometry, material, name, position, rotation, parent);
  };

  // Two laminated panes leave a real central seal instead of one dark opaque slab.
  for (const side of [-1, 1]) {
    box("laminated_windshield_pane", [2.04, 1.72, .022], [side * 1.05, 3.6, frontZ - .73], glass, [-.025, 0, side * .012]);
    box("windshield_lower_rubber_seal", [2.12, .055, .06], [side * 1.05, 2.72, frontZ - .72], rubber);
    box("windshield_upper_rubber_seal", [2.12, .055, .06], [side * 1.05, 4.47, frontZ - .66], rubber);
  }
  box("windshield_centre_seal", [.075, 1.78, .065], [0, 3.59, frontZ - .72], rubber);

  for (const side of [-1, 1]) {
    const door = new T.Group(); door.name = side < 0 ? "driver_door_complete" : "passenger_door_complete";
    rounded("door_card", 2.48, 1.82, .12, .17, [0, 0, 0], polymer, [0, side * Math.PI / 2, 0], door);
    door.position.set(side * sideX, 2.02, frontZ + 1.05); root.add(door);
    rounded("door_armrest", 1.05, .25, .28, .09, [-side * .13, .05, -.22], polymer, [0, side * Math.PI / 2, 0], door);
    rounded("deep_door_pocket", .78, .38, .12, .1, [-side * .075, -.66, .23], rubber, [0, side * Math.PI / 2, 0], door);
    add(new T.TorusGeometry(.15, .032, 8, 24, Math.PI), alloy, "door_release_handle", [-side * .17, .38, -.56], [0, Math.PI / 2, side * Math.PI / 2], door);
    for (let button = 0; button < 4; button++) box("window_mirror_switch", [.035, .07, .11], [-side * .165, .22, -.1 + button * .14], button === 3 ? accent : alloy, undefined, door);
    add(new T.CylinderGeometry(.22, .22, .025, qualityLevel > 1 ? 32 : 18), speaker, "door_speaker_grille", [-side * .075, -.55, -.58], [0, 0, Math.PI / 2], door);
    for (let slot = -3; slot <= 3; slot++) box("speaker_grille_slot", [.018, .31, .018], [-side * .095, -.55 + slot * .035, -.58], alloy, undefined, door);

    // Side glass and structural frames align the door with the windscreen.
    box("clear_side_window", [.02, 1.42, 1.68], [side * (sideX + .015), 3.44, frontZ + .46], glass);
    box("a_pillar_trim", [.2, 2.16, .22], [side * 2.08, 3.54, frontZ - .62], polymer, [0, 0, side * .06]);
    box("b_pillar_trim", [.18, 2.02, .2], [side * 2.13, 3.38, frontZ + 1.42], polymer);
    box("side_window_lower_seal", [.07, .07, 1.76], [side * 2.13, 2.7, frontZ + .45], rubber);

    // Main wide-angle and lower convex mirror, with two articulated support arms.
    const mirror = new T.Group(); mirror.name = side < 0 ? "driver_functional_mirror" : "passenger_functional_mirror";
    mirror.position.set(side * (sideX + .46), 3.66, frontZ - .44); root.add(mirror);
    for (const y of [-.28, .34]) {
      const arm = add(new T.CylinderGeometry(.025, .035, .68, 12), polymer, "articulated_mirror_arm", [-side * .18, y, .2], [0, 0, side * .72], mirror);
      arm.userData.adjustableMirrorSupport = true;
    }
    rounded("mirror_housing", .72, 1.18, .13, .16, [side * .08, 0, 0], polymer, [0, side * Math.PI / 2, 0], mirror);
    const sideMirrorMaterial = mirrorGlass.clone();
    sideMirrorMaterial.name = side < 0 ? "driver_live_mirror" : "passenger_live_mirror";
    rounded("main_mirror_glass", .56, .72, .018, .1, [side * .155, .17, -.01], sideMirrorMaterial, [0, side * Math.PI / 2, 0], mirror).userData.mirrorSurface = side;
    rounded("convex_mirror_glass", .55, .25, .02, .1, [side * .16, -.37, -.01], sideMirrorMaterial, [0, side * Math.PI / 2, 0], mirror).userData.mirrorSurface = side;

    // Cube captures are intentionally scaled and throttled: one side is refreshed
    // per tick, keeping the useful live reflection without twelve extra renders/frame.
    if (qualityLevel > 0) {
      const resolution = qualityLevel > 2 ? 256 : qualityLevel > 1 ? 128 : 64;
      const target = new T.WebGLCubeRenderTarget(resolution, {
        generateMipmaps: true,
        minFilter: T.LinearMipmapLinearFilter,
        magFilter: T.LinearFilter,
        type: T.UnsignedByteType,
        colorSpace: T.SRGBColorSpace,
      });
      target.texture.name = side < 0 ? "driver_mirror_live_capture" : "passenger_mirror_live_capture";
      const capture = new T.CubeCamera(.25, qualityLevel > 1 ? 420 : 220, target);
      capture.name = side < 0 ? "driver_mirror_camera" : "passenger_mirror_camera";
      capture.position.set(side * .16, .12, -.02); mirror.add(capture);
      sideMirrorMaterial.envMap = target.texture;
      sideMirrorMaterial.envMapIntensity = qualityLevel > 1 ? 1.18 : .9;
      sideMirrorMaterial.needsUpdate = true;
      mirrorCaptures.push({ camera: capture, target, side, lastUpdate: -Infinity });
    }
  }

  root.userData.glassMaterial = glass;
  root.userData.mirrorSurfaces = [];
  root.traverse((object) => { if (object.userData?.mirrorSurface) root.userData.mirrorSurfaces.push(object); });
  let nextMirror = 0;
  root.userData.update = (renderer, scene, now = performance.now(), active = true) => {
    if (!active || !renderer || !scene || !mirrorCaptures.length) return;
    const interval = qualityLevel > 2 ? 180 : qualityLevel > 1 ? 360 : 760;
    const capture = mirrorCaptures[nextMirror % mirrorCaptures.length];
    if (now - capture.lastUpdate < interval) return;
    const visibility = root.userData.mirrorSurfaces.map((surface) => surface.visible);
    root.userData.mirrorSurfaces.forEach((surface) => { surface.visible = false; });
    try { capture.camera.update(renderer, scene); }
    finally { root.userData.mirrorSurfaces.forEach((surface, index) => { surface.visible = visibility[index]; }); }
    capture.lastUpdate = now;
    nextMirror = (nextMirror + 1) % mirrorCaptures.length;
  };
  root.userData.dispose = () => { mirrorCaptures.forEach(({ target }) => target.dispose()); doorMap?.dispose(); mirrorGlass.dispose(); };
  return root;
}
