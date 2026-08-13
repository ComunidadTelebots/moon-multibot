/** Efficient road renderer for routes projected from OpenStreetMap. */
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
    group.traverse(o=>{if(o!==group)o.geometry?.dispose()});
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
  function furniture(metadata={}){
    const rails=[],reflectors=[],signs=[],junctions=[];
    const stride=roadWidth<13?10:8;
    for(let i=4;i<route.length-4;i+=stride){const p=route[i],f=frame(route,i),angle=Math.atan2(f.tx,f.tz);[-1,1].forEach(side=>{const edge=roadWidth/2+1.15;rails.push({x:p.x+f.nx*edge,y:p.y+.58,z:p.z+f.nz*edge,ry:angle,sx:1,sy:1,sz:Math.max(2.4,stride*.65)});reflectors.push({x:p.x+f.nx*(roadWidth/2+.35),y:p.y+.16,z:p.z+f.nz*(roadWidth/2+.35),ry:angle})})}
    const nodes=Array.isArray(metadata.junctions)?metadata.junctions:route.filter(p=>p.junction||p.exit||p.destination);
    nodes.slice(0,48).forEach(n=>{let idx=Number.isInteger(n.index)?n.index:route.indexOf(n);if(idx<0&&Number.isFinite(n.routeIndex))idx=n.routeIndex;if(idx<0||idx>=route.length)return;const p=route[idx],f=frame(route,idx),angle=Math.atan2(f.tx,f.tz);junctions.push({x:p.x,y:p.y+.035,z:p.z,rx:-Math.PI/2,rz:-angle,sx:Math.min(roadWidth*.6,7),sz:2.4});signs.push({x:p.x+f.nx*(roadWidth/2+2),y:p.y+2.4,z:p.z+f.nz*(roadWidth/2+2),ry:angle})});
    instances("road-guardrails",new THREE.BoxGeometry(.12,.34,1),materials.rail,rails);
    instances("road-reflectors",new THREE.BoxGeometry(.1,.28,.08),materials.reflector,reflectors);
    instances("road-junction-markers",new THREE.PlaneGeometry(1,1),materials.junction,junctions);
    instances("road-direction-signs",new THREE.BoxGeometry(1.9,.9,.08),materials.sign,signs);
  }
  function setRoute(points,metadata={}){
    clear();route=clean(points);group.visible=route.length>1;if(!group.visible)return false;
    ribbon(route,roadWidth/2+1.8,materials.shoulder,-.08,"road-shoulders");ribbon(route,roadWidth/2,materials.asphalt,0,"road-asphalt");
    marking(-roadWidth/2+.35,.2,materials.white);marking(roadWidth/2-.35,.2,materials.white);marking(0,.18,materials.yellow,true);
    if(roadWidth>=14){marking(-roadWidth/4,.13,materials.white,true);marking(roadWidth/4,.13,materials.white,true)}furniture(metadata);return true;
  }
  function update(deltaSeconds=0){elapsed+=Math.max(0,deltaSeconds);return{active:group.visible,points:route.length,elapsed}}
  function dispose(){clear();Object.values(materials).forEach(material=>material.dispose());scene.remove(group)}
  return{group,setRoute,update,dispose};
}
