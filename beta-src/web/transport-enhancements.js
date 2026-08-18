/* Procedural, original visual enhancements for Rutas 3D.
 * This module deliberately has no imports: pass the active THREE namespace in.
 */

const clamp = (value, min, max) => Math.max(min, Math.min(max, value));

export function createTransportEnhancements(options) {
  const {
    THREE: T,
    scene,
    renderer,
    sun,
    vehicle,
    qualityLevel = 2,
    roadWidth = 30,
  } = options;
  if (!T || !scene) throw new Error("THREE and scene are required");

  const root = new T.Group();
  root.name = "transport-enhancements";
  scene.add(root);
  const animated = [];
  const disposable = [];
  const originalBackground = scene.background;
  const originalEnvironmentIntensity = scene.environmentIntensity;
  const material = (params) => {
    const value = new T.MeshStandardMaterial(params);
    disposable.push(value);
    return value;
  };
  const mesh = (geometry, surface) => {
    disposable.push(geometry);
    const value = new T.Mesh(geometry, surface);
    value.castShadow = qualityLevel > 1;
    value.receiveShadow = true;
    return value;
  };

  // Large inverted sphere with a vertical atmospheric gradient and a moving sun halo.
  const skyUniforms = {
    topColor: { value: new T.Color(0x2878bd) },
    horizonColor: { value: new T.Color(0xd8eff8) },
    sunsetColor: { value: new T.Color(0xffa45d) },
    sunDirection: { value: new T.Vector3(-0.35, 0.78, -0.25).normalize() },
    daylight: { value: 1 },
  };
  const skyMaterial = new T.ShaderMaterial({
    side: T.BackSide,
    depthWrite: false,
    uniforms: skyUniforms,
    vertexShader: `varying vec3 vWorld; void main(){
      vec4 world=modelMatrix*vec4(position,1.0); vWorld=normalize(world.xyz-cameraPosition);
      gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.0);
    }`,
    fragmentShader: `varying vec3 vWorld; uniform vec3 topColor,horizonColor,sunsetColor,sunDirection; uniform float daylight;
      void main(){
        float h=clamp(vWorld.y*.72+.28,0.,1.);
        vec3 sky=mix(horizonColor,topColor,smoothstep(0.,.72,h));
        float sunDot=max(dot(normalize(vWorld),normalize(sunDirection)),0.);
        float glow=pow(sunDot,18.)*.55+pow(sunDot,320.)*1.8;
        float dusk=1.-smoothstep(.08,.35,abs(sunDirection.y));
        sky=mix(sky,sunsetColor,dusk*(1.-smoothstep(0.,.32,h))*.72);
        sky+=vec3(1.,.76,.42)*glow;
        vec3 night=vec3(.012,.025,.075)+vec3(.025,.035,.075)*h;
        gl_FragColor=vec4(mix(night,sky,daylight),1.);
        #include <tonemapping_fragment>
        #include <colorspace_fragment>
      }`,
    toneMapped: true,
  });
  disposable.push(skyMaterial);
  const sky = mesh(new T.SphereGeometry(700, qualityLevel > 1 ? 48 : 24, 18), skyMaterial);
  sky.frustumCulled = false;
  root.add(sky);

  const mountainMaterial = material({ color: 0x567366, roughness: 1, flatShading: true });
  const ridgeGeometry = new T.ConeGeometry(22, 34, 7);
  disposable.push(ridgeGeometry);
  const ridgeCount = qualityLevel > 1 ? 42 : 22;
  const ridges = new T.InstancedMesh(ridgeGeometry, mountainMaterial, ridgeCount);
  const dummy = new T.Object3D();
  for (let i = 0; i < ridgeCount; i += 1) {
    const side = i % 2 ? -1 : 1;
    const depth = Math.floor(i / 2);
    dummy.position.set(side * (110 + (depth % 4) * 16), 8 + (i % 5) * 2, -430 + depth * 45);
    dummy.scale.set(1.6 + (i % 3) * 0.35, 0.8 + (i % 4) * 0.12, 1.4);
    dummy.rotation.y = (i * 1.73) % Math.PI;
    dummy.updateMatrix();
    ridges.setMatrixAt(i, dummy.matrix);
  }
  ridges.receiveShadow = true;
  root.add(ridges);

  // A low-cost second atmospheric layer gives depth without a post-processing pass.
  const hazeMaterial = new T.MeshBasicMaterial({
    color: 0xb9d4df,
    transparent: true,
    opacity: qualityLevel > 1 ? 0.075 : 0.04,
    depthWrite: false,
    side: T.DoubleSide,
  });
  disposable.push(hazeMaterial);
  const hazeGeometry = new T.PlaneGeometry(560, 42);
  disposable.push(hazeGeometry);
  for (const z of [-390, 390]) {
    const haze = new T.Mesh(hazeGeometry, hazeMaterial);
    haze.position.set(0, 18, z);
    if (z > 0) haze.rotation.y = Math.PI;
    root.add(haze);
  }

  // Road texture cues: subtle wheel wear, reflectors, drain covers and delineator posts.
  const wear = material({ color: 0x191d21, roughness: 0.96, transparent: true, opacity: 0.28 });
  for (const laneX of [-8, -3.2, 3.2, 8]) {
    for (const offset of [-0.72, 0.72]) {
      const strip = mesh(new T.PlaneGeometry(0.42, 880), wear);
      strip.rotation.x = -Math.PI / 2;
      strip.position.set(laneX + offset, 0.181, 0);
      root.add(strip);
    }
  }
  const wetRoad = material({
    color: 0x15202a,
    roughness: 0.2,
    metalness: 0,
    transparent: true,
    opacity: 0,
    depthWrite: false,
  });
  const wetOverlay = mesh(new T.PlaneGeometry(roadWidth - 1.4, 880), wetRoad);
  wetOverlay.rotation.x = -Math.PI / 2;
  wetOverlay.position.y = 0.184;
  wetOverlay.receiveShadow = qualityLevel > 0;
  root.add(wetOverlay);

  // Irregular puddles are reserved for high/ultra, keeping mobile draw calls bounded.
  const puddles = [];
  if (qualityLevel > 1) {
    const puddleMaterial = material({
      color: 0x476579,
      roughness: 0.08,
      metalness: 0.05,
      transparent: true,
      opacity: 0,
      depthWrite: false,
    });
    const puddleGeometry = new T.CircleGeometry(1, 18);
    disposable.push(puddleGeometry);
    for (let i = 0; i < 18; i += 1) {
      const puddle = new T.Mesh(puddleGeometry, puddleMaterial);
      puddle.rotation.x = -Math.PI / 2;
      puddle.rotation.z = i * 1.91;
      puddle.scale.set(0.7 + (i % 4) * 0.42, 1.5 + (i % 3) * 0.55, 1);
      puddle.position.set(((i * 7.7) % (roadWidth - 7)) - (roadWidth - 7) / 2, 0.188, -410 + i * 48);
      root.add(puddle);
      puddles.push(puddle);
    }
  }
  const reflectorMaterial = new T.MeshBasicMaterial({ color: 0xe8f7ff });
  disposable.push(reflectorMaterial);
  const reflectorGeometry = new T.BoxGeometry(0.12, 0.045, 0.24);
  disposable.push(reflectorGeometry);
  for (let z = -430; z <= 430; z += 12) {
    for (const x of [-roadWidth / 2 + 0.55, roadWidth / 2 - 0.55]) {
      const reflector = new T.Mesh(reflectorGeometry, reflectorMaterial);
      reflector.position.set(x, 0.205, z);
      root.add(reflector);
    }
  }

  const postMaterial = material({ color: 0xf3f1df, roughness: 0.75 });
  const black = material({ color: 0x111820, roughness: 0.7 });
  for (let z = -420; z < 440; z += qualityLevel > 0 ? 40 : 80) {
    for (const side of [-1, 1]) {
      const post = new T.Group();
      const body = mesh(new T.BoxGeometry(0.22, 1.05, 0.18), postMaterial);
      body.position.y = 0.52;
      const marker = mesh(new T.BoxGeometry(0.235, 0.24, 0.19), black);
      marker.position.y = 0.74;
      post.add(body, marker);
      post.position.set(side * (roadWidth / 2 + 2.1), 0, z);
      root.add(post);
    }
  }

  // Original overhead gantry and signs; blank panels are safe to localise later with CanvasTexture.
  const metal = material({ color: 0x76838a, roughness: 0.38, metalness: 0.72 });
  const signBlue = material({ color: 0x176ca4, roughness: 0.58, metalness: 0.08 });
  for (const z of [-250, 185]) {
    const gantry = new T.Group();
    for (const x of [-17, 17]) {
      const column = mesh(new T.CylinderGeometry(0.16, 0.21, 8.5, 10), metal);
      column.position.set(x, 4.25, 0);
      gantry.add(column);
    }
    const beam = mesh(new T.BoxGeometry(34.5, 0.25, 0.25), metal);
    beam.position.y = 8.35;
    gantry.add(beam);
    for (const x of [-6, 6]) {
      const panel = mesh(new T.BoxGeometry(9.2, 2.35, 0.16), signBlue);
      panel.position.set(x, 7.05, 0);
      gantry.add(panel);
    }
    gantry.position.z = z;
    root.add(gantry);
  }

  // Attach non-invasive detail pieces and animation anchors to the current vehicle.
  const vehicleDetails = new T.Group();
  vehicleDetails.name = "enhanced-vehicle-details";
  if (vehicle) {
    const ownsDetailedExterior=Boolean(vehicle.getObjectByName?.("aster_viento_detailed_exterior"));
    const glassParams = { color: 0x153447, roughness: 0.12, metalness: 0, transparent: true, opacity: 0.68 };
    const glass = qualityLevel > 1 && T.MeshPhysicalMaterial
      ? new T.MeshPhysicalMaterial({ ...glassParams, clearcoat: 0.72, clearcoatRoughness: 0.16 })
      : material(glassParams);
    if (!disposable.includes(glass)) disposable.push(glass);
    if(!ownsDetailedExterior){const windshield = mesh(new T.BoxGeometry(4.3, 1.65, 0.055), glass);windshield.position.set(0, 3.52, -7.16);vehicleDetails.add(windshield);}
    const trim = material({ color: 0x10151a, roughness: 0.48, metalness: 0.35 });
    if(!ownsDetailedExterior) for (const side of [-1, 1]) {
      const wiper = mesh(new T.BoxGeometry(0.055, 1.4, 0.06), trim);
      wiper.position.set(side * 1.08, 3.25, -7.22);
      wiper.rotation.z = side * 0.45;
      wiper.userData.baseRotation = wiper.rotation.z;
      wiper.userData.isAnimatedWiper = true;
      animated.push(wiper);
      vehicleDetails.add(wiper);
      for (let z = -5.2; z <= 9.2; z += 1.3) {
        const lampSurface = new T.MeshBasicMaterial({ color: z < 0 ? 0xffb13c : 0xef3b31 });
        disposable.push(lampSurface);
        const lamp = mesh(new T.BoxGeometry(0.09, 0.16, 0.3), lampSurface);
        lamp.position.set(side * 2.69, 1.08, z);
        vehicleDetails.add(lamp);
      }
    }
    const shadow = new T.Mesh(
      new T.PlaneGeometry(5.8, 18),
      new T.MeshBasicMaterial({ color: 0x000000, transparent: true, opacity: 0.22, depthWrite: false }),
    );
    disposable.push(shadow.geometry, shadow.material);
    shadow.rotation.x = -Math.PI / 2;
    shadow.position.set(0, 0.06, 1.2);
    vehicleDetails.add(shadow);
    vehicle.add(vehicleDetails);
  }

  if (renderer && "outputColorSpace" in renderer && T.SRGBColorSpace) {
    renderer.outputColorSpace = T.SRGBColorSpace;
  }

  // Neutral fill light prevents crushed shadows while preserving the directional sun.
  const fill = new T.HemisphereLight(0xb9d8f0, 0x34412f, qualityLevel > 1 ? 0.72 : 0.55);
  fill.name = "transport-atmospheric-fill";
  root.add(fill);

  function update(state = {}) {
    const time = Number(state.time || performance.now()) * 0.001;
    const speed = Math.max(0, Number(state.speed || 0));
    const steering = clamp(Number(state.steering || 0), -1, 1);
    const weather = state.weather || "clear";
    const dayPhase = state.dayPhase == null ? 0.34 : Number(state.dayPhase) % 1;
    const angle = dayPhase * Math.PI * 2 - Math.PI / 2;
    const sunDirection = skyUniforms.sunDirection.value;
    sunDirection.set(Math.cos(angle) * 0.65, Math.sin(angle), -0.35).normalize();
    const daylight = clamp(sunDirection.y * 2.2 + 0.35, 0.035, 1);
    skyUniforms.daylight.value = daylight;
    if (sun) {
      sun.position.copy(sunDirection).multiplyScalar(145);
      sun.intensity = daylight * (weather === "rain" ? 1.35 : 3.1);
      sun.color.set(weather === "rain" ? 0xd8e4ee : 0xffe4b3);
    }
    skyUniforms.topColor.value.set(weather === "rain" ? 0x596b79 : 0x2878bd);
    skyUniforms.horizonColor.value.set(weather === "rain" ? 0xaab6bd : 0xd8eff8);
    fill.intensity = (qualityLevel > 1 ? 0.72 : 0.55) * (0.3 + daylight * 0.7);
    fill.color.set(weather === "rain" ? 0xaab9c4 : daylight < 0.2 ? 0x6074a5 : 0xb9d8f0);
    wetRoad.opacity += ((weather === "rain" ? 0.36 : 0) - wetRoad.opacity) * 0.035;
    hazeMaterial.opacity += ((weather === "fog" ? 0.2 : weather === "rain" ? 0.11 : qualityLevel > 1 ? 0.075 : 0.04) - hazeMaterial.opacity) * 0.025;
    for (const puddle of puddles) puddle.material.opacity = wetRoad.opacity * 0.72;
    if (scene.fog) {
      scene.fog.color.set(weather === "rain" ? 0x8799a5 : daylight < 0.2 ? 0x10182d : 0xa6d0e5);
      scene.fog.near = weather === "fog" ? 34 : 90;
      scene.fog.far = weather === "fog" ? 220 : weather === "rain" ? 330 : 520;
    }
    sky.position.copy(state.cameraPosition || vehicle?.position || new T.Vector3());
    for (const item of animated) {
      const sweep = state.wipers ? Math.sin(time * 8) * 0.62 : 0;
      item.rotation.z += (item.userData.baseRotation + sweep - item.rotation.z) * 0.3;
    }
    if (vehicle) {
      // Mild suspension movement and cab roll; keep small to preserve existing handling.
      vehicleDetails.position.y = Math.sin(time * (3.4 + speed * 0.018)) * Math.min(0.035, speed * 0.0005);
      vehicleDetails.rotation.z = -steering * Math.min(0.018, speed * 0.00024);
    }
  }

  function dispose() {
    scene.remove(root);
    scene.background = originalBackground;
    if (originalEnvironmentIntensity !== undefined) scene.environmentIntensity = originalEnvironmentIntensity;
    if (vehicle) vehicle.remove(vehicleDetails);
    for (const item of disposable) item?.dispose?.();
  }

  return { root, vehicleDetails, update, dispose, uniforms: skyUniforms };
}

export function applyRealisticRendererSettings(THREE, renderer, qualityLevel = 2) {
  if (!renderer) return;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = qualityLevel >= 2 ? 1.08 : 1;
  if (THREE.SRGBColorSpace) renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.shadowMap.enabled = qualityLevel > 0;
  renderer.shadowMap.autoUpdate = qualityLevel > 0;
  if (THREE.PCFSoftShadowMap !== undefined) renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  renderer.sortObjects = true;
}
