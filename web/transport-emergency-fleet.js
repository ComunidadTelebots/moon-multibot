const DEFINITIONS = {
  ambulance: { name:"Ambulancia Orion M7", maxSpeed:145, body:"ambulance", length:6.4, cockpit:[-.58,2.28,-2.45] },
  fire: { name:"Unidad Vulcano R4", maxSpeed:118, body:"fire", length:7.8, cockpit:[-.62,2.55,-3.18] },
  recovery: { name:"Asistencia Atlas RX", maxSpeed:125, body:"recovery", length:7.2, cockpit:[-.58,2.3,-2.85] },
};

export function createEmergencyFleet({ THREE:T, qualityLevel=2, atlasUrl }) {
  const mats={
    ambulance:new T.MeshPhysicalMaterial({color:0xffffff,roughness:.28,metalness:.22,clearcoat:.86}),
    fire:new T.MeshPhysicalMaterial({color:0xb8171d,roughness:.25,metalness:.28,clearcoat:.9}),
    recovery:new T.MeshPhysicalMaterial({color:0xe6b91e,roughness:.42,metalness:.22,clearcoat:.52}),
    medical:new T.MeshStandardMaterial({color:0xd9dddc,roughness:.72}),
    dark:new T.MeshStandardMaterial({color:0x151a1d,roughness:.58,metalness:.35}),
    glass:new T.MeshPhysicalMaterial({color:0x315d6b,roughness:.08,transmission:.16,transparent:true,opacity:.76,clearcoat:1}),
    chrome:new T.MeshStandardMaterial({color:0xaeb8ba,roughness:.22,metalness:.84}),
    tyre:new T.MeshStandardMaterial({color:0x0d0f10,roughness:.96}),
    blue:new T.MeshStandardMaterial({color:0x248dff,emissive:0x095bd2,emissiveIntensity:2.4}),
    amber:new T.MeshStandardMaterial({color:0xffa51e,emissive:0xe76500,emissiveIntensity:2.2}),
    lamp:new T.MeshStandardMaterial({color:0xf6f1db,emissive:0xd8eaff,emissiveIntensity:1.8}),
    interior:new T.MeshStandardMaterial({color:0x20272b,roughness:.82,metalness:.08}),
    seat:new T.MeshStandardMaterial({color:0x30383d,roughness:.94}),
    redLamp:new T.MeshStandardMaterial({color:0xd72a25,emissive:0x8c0806,emissiveIntensity:1.5}),
    fireCompartment:new T.MeshStandardMaterial({color:0xaeb8ba,roughness:.5,metalness:.55}),
    recoveryBed:new T.MeshStandardMaterial({color:0x596269,roughness:.68,metalness:.42}),
  };
  const resources=[];
  const authoredTextures=[];
  const authoredUrls={ambulance:"./generated-textures/land-ambulance-exterior-v1.png",medical:"./generated-textures/land-ambulance-interior-v1.png",fire:"./generated-textures/land-fire-exterior-v1.png",fireCompartment:"./generated-textures/land-fire-compartment-v1.png",recovery:"./generated-textures/land-recovery-exterior-v1.png",recoveryBed:"./generated-textures/land-recovery-flatbed-v1.png",tyre:"./generated-textures/land-tyre-sidewall-v1.png"};
  const loadAuthored=()=>Promise.all(Object.entries(authoredUrls).map(([name,url])=>new Promise((resolve,reject)=>new T.TextureLoader().load(url,texture=>{texture.colorSpace=T.SRGBColorSpace;texture.wrapS=texture.wrapT=T.RepeatWrapping;texture.repeat.set(name==="tyre"?2:1,1);texture.anisotropy=qualityLevel>2?16:8;mats[name].map=texture;mats[name].color.set(0xffffff);mats[name].needsUpdate=true;authoredTextures.push(texture);resolve(texture)},undefined,reject))));
  const ready=qualityLevel>=2?loadAuthored():atlasUrl?new Promise((resolve,reject)=>new T.TextureLoader().load(atlasUrl,source=>{
    const size=Math.floor(Math.min(source.image.width,source.image.height)/2);
    [["ambulance",0,0],["fire",1,0],["recovery",0,1],["medical",1,1]].forEach(([name,c,r])=>{const canvas=document.createElement("canvas");canvas.width=canvas.height=size;canvas.getContext("2d").drawImage(source.image,c*size,r*size,size,size,0,0,size,size);const texture=new T.CanvasTexture(canvas);texture.colorSpace=T.SRGBColorSpace;texture.wrapS=texture.wrapT=T.RepeatWrapping;texture.repeat.set(1.25,1.25);texture.anisotropy=qualityLevel>2?16:qualityLevel>1?8:2;mats[name].map=texture;mats[name].bumpMap=texture;mats[name].bumpScale=.022;mats[name].color.set(0xffffff);mats[name].needsUpdate=true;});source.dispose();resolve();
  },undefined,reject)):Promise.resolve();
  const add=(parent,geometry,material,name,p)=>{resources.push(geometry);const mesh=new T.Mesh(geometry,material);mesh.name=name;mesh.position.set(...p);mesh.castShadow=mesh.receiveShadow=true;parent.add(mesh);return mesh;};
  const box=(p,size,material,name,position)=>add(p,new T.BoxGeometry(...size),material,name,position);
  function wheels(root,zs,width=1.18,radius=.58){for(const z of zs)for(const side of [-1,1]){const group=new T.Group();group.position.set(side*width,radius,z);group.userData.isWheel=true;const tyre=add(group,new T.CylinderGeometry(radius,radius,.3,qualityLevel>1?24:14),mats.tyre,"emergency_tyre",[0,0,0]);tyre.rotation.z=Math.PI/2;const rim=add(group,new T.CylinderGeometry(radius*.48,radius*.48,.32,qualityLevel>1?18:10),mats.chrome,"emergency_rim",[0,0,0]);rim.rotation.z=Math.PI/2;if(qualityLevel>1){const hub=add(group,new T.CylinderGeometry(radius*.13,radius*.13,.35,12),mats.dark,"wheel_hub",[0,0,0]);hub.rotation.z=Math.PI/2;for(let i=0;i<6;i++){const bolt=add(group,new T.SphereGeometry(.025,6,4),mats.dark,"wheel_bolt",[side*.17,Math.cos(i*Math.PI/3)*radius*.27,Math.sin(i*Math.PI/3)*radius*.27]);bolt.castShadow=false;}}root.add(group);}}
  function lights(root,width,y,z,color=mats.blue){for(const side of [-1,1]){const beacon=box(root,[.62,.16,.28],color,"emergency_beacon",[side*width,y,z]);beacon.userData.emergencyBeacon=true;}}
  function cab(root,z,material,height=2.35){
    box(root,[2.55,height,2.65],material,"response_cab",[0,1.75,z]);
    const wind=box(root,[2.18,.92,.055],mats.glass,"response_windshield",[0,2.12,z-1.37]);
    box(root,[2.65,.36,.3],mats.chrome,"response_bumper",[0,.62,z-1.48]);
    box(root,[1.05,.48,.06],mats.dark,"response_grille",[0,.96,z-1.655]);
    box(root,[.72,.2,.04],mats.medical,"response_plate",[0,.64,z-1.675]);
    for(const side of [-1,1]){
      box(root,[.58,.38,.1],mats.lamp,"response_headlamp",[side*.78,1.02,z-1.55]);
      box(root,[.055,.82,1.02],mats.glass,"response_side_window",[side*1.295,2.08,z-.35]);
      const mirrorArm=box(root,[.36,.055,.055],mats.dark,"mirror_arm",[side*1.43,2.2,z-1]);mirrorArm.rotation.z=side*.1;
      const mirror=box(root,[.08,.34,.25],mats.dark,"heated_door_mirror",[side*1.62,2.2,z-1.02]);mirror.rotation.y=side*.08;
      box(root,[.04,.06,.38],mats.chrome,"door_handle",[side*1.3,1.78,z-.12]);
      box(root,[.62,.72,.5],mats.seat,"cab_seat",[side*.58,1.4,z-.08]);
    }
    box(root,[2.12,.38,.72],mats.interior,"cab_dashboard",[0,1.55,z-1.02]);
    const steering=add(root,new T.TorusGeometry(.29,.045,8,24),mats.dark,"steering_wheel",[-.58,1.86,z-.82]);steering.rotation.x=Math.PI/2;steering.rotation.z=-.18;
    if(qualityLevel>1){
      box(root,[.56,.23,.025],mats.glass,"instrument_cluster",[-.57,1.73,z-1.405]);
      box(root,[.22,.32,.2],mats.dark,"radio_console",[0,1.72,z-1.16]);
      for(const x of[-.82,.82])box(root,[.045,.72,.045],mats.dark,"windscreen_pillar",[x,2.12,z-1.415]);
    }
    return wind;
  }
  function ambulance(root){cab(root,-1.8,mats.ambulance,2.25);box(root,[2.62,2.75,4.1],mats.ambulance,"ambulance_patient_module",[0,2.03,1.55]);box(root,[2.25,2.35,.08],mats.medical,"ambulance_rear_doors",[0,2.0,3.63]);box(root,[.06,2.2,.05],mats.dark,"rear_door_split",[0,2,3.685]);for(const side of [-1,1]){box(root,[.08,.92,1.4],mats.glass,"ambulance_side_window",[side*1.32,2.36,-1.74]);box(root,[.09,.12,3.4],mats.chrome,"ambulance_rubrail",[side*1.34,1.2,1.4]);box(root,[.12,.32,.42],mats.redLamp,"ambulance_rear_lamp",[side*.92,1,3.69]);}if(qualityLevel>0){box(root,[1.85,.16,.75],mats.medical,"patient_bench",[0,.7,1.8]);box(root,[.58,.14,1.85],mats.dark,"stretcher",[0,1.03,1.72]);}box(root,[2.0,.22,.72],mats.blue,"ambulance_roof_lightbar",[0,3.5,-.75]);lights(root,.92,3.42,3.72);wheels(root,[-2.1,2.15]);}
  function fire(root){cab(root,-2.45,mats.fire,2.55);box(root,[2.72,2.85,4.95],mats.fire,"fire_equipment_body",[0,2.05,1.35]);for(const side of [-1,1])for(let z=-.35;z<3.2;z+=1.15)box(root,[.08,1.35,.94],mats.chrome,"fire_roller_shutter",[side*1.39,2.05,z]);const ladder=box(root,[.58,.18,5.7],mats.chrome,"roof_rescue_ladder",[0,3.62,.5]);for(let z=-2;z<3;z+=.45)box(root,[1.12,.05,.07],mats.chrome,"ladder_rung",[0,3.72,z]);for(const side of[-1,1])add(root,new T.TorusGeometry(.48,.08,10,28),mats.dark,"hose_reel",[side*1.4,1.35,2.5]).rotation.y=Math.PI/2;box(root,[2.15,.22,.65],mats.blue,"fire_lightbar",[0,3.25,-2.6]);lights(root,1,3.42,3.9);wheels(root,[-2.55,1.8,3.05],1.25,.62);}
  function recovery(root){cab(root,-2.25,mats.recovery,2.3);const bed=box(root,[2.55,.28,4.9],mats.recovery,"tilting_recovery_bed",[0,1.15,1.35]);bed.rotation.x=-.035;for(const side of[-1,1])box(root,[.12,.4,4.5],mats.chrome,"recovery_bed_rail",[side*1.26,1.35,1.35]);add(root,new T.CylinderGeometry(.42,.42,.75,20),mats.dark,"recovery_winch",[0,1.55,-.65]).rotation.z=Math.PI/2;const boom=box(root,[.25,.25,3.5],mats.chrome,"recovery_boom",[0,1.45,2.1]);boom.rotation.x=-.24;add(root,new T.TorusGeometry(.22,.045,8,18,Math.PI*1.5),mats.dark,"tow_hook",[0,.5,3.55]).rotation.y=Math.PI/2;box(root,[1.65,.18,.42],mats.amber,"recovery_lightbar",[0,3.05,-2.2]);lights(root,.78,3.05,3.88,mats.amber);wheels(root,[-2.5,1.65,2.8],1.2,.6);}
  function create(type){const definition=DEFINITIONS[type];if(!definition)throw new Error(`Unknown emergency vehicle ${type}`);const root=new T.Group();root.name=`drivable_${type}`;({ambulance,fire,recovery})[type](root);root.traverse(object=>{if(object.name==="fire_roller_shutter")object.material=mats.fireCompartment;if(object.name==="tilting_recovery_bed")object.material=mats.recoveryBed});root.userData.definition=definition;root.userData.cockpitOffset=definition.cockpit;root.userData.maxSpeed=definition.maxSpeed;return root;}
  function update(vehicle,time,siren){if(!vehicle)return;vehicle.traverse(object=>{if(!object.userData.emergencyBeacon)return;const pulse=Math.sin(time*.018+object.id*1.7)>.05;object.visible=!siren||pulse;object.material.emissiveIntensity=siren?4.2:.45;});}
  function dispose(){resources.forEach(r=>r.dispose());authoredTextures.forEach(texture=>texture.dispose());Object.values(mats).forEach(m=>{if(!authoredTextures.includes(m.map))m.map?.dispose();m.dispose();});}
  return { definitions:DEFINITIONS, materials:mats, ready, create, update, dispose };
}
