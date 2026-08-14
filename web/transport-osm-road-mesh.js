/** Efficient road renderer for routes projected from OpenStreetMap. */
export function roadSignLabel(step = {}) {
  const raw = String(step.destination || step.destinations || step.ref || step.name || "").trim();
  const clean = raw.replace(/\s+/g, " ").replace(/^Carretera sin nombre$/i, "");
  if (!clean) return "Siguiente salida";
  return clean.length > 34 ? `${clean.slice(0, 31).trimEnd()}…` : clean;
}

export function buildRoadSignPlan(route = [], steps = [], maximum = 24) {
  if (!Array.isArray(route) || route.length < 2 || !Array.isArray(steps) || !steps.length) return [];
  const totalKm = Math.max(0, Number(route.at(-1)?.distanceKm) || 0);
  let travelledKm = 0;
  return steps.slice(0, Math.max(0, maximum)).map((step, order) => {
    travelledKm += Math.max(0, Number(step.distanceKm) || 0);
    const targetKm = totalKm ? Math.min(totalKm, travelledKm) : (order + 1) / (steps.length + 1);
    let index = 1;
    if (totalKm) {
      let best = Infinity;
      route.forEach((point, candidate) => {
        const delta = Math.abs((Number(point.distanceKm) || 0) - targetKm);
        if (delta < best) { best = delta; index = candidate; }
      });
    } else index = Math.max(1, Math.min(route.length - 2, Math.round(targetKm * (route.length - 1))));
    return { index, label: roadSignLabel(step), maneuver: String(step.maneuver || "continue"), distanceKm: targetKm };
  }).filter((item, index, list) => item.index > 0 && item.index < route.length - 1 && !list.slice(0, index).some(previous => previous.index === item.index || previous.label === item.label));
}

