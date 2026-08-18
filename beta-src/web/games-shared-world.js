(function (global) {
  const typeOf = row => row.vehicle || ({ air: "plane", sea: "ship", rail: "train" }[row.game] || row.game || "player");
  function createVehicle(T, type) {
    const group = new T.Group(), material = new T.MeshStandardMaterial({ color: ({ truck: 0x42d9c2, bus: 0x4fa7ee, helicopter: 0xf3b63b, plane: 0xe8eef2, ship: 0x37a8d1, train: 0xe08e38 }[type] || 0xb986ef), roughness: .55, metalness: .18 });
    const dark = new T.MeshStandardMaterial({ color: 0x182128, roughness: .8 });
    const mesh = (geometry, mat, x, y, z) => { const item = new T.Mesh(geometry, mat); item.position.set(x, y, z); item.castShadow = true; group.add(item); return item; };
    if (type === "plane") { mesh(new T.ConeGeometry(.45, 4.8, 8), material, 0, .5, 0).rotation.x = -Math.PI / 2; mesh(new T.BoxGeometry(6.4,.12,1), material,0,.5,0); mesh(new T.BoxGeometry(2.3,.1,.8),material,0,.75,2); }
    else if (type === "helicopter") { mesh(new T.SphereGeometry(1,12,8),material,0,.7,0).scale.set(1,.7,1.5); mesh(new T.BoxGeometry(.25,.25,4),material,0,.7,2); mesh(new T.BoxGeometry(6,.08,.25),dark,0,1.8,0); }
    else if (type === "ship") { mesh(new T.BoxGeometry(3,.8,7),material,0,.45,0); mesh(new T.BoxGeometry(2,1.4,2.2),dark,0,1.45,1.2); }
    else if (type === "train") { mesh(new T.BoxGeometry(2.6,2.3,7),material,0,1.2,0); mesh(new T.BoxGeometry(2.2,.7,1),dark,0,1.6,-3.55); }
    else { mesh(new T.BoxGeometry(2.6,2.4,4),material,0,1.35,-1.3); mesh(new T.BoxGeometry(2.8,2.6,5),dark,0,1.45,3); for(const x of[-1.45,1.45])for(const z of[-2,2.7]){const w=mesh(new T.CylinderGeometry(.55,.55,.35,14),dark,x,.55,z);w.rotation.z=Math.PI/2;} }
    const lampMaterial=new T.MeshStandardMaterial({color:0x333333,emissive:0x000000,emissiveIntensity:0});for(const side of[-1,1]){const front=mesh(new T.SphereGeometry(.13,8,6),lampMaterial.clone(),side*.7,.8,-2.35);front.userData.sharedLamp="headlight";const rear=mesh(new T.SphereGeometry(.13,8,6),lampMaterial.clone(),side*.7,.7,3.5);rear.userData.sharedLamp="rear";rear.userData.side=side}group.userData.target=new T.Vector3();group.userData.targetHeading=0;
    group.userData.dispose = () => { group.traverse(object => object.geometry?.dispose?.()); material.dispose(); dark.dispose(); };
    return group;
  }
  function createThreePresence({ THREE: T, scene, scale = 1 }) {
    const entries = new Map();
    function update(state, ownId) {
      const visible = [...(state?.players || []), ...(state?.ai || [])].filter(row => row.id !== ownId), ids = new Set(visible.map(row => row.id));
      for (const [id, entry] of entries) if (!ids.has(id)) { scene.remove(entry.group); entry.group.userData.dispose?.(); entries.delete(id); }
      for (const row of visible) { const type=typeOf(row); let entry=entries.get(row.id); if(!entry||entry.type!==type){if(entry){scene.remove(entry.group);entry.group.userData.dispose?.()}entry={type,group:createVehicle(T,type)};entries.set(row.id,entry);scene.add(entry.group)} const z=Number(row.z ?? row.y ?? 0), altitude=Number(row.altitude || 0);entry.group.userData.target.set(Number(row.x||0)*scale,Math.max(.05,altitude)*scale,z*scale);entry.group.userData.targetHeading=Number(row.heading||0);entry.group.visible=true;entry.group.userData.peer=row;entry.group.traverse(part=>{if(!part.userData.sharedLamp)return;const active=part.userData.sharedLamp==="headlight"?row.headlights:(row.braking||row.hazards||Number(row.indicator)===part.userData.side);part.material.emissive.setHex(active?(part.userData.sharedLamp==="headlight"?0xe7f5ff:0xff240d):0x000000);part.material.emissiveIntensity=active?3:0}); }
      return visible;
    }
    function tick(dt){const alpha=1-Math.exp(-Math.max(0,dt)*9);for(const entry of entries.values()){entry.group.position.lerp(entry.group.userData.target,alpha);let delta=entry.group.userData.targetHeading-entry.group.rotation.y;delta=Math.atan2(Math.sin(delta),Math.cos(delta));entry.group.rotation.y+=delta*alpha}}
    function dispose(){for(const entry of entries.values()){scene.remove(entry.group);entry.group.userData.dispose?.()}entries.clear()}
    return { entries, update, tick, dispose };
  }
  global.MoonSharedWorld = { typeOf, createThreePresence };
})(window);
