const CACHE_VERSION = 1;
const CACHE_TTL = 7 * 24 * 60 * 60 * 1000;
export const OSM_CITY_PRESETS = {
  madrid: { name: "Madrid", lat: 40.4168, lon: -3.7038 },
  paris: { name: "París", lat: 48.8566, lon: 2.3522 },
  berlin: { name: "Berlín", lat: 52.52, lon: 13.405 },
  prague: { name: "Praga", lat: 50.0755, lon: 14.4378 },
};

export function createOsmScenery({ THREE: T, scene, qualityLevel = 2, city = "madrid" }) {
  const root = new T.Group(); root.name = "openstreetmap_generated_scenery"; root.position.z = -520; scene.add(root);
  const preset = OSM_CITY_PRESETS[city] || OSM_CITY_PRESETS.madrid;
  const materials = {
    trunk: new T.MeshStandardMaterial({ color: 0x62452f, roughness: .96 }),
    leaf: new T.MeshStandardMaterial({ color: 0x2d6939, roughness: .93 }),
    park: new T.MeshStandardMaterial({ color: 0x4f8a45, roughness: .98, transparent: true, opacity: .92 }),
    garden: new T.MeshStandardMaterial({ color: 0x6a9948, roughness: .96 }),
    road: new T.MeshStandardMaterial({ color: 0x34383b, roughness: .91 }),
    kerb: new T.MeshStandardMaterial({ color: 0xb8bbb7, roughness: .74 }),
    flower: new T.MeshStandardMaterial({ color: 0xe6b441, roughness: .85 }),
  };
  const geometry = [];
  const entities = { trees: 0, gardens: 0, roundabouts: 0 };
  const project = (lat, lon) => ({ x: (lon - preset.lon) * 111320 * Math.cos(preset.lat * Math.PI / 180) * .22, z: -(lat - preset.lat) * 111320 * .22 });
  const treeGeometry = new T.CylinderGeometry(.23,.38,3.8,qualityLevel > 1 ? 9 : 6); geometry.push(treeGeometry);
  const crownGeometry = new T.IcosahedronGeometry(2.25,qualityLevel > 1 ? 1 : 0); geometry.push(crownGeometry);
  function addTrees(points) {
    const limit = [35,80,180,320][qualityLevel], selected = points.slice(0,limit); if (!selected.length) return;
    const trunks = new T.InstancedMesh(treeGeometry,materials.trunk,selected.length), crowns = new T.InstancedMesh(crownGeometry,materials.leaf,selected.length), dummy = new T.Object3D();
    selected.forEach((point,index) => { const p=project(point.lat,point.lon), scale=.72+(index%7)*.06; dummy.position.set(p.x,1.9,p.z);dummy.scale.setScalar(scale);dummy.rotation.y=index*2.399;dummy.updateMatrix();trunks.setMatrixAt(index,dummy.matrix);dummy.position.y=5.1*scale;dummy.updateMatrix();crowns.setMatrixAt(index,dummy.matrix); });
    trunks.castShadow=crowns.castShadow=qualityLevel>0;trunks.receiveShadow=crowns.receiveShadow=true;root.add(trunks,crowns);entities.trees=selected.length;
  }
  function addArea(element, type) {
    const points=(element.geometry||[]).map(p=>project(p.lat,p.lon)); if(points.length<3)return;
    const shape=new T.Shape();shape.moveTo(points[0].x,points[0].z);for(let i=1;i<points.length;i++)shape.lineTo(points[i].x,points[i].z);
    const geo=new T.ShapeGeometry(shape);geometry.push(geo);const mesh=new T.Mesh(geo,type==="garden"?materials.garden:materials.park);mesh.rotation.x=-Math.PI/2;mesh.position.y=.03;mesh.receiveShadow=true;root.add(mesh);
    const centre=points.reduce((a,p)=>({x:a.x+p.x/points.length,z:a.z+p.z/points.length}),{x:0,z:0});
    if(type==="garden"&&qualityLevel>0)for(let i=0;i<12;i++){const flower=new T.Mesh(new T.SphereGeometry(.16,7,5),materials.flower);flower.position.set(centre.x+Math.cos(i*2.399)*(1+i%4),.2,centre.z+Math.sin(i*2.399)*(1+i%4));root.add(flower);geometry.push(flower.geometry);}
    entities.gardens++;
  }
  function addRoundabout(element) {
    const points=(element.geometry||[]).map(p=>project(p.lat,p.lon));if(points.length<4)return;
    const centre=points.reduce((a,p)=>({x:a.x+p.x/points.length,z:a.z+p.z/points.length}),{x:0,z:0});
    const radius=Math.max(5,Math.min(18,points.reduce((sum,p)=>sum+Math.hypot(p.x-centre.x,p.z-centre.z),0)/points.length));
    const road=new T.Mesh(new T.RingGeometry(radius-2.7,radius+2.7,qualityLevel>1?64:32),materials.road);road.rotation.x=-Math.PI/2;road.position.set(centre.x,.08,centre.z);road.receiveShadow=true;root.add(road);geometry.push(road.geometry);
    const island=new T.Mesh(new T.CylinderGeometry(radius-3.1,radius-3, .42,qualityLevel>1?48:24),materials.garden);island.position.set(centre.x,.18,centre.z);island.receiveShadow=true;root.add(island);geometry.push(island.geometry);
    const kerb=new T.Mesh(new T.TorusGeometry(radius-2.95,.18,8,qualityLevel>1?64:32),materials.kerb);kerb.rotation.x=Math.PI/2;kerb.position.set(centre.x,.42,centre.z);root.add(kerb);geometry.push(kerb.geometry);
    for(let i=0;i<Math.min(10,qualityLevel*3+4);i++){const crown=new T.Mesh(new T.IcosahedronGeometry(.75,1),materials.leaf);const angle=i*2.399,distance=(radius-4)*(.35+(i%3)*.2);crown.position.set(centre.x+Math.cos(angle)*distance,1,centre.z+Math.sin(angle)*distance);crown.castShadow=true;root.add(crown);geometry.push(crown.geometry);}
    entities.roundabouts++;
  }
  function build(data) {
    const trees=[], areas=[], roundabouts=[];
    for(const element of data.elements||[]){if(element.type==="node"&&element.tags?.natural==="tree")trees.push(element);else if(element.tags?.junction==="roundabout")roundabouts.push(element);else if(["park","garden"].includes(element.tags?.leisure))areas.push(element);}
    addTrees(trees);areas.slice(0,qualityLevel>1?18:8).forEach(element=>addArea(element,element.tags.leisure));roundabouts.slice(0,qualityLevel>1?5:2).forEach(addRoundabout);
    return entities;
  }
  async function load() {
    const key=`moon.osm.${CACHE_VERSION}.${city}`;let cached=null,data;
    try{cached=localStorage.getItem(key);}catch{}
    if(cached){try{const parsed=JSON.parse(cached);if(Date.now()-parsed.at<CACHE_TTL)data=parsed.data;}catch{localStorage.removeItem(key);}}
    if(!data){const radius=qualityLevel>1?1800:1100,query=`[out:json][timeout:15];(node(around:${radius},${preset.lat},${preset.lon})[natural=tree];way(around:${radius},${preset.lat},${preset.lon})[leisure~"^(park|garden)$"];way(around:${radius},${preset.lat},${preset.lon})[junction=roundabout];);out body geom qt;`;const response=await fetch(`https://overpass-api.de/api/interpreter?data=${encodeURIComponent(query)}`);if(!response.ok)throw new Error(`OSM ${response.status}`);data=await response.json();try{localStorage.setItem(key,JSON.stringify({at:Date.now(),data}));}catch{}}
    return build(data);
  }
  function dispose(){root.removeFromParent();geometry.forEach(g=>g.dispose());Object.values(materials).forEach(m=>m.dispose());}
  return { root, entities, preset, load, dispose };
}
