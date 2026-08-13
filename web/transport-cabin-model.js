export function createOriginalEuropeanCabin({ THREE: T, bus = false, qualityLevel = 2 }) {
  const root = new T.Group(); root.name = "aster_original_cabin";
  const material = (name, color, roughness, metalness = 0, extra = {}) => {
    const value = new T.MeshPhysicalMaterial({ name, color, roughness, metalness, ...extra });
    return value;
  };
  const soft = material("soft_touch_dashboard", 0x171b1e, .88, .02, { clearcoat: .08 });
  const polymer = material("satin_polymer", 0x272d30, .56, .05);
  const leather = material("stitched_charcoal_leather", 0x111416, .82, .01, { sheen: .18, sheenColor: new T.Color(0x697379) });
  const aluminium = material("brushed_aluminium", 0x8b969b, .28, .76, { clearcoat: .22 });
  const piano = material("black_glass_controls", 0x050708, .12, .22, { clearcoat: 1, clearcoatRoughness: .08 });
  const fabric = material("woven_seat_fabric", 0x242a2e, .98, 0, { sheen: .32, sheenColor: new T.Color(0x53626a) });
  const headliner = material("woven_headliner", 0xaab0ad, .96, 0, { sheen: .12, sheenColor: new T.Color(0xd8d4c8) });
  const sleeperFabric = material("sleeper_textile", 0x31434a, .94, 0, { sheen: .28, sheenColor: new T.Color(0x63868c) });
  const screenMaterial = new T.MeshBasicMaterial({ name: "live_instrument_display", color: 0xffffff, toneMapped: false });
  const accent = new T.MeshBasicMaterial({ color: 0x57e5d0, toneMapped: false });
  const add = (geometry, mat, name, position, rotation = [0, 0, 0], parent = root) => {
    const mesh = new T.Mesh(geometry, mat); mesh.name = name; mesh.position.set(...position); mesh.rotation.set(...rotation);
    mesh.castShadow = true; mesh.receiveShadow = true; parent.add(mesh); return mesh;
  };
  const box = (name, size, position, mat = soft, rotation) => add(new T.BoxGeometry(...size, 3, 2, 3), mat, name, position, rotation);
  const roundedPanel = (name, width, height, depth, radius, position, mat, rotation = [0, 0, 0]) => {
    const shape = new T.Shape(); const x = -width / 2, y = -height / 2;
    shape.moveTo(x + radius, y); shape.lineTo(x + width - radius, y); shape.quadraticCurveTo(x + width, y, x + width, y + radius);
    shape.lineTo(x + width, y + height - radius); shape.quadraticCurveTo(x + width, y + height, x + width - radius, y + height);
    shape.lineTo(x + radius, y + height); shape.quadraticCurveTo(x, y + height, x, y + height - radius);
    shape.lineTo(x, y + radius); shape.quadraticCurveTo(x, y, x + radius, y);
    const geometry = new T.ExtrudeGeometry(shape, { depth, bevelEnabled: true, bevelSegments: qualityLevel > 1 ? 3 : 1, bevelSize: .035, bevelThickness: .035, curveSegments: qualityLevel > 1 ? 12 : 5 });
    geometry.center(); return add(geometry, mat, name, position, rotation);
  };
  const frontZ = bus ? -5.93 : -5.79, sideX = bus ? 2.35 : 2.18;
  roundedPanel("dashboard_swept_shell", bus ? 4.72 : 4.42, .68, .72, .18, [0, 2.22, frontZ], soft, [-.06, 0, 0]);
  roundedPanel("dashboard_upper_pad", bus ? 4.82 : 4.52, .18, 1.25, .09, [0, 2.63, frontZ + .12], polymer, [-.04, 0, 0]);
  roundedPanel("driver_instrument_hood", 1.92, .48, .64, .2, [-.75, 2.66, frontZ - .08], soft, [-.08, 0, 0]);
  roundedPanel("centre_stack", 1.18, 1.18, .18, .16, [.92, 2.15, frontZ - .49], piano, [0, 0, -.035]);
  const displayCanvas = document.createElement("canvas"); displayCanvas.width = 768; displayCanvas.height = 288;
  const displayTexture = new T.CanvasTexture(displayCanvas); displayTexture.colorSpace = T.SRGBColorSpace; screenMaterial.map = displayTexture;
  add(new T.PlaneGeometry(1.64, .61), screenMaterial, "instrument_cluster_live", [-.67, 2.48, frontZ - .47]);
  const navCanvas = document.createElement("canvas"); navCanvas.width = 384; navCanvas.height = 384;
  const navTexture = new T.CanvasTexture(navCanvas); navTexture.colorSpace = T.SRGBColorSpace;
  add(new T.PlaneGeometry(.82, .72), new T.MeshBasicMaterial({ map: navTexture, toneMapped: false }), "navigation_touchscreen", [.92, 2.29, frontZ - .61]);
  const wheel = new T.Group(); wheel.name = "steering_wheel"; wheel.position.set(-1.04, 2.55, frontZ + .5); wheel.rotation.x = -.18;
  add(new T.TorusGeometry(.54, .075, qualityLevel > 1 ? 16 : 10, qualityLevel > 1 ? 48 : 24), leather, "steering_rim", [0, 0, 0], [0, 0, 0], wheel);
  for (const angle of [-2.48, -.66, Math.PI / 2]) {
    const spoke = box("steering_spoke", [.42, .09, .09], [Math.cos(angle) * .22, Math.sin(angle) * .22, 0], polymer, [0, 0, angle]); wheel.add(spoke);
  }
  add(new T.CylinderGeometry(.2, .2, .1, 32), piano, "steering_hub", [0, 0, 0], [Math.PI / 2, 0, 0], wheel);
  for (const side of [-1, 1]) for (let row = 0; row < 2; row++) add(new T.CylinderGeometry(.035, .035, .022, 12), accent, "steering_button", [side * .24, .06 - row * .13, -.065], [Math.PI / 2, 0, 0], wheel);
  root.add(wheel);
  add(new T.CylinderGeometry(.07, .11, .72, 18), polymer, "steering_column", [-1.04, 2.2, frontZ + .84], [Math.PI / 2, 0, 0]);
  for (const side of [-1, 1]) {
    add(new T.CylinderGeometry(.025, .035, .48, 12), polymer, side < 0 ? "indicator_stalk" : "retarder_stalk", [-1.04 + side * .45, 2.51, frontZ + .5], [0, 0, Math.PI / 2]);
    const vent = new T.Group(); vent.name = "round_air_vent"; vent.position.set(side * 1.68, 2.39, frontZ - .48);
    add(new T.TorusGeometry(.21, .04, 10, 32), aluminium, "vent_bezel", [0, 0, 0], [0, 0, 0], vent);
    for (let line = -2; line <= 2; line++) add(new T.BoxGeometry(.31, .018, .025), aluminium, "vent_fin", [0, line * .065, -.012], [0, 0, 0], vent);
    root.add(vent);
  }
  for (let i = 0; i < 10; i++) add(new T.CylinderGeometry(.052, .052, .035, 14), i === 2 ? material("hazard_red", 0xb92324, .3) : polymer, "centre_control", [.56 + (i % 5) * .18, 1.76 + Math.floor(i / 5) * .18, frontZ - .59], [Math.PI / 2, 0, 0]);
  for (const x of [-1.25, -.88]) roundedPanel("pedal", .24, .4, .05, .035, [x, .59, frontZ + .12], aluminium, [-.34, 0, 0]);
  const selector = add(new T.CylinderGeometry(.045, .07, .65, 14), aluminium, "drive_selector", [.23, 1.68, frontZ + .92], [0, 0, -.2]);
  add(new T.SphereGeometry(.1, 16, 12), leather, "selector_grip", [selector.position.x + .12, selector.position.y + .31, selector.position.z], [0, 0, 0]);
  for (const x of [-1.04, 1.08]) {
    const seat = new T.Group(); seat.name = x < 0 ? "driver_air_seat" : "passenger_air_seat";
    add(new T.CapsuleGeometry(.43, .48, 8, qualityLevel > 1 ? 20 : 12), fabric, "seat_cushion", [0, 1.05, frontZ + 2.25], [Math.PI / 2, 0, 0], seat);
    add(new T.CapsuleGeometry(.46, .8, 8, qualityLevel > 1 ? 20 : 12), fabric, "seat_back", [0, 1.71, frontZ + 2.54], [-.13, 0, 0], seat);
    add(new T.CapsuleGeometry(.3, .16, 8, 16), leather, "head_rest", [0, 2.51, frontZ + 2.64], [0, 0, 0], seat);
    for (const sx of [-.29, .29]) add(new T.BoxGeometry(.014, .82, .018), aluminium, "seat_stitching", [sx, 1.73, frontZ + 2.13], [0, 0, 0], seat);
    seat.position.x = x; root.add(seat);
    box("seat_suspension_base", [.78,.48,.82], [x,.63,frontZ+2.35], polymer);
    const belt = box("three_point_seatbelt", [.045,1.38,.035], [x + (x < 0 ? -.32 : .32),1.72,frontZ+2.15], material("seatbelt_webbing",0x090b0c,.9));
    belt.rotation.z = x < 0 ? -.16 : .16;
  }
  for (const side of [-1, 1]) {
    roundedPanel("door_card", 2.45, 1.8, .1, .18, [side * sideX, 2.0, frontZ + 1.02], soft, [0, Math.PI / 2, 0]);
    box("door_armrest", [.26, .24, 1.08], [side * (sideX - .11), 2.04, frontZ + .78], polymer);
    add(new T.TorusGeometry(.15, .032, 8, 20, Math.PI), aluminium, "door_handle", [side * (sideX - .16), 2.4, frontZ + .43], [0, Math.PI / 2, side * Math.PI / 2]);
    roundedPanel("door_storage", .72, .33, .08, .12, [side * (sideX - .09), 1.27, frontZ + 1.15], polymer, [0, Math.PI / 2, 0]);
    add(new T.PlaneGeometry(.72, .9), material("mirror_glass", 0x91aab3, .06, .9, { clearcoat: 1 }), "interior_mirror_surface", [side * (sideX + .34), 3.42, frontZ - .48], [0, side * Math.PI / 2, 0]);
  }
  box("rubber_floor", [4.1, .04, 3.4], [0, .47, frontZ + 1.12], material("rubber_floor", 0x080a0b, 1));
  roundedPanel("central_engine_tunnel", 1.12, .38, 2.25, .18, [0,.68,frontZ+1.5], polymer);
  box("cab_rear_wall", [4.55,3.72,.14], [0,2.5,frontZ+4.2], soft);
  box("cab_ceiling_headliner", [4.38,.12,4.5], [0,4.73,frontZ+1.68], headliner);
  for (const side of [-1,1]) box("sleeper_side_liner", [.12,2.4,1.55], [side*2.2,2.55,frontZ+3.45], headliner);
  if (!bus) {
    roundedPanel("sleeper_mattress", 4.05, .38, 1.42, .17, [0,1.05,frontZ+3.55], sleeperFabric);
    box("sleeper_bed_base", [4.2,.32,1.55], [0,.74,frontZ+3.55], polymer);
    roundedPanel("sleeper_pillow", 1.05,.24,.55,.12, [-1.35,1.32,frontZ+3.78], headliner, [0,0,.08]);
    for (const side of [-1,1]) {
      roundedPanel("upper_storage_cabinet", 1.78,.72,.5,.14, [side*1.04,4.18,frontZ+3.73], polymer);
      box("cabinet_handle", [.56,.045,.06], [side*1.04,4.02,frontZ+3.46], aluminium);
      const curtain = box("sleeper_blackout_curtain", [.05,2.2,1.35], [side*2.13,2.78,frontZ+3.42], sleeperFabric);
      curtain.rotation.z = side*.035;
    }
    roundedPanel("folding_table", 1.18,.08,.72,.1, [1.14,1.72,frontZ+2.93], aluminium, [-.08,0,0]);
  }
  for (const x of [-.18,.18]) add(new T.CylinderGeometry(.09,.075,.18,18), polymer, "dashboard_cupholder", [x,1.5,frontZ+.96]);
  box("overhead_console", [2.3, .3, .72], [0, 4.55, frontZ + .03], polymer);
  for (const side of [-1,1]) box("sun_visor", [1.48,.46,.055], [side*.92,4.3,frontZ-.56], headliner, [.08,0,0]);
  add(new T.PlaneGeometry(.62,.28), material("interior_centre_mirror",0x91aab3,.05,.88,{clearcoat:1}), "interior_centre_mirror", [0,4.08,frontZ-.64]);
  for (let i = 0; i < 5; i++) add(new T.CylinderGeometry(.045, .045, .025, 12), accent, "overhead_switch", [-.36 + i * .18, 4.39, frontZ - .2], [Math.PI / 2, 0, 0]);
  const glow = new T.PointLight(0x82d8d0, qualityLevel > 1 ? .55 : .2, 5, 2); glow.name = "ambient_cabin_light"; glow.position.set(0, 3.65, frontZ + .7); root.add(glow);
  root.userData.steering = wheel;
  root.userData.instrument = { canvas: displayCanvas, context: displayCanvas.getContext("2d"), texture: displayTexture };
  root.userData.navigation = { canvas: navCanvas, context: navCanvas.getContext("2d"), texture: navTexture };
  root.userData.dispose = () => root.traverse((object) => { object.geometry?.dispose?.(); if (Array.isArray(object.material)) object.material.forEach((m) => m.dispose()); else object.material?.dispose?.(); });
  return root;
}
