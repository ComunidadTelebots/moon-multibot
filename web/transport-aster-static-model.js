const REPLACED_NAMES=new Set(["sculpted_cab_shell","aerodynamic_roof_cap","sloped_front_brow","cab_corner_fairing","cab_door_skin","rear_cab_equipment_panel"]);
export function createAsterStaticModelLoader({THREE:T,qualityLevel=2,url="./models/aster-viento-high.json",fetchImpl=fetch}={}){
  let disposed=false,active=null;
  async function apply(exterior){
    if(qualityLevel<2||!exterior||disposed)return false;
    const response=await fetchImpl(url);if(!response.ok)throw new Error(`Aster static model HTTP ${response.status}`);const data=await response.json();
    if(!Array.isArray(data.components)||data.version!==1)throw new Error("Aster static model invalido");
    const paint=exterior.getObjectByName("sculpted_cab_shell")?.material;if(!paint)throw new Error("Material exterior Aster no disponible");
    const group=new T.Group();group.name="aster_viento_static_high_body";group.userData.source=data.source;
    for(const item of data.components){const geometry=new T.BufferGeometry();geometry.setAttribute("position",new T.Float32BufferAttribute(item.positions,3));geometry.setAttribute("uv",new T.Float32BufferAttribute(item.uvs,2));geometry.setIndex(item.indices);geometry.computeVertexNormals();const mesh=new T.Mesh(geometry,paint);mesh.name=item.name;mesh.castShadow=mesh.receiveShadow=true;group.add(mesh);}
    exterior.traverse(object=>{if(REPLACED_NAMES.has(object.name)){object.userData.staticModelHidden=object.visible;object.visible=false;}});
    exterior.add(group);active=group;return true;
  }
  function dispose(){disposed=true;if(active){active.traverse(object=>object.geometry?.dispose?.());active.removeFromParent();active=null;}}
  return{apply,dispose,get active(){return active;}};
}
