/** Builds a continuous, disposable road from projectRouteToWorld points. */
export function createOsmRoadMesh({ THREE, scene, roadWidth = 15 } = {}) {
  if (!THREE || !scene) throw new Error("THREE and scene are required");
  const group = new THREE.Group(); group.name = "osm-route-road"; group.visible = false; scene.add(group);
  const materials = {
    asphalt: new THREE.MeshStandardMaterial({ color:0x34383c, roughness:.92, metalness:.02 }),
    shoulder: new THREE.MeshStandardMaterial({ color:0x77736a, roughness:.97 }),
    white: new THREE.MeshStandardMaterial({ color:0xf4f3e9, roughness:.7 }),
    yellow: new THREE.MeshStandardMaterial({ color:0xf1d058, roughness:.7 })
  };
  let route = [], elapsed = 0;
  function clear(){ while(group.children.length) group.children.pop().geometry?.dispose(); }
  function clean(points){const result=[];(points||[]).forEach(p=>{if(!Number.isFinite(p?.x)||!Number.isFinite(p?.z))return;const last=result.at(-1);if(!last||Math.hypot(p.x-last.x,p.z-last.z)>.25)result.push(p)});return result}
  function offset(points,amount){return points.map((p,i)=>{const a=points[Math.max(0,i-1)],b=points[Math.min(points.length-1,i+1)],dx=b.x-a.x,dz=b.z-a.z,l=Math.hypot(dx,dz)||1;return{x:p.x-dz/l*amount,z:p.z+dx/l*amount}})}
  function ribbon(points,halfWidth,material,y,name){
    const positions=[],uvs=[],indices=[];let distance=0;
    points.forEach((p,i)=>{const a=points[Math.max(0,i-1)],b=points[Math.min(points.length-1,i+1)],dx=b.x-a.x,dz=b.z-a.z,l=Math.hypot(dx,dz)||1,nx=-dz/l,nz=dx/l;if(i)distance+=Math.hypot(p.x-points[i-1].x,p.z-points[i-1].z);positions.push(p.x+nx*halfWidth,y,p.z+nz*halfWidth,p.x-nx*halfWidth,y,p.z-nz*halfWidth);uvs.push(0,distance/8,1,distance/8);if(i){const k=(i-1)*2;indices.push(k,k+1,k+2,k+1,k+3,k+2)}});
    const geometry=new THREE.BufferGeometry();geometry.setAttribute("position",new THREE.Float32BufferAttribute(positions,3));geometry.setAttribute("uv",new THREE.Float32BufferAttribute(uvs,2));geometry.setIndex(indices);geometry.computeVertexNormals();geometry.computeBoundingSphere();
    const mesh=new THREE.Mesh(geometry,material);mesh.name=name;mesh.receiveShadow=true;group.add(mesh);return mesh;
  }
  function marking(amount,width,material,dashed=false){const points=offset(route,amount);if(!dashed)return ribbon(points,width/2,material,.045,"road-marking");for(let i=0;i<points.length-1;i+=4){const part=points.slice(i,Math.min(i+3,points.length));if(part.length>1)ribbon(part,width/2,material,.05,"road-marking-dash")}}
  function setRoute(points){clear();route=clean(points);group.visible=route.length>1;if(!group.visible)return false;ribbon(route,roadWidth/2+1.8,materials.shoulder,-.08,"road-shoulders");ribbon(route,roadWidth/2,materials.asphalt,0,"road-asphalt");marking(-roadWidth/2+.35,.2,materials.white);marking(roadWidth/2-.35,.2,materials.white);marking(0,.18,materials.yellow,true);if(roadWidth>=14){marking(-roadWidth/4,.13,materials.white,true);marking(roadWidth/4,.13,materials.white,true)}return true}
  function update(deltaSeconds=0){elapsed+=Math.max(0,deltaSeconds);return{active:group.visible,points:route.length,elapsed}}
  function dispose(){clear();Object.values(materials).forEach(material=>material.dispose());scene.remove(group)}
  return{group,setRoute,update,dispose};
}
