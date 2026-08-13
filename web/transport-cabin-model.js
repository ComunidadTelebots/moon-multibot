export function createOriginalEuropeanCabin({ THREE: T, bus = false, qualityLevel = 2 }) {
  const root = new T.Group(); root.name = "aster_original_cabin";
  const cabinTextures = [];
  const texture = (name, base, detail, pattern = "grain") => {
    const canvas=document.createElement("canvas"),size=qualityLevel>1?512:256;canvas.width=canvas.height=size;const x=canvas.getContext("2d");
    x.fillStyle=base;x.fillRect(0,0,size,size);let seed=name.length*7919;
    if(pattern==="weave") for(let p=-size;p<size*2;p+=7){x.strokeStyle=`rgba(${detail},${detail},${detail},.11)`;x.lineWidth=2;x.beginPath();x.moveTo(p,0);x.lineTo(p-size,size);x.stroke();x.beginPath();x.moveTo(p,0);x.lineTo(p+size,size);x.stroke();}
    else if(pattern==="brushed") for(let y=0;y<size;y+=2){seed=(seed*48271)%2147483647;x.fillStyle=`rgba(${detail},${detail},${detail},${.025+(seed%12)/220})`;x.fillRect(0,y,size,1);}
    else if(pattern==="rubber") { for(let y=4;y<size;y+=18){x.fillStyle="rgba(150,160,160,.13)";x.fillRect(0,y,size,4);} }
    else for(let i=0;i<size*6;i++){seed=(seed*48271)%2147483647;const px=seed%size;seed=(seed*48271)%2147483647;const py=seed%size;x.fillStyle=`rgba(${detail},${detail},${detail},${.022+(seed%9)/280})`;x.fillRect(px,py,1+(seed%2),1+(seed%2));}
    const map=new T.CanvasTexture(canvas);map.name=name;map.colorSpace=T.SRGBColorSpace;map.wrapS=map.wrapT=T.RepeatWrapping;map.repeat.set(pattern==="weave"?5:3,pattern==="weave"?7:3);map.anisotropy=qualityLevel>2?16:qualityLevel>1?8:2; cabinTextures.push(map);return map;
  };
  const softMap=texture("dashboard_grain","#303438",105), leatherMap=texture("leather_grain","#24282b",80), fabricMap=texture("seat_weave","#394147",135,"weave"), headlinerMap=texture("headliner_weave","#b2b3ae",190,"weave"), sleeperMap=texture("sleeper_fabric","#42565c",125,"weave"), aluminiumMap=texture("brushed_aluminium","#9ba3a5",210,"brushed"), rubberMap=texture("ribbed_floor","#111416",90,"rubber");
  const material = (name, color, roughness, metalness = 0, extra = {}) => {
    const value = new T.MeshPhysicalMaterial({ name, color, roughness, metalness, ...extra });
    return value;
  };
  const soft = material("soft_touch_dashboard", 0xffffff, .88, .02, { map:softMap,bumpMap:softMap,bumpScale:.018,clearcoat: .08 });
  const polymer = material("satin_polymer", 0x8b9295, .56, .05, { map:softMap,bumpMap:softMap,bumpScale:.012 });
  const leather = material("stitched_charcoal_leather", 0xffffff, .82, .01, { map:leatherMap,bumpMap:leatherMap,bumpScale:.028,sheen: .18, sheenColor: new T.Color(0x697379) });
  const aluminium = material("brushed_aluminium", 0xffffff, .28, .76, { map:aluminiumMap,bumpMap:aluminiumMap,bumpScale:.008,clearcoat: .22 });
  const piano = material("black_glass_controls", 0x050708, .12, .22, { clearcoat: 1, clearcoatRoughness: .08 });
  const fabric = material("woven_seat_fabric", 0xffffff, .98, 0, { map:fabricMap,bumpMap:fabricMap,bumpScale:.035,sheen: .32, sheenColor: new T.Color(0x53626a) });
  const seatLeather = material("seat_side_leather", 0xffffff, .72, .01, { map:leatherMap,bumpMap:leatherMap,bumpScale:.02,clearcoat:.06 });
  const headliner = material("woven_headliner", 0xffffff, .96, 0, { map:headlinerMap,bumpMap:headlinerMap,bumpScale:.022,sheen: .12, sheenColor: new T.Color(0xd8d4c8) });
  const sleeperFabric = material("sleeper_textile", 0xffffff, .94, 0, { map:sleeperMap,bumpMap:sleeperMap,bumpScale:.032,sheen: .28, sheenColor: new T.Color(0x63868c) });
  const rubber = material("ribbed_cabin_rubber", 0xffffff, 1, 0, { map:rubberMap,bumpMap:rubberMap,bumpScale:.045 });
  const screenMaterial = new T.MeshBasicMaterial({ name: "live_instrument_display", color: 0xffffff, toneMapped: false });
  const accent = new T.MeshBasicMaterial({ color: 0x57e5d0, toneMapped: false });
  const add = (geometry, mat, name, position, rotation = [0, 0, 0], parent = root) => {
    const mesh = new T.Mesh(geometry, mat); mesh.name = name; mesh.position.set(...position); mesh.rotation.set(...rotation);
    mesh.castShadow = true; mesh.receiveShadow = true; parent.add(mesh); return mesh;
  };
  const box = (name, size, position, mat = soft, rotation) => add(new T.BoxGeometry(...size, 3, 2, 3), mat, name, position, rotation);
  const roundedPanel = (name, width, height, depth, radius, position, mat, rotation = [0, 0, 0], parent = root) => {
    const shape = new T.Shape(); const x = -width / 2, y = -height / 2;
    shape.moveTo(x + radius, y); shape.lineTo(x + width - radius, y); shape.quadraticCurveTo(x + width, y, x + width, y + radius);
    shape.lineTo(x + width, y + height - radius); shape.quadraticCurveTo(x + width, y + height, x + width - radius, y + height);
    shape.lineTo(x + radius, y + height); shape.quadraticCurveTo(x, y + height, x, y + height - radius);
    shape.lineTo(x, y + radius); shape.quadraticCurveTo(x, y, x + radius, y);
    const geometry = new T.ExtrudeGeometry(shape, { depth, bevelEnabled: true, bevelSegments: qualityLevel > 1 ? 3 : 1, bevelSize: .035, bevelThickness: .035, curveSegments: qualityLevel > 1 ? 12 : 5 });
    geometry.center(); return add(geometry, mat, name, position, rotation, parent);
  };
  const frontZ = bus ? -5.93 : -5.79, sideX = bus ? 2.35 : 2.18;
  roundedPanel("dashboard_swept_shell", bus ? 4.72 : 4.42, .68, .72, .18, [0, 2.22, frontZ], soft, [-.06, 0, 0]);
  roundedPanel("dashboard_upper_pad", bus ? 4.82 : 4.52, .18, 1.25, .09, [0, 2.63, frontZ + .12], polymer, [-.04, 0, 0]);
  roundedPanel("driver_instrument_hood", 1.92, .48, .64, .2, [-.75, 2.66, frontZ - .08], soft, [-.08, 0, 0]);
  roundedPanel("centre_stack", 1.18, 1.18, .18, .16, [.92, 2.15, frontZ - .49], piano, [0, 0, -.035]);
  roundedPanel("wraparound_driver_console", 2.05,.48,1.75,.18,[-1.18,1.83,frontZ+.62],soft,[-.08,.04,0]);
  roundedPanel("wraparound_passenger_console", 2.18,.44,1.58,.18,[1.15,1.82,frontZ+.7],soft,[-.06,-.045,0]);
  roundedPanel("floor_height_centre_console", 1.22,1.18,2.15,.22,[.72,1.08,frontZ+1.28],polymer,[-.05,0,0]);
  const displayCanvas = document.createElement("canvas"); displayCanvas.width = 768; displayCanvas.height = 288;
  const displayTexture = new T.CanvasTexture(displayCanvas); displayTexture.colorSpace = T.SRGBColorSpace; screenMaterial.map = displayTexture;
  add(new T.PlaneGeometry(1.64, .61), screenMaterial, "instrument_cluster_live", [-.67, 2.48, frontZ - .47]);
  for (const gaugeX of [-1.17, -.19]) {
    add(new T.CylinderGeometry(.31,.31,.055,qualityLevel>1?40:24), piano, "analogue_gauge_bezel", [gaugeX,2.49,frontZ-.5], [Math.PI/2,0,0]);
    add(new T.TorusGeometry(.265,.025,10,qualityLevel>1?40:24), aluminium, "analogue_gauge_ring", [gaugeX,2.49,frontZ-.535]);
    for(let tick=0;tick<11;tick++){
      const angle=-2.35+tick*.47, mark=box("gauge_tick",[.018,.075,.012],[gaugeX+Math.cos(angle)*.215,2.49+Math.sin(angle)*.215,frontZ-.568],accent);
      mark.rotation.z=angle-Math.PI/2;
    }
  }
  const navCanvas = document.createElement("canvas"); navCanvas.width = 384; navCanvas.height = 384;
  const navTexture = new T.CanvasTexture(navCanvas); navTexture.colorSpace = T.SRGBColorSpace;
  add(new T.PlaneGeometry(.82, .72), new T.MeshBasicMaterial({ map: navTexture, toneMapped: false }), "navigation_touchscreen", [.92, 2.29, frontZ - .61]);
  const switchIcons=["L","P","△","A","R","M","+","−","F","C","D","S"];
  for(let row=0;row<2;row++)for(let column=0;column<6;column++){
    const switchCanvas=document.createElement("canvas");switchCanvas.width=switchCanvas.height=64;const sx=switchCanvas.getContext("2d");sx.fillStyle=column===2&&row===0?"#8e1f22":"#222a2e";sx.fillRect(0,0,64,64);sx.fillStyle="#d9f5ef";sx.font="bold 27px sans-serif";sx.textAlign="center";sx.textBaseline="middle";sx.fillText(switchIcons[row*6+column],32,34);
    const switchMap=new T.CanvasTexture(switchCanvas);switchMap.colorSpace=T.SRGBColorSpace;cabinTextures.push(switchMap);
    add(new T.BoxGeometry(.115,.105,.035),new T.MeshPhysicalMaterial({map:switchMap,roughness:.3,clearcoat:.55}),"labelled_dashboard_switch",[.48+column*.17,1.83-row*.17,frontZ-.62]);
  }
  const wheel = new T.Group(); wheel.name = "steering_wheel"; wheel.position.set(-1.04, 2.55, frontZ + .5); wheel.rotation.x = -.18;
  add(new T.TorusGeometry(.54, .075, qualityLevel > 1 ? 16 : 10, qualityLevel > 1 ? 48 : 24), leather, "steering_rim", [0, 0, 0], [0, 0, 0], wheel);
  for (const angle of [-2.48, -.66, Math.PI / 2]) {
    const spoke = box("steering_spoke", [.42, .09, .09], [Math.cos(angle) * .22, Math.sin(angle) * .22, 0], polymer, [0, 0, angle]); wheel.add(spoke);
  }
  add(new T.CylinderGeometry(.2, .2, .1, 32), piano, "steering_hub", [0, 0, 0], [Math.PI / 2, 0, 0], wheel);
  add(new T.TorusGeometry(.455,.012,8,48), aluminium, "steering_stitching", [0,0,-.074], [0,0,0], wheel);
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
    roundedPanel("seat_pan_side_shell",1.02,.28,.9,.12,[0,.88,frontZ+2.27],seatLeather,[Math.PI/2,0,0],seat);
    const cushion=add(new T.CapsuleGeometry(.43,.56,10,qualityLevel>1?24:14),fabric,"extendable_multi_zone_cushion",[0,1.08,frontZ+2.18],[Math.PI/2,0,0],seat);cushion.scale.set(1.08,1,.78);
    for(const side of[-1,1]){const bolster=add(new T.CapsuleGeometry(.12,.56,7,14),seatLeather,"cushion_side_bolster",[side*.43,1.14,frontZ+2.18],[Math.PI/2,0,0],seat);bolster.rotation.z=side*.1;}
    const back=add(new T.CapsuleGeometry(.43,.88,10,qualityLevel>1?24:14),fabric,"anatomical_backrest",[0,1.83,frontZ+2.53],[-.12,0,0],seat);back.scale.set(1.05,1,.5);
    for(const side of[-1,1]){const wing=add(new T.CapsuleGeometry(.13,.68,7,14),seatLeather,"pneumatic_side_bolster",[side*.43,1.84,frontZ+2.48],[-.12,0,side*.08],seat);wing.scale.z=.72;}
    const lumbar=add(new T.CapsuleGeometry(.31,.18,7,16),fabric,"pneumatic_lumbar_support",[0,1.68,frontZ+2.23],[-.12,0,0],seat);lumbar.scale.z=.45;
    add(new T.CapsuleGeometry(.31,.18,8,18),seatLeather,"integrated_adjustable_headrest",[0,2.69,frontZ+2.65],[0,0,0],seat);
    for (const sx of [-.3, .3]) add(new T.BoxGeometry(.014, 1.05, .018), aluminium, "seat_double_stitching", [sx, 1.88, frontZ + 2.18], [0, 0, sx*.1], seat);
    for(const side of[-1,1]) roundedPanel("folding_armrest",.17,.2,.76,.07,[side*.57,1.91,frontZ+2.27],seatLeather,[Math.PI/2,0,0],seat);
    seat.position.x = x; root.add(seat);
    box("seat_upper_suspension_frame", [.88,.12,.8], [x,.78,frontZ+2.35], aluminium);
    box("seat_lower_slide_rail", [.92,.08,.88], [x,.44,frontZ+2.35], aluminium);
    for(const sx of[-.3,.3]){const scissorA=box("air_suspension_scissor",[.07,.62,.08],[x+sx,.61,frontZ+2.35],aluminium);scissorA.rotation.z=sx<0?.52:-.52;}
    const airBellows=add(new T.CylinderGeometry(.3,.34,.3,24),rubber,"air_suspension_bellows",[x,.61,frontZ+2.35]);
    for(let control=0;control<4;control++) add(new T.CylinderGeometry(.055,.055,.05,14),control===0?accent:polymer,"seat_adjustment_control",[x-.53,.72+control*.12,frontZ+2.15],[0,0,Math.PI/2]);
    const belt = box("three_point_seatbelt", [.045,1.38,.035], [x + (x < 0 ? -.32 : .32),1.72,frontZ+2.15], material("seatbelt_webbing",0x090b0c,.9));
    belt.rotation.z = x < 0 ? -.16 : .16;
    box("belt_upper_guide",[.11,.16,.08],[x+(x<0?-.38:.38),2.48,frontZ+2.54],polymer);
  }
  for (const side of [-1, 1]) {
    roundedPanel("door_card", 2.45, 1.8, .1, .18, [side * sideX, 2.0, frontZ + 1.02], soft, [0, Math.PI / 2, 0]);
    box("door_armrest", [.26, .24, 1.08], [side * (sideX - .11), 2.04, frontZ + .78], polymer);
    add(new T.TorusGeometry(.15, .032, 8, 20, Math.PI), aluminium, "door_handle", [side * (sideX - .16), 2.4, frontZ + .43], [0, Math.PI / 2, side * Math.PI / 2]);
    roundedPanel("door_storage", .72, .33, .08, .12, [side * (sideX - .09), 1.27, frontZ + 1.15], polymer, [0, Math.PI / 2, 0]);
    add(new T.PlaneGeometry(.72, .9), material("mirror_glass", 0x91aab3, .06, .9, { clearcoat: 1 }), "interior_mirror_surface", [side * (sideX + .34), 3.42, frontZ - .48], [0, side * Math.PI / 2, 0]);
    box("windshield_a_pillar", [.2,2.38,.24], [side*2.11,3.38,frontZ-.68], polymer, [0,0,side*.065]);
    box("windshield_lower_frame", [2.08,.16,.22], [side*1.02,2.7,frontZ-.73], polymer);
    box("door_ambient_light", [.035,.045,1.45], [side*(sideX-.18),1.72,frontZ+.82], accent);
  }
  box("rubber_floor", [4.1, .04, 3.4], [0, .47, frontZ + 1.12], rubber);
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
  for(const side of[-1,1]){
    roundedPanel("front_overhead_locker",1.82,.64,.72,.14,[side*1.03,4.42,frontZ+.52],soft);
    roundedPanel("side_overhead_locker",.58,.72,2.3,.14,[side*1.88,4.2,frontZ+1.85],soft,[0,side*Math.PI/2,0]);
    box("locker_release",[.45,.035,.055],[side*1.03,4.2,frontZ+.14],aluminium);
  }
  box("dashboard_ambient_strip",[3.9,.035,.035],[0,2.02,frontZ-.69],accent);
  for(const cupX of[.42,.78]){
    const holder=add(new T.TorusGeometry(.11,.025,8,22),polymer,"deep_cupholder",[cupX,1.61,frontZ+1.1],[Math.PI/2,0,0]);holder.scale.y=1.15;
  }
  for (const side of [-1,1]) box("sun_visor", [1.48,.46,.055], [side*.92,4.3,frontZ-.56], headliner, [.08,0,0]);
  add(new T.PlaneGeometry(.62,.28), material("interior_centre_mirror",0x91aab3,.05,.88,{clearcoat:1}), "interior_centre_mirror", [0,4.08,frontZ-.64]);
  for (let i = 0; i < 5; i++) add(new T.CylinderGeometry(.045, .045, .025, 12), accent, "overhead_switch", [-.36 + i * .18, 4.39, frontZ - .2], [Math.PI / 2, 0, 0]);
  const glow = new T.PointLight(0xffe0b0, qualityLevel > 1 ? 1.15 : .55, 6, 2); glow.name = "ambient_cabin_light"; glow.position.set(0, 3.8, frontZ + 1.2); root.add(glow);
  const dashGlow = new T.PointLight(0x77d9cf,qualityLevel>1?.48:.2,3.5,2);dashGlow.position.set(-.25,2.65,frontZ+.35);root.add(dashGlow);
  root.userData.steering = wheel;
  root.userData.instrument = { canvas: displayCanvas, context: displayCanvas.getContext("2d"), texture: displayTexture };
  root.userData.navigation = { canvas: navCanvas, context: navCanvas.getContext("2d"), texture: navTexture };
  // Eye point of a seated driver. It must remain behind and above the wheel;
  // placing it near the steering column makes the rim fill the whole viewport.
  root.userData.cockpitOffset = [-1.04, 3.36, frontZ + 1.55];
  root.userData.dispose = () => { cabinTextures.forEach(map=>map.dispose()); root.traverse((object) => { object.geometry?.dispose?.(); if (Array.isArray(object.material)) object.material.forEach((m) => m.dispose()); else object.material?.dispose?.(); }); };
  return root;
}
