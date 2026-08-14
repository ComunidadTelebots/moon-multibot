const BIOMES = {
  mediterranean: ["boar", "deer", "fox", "rabbit"],
  alpine: ["ibex", "deer", "marmot"],
  atlantic: ["deer", "badger", "fox"],
  nordic: ["moose", "reindeer", "lynx"],
  wetland: ["heron", "otter", "gull"],
  rural: ["sheep", "cow", "horse", "dog"],
};

function seeded(index, salt = 0) {
  const value = Math.sin(index * 91.17 + salt * 37.31) * 43758.5453;
  return value - Math.floor(value);
}

export function createAmbientLife({ THREE, scene, qualityLevel = 2, roadHalfWidth = 15 }) {
  const root = new THREE.Group();
  root.name = "ambient-life";
  scene.add(root);
  const count = [8, 14, 24, 36][qualityLevel] || 14;
  const pool = [];
  const bodyGeometry = new THREE.CapsuleGeometry(.28, .62, 3, 6);
  const headGeometry = new THREE.SphereGeometry(.23, 7, 5);
  const distantGeometry = new THREE.BoxGeometry(.48, .72, .32);
  const animalMaterial = new THREE.MeshStandardMaterial({ color: 0x78583b, roughness: .94 });
  const pedestrianMaterial = new THREE.MeshStandardMaterial({ color: 0x426b82, roughness: .86 });
  const safetyMaterial = new THREE.MeshStandardMaterial({ color: 0xf2a326, roughness: .78 });
  const workwearMaterial = new THREE.MeshStandardMaterial({ color: 0x173b55, roughness: .88 });
  const skinMaterial = new THREE.MeshStandardMaterial({ color: 0xc68f6c, roughness: .92 });

  function limb(parent, name, material, radius, length, x, y) {
    const pivot = new THREE.Group(); pivot.name = `${name}_pivot`; pivot.position.set(x, y, 0);
    const mesh = new THREE.Mesh(new THREE.CapsuleGeometry(radius, length, 3, 6), material);
    mesh.name = name; mesh.position.y = -length * .5; pivot.add(mesh); parent.add(pivot);
    return pivot;
  }

  function makeActor(index) {
    const pedestrian = index % 5 === 0;
    const group = new THREE.Group();
    const detailed = new THREE.Group();
    const role = pedestrian ? ["road_worker", "logistics", "civilian"][Math.floor(seeded(index, 13) * 3)] : "wildlife";
    const clothing = role === "road_worker" ? safetyMaterial : role === "logistics" ? workwearMaterial : pedestrianMaterial;
    const body = new THREE.Mesh(bodyGeometry, pedestrian ? clothing : animalMaterial);
    body.position.y = pedestrian ? .9 : .58;
    if (!pedestrian) { body.rotation.z = Math.PI / 2; body.scale.set(1.2, .72, .75); }
    detailed.add(body);
    const head = new THREE.Mesh(headGeometry, pedestrian ? skinMaterial : animalMaterial);
    head.position.set(pedestrian ? 0 : .5, pedestrian ? 1.55 : .72, 0);
    detailed.add(head);
    const animatedParts = {};
    if (pedestrian) {
      animatedParts.leftArm = limb(detailed, "pedestrian_left_arm", clothing, .075, .52, -.34, 1.28);
      animatedParts.rightArm = limb(detailed, "pedestrian_right_arm", clothing, .075, .52, .34, 1.28);
      animatedParts.leftLeg = limb(detailed, "pedestrian_left_leg", workwearMaterial, .09, .58, -.16, .66);
      animatedParts.rightLeg = limb(detailed, "pedestrian_right_leg", workwearMaterial, .09, .58, .16, .66);
      if (role !== "civilian") {
        const helmet = new THREE.Mesh(new THREE.SphereGeometry(.255, 8, 5, 0, Math.PI * 2, 0, Math.PI * .55), safetyMaterial);
        helmet.name = "professional_safety_helmet"; helmet.position.y = 1.69; detailed.add(helmet);
      }
    } else {
      for (const [key, x, z] of [["frontLeft", .34, -.24], ["frontRight", .34, .24], ["rearLeft", -.34, -.24], ["rearRight", -.34, .24]]) {
        const leg = new THREE.Group(); leg.name = `animal_${key}_leg_pivot`; leg.position.set(x, .45, z);
        const hoof = new THREE.Mesh(new THREE.CapsuleGeometry(.055, .34, 2, 5), animalMaterial); hoof.position.y = -.24; leg.add(hoof); detailed.add(leg); animatedParts[key] = leg;
      }
    }
    const distant = new THREE.Mesh(distantGeometry, pedestrian ? pedestrianMaterial : animalMaterial);
    distant.position.y = pedestrian ? .85 : .48;
    group.add(detailed, distant);
    group.userData = { index, pedestrian, role, animatedParts, detailed, distant, state: "idle", stateUntil: 0, heading: seeded(index, 2) * Math.PI * 2, speed: 0 };
    root.add(group); pool.push(group); return group;
  }

  function place(actor, vehicle, recycle = false) {
    const i = actor.userData.index;
    const side = seeded(i, recycle ? Date.now() % 997 : 3) > .5 ? 1 : -1;
    const verge = roadHalfWidth + 7 + seeded(i, 4) * 42;
    actor.position.set(side * verge, 0, vehicle.position.z - 80 - seeded(i, 5) * 620);
    actor.rotation.y = actor.userData.heading;
  }
  for (let i = 0; i < count; i++) makeActor(i);
  let initialized = false;

  return {
    update({ vehicle, camera, biome = "rural", time = performance.now(), dt = 1 / 60 }) {
      if (!vehicle || !camera) return;
      if (!initialized) { pool.forEach(actor => place(actor, vehicle)); initialized = true; }
      const species = BIOMES[biome] || BIOMES.rural;
      for (const actor of pool) {
        const data = actor.userData;
        data.species = data.pedestrian ? "pedestrian" : species[data.index % species.length];
        const dx = actor.position.x - vehicle.position.x, dz = actor.position.z - vehicle.position.z;
        const distance = Math.hypot(dx, dz);
        if (dz > 120 || dz < -720) place(actor, vehicle, true);
        actor.visible = distance < (qualityLevel >= 2 ? 380 : 240);
        if (!actor.visible) continue;
        data.detailed.visible = distance < 95;
        data.distant.visible = !data.detailed.visible;
        const threatened = distance < (data.pedestrian ? 22 : 34);
        if (threatened) { data.state = "flee"; data.stateUntil = time + 2600; }
        else if (time > data.stateUntil) {
          data.state = seeded(data.index, Math.floor(time / 5000)) > .54 ? "walk" : "idle";
          data.stateUntil = time + 2400 + seeded(data.index, 8) * 4200;
          data.heading += (seeded(data.index, Math.floor(time / 3000)) - .5) * 1.2;
        }
        data.speed = data.state === "flee" ? 4.2 : data.state === "walk" ? (data.pedestrian ? 1.2 : .75) : 0;
        if (threatened) data.heading = Math.atan2(dx, dz);
        actor.rotation.y = data.heading;
        actor.position.x += Math.sin(data.heading) * data.speed * dt;
        actor.position.z += Math.cos(data.heading) * data.speed * dt;
        const minVerge = roadHalfWidth + (data.pedestrian ? 3 : 6);
        if (Math.abs(actor.position.x) < minVerge) actor.position.x = Math.sign(actor.position.x || 1) * minVerge;
        const moving = data.state === "walk" || data.state === "flee";
        const cadence = data.state === "flee" ? .015 : data.pedestrian ? .009 : .011;
        const stride = moving ? Math.sin(time * cadence + data.index) : 0;
        data.detailed.position.y = moving ? Math.abs(stride) * (data.pedestrian ? .045 : .025) : 0;
        if (data.pedestrian) {
          data.animatedParts.leftArm.rotation.x = stride * .62;
          data.animatedParts.rightArm.rotation.x = -stride * .62;
          data.animatedParts.leftLeg.rotation.x = -stride * .7;
          data.animatedParts.rightLeg.rotation.x = stride * .7;
          data.detailed.rotation.z = moving ? Math.sin(time * cadence * .5 + data.index) * .018 : 0;
        } else {
          data.animatedParts.frontLeft.rotation.z = stride * .48;
          data.animatedParts.rearRight.rotation.z = stride * .48;
          data.animatedParts.frontRight.rotation.z = -stride * .48;
          data.animatedParts.rearLeft.rotation.z = -stride * .48;
          data.detailed.rotation.x = moving ? Math.sin(time * cadence * 2 + data.index) * .018 : 0;
        }
      }
    },
    dispose() { scene.remove(root); bodyGeometry.dispose(); headGeometry.dispose(); distantGeometry.dispose(); animalMaterial.dispose(); pedestrianMaterial.dispose(); safetyMaterial.dispose(); workwearMaterial.dispose(); skinMaterial.dispose(); },
    root,
  };
}