export function createOsmRoadMesh({ THREE, scene, roadWidth = 15 } = {}) {
  if (!THREE || !scene) throw new Error("THREE and scene are required");
  const group = new THREE.Group(); group.name = "osm-route-road"; group.visible = false; scene.add(group);
  const materials = {
    asphalt: new THREE.MeshStandardMaterial({ color:0x30343a, roughness:.94, metalness:.015 }),
    shoulder: new THREE.MeshStandardMaterial({ color:0x696963, roughness:1, metalness:0 }),
    white: new THREE.MeshStandardMaterial({ color:0xf7f5df, roughness:.58 }),
    yellow: new THREE.MeshStandardMaterial({ color:0xe8c74e, roughness:.62 }),
    rail: new THREE.MeshStandardMaterial({ color:0xaeb5ba, roughness:.38, metalness:.72 }),
    reflector: new THREE.MeshStandardMaterial({ color:0xf8f3d6, emissive:0xffd889, emissiveIntensity:.45, roughness:.35 }),
    sign: new THREE.MeshStandardMaterial({ color:0x17629a, roughness:.52, metalness:.08 }),
    junction: new THREE.MeshStandardMaterial({ color:0xe5b53c, emissive:0x5a3200, emissiveIntensity:.16, roughness:.68 })
  };
  let route = [], elapsed = 0;
  const clamp=(v,a,b)=>Math.max(a,Math.min(b,v));
  function clear(){
    group.traverse(o=>{if(o!==group){o.geometry?.dispose();if(o.userData?.uniqueMaterial){o.userData.texture?.dispose?.();o.material?.dispose?.()}}});
    while(group.children.length)group.remove(group.children[0]);
  }
  function clean(points){
    const result=[];
    (points||[]).forEach((p,i)=>{
      if(!Number.isFinite(p?.x)||!Number.isFinite(p?.z))return;
      const last=result.at(-1); if(last&&Math.hypot(p.x-last.x,p.z-last.z)<=.25)return;
      const rawY=Number(p.y??p.elevation??p.altitude);
      result.push({ ...p, x:+p.x, z:+p.z, y:Number.isFinite(rawY)?rawY:Math.sin(i*.17)*.08 });
    });
    // A short low-pass pass removes OSM/GPS altitude spikes that produce broken asphalt.
    for(let pass=0;pass<2;pass++){const ys=result.map(p=>p.y);for(let i=1;i<result.length-1;i++)result[i].y=(ys[i-1]+ys[i]*2+ys[i+1])/4}
    return result;
  }
  function frame(points,i){
    const a=points[Math.max(0,i-1)],b=points[Math.min(points.length-1,i+1)];
    const dx=b.x-a.x,dz=b.z-a.z,l=Math.hypot(dx,dz)||1;
    let bank=0;
    if(i>0&&i<points.length-1){
      const p=points[i-1],n=points[i+1],ax=points[i].x-p.x,az=points[i].z-p.z,bx=n.x-points[i].x,bz=n.z-points[i].z;
      bank=clamp((ax*bz-az*bx)/((Math.hypot(ax,az)*Math.hypot(bx,bz))||1)*.055,-.045,.045);
    }
    return{tx:dx/l,tz:dz/l,nx:-dz/l,nz:dx/l,bank};
  }
  function offset(points,amount){return points.map((p,i)=>{const f=frame(points,i);return{...p,x:p.x+f.nx*amount,z:p.z+f.nz*amount,y:p.y+f.bank*amount}})}
  function ribbon(points,halfWidth,material,lift,name){
    const positions=[],uvs=[],indices=[];let distance=0;
    points.forEach((p,i)=>{const f=frame(points,i);if(i)distance+=Math.hypot(p.x-points[i-1].x,p.z-points[i-1].z);positions.push(p.x+f.nx*halfWidth,p.y+lift+f.bank*halfWidth,p.z+f.nz*halfWidth,p.x-f.nx*halfWidth,p.y+lift-f.bank*halfWidth,p.z-f.nz*halfWidth);uvs.push(0,distance/7,1,distance/7);if(i){const k=(i-1)*2;indices.push(k,k+1,k+2,k+1,k+3,k+2)}});
    const geometry=new THREE.BufferGeometry();geometry.setAttribute("position",new THREE.Float32BufferAttribute(positions,3));geometry.setAttribute("uv",new THREE.Float32BufferAttribute(uvs,2));geometry.setIndex(indices);geometry.computeVertexNormals();geometry.computeBoundingSphere();
    const mesh=new THREE.Mesh(geometry,material);mesh.name=name;mesh.receiveShadow=true;group.add(mesh);return mesh;
  }
  function marking(amount,width,material,dashed=false){const points=offset(route,amount);if(!dashed)return ribbon(points,width/2,material,.045,"road-marking");for(let i=0;i<points.length-1;i+=4){const part=points.slice(i,Math.min(i+3,points.length));if(part.length>1)ribbon(part,width/2,material,.05,"road-marking-dash")}}
  function instances(name, geometry, material, placements){
    if(!placements.length){geometry.dispose();return}
    const mesh=new THREE.InstancedMesh(geometry,material,placements.length),dummy=new THREE.Object3D();mesh.name=name;
    placements.forEach((p,i)=>{dummy.position.set(p.x,p.y,p.z);dummy.rotation.set(p.rx||0,p.ry||0,p.rz||0);dummy.scale.set(p.sx||1,p.sy||1,p.sz||1);dummy.updateMatrix();mesh.setMatrixAt(i,dummy.matrix)});
    mesh.instanceMatrix.needsUpdate=true;mesh.frustumCulled=true;group.add(mesh);
  }
  function directionSign(plan, p, f, angle){
    let material=materials.sign, texture=null;
    if(typeof document!=="undefined"){
      const canvas=document.createElement("canvas"),ctx=canvas.getContext?.("2d");
      if(ctx){
        canvas.width=768;canvas.height=256;ctx.fillStyle="#12609a";ctx.fillRect(0,0,768,256);ctx.strokeStyle="#f5f7ed";ctx.lineWidth=14;ctx.strokeRect(10,10,748,236);
        ctx.fillStyle="#fff";ctx.font="700 52px system-ui, sans-serif";ctx.textAlign="center";ctx.textBaseline="middle";ctx.fillText(plan.label,384,102,690);
        ctx.font="800 70px system-ui, sans-serif";ctx.fillText(/left/.test(plan.maneuver)?"←":/right/.test(plan.maneuver)?"→":"↑",384,184);
        texture=new THREE.CanvasTexture(canvas);texture.colorSpace=THREE.SRGBColorSpace||texture.colorSpace;texture.needsUpdate=true;
        material=new THREE.MeshStandardMaterial({map:texture,color:0xffffff,roughness:.5,metalness:.04});
      }
    }
    const sign=new THREE.Mesh(new THREE.BoxGeometry(4.8,1.6,.1),material);sign.name="road-direction-sign";sign.position.set(p.x+f.nx*(roadWidth/2+2),p.y+2.6,p.z+f.nz*(roadWidth/2+2));sign.rotation.y=angle;sign.userData={label:plan.label,maneuver:plan.maneuver,texture,uniqueMaterial:material!==materials.sign};group.add(sign);
    const post=new THREE.Mesh(new THREE.CylinderGeometry(.07,.09,2.25,8),materials.rail);post.name="road-sign-post";post.position.set(sign.position.x,p.y+1.12,sign.position.z);group.add(post);
  }
  function furniture(metadata={}){
    const rails=[],reflectors=[],junctions=[];
    const stride=roadWidth<13?10:8;
    for(let i=4;i<route.length-4;i+=stride){const p=route[i],f=frame(route,i),angle=Math.atan2(f.tx,f.tz);[-1,1].forEach(side=>{const edge=roadWidth/2+1.15;rails.push({x:p.x+f.nx*edge,y:p.y+.58,z:p.z+f.nz*edge,ry:angle,sx:1,sy:1,sz:Math.max(2.4,stride*.65)});reflectors.push({x:p.x+f.nx*(roadWidth/2+.35),y:p.y+.16,z:p.z+f.nz*(roadWidth/2+.35),ry:angle})})}
    const nodes=buildRoadSignPlan(route,Array.isArray(metadata.junctions)?metadata.junctions:[],metadata.mobile?10:24);
    nodes.forEach(n=>{const p=route[n.index],f=frame(route,n.index),angle=Math.atan2(f.tx,f.tz);junctions.push({x:p.x,y:p.y+.035,z:p.z,rx:-Math.PI/2,rz:-angle,sx:Math.min(roadWidth*.6,7),sz:2.4});directionSign(n,p,f,angle)});
    instances("road-guardrails",new THREE.BoxGeometry(.12,.34,1),materials.rail,rails);
    instances("road-reflectors",new THREE.BoxGeometry(.1,.28,.08),materials.reflector,reflectors);
    instances("road-junction-markers",new THREE.PlaneGeometry(1,1),materials.junction,junctions);
  }
  function setRoute(points,metadata={}){
    clear();route=clean(points);group.visible=route.length>1;if(!group.visible)return false;
    ribbon(route,roadWidth/2+1.8,materials.shoulder,-.08,"road-shoulders");ribbon(route,roadWidth/2,materials.asphalt,0,"road-asphalt");
    marking(-roadWidth/2+.35,.2,materials.white);marking(roadWidth/2-.35,.2,materials.white);marking(0,.18,materials.yellow,true);
    if(roadWidth>=14){marking(-roadWidth/4,.13,materials.white,true);marking(roadWidth/4,.13,materials.white,true)}furniture(metadata);return true;
  }
  function update(deltaSeconds=0){elapsed+=Math.max(0,deltaSeconds);return{active:group.visible,points:route.length,elapsed}}
  function applyMaterials(regional={}){
    const source=regional.materials||regional;
    const copyMaps=(target,value)=>{if(!target||!value)return;for(const key of ["map","normalMap","roughnessMap","bumpMap","aoMap"]){if(value[key]?.isTexture)target[key]=value[key]}if(Number.isFinite(value.roughness))target.roughness=value.roughness;if(Number.isFinite(value.bumpScale))target.bumpScale=value.bumpScale;target.needsUpdate=true};
    copyMaps(materials.asphalt,source.asphalt);copyMaps(materials.shoulder,source.shoulder);copyMaps(materials.sign,source.sign);return api;
  }
  function dispose(){clear();Object.values(materials).forEach(material=>material.dispose());scene.remove(group)}
  const api={group,materials,setRoute,update,applyMaterials,dispose};return api;
}
