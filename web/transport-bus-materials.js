const URLS=Object.freeze({
 exterior:"./generated-textures/land-bus-exterior-v1.png",
 cockpit:"./generated-textures/land-bus-cockpit-v1.png",
 floor:"./generated-textures/land-bus-floor-v1.png",
 upholstery:"./generated-textures/land-bus-upholstery-v1.png",
});
export function busMaterialRole(name=""){
 const value=String(name).toLowerCase();
 if(/seat|upholstery|bench/.test(value))return"upholstery";
 if(/floor|step|platform/.test(value))return"floor";
 if(/dashboard|console|control|ticket|validator|instrument|steering/.test(value))return"cockpit";
 if(/bus_roof|door_panel|windscreen|window|glass/.test(value))return"";
 if(/bus_body|exterior/.test(value))return"exterior";
 return"";
}
export function createBusAuthoredMaterials({THREE:T,qualityLevel=2}={}){
 const textures=new Map(),materials=new Map(),enabled=qualityLevel>=2;
 const ready=enabled?Promise.all(Object.entries(URLS).map(([role,url])=>new Promise((resolve,reject)=>new T.TextureLoader().load(url,texture=>{texture.colorSpace=T.SRGBColorSpace;texture.wrapS=texture.wrapT=T.RepeatWrapping;texture.repeat.set(role==="floor"?2:1,role==="floor"?3:1);texture.anisotropy=qualityLevel>2?16:8;textures.set(role,texture);materials.set(role,new T.MeshPhysicalMaterial({map:texture,color:0xffffff,roughness:role==="floor"?.88:role==="upholstery"?.82:.32,metalness:role==="exterior"?.3:.04,clearcoat:role==="exterior"?.72:.08}));resolve(texture)},undefined,reject)))):Promise.resolve([]);
 const apply=root=>{if(!enabled)return 0;let count=0;root?.traverse?.(object=>{if(!object.isMesh)return;const role=busMaterialRole(object.name);if(!role||!materials.has(role))return;object.material=materials.get(role).clone();object.material.userData={...object.material.userData,authoredBusRole:role,independentComponent:object.name};count++});return count};
 const dispose=()=>{textures.forEach(texture=>texture.dispose());materials.forEach(material=>material.dispose());textures.clear();materials.clear()};
 return{ready,apply,dispose,enabled};
}
export default createBusAuthoredMaterials;
