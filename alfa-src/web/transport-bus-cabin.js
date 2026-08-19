/**
 * Converts the shared European cockpit into a purpose-built low-floor bus cab.
 * The instrument panel, steering wheel, driver seat and their materials remain
 * owned by transport-cabin-model; this module only adds bus-specific structure.
 */
export function createBusCabinVariant({ THREE: T, cabin, qualityLevel = 2 }) {
  const root = new T.Group();
  root.name = "nortia_bus_cabin_variant";

  const findMaterial = (name, fallback) => cabin.getObjectByName(name)?.material || fallback;
  const soft = findMaterial("dashboard_swept_shell", new T.MeshStandardMaterial({ color: 0x242b30, roughness: .82 }));
  const polymer = findMaterial("floor_height_centre_console", soft);
  const metal = findMaterial("seat_upper_suspension_frame", new T.MeshStandardMaterial({ color: 0x9aa4a8, roughness: .32, metalness: .7 }));
  const rubber = findMaterial("rubber_floor", new T.MeshStandardMaterial({ color: 0x111416, roughness: 1 }));
  const glass = new T.MeshPhysicalMaterial({
    name: "bus_partition_safety_glass", color: 0xb8e0e4, roughness: .08,
    metalness: 0, transmission: .82, transparent: true, opacity: .28,
    thickness: .025, ior: 1.5, clearcoat: .6, side: T.DoubleSide,
  });
  const screen = new T.MeshBasicMaterial({ name: "bus_fare_screen", color: 0x52e2d0, toneMapped: false });
  const yellow = new T.MeshPhysicalMaterial({ name: "bus_handrail_yellow", color: 0xf5c842, roughness: .3, metalness: .45, clearcoat: .25 });

  const add = (geometry, material, name, position, rotation = [0, 0, 0]) => {
    const mesh = new T.Mesh(geometry, material);
    mesh.name = name;
    mesh.position.set(...position);
    mesh.rotation.set(...rotation);
    mesh.castShadow = material !== glass;
    mesh.receiveShadow = true;
    root.add(mesh);
    return mesh;
  };
  const box = (name, size, position, material = soft, rotation) =>
    add(new T.BoxGeometry(...size), material, name, position, rotation);
  const tube = (name, radius, length, position, rotation = [0, 0, 0], material = yellow) =>
    add(new T.CylinderGeometry(radius, radius, length, qualityLevel > 1 ? 18 : 10), material, name, position, rotation);

  // Remove truck/passenger architecture while retaining the shared driver rig.
  for (const name of ["passenger_air_seat", "cab_rear_wall", "central_engine_tunnel"]) {
    const object = cabin.getObjectByName(name);
    if (object) object.visible = false;
  }
  const passengerOnly = new Set([
    "seat_upper_suspension_frame", "seat_lower_slide_rail", "air_suspension_scissor",
    "air_suspension_bellows", "seat_adjustment_control", "three_point_seatbelt",
    "belt_upper_guide", "door_card", "door_armrest", "door_handle", "door_storage",
    "interior_mirror_surface", "door_ambient_light",
  ]);
  cabin.traverse((object) => {
    if (passengerOnly.has(object.name) && object.position.x > .2) object.visible = false;
  });

  // Low-floor entrance and anti-slip stair nosings on the right-hand side.
  box("bus_low_floor_platform", [2.05, .09, 3.35], [1.25, .5, -3.72], rubber);
  for (let step = 0; step < 3; step++) {
    const y = .18 + step * .13, z = -2.32 - step * .38;
    box("bus_entry_step", [1.34, .16, .48], [1.68, y, z], rubber);
    box("bus_step_safety_edge", [1.36, .035, .07], [1.68, y + .095, z - .22], yellow);
  }

  // Driver safety enclosure: lower solid bulkhead, glazed upper partition and frame.
  box("bus_driver_partition_base", [.12, 1.2, 2.25], [.18, 1.08, -2.8], polymer);
  add(new T.PlaneGeometry(2.05, 1.65), glass, "bus_driver_partition_glass", [.115, 2.45, -2.8], [0, Math.PI / 2, 0]);
  tube("bus_partition_front_post", .045, 3.05, [.1, 2.05, -3.85], [0, 0, 0], metal);
  tube("bus_partition_rear_post", .045, 3.05, [.1, 2.05, -1.77], [0, 0, 0], metal);
  tube("bus_partition_top_rail", .045, 2.08, [.1, 3.58, -2.81], [Math.PI / 2, 0, 0], metal);

  // Curved-looking driver-side command console built as an angled three-piece unit.
  const consoleA = box("bus_driver_side_console", [.72, .72, 1.72], [-1.72, 1.35, -4.43], soft, [0, -.14, 0]);
  consoleA.material = soft;
  box("bus_door_control_bank", [.45, .035, .8], [-1.67, 1.76, -4.55], polymer, [-.24, 0, 0]);
  for (let i = 0; i < 8; i++) {
    const button = add(new T.CylinderGeometry(.045, .045, .028, 12), i === 2 ? yellow : screen,
      "bus_console_switch", [-1.82 + (i % 2) * .2, 1.89, -4.8 + Math.floor(i / 2) * .18], [Math.PI / 2, 0, 0]);
    button.userData.busControl = ["frontDoor", "rearDoor", "kneeling", "ramp", "stop", "lights", "camera", "PA"][i];
  }

  // Fare machine and passenger validator face the entrance without obstructing sightlines.
  box("bus_ticket_machine_body", [.62, .92, .48], [.72, 1.38, -3.86], polymer, [0, -.12, 0]);
  box("bus_ticket_machine_screen", [.48, .36, .025], [.72, 1.62, -4.115], screen, [-.05, 0, 0]);
  box("bus_contactless_validator", [.32, .5, .22], [1.25, 1.58, -2.9], polymer);
  add(new T.RingGeometry(.065, .09, 24), screen, "bus_contactless_symbol", [1.25, 1.63, -3.02]);

  // Front entrance glazing and the characteristic double-leaf inward door.
  for (const side of [-1, 1]) {
    add(new T.PlaneGeometry(.73, 2.45), glass, "bus_front_door_glass", [1.99, 2.2, -3.1 + side * .39], [0, Math.PI / 2, 0]);
    tube("bus_door_vertical_frame", .035, 2.5, [1.96, 2.18, -3.1 + side * .75], [0, 0, 0], metal);
  }
  tube("bus_entry_handrail", .055, 2.3, [1.25, 1.7, -2.35]);
  tube("bus_entry_grab_bar", .05, 1.2, [1.65, 2.55, -2.25], [Math.PI / 2, 0, 0]);

  // Dedicated ceiling panels and neutral task light distinguish the bus cabin.
  box("bus_driver_ceiling_panel", [2.2, .1, 2.4], [-.9, 4.68, -4.15], soft);
  box("bus_driver_task_lamp", [.48, .035, .22], [-.9, 4.6, -3.72], screen);
  const taskLight = new T.PointLight(0xe8f5ef, qualityLevel > 1 ? .7 : .3, 3.5, 2);
  taskLight.name = "bus_driver_task_light";
  taskLight.position.set(-.9, 4.45, -3.75);
  root.add(taskLight);

  root.userData.dispose = () => {
    root.traverse((object) => object.geometry?.dispose?.());
    glass.dispose(); screen.dispose(); yellow.dispose();
  };
  return root;
}
