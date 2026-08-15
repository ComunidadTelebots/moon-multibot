export const EXTERIOR_TILES={
  paint:[0,0],trim:[1,0],grille:[2,0],chrome:[3,0],rim:[0,1],rubber:[1,1],tread:[2,1],lamp:[3,1],amber:[0,2],red:[1,2],trailer:[2,2],rail:[3,2],chassis:[0,3],tank:[1,3],dirty:[2,3]
};
export const CABIN_TILES={soft:[0,0],polymer:[1,0],piano:[2,0],leather:[3,0],fabric:[0,1],headliner:[1,1],rubber:[2,1],aluminium:[3,1],screen:[0,2],glass:[2,2],sleeper:[0,3],curtain:[1,3],cabinet:[2,3],seatbelt:[3,3]};

const PART_ROOT="./generated-textures/vehicle-parts/aster-viento";
export const INDEPENDENT_TEXTURES={
  exterior:Object.fromEntries(Object.keys(EXTERIOR_TILES).map(key=>[key,`${PART_ROOT}/exterior/${key}-v1.png`])),
  cabin:Object.fromEntries(Object.keys(CABIN_TILES).map(key=>[key,`${PART_ROOT}/cabin/${key}-v1.png`]))
};

export function atlasTileTransform(column,row){return {repeat:[.25,.25],offset:[column*.25,.75-row*.25]};}
export function hasTileSafeUv(object){const values=object?.geometry?.attributes?.uv?.array;if(!values?.length)return false;for(const value of values){const number=Number(value);if(!Number.isFinite(number)||number<-.001||number>1.001)return false}return true;}

function exteriorKind(name=""){
  if(/tyre_tread/.test(name))return"tread";if(/tyre|sidewall/.test(name))return"rubber";if(/rim|wheel_nut|brake_disc/.test(name))return"rim";
  if(/grille|cooling_intake|condenser/.test(name))return"grille";if(/headlamp|daylight/.test(name))return"lamp";if(/indicator|marker/.test(name))return"amber";if(/tail_lamp/.test(name))return"red";
  if(/trailer_body|rear_door/.test(name))return"trailer";if(/trailer_roof|panel_seam|side_guard|door_lock/.test(name))return"rail";if(/fuel_tank|adblue/.test(name))return"tank";
  if(/chassis|frame|fifth|underframe|caliper/.test(name))return"chassis";if(/cab|roof|pillar|door_skin|fairing|bumper|side_skirt|wheel_arch/.test(name))return"paint";
  if(/chrome|blade|step|badge|mirror_glass/.test(name))return"chrome";return"trim";
}
function cabinKind(name=""){
  if(/screen|display|camera_feed/.test(name))return"screen";if(/glass|windshield|window|mirror/.test(name))return"glass";if(/seatbelt/.test(name))return"seatbelt";
  if(/seat|bolster|lumbar|armrest|steering_rim/.test(name))return/leather|bolster|armrest|rim/.test(name)?"leather":"fabric";
  if(/headliner|visor|pillow/.test(name))return"headliner";if(/mattress|sleeper_fabric/.test(name))return"sleeper";if(/curtain/.test(name))return"curtain";if(/locker|cabinet|drawer/.test(name))return"cabinet";
  if(/floor|bellows/.test(name))return"rubber";if(/aluminium|bezel|ring|pedal|rail|stitching/.test(name))return"aluminium";if(/piano|rocker|toggle/.test(name))return"piano";if(/dashboard|console|panel|hood/.test(name))return"soft";return"polymer";
}

export function createBakedMaterialLibrary({THREE:T,qualityLevel=2}={}){
  const enabled=qualityLevel>=2,loader=enabled?new T.TextureLoader():null,textures={exterior:{},cabin:{}},materials=new Map();
  const entries=Object.entries(INDEPENDENT_TEXTURES).flatMap(([family,table])=>Object.entries(table).map(([kind,url])=>({family,kind,url})));
  const ready=enabled?Promise.all(entries.map(async({family,kind,url})=>{const texture=await loader.loadAsync(url);texture.name=`aster_${family}_${kind}_authored`;texture.colorSpace=T.SRGBColorSpace;texture.wrapS=texture.wrapT=T.RepeatWrapping;texture.anisotropy=qualityLevel>2?16:8;textures[family][kind]=texture;})).then(()=>true):Promise.resolve(false);
  function materialFor(base,map,key){const cacheKey=`${base.uuid}:${key}`;if(materials.has(cacheKey))return materials.get(cacheKey);const material=base.clone();
    // HIGH/ULTRA use only authored, baked atlas assets. Remove the canvas/noise
    // maps inherited from the legacy material instead of mixing both systems.
    material.map=map;material.normalMap=null;material.bumpMap=map;material.bumpScale=key.startsWith("c:")?.012:.018;material.roughnessMap=null;material.metalnessMap=null;material.aoMap=null;material.displacementMap=null;material.userData={...material.userData,authoredIndependentTexture:true,authoredPart:key};material.needsUpdate=true;materials.set(cacheKey,material);return material;}
  function apply(root){if(!enabled||!Object.keys(textures.exterior).length||!root)return false;root.traverse(object=>{if(!object.isMesh||!object.material||Array.isArray(object.material)||!hasTileSafeUv(object))return;const isCabin=object.parent?.name==="aster_original_cabin"||(()=>{let p=object.parent;while(p){if(p.name==="aster_original_cabin")return true;p=p.parent;}return false;})();const kind=isCabin?cabinKind(object.name):exteriorKind(object.name);if(isCabin&&(kind==="screen"||kind==="glass"))return;const map=textures[isCabin?"cabin":"exterior"][kind];if(map)object.material=materialFor(object.material,map,`${isCabin?"c":"e"}:${kind}`);});return true;}
  return{enabled,ready,apply,dispose(){for(const material of materials.values())material.dispose();for(const family of Object.values(textures))for(const texture of Object.values(family))texture.dispose();materials.clear();}};
}
