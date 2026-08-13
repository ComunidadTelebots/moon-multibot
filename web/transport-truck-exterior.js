export function createDetailedTruckExterior({ THREE: T, paint, glass, chrome, qualityLevel = 2 }) {
  const root = new T.Group(); root.name = "aster_viento_detailed_exterior";
  const dark = new T.MeshStandardMaterial({ color: 0x11191e, roughness: .48, metalness: .42 });
  const rubber = new T.MeshStandardMaterial({ color: 0x0b0d0f, roughness: .94 });
  const lamp = new T.MeshPhysicalMaterial({ color: 0xe9f4f3, emissive: 0xb9e7dc, emissiveIntensity: 1.15, roughness: .1, transmission: .08, clearcoat: 1 });
  const amber = new T.MeshStandardMaterial({ color: 0xffa62c, emissive: 0xff6d00, emissiveIntensity: 1.7, roughness: .24 });
  const red = new T.MeshStandardMaterial({ color: 0xd91d32, emissive: 0x76000c, emissiveIntensity: 1.2, roughness: .28 });
  const resources = [dark, rubber, lamp, amber, red];
  const add = (geometry, material, name, position, rotation = [0,0,0]) => {
    resources.push(geometry); const mesh = new T.Mesh(geometry, material); mesh.name = name;
    mesh.position.set(...position); mesh.rotation.set(...rotation); mesh.castShadow = mesh.receiveShadow = true; root.add(mesh); return mesh;
  };
  const box = (size, material, name, position, rotation) => add(new T.BoxGeometry(...size), material, name, position, rotation);
  function taperedCabGeometry() {
    const positions = new Float32Array([
      -2.5,-1.8,-2.6, 2.5,-1.8,-2.6, -2.5,-1.8,2.45, 2.5,-1.8,2.45,
      -2.22,1.8,-2.22, 2.22,1.8,-2.22, -2.28,1.8,2.3, 2.28,1.8,2.3,
    ]);
    const indices = [0,1,4,1,5,4, 1,3,5,3,7,5, 3,2,7,2,6,7, 2,0,6,0,4,6, 4,5,6,5,7,6, 0,2,1,1,2,3];
    const geometry = new T.BufferGeometry(); geometry.setAttribute("position", new T.BufferAttribute(positions,3)); geometry.setIndex(indices); geometry.computeVertexNormals(); return geometry;
  }
  add(taperedCabGeometry(), paint, "sculpted_cab_shell", [0,2.82,-4.2]);
  box([4.48,.28,4.75], paint, "aerodynamic_roof_cap", [0,4.72,-4.08], [-.035,0,0]);
  box([4.3,.28,1.3], paint, "roof_air_deflector", [0,5.14,-2.65], [-.22,0,0]);
  box([4.24,1.62,.08], glass, "panoramic_split_windshield", [0,3.55,-6.66], [-.025,0,0]);
  box([.085,1.64,.12], dark, "windshield_centre_divider", [0,3.55,-6.72]);
  for (const side of [-1,1]) {
    box([.24,1.9,.26], paint, "sculpted_a_pillar", [side*2.23,3.48,-6.48], [0,0,side*.07]);
    const door = box([.075,2.72,2.68], paint, "cab_door_skin", [side*2.49,2.78,-4.38], [0,0,0]);
    door.material = paint;
    box([.09,.09,1.08], chrome, "door_handle", [side*2.555,3.02,-3.9]);
    box([.12,.3,1.95], dark, "lower_side_step", [side*2.57,.82,-4.2]);
    box([.13,.24,1.62], chrome, "upper_side_step", [side*2.58,1.18,-4.55]);
    const arch = add(new T.TorusGeometry(1.12,.16,10,qualityLevel > 1 ? 32 : 20,Math.PI), paint, "front_wheel_arch", [side*2.48,1.48,-4.6], [0,Math.PI/2,0]); arch.rotation.z = Math.PI/2;
    const mirrorArm = add(new T.CylinderGeometry(.055,.075,1.05,12), dark, "mirror_support", [side*2.82,3.76,-5.74], [0,0,side*.52]);
    const mirror = box([.18,.98,.62], dark, "aerodynamic_mirror_housing", [side*3.02,3.72,-5.96]); mirror.scale.set(1,.9,1);
    box([.025,.76,.45], chrome, "mirror_glass", [side*3.12,3.72,-5.96]);
    box([.2,.2,.08], amber, "side_indicator", [side*2.57,2.0,-6.02]);
  }
  box([4.64,.94,.34], dark, "deep_front_grille", [0,1.72,-6.82]);
  for (let y=1.42;y<=2.02;y+=.2) box([3.85,.065,.09], chrome, "grille_horizontal_blade", [0,y,-7.02]);
  box([4.88,.48,.48], chrome, "reinforced_front_bumper", [0,.88,-6.83]);
  for (const side of [-1,1]) {
    const housing = box([1.02,.78,.18], dark, "headlamp_housing", [side*1.72,1.35,-7.06], [0,0,side*.04]);
    box([.72,.48,.07], lamp, "led_headlamp", [side*1.72,1.37,-7.17]);
    box([.58,.08,.075], amber, "front_indicator", [side*1.72,1.08,-7.18]);
  }
  box([4.55,.12,.72], dark, "windshield_sun_visor", [0,4.48,-6.48], [-.14,0,0]);
  for (const x of [-1.55,-.78,0,.78,1.55]) add(new T.SphereGeometry(.075,10,7), amber, "roof_marker_lamp", [x,5.03,-5.95]);
  box([4.55,3.9,.22], dark, "rear_cab_equipment_panel", [0,2.8,-1.72]);
  for (let y=1.35;y<4.2;y+=.44) box([3.7,.08,.11], chrome, "rear_cab_vent", [0,y,-1.56]);
  box([1.12,1.18,3.25], chrome, "left_fuel_tank", [-2.18,.92,-.18], [0,0,Math.PI/2]);
  box([1.12,1.18,3.25], chrome, "right_fuel_tank", [2.18,.92,-.18], [0,0,Math.PI/2]);
  for (const side of [-1,1]) for (const z of [-1.48,1.12]) box([.09,1.22,.12], dark, "tank_retaining_band", [side*2.18,.92,z]);
  root.userData.dispose = () => resources.forEach(resource => resource.dispose?.());
  return root;
}
