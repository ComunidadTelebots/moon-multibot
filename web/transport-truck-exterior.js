export function createDetailedTruckExterior({ THREE: T, paint, glass, chrome, qualityLevel = 2 }) {
  const root = new T.Group(); root.name = "aster_viento_detailed_exterior";
  const dark = new T.MeshStandardMaterial({ color: 0x11191e, roughness: .48, metalness: .42 });
  const rubber = new T.MeshStandardMaterial({ color: 0x0b0d0f, roughness: .94 });
  const lamp = new T.MeshPhysicalMaterial({ color: 0xe9f4f3, emissive: 0xb9e7dc, emissiveIntensity: 1.15, roughness: .1, transmission: .08, clearcoat: 1 });
  const amber = new T.MeshStandardMaterial({ color: 0xffa62c, emissive: 0xff6d00, emissiveIntensity: 1.7, roughness: .24 });
  const red = new T.MeshStandardMaterial({ color: 0xd91d32, emissive: 0x76000c, emissiveIntensity: 1.2, roughness: .28 }); red.userData.vehicleLamp="brake";
  const trailerWhite = new T.MeshPhysicalMaterial({ color: 0xf1f3f2, roughness:.38, metalness:.18, clearcoat:.42 });
  const resources = [dark, rubber, lamp, amber, red, trailerWhite];
  const add = (geometry, material, name, position, rotation = [0,0,0], parent = root) => {
    resources.push(geometry); const mesh = new T.Mesh(geometry, material); mesh.name = name;
    mesh.position.set(...position); mesh.rotation.set(...rotation); mesh.castShadow = mesh.receiveShadow = true; mesh.userData.exteriorCabSkin = parent === root && /cab|roof|windshield|pillar|door|visor/.test(name); parent.add(mesh); return mesh;
  };
  const box = (size, material, name, position, rotation) => add(new T.BoxGeometry(...size), material, name, position, rotation);
  const roundedBody = (width,height,depth,radius,material,name,position,rotation=[0,0,0],parent=root) => {
    const shape=new T.Shape(),x=-width/2,y=-height/2;shape.moveTo(x+radius,y);shape.lineTo(-x-radius,y);shape.quadraticCurveTo(-x,y,-x,y+radius);shape.lineTo(-x,-y-radius);shape.quadraticCurveTo(-x,-y,-x-radius,-y);shape.lineTo(x+radius,-y);shape.quadraticCurveTo(x,-y,x,-y-radius);shape.lineTo(x,y+radius);shape.quadraticCurveTo(x,y,x+radius,y);
    const geometry=new T.ExtrudeGeometry(shape,{depth,bevelEnabled:true,bevelSize:.055,bevelThickness:.05,bevelSegments:qualityLevel>1?4:2,curveSegments:qualityLevel>1?14:7});geometry.center();return add(geometry,material,name,position,rotation,parent);
  };
  function taperedCabGeometry() {
    const positions = new Float32Array([
      -2.5,-1.8,-2.6, 2.5,-1.8,-2.6, -2.5,-1.8,2.45, 2.5,-1.8,2.45,
      -2.22,1.8,-2.22, 2.22,1.8,-2.22, -2.28,1.8,2.3, 2.28,1.8,2.3,
    ]);
    const indices = [0,1,4,1,5,4, 1,3,5,3,7,5, 3,2,7,2,6,7, 2,0,6,0,4,6, 4,5,6,5,7,6, 0,2,1,1,2,3];
    const geometry = new T.BufferGeometry(); geometry.setAttribute("position", new T.BufferAttribute(positions,3)); geometry.setIndex(indices); geometry.computeVertexNormals(); return geometry;
  }
  add(taperedCabGeometry(), paint, "sculpted_cab_shell", [0,2.82,-4.2]);
  roundedBody(4.42,.38,4.55,.18,paint,"aerodynamic_roof_cap",[0,4.78,-4.08],[-.035,0,0]);
  roundedBody(4.12,.42,1.36,.17,paint,"roof_air_deflector",[0,5.12,-2.68],[-.22,0,0]);
  for(const side of[-1,1]) roundedBody(.48,3.55,2.1,.2,paint,"cab_corner_fairing",[side*2.24,2.92,-4.38],[0,side*.06,side*.025]);
  roundedBody(4.3,.72,.48,.2,paint,"sloped_front_brow",[0,4.48,-6.42],[-.12,0,0]);
  box([4.24,1.62,.08], glass, "panoramic_split_windshield", [0,3.55,-6.66], [-.025,0,0]);
  box([.085,1.64,.12], dark, "windshield_centre_divider", [0,3.55,-6.72]);
  for (const side of [-1,1]) {
    box([.24,1.9,.26], paint, "sculpted_a_pillar", [side*2.23,3.48,-6.48], [0,0,side*.07]);
    const door = roundedBody(2.62,2.68,.075,.18,paint,"cab_door_skin",[side*2.45,2.78,-4.38],[0,side*Math.PI/2,0]);
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
  box([1.02,.95,1.35], chrome,"battery_and_adblue_box",[-2.2,.9,1.72]);
  box([1.02,.95,1.35],chrome,"exhaust_treatment_box",[2.2,.9,1.72]);
  box([3.6,.38,7.1],dark,"tractor_ladder_chassis",[0,.82,-.25]);
  for(const side of[-1,1])box([.24,.48,7.4],dark,"tractor_frame_rail",[side*.82,.76,-.2]);
  const fifth=add(new T.CylinderGeometry(1.02,1.02,.22,qualityLevel>1?30:18),dark,"fifth_wheel_coupling",[0,1.28,1.82]);fifth.rotation.x=Math.PI/2;
  function wheel(x,z,radius=1.02,width=.62){
    const group=new T.Group();group.name="detailed_road_wheel";group.position.set(x,radius,z);group.userData.isWheel=true;group.userData.frontWheel=z< -2;
    add(new T.CylinderGeometry(radius*.98,radius,width,qualityLevel>1?48:24,2),rubber,"radial_tyre_carcass",[0,0,0],[0,0,Math.PI/2],group);
    for(const side of[-1,1]){add(new T.TorusGeometry(radius*.74,radius*.22,qualityLevel>1?12:7,qualityLevel>1?48:24),rubber,"rounded_tyre_sidewall",[side*width*.48,0,0],[0,Math.PI/2,0],group);add(new T.TorusGeometry(radius*.47,.06,8,qualityLevel>1?40:20),chrome,"polished_rim_lip",[side*width*.54,0,0],[0,Math.PI/2,0],group);}
    add(new T.CylinderGeometry(radius*.5,radius*.5,width+.055,qualityLevel>1?36:18),chrome,"deep_wheel_rim",[0,0,0],[0,0,Math.PI/2],group);
    for(let i=0;i<(qualityLevel>1?12:7);i++){const angle=i*Math.PI*2/(qualityLevel>1?12:7);add(new T.BoxGeometry(width+.08,.075,.2),dark,"rim_vent",[0,Math.cos(angle)*radius*.36,Math.sin(angle)*radius*.36],[angle,0,Math.PI/2],group);}
    add(new T.CylinderGeometry(radius*.17,radius*.17,width+.1,qualityLevel>1?24:14),dark,"wheel_hub",[0,0,0],[0,0,Math.PI/2],group);
    for(let i=0;i<10;i++){const angle=i*Math.PI/5;add(new T.CylinderGeometry(.045,.045,.09,8),chrome,"wheel_nut",[0,Math.cos(angle)*radius*.25,Math.sin(angle)*radius*.25],[0,0,Math.PI/2],group);}
    const treadCount=qualityLevel>1?32:16;for(let i=0;i<treadCount;i++){const angle=i*Math.PI*2/treadCount;for(const side of[-1,1]){const block=add(new T.BoxGeometry(width*.42,.055,radius*.16),rubber,"tyre_tread_block",[side*width*.23,Math.cos(angle)*radius*1.015,Math.sin(angle)*radius*1.015],[angle,0,side*.16],group);block.castShadow=qualityLevel>1;}}
    root.add(group);return group;
  }
  for(const side of[-1,1])for(const z of[-4.55,1.48])wheel(side*2.42,z);
  const trailer=new T.Group();trailer.name="pearl_white_box_trailer";root.add(trailer);
  const trailerBody=add(new T.BoxGeometry(5.02,4.35,12.4),trailerWhite,"insulated_trailer_body",[0,3.12,6.95],[0,0,0],trailer);
  add(new T.BoxGeometry(5.16,.2,12.55),chrome,"trailer_roof_edge",[0,5.34,6.95],[0,0,0],trailer);
  add(new T.BoxGeometry(5.2,.42,12.5),dark,"trailer_underframe",[0,.94,6.95],[0,0,0],trailer);
  for(let z=1.25;z<12.8;z+=1.2)for(const side of[-1,1])add(new T.BoxGeometry(.065,4.08,.075),chrome,"trailer_panel_seam",[side*2.54,3.12,z],[0,0,0],trailer);
  for(const side of[-1,1]){add(new T.BoxGeometry(.16,.54,9.2),chrome,"trailer_side_guard",[side*2.58,.8,6.2],[0,0,0],trailer);for(const z of[3.2,5.45,7.7,9.95])add(new T.BoxGeometry(.09,.72,.12),dark,"side_guard_support",[side*2.54,.75,z],[0,0,0],trailer);}
  for(const side of[-1,1])for(const z of[9.15,11.35,13.55])wheel(side*2.38,z,.88,.56);
  add(new T.BoxGeometry(4.78,3.95,.12),trailerWhite,"double_rear_door",[0,3.05,13.18],[0,0,0],trailer);
  add(new T.BoxGeometry(.09,3.74,.16),dark,"rear_door_divider",[0,3.05,13.27],[0,0,0],trailer);
  for(const side of[-1,1]){add(new T.CylinderGeometry(.055,.055,3.42,10),chrome,"rear_door_lock",[side*1.88,3.05,13.3],[0,0,0],trailer);add(new T.BoxGeometry(.58,.28,.12),red,"trailer_tail_lamp",[side*1.82,.86,13.32],[0,0,0],trailer);}
  for(let z=.8;z<13;z+=1.25)for(const side of[-1,1])add(new T.BoxGeometry(.12,.1,.06),amber,"trailer_side_marker",[side*2.61,1.22,z],[0,0,0],trailer);
  for(const side of[-1,1]){const indicator=add(new T.BoxGeometry(.28,.22,.13),amber,"trailer_turn_indicator",[side*1.25,.86,13.34],[0,0,0],trailer);indicator.userData.turnSide=side;}
  root.userData.dispose = () => resources.forEach(resource => resource.dispose?.());
  return root;
}
