const PROFILE_STEP=Object.freeze({LEGACY:12,LOW:8,MEDIUM:5,HIGH:3,ULTRA:1});
export function worldTileId(lon,lat,size=.25){return `${size}:${Math.floor((Number(lon)+180)/size)}:${Math.floor((Number(lat)+90)/size)}`;}
export function worldPolygonProfile(profile="MEDIUM"){const key=String(profile).toUpperCase();return{name:PROFILE_STEP[key]?key:"MEDIUM",sampleStep:PROFILE_STEP[key]||5,far:key==="LEGACY"?1000:key==="LOW"?1800:key==="ULTRA"?5200:3200};}
export function buildWorldPolygonPlan(geoRoute=[],worldRoute=[],profile="MEDIUM"){
  const cfg=worldPolygonProfile(profile),count=Math.min(geoRoute.length,worldRoute.length),tiles=new Map();if(count<2)return[];
  for(let i=0;i<count-1;i+=cfg.sampleStep){const end=Math.min(count-1,i+cfg.sampleStep),g=geoRoute[Math.floor((i+end)/2)],key=worldTileId(g[0]??g.lon,g[1]??g.lat);if(!tiles.has(key))tiles.set(key,{id:key,segments:[],center:{x:0,z:0},points:0});const tile=tiles.get(key);for(let j=i;j<end;j++){tile.segments.push([worldRoute[j],worldRoute[j+1]]);tile.center.x+=(worldRoute[j].x+worldRoute[j+1].x)/2;tile.center.z+=(worldRoute[j].z+worldRoute[j+1].z)/2;tile.points++;}}
  return[...tiles.values()].map(tile=>({...tile,center:{x:tile.center.x/tile.points,z:tile.center.z/tile.points}}));
}
export function createWorldPolygonMesh({THREE:T,scene,qualityProfile="MEDIUM",corridorWidth=900}={}){
  if(!T||!scene)throw Error("THREE and scene are required");const root=new T.Group();root.name="world-polygon-tiles";scene.add(root);const cfg=worldPolygonProfile(qualityProfile),tiles=[];let tick=0;
  const fallback=new T.MeshStandardMaterial({color:0x486b3d,roughness:.98});
  function clear(){while(root.children.length){const child=root.children.pop();child.geometry?.dispose?.();}tiles.length=0;}
  function makeTile(plan){const positions=[],indices=[];let v=0;for(const[a,b]of plan.segments){const dx=b.x-a.x,dz=b.z-a.z,len=Math.hypot(dx,dz)||1,nx=-dz/len,nz=dx/len,w=corridorWidth,ay=Number(a.y)||0,by=Number(b.y)||0;positions.push(a.x+nx*w,ay-.22,a.z+nz*w,a.x-nx*w,ay-.22,a.z-nz*w,b.x+nx*w,by-.22,b.z+nz*w,b.x-nx*w,by-.22,b.z-nz*w);indices.push(v,v+2,v+1,v+1,v+2,v+3);v+=4;}const geometry=new T.BufferGeometry();geometry.setAttribute("position",new T.Float32BufferAttribute(positions,3));geometry.setIndex(indices);geometry.computeVertexNormals();const mesh=new T.Mesh(geometry,fallback);mesh.name=`world-tile-${plan.id}`;mesh.receiveShadow=true;mesh.userData.streamCenter=new T.Vector3(plan.center.x,0,plan.center.z);root.add(mesh);tiles.push(mesh);}
  function setRoute(route,worldRoute){clear();const geo=route?.coordinates||route||[];buildWorldPolygonPlan(geo,worldRoute||[],cfg.name).forEach(makeTile);root.visible=tiles.length>0;return{tiles:tiles.length,triangles:tiles.reduce((n,t)=>n+(t.geometry.index?.count||0)/3,0),profile:cfg.name};}
  function applyMaterials(library){for(const mesh of tiles){const next=library?.materialFor?.("terrain grass")||library?.terrain;if(next)mesh.material=next;}}
  function update(dt,{camera,playerPosition,visibilityDistance}={}){tick-=Math.max(0,Number(dt)||0);if(tick>0)return;tick=.25;const p=camera?.position||playerPosition;if(!p)return;const limit=Number(visibilityDistance)||cfg.far;for(const mesh of tiles){const c=mesh.userData.streamCenter,d=Math.hypot(c.x-p.x,c.z-p.z);mesh.visible=d<=limit*(mesh.visible?1.12:1);}}
  function dispose(){clear();fallback.dispose();root.removeFromParent();}
  return{root,tiles,setRoute,applyMaterials,update,dispose,get profile(){return cfg.name;}};
}
