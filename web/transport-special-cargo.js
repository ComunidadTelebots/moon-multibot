export const SPECIAL_CARGOES = [
  { id: "reactor", name: "Cámara industrial", mass: 52000, width: 6.2, height: 6.5, length: 12, reward: 148000, color: 0x9e3832 },
  { id: "transformer", name: "Transformador energético", mass: 68000, width: 5.4, height: 5.2, length: 9, reward: 172000, color: 0x38594d },
  { id: "excavator", name: "Excavadora minera", mass: 47000, width: 5.8, height: 5.5, length: 11, reward: 136000, color: 0xd39a28 },
  { id: "turbine", name: "Turbina eólica", mass: 39000, width: 5.7, height: 5.8, length: 10, reward: 129000, color: 0xd9e1e3 },
  { id: "generator", name: "Generador de emergencia", mass: 74000, width: 5.1, height: 5.3, length: 8.5, reward: 191000, color: 0x315b72 },
];

export function createSpecialTransport({ THREE: T, scene, vehicle, qualityLevel = 2 }) {
  const root = new T.Group(); root.name = "special_transport_load"; vehicle.add(root);
  const escorts = new T.Group(); escorts.name = "pilot_escort_convoy"; scene.add(escorts);
  const mat = (color, roughness = .55, metalness = .22) => new T.MeshStandardMaterial({ color, roughness, metalness });
  const add = (parent, geometry, material, position, name) => { const mesh = new T.Mesh(geometry, material); mesh.position.set(...position); mesh.name = name; mesh.castShadow = mesh.receiveShadow = true; parent.add(mesh); return mesh; };
  const box = (parent, size, color, position, name) => add(parent, new T.BoxGeometry(...size), mat(color), position, name);
  const cylinder = (parent, radius, length, color, position, rotation = [0, 0, 0], name = "cylinder") => { const mesh = add(parent, new T.CylinderGeometry(radius, radius, length, qualityLevel > 1 ? 32 : 16), mat(color, .42, .38), position, name); mesh.rotation.set(...rotation); return mesh; };
  let active = null, amberPhase = 0, restricted = false, completedMeters = 0;
  const clear = () => { while (root.children.length) { const object = root.children.pop(); object.traverse?.((node) => { node.geometry?.dispose?.(); node.material?.dispose?.(); }); } };
  const modularTrailer = (cargo) => {
    box(root, [cargo.width + .45, .36, cargo.length + 2.6], 0x234c66, [0, 1.58, 4.5], "hydraulic_modular_platform");
    for (let z = 4.5 - cargo.length / 2; z <= 4.5 + cargo.length / 2; z += 1.15) for (const x of [-cargo.width / 2, cargo.width / 2]) {
      const wheel = cylinder(root, .42, .32, 0x101316, [x, 1.03, z], [0, 0, Math.PI / 2], "steerable_axle_wheel"); wheel.userData.modularWheel = true;
    }
    for (const x of [-cargo.width / 2 + .32, cargo.width / 2 - .32]) box(root, [.12, .12, cargo.length + 2], 0xf0b72e, [x, 1.82, 4.5], "warning_edge");
  };
  const buildCargo = (cargo) => {
    clear(); modularTrailer(cargo);
    if (cargo.id === "reactor") {
      cylinder(root, cargo.width * .45, cargo.height * .72, cargo.color, [0, 4.35, 4.5], [0, 0, Math.PI / 2], "industrial_pressure_chamber");
      for (const z of [1.2, 7.8]) cylinder(root, cargo.width * .49, .28, 0x5d2522, [0, 4.35, z], [Math.PI / 2, 0, 0], "reinforcement_ring");
    } else if (cargo.id === "transformer") {
      box(root, [cargo.width * .82, cargo.height * .7, cargo.length * .72], cargo.color, [0, 3.6, 4.5], "power_transformer_body");
      for (const x of [-1.6, 1.6]) for (let z = 1.8; z < 7.5; z += .65) box(root, [.35, 2.7, .12], 0x738d82, [x, 3.55, z], "cooling_fin");
      for (const x of [-1.2, 0, 1.2]) cylinder(root, .18, 1.3, 0x754f32, [x, 6.05, 4.5], [0, 0, 0], "ceramic_insulator");
    } else if (cargo.id === "excavator") {
      box(root, [4.3, 1.15, 5.5], cargo.color, [0, 2.45, 4.8], "mining_machine_chassis");
      for (const x of [-2.15, 2.15]) box(root, [.72, 1.05, 6.5], 0x24282a, [x, 2.1, 4.8], "crawler_track");
      box(root, [3.3, 2.5, 3], cargo.color, [0, 4.15, 4.8], "operator_body");
      const boom = box(root, [.72, .72, 6], cargo.color, [0, 5.2, 1.55], "folded_excavator_boom"); boom.rotation.x = -.24;
    } else if (cargo.id === "turbine") {
      cylinder(root, 2.35, 4.6, cargo.color, [0, 4.25, 4.5], [Math.PI / 2, 0, 0], "wind_turbine_nacelle");
      cylinder(root, 1.05, 2.3, 0xaeb9bc, [0, 4.25, 1.05], [Math.PI / 2, 0, 0], "turbine_hub");
    } else {
      roundedGenerator(root, cargo);
    }
    for (const x of [-cargo.width / 2, cargo.width / 2]) for (const z of [4.5 - cargo.length / 2, 4.5 + cargo.length / 2]) {
      const beacon = add(root, new T.SphereGeometry(.13, 12, 8), new T.MeshBasicMaterial({ color: 0xffa000 }), [x, 2.02, z], "load_amber_beacon"); beacon.userData.beacon = true;
    }
  };
  const roundedGenerator = (parent, cargo) => {
    box(parent, [cargo.width * .82, cargo.height * .68, cargo.length * .76], cargo.color, [0, 3.65, 4.5], "generator_body");
    for (let x = -1.65; x <= 1.65; x += .55) box(parent, [.1, 2.4, 6], 0x547990, [x, 3.65, 4.5], "generator_rib");
  };
  const pilotCar = (offset, police = false) => {
    const group = new T.Group(); group.userData.offset = offset;
    box(group, [2.05, .72, 4.15], police ? 0x1c5e94 : 0xf1bd25, [0, .78, 0], "escort_vehicle");
    box(group, [1.72, .62, 1.85], 0x23323a, [0, 1.38, .12], "escort_cabin");
    box(group, [1.2, .12, .28], police ? 0x438eff : 0xff9f18, [0, 1.78, 0], "escort_lightbar");
    for (const x of [-.88, .88]) for (const z of [-1.28, 1.28]) cylinder(group, .34, .23, 0x111315, [x, .38, z], [0, 0, Math.PI / 2], "escort_wheel");
    escorts.add(group); return group;
  };
  const frontEscort = pilotCar(-34, true), rearEscort = pilotCar(31, false);
  const select = (id) => { active = SPECIAL_CARGOES.find((cargo) => cargo.id === id) || null; root.visible = escorts.visible = Boolean(active); if (active) buildCargo(active); completedMeters = 0; return active; };
  const update = ({ dt, speed, laneOffset = 0 }) => {
    if (!active) return { active: false };
    amberPhase += dt * 7; completedMeters += speed * dt / 3.6;
    restricted = Math.abs(laneOffset) > 2.4 || speed > 62;
    for (const escort of [frontEscort, rearEscort]) { escort.position.set(vehicle.position.x * .82, vehicle.position.y, vehicle.position.z + escort.userData.offset); escort.rotation.y = vehicle.rotation.y; }
    [...root.children, ...frontEscort.children, ...rearEscort.children].forEach((object) => { if (/beacon|lightbar/.test(object.name)) object.visible = Math.sin(amberPhase + (object.id % 3)) > -.15; });
    return { active: true, cargo: active, maxSpeed: 60, restricted, completedMeters, escortCount: 2, routeWidth: active.width + 1.2, routeHeight: active.height + 1.1 };
  };
  select(null);
  return { root, escorts, select, update, get active() { return active; }, dispose() { clear(); scene.remove(escorts); vehicle.remove(root); } };
}
