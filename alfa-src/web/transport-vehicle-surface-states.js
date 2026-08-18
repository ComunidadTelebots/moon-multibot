export const VEHICLE_STATE_TEXTURES=Object.freeze({
 tyre:"./generated-textures/land-tyre-tread-v1.png",motion:"./generated-textures/land-wheel-motion-v1.png",
 rain:"./generated-textures/land-rain-state-v1.png",mud:"./generated-textures/land-dried-mud-v1.png",
 grime:"./generated-textures/land-road-grime-v1.png",
});
const isWheel=name=>/tyre|tire|wheel_rolling|tread/i.test(name||"");
const isBody=(object)=>/body|cab|exterior|paint|door|trailer/i.test(object.name||"")||["paint","commercial"].includes(object.material?.userData?.vehicleSurface);
export function createVehicleSurfaceStates({THREE:T,qualityLevel=2}={}){
 const enabled=qualityLevel>=2,textures=new Map(),entries=[],loader=new T.TextureLoader();let vehicle=null,lastMode="";
 const ready=enabled?Promise.all(Object.entries(VEHICLE_STATE_TEXTURES).map(([key,url])=>new Promise((resolve,reject)=>loader.load(url,texture=>{texture.colorSpace=key==="rain"||key==="mud"||key==="grime"?T.NoColorSpace:T.SRGBColorSpace;texture.wrapS=texture.wrapT=T.RepeatWrapping;texture.repeat.set(key==="motion"?1:2,key==="motion"?1:2);texture.anisotropy=qualityLevel>2?16:8;textures.set(key,texture);resolve(texture)},undefined,reject)))):Promise.resolve([]);
 function setVehicle(root){entries.length=0;vehicle=root;if(!enabled||!root)return;root.traverse(object=>{if(!object.isMesh||!object.material)return;if(isWheel(object.name)||isBody(object))entries.push({object,material:object.material,baseMap:object.material.map||null,baseRoughnessMap:object.material.roughnessMap||null,baseBumpMap:object.material.bumpMap||null,baseRoughness:object.material.roughness})});lastMode=""}
 function update({speed=0,weather="clear",surface="asphalt",distanceKm=0}={}){if(!enabled||!vehicle||textures.size<5)return;const wet=/rain|storm|thunder/i.test(weather),dirty=/mud|dirt|gravel|offroad/i.test(surface),bodyState=wet?"rain":dirty?"mud":distanceKm>20?"grime":"clean",wheelState=Math.abs(speed)>18?"motion":"tyre",mode=`${bodyState}:${wheelState}`;if(mode===lastMode)return;lastMode=mode;for(const entry of entries){const wheel=isWheel(entry.object.name),material=entry.material;if(wheel){material.map=textures.get(wheelState);material.roughness=.82}else{const state=bodyState==="clean"?null:textures.get(bodyState);material.roughnessMap=state||entry.baseRoughnessMap;material.bumpMap=state||entry.baseBumpMap;material.bumpScale=state?.03:material.bumpScale;material.roughness=wet?.24:entry.baseRoughness}material.needsUpdate=true}}
 function dispose(){for(const entry of entries){entry.material.map=entry.baseMap;entry.material.roughnessMap=entry.baseRoughnessMap;entry.material.bumpMap=entry.baseBumpMap;entry.material.roughness=entry.baseRoughness;entry.material.needsUpdate=true}textures.forEach(texture=>texture.dispose());textures.clear();entries.length=0;vehicle=null}
 return{ready,setVehicle,update,dispose,enabled};
}
export default createVehicleSurfaceStates;
