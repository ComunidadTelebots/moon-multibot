export const BUSINESS_TYPES = Object.freeze([
  { id:"bakery", label:"Panadería", open:[6,14], color:0xf2b85b, routines:["desayuno","reparto"] },
  { id:"market", label:"Mercado", open:[8,20], color:0x50c9a8, routines:["compras","descarga"] },
  { id:"cafe", label:"Café", open:[7,23], color:0xd88755, routines:["desayuno","encuentro"] },
  { id:"pharmacy", label:"Farmacia", open:[9,21], color:0x58d7bd, routines:["consulta","guardia"] },
  { id:"workshop", label:"Taller", open:[8,19], color:0xf19a3e, routines:["diagnóstico","reparación"] },
  { id:"hardware", label:"Ferretería", open:[8,19], color:0x7db5dd, routines:["suministros","obra"] },
  { id:"restaurant", label:"Restaurante", open:[12,24], color:0xe66d61, routines:["comida","cena"] },
  { id:"cooperative", label:"Cooperativa", open:[7,18], color:0x8fc66c, routines:["cosecha","expedición"] },
]);

export function cityLifeFrame({ hour=12, settlement="city", day=1 }={}) {
  const h=((Number(hour)||0)%24+24)%24;
  const weekend=Number(day)===0||Number(day)===6;
  const phase=h<6?"night":h<9?"morning":h<14?"midday":h<18?"afternoon":h<22?"evening":"night";
  const density={night:.12,morning:.72,midday:.86,afternoon:.68,evening:.9}[phase]*(settlement==="village"?.62:1)*(weekend?1.08:1);
  const routine=phase==="morning"?(settlement==="village"?"mercado y labores":"colegio y trabajo")
    :phase==="midday"?"compras y comida":phase==="afternoon"?(settlement==="village"?"campo y talleres":"servicios y reparto")
    :phase==="evening"?"paseo, comercio y hostelería":"descanso y servicios nocturnos";
  return {hour:h,phase,density:Math.min(1,density),routine,weekend};
}

export function isBusinessOpen(type,hour=12) {
  const business=typeof type==="string"?BUSINESS_TYPES.find(row=>row.id===type):type;
  if(!business)return false;
  const [start,end]=business.open,h=((Number(hour)||0)%24+24)%24;
  return end===24?h>=start:h>=start&&h<end;
}

export function createCityLife({THREE:T,scene,qualityLevel=2}={}) {
  if(!T||!scene)throw new Error("THREE y scene son obligatorios");
  const root=new T.Group();root.name="city_life_businesses";scene.add(root);
  const signGeometry=new T.BoxGeometry(3.8,1.05,.16),postGeometry=new T.BoxGeometry(.12,2.4,.12);
  const dark=new T.MeshStandardMaterial({color:0x14252d,roughness:.72,metalness:.12});
  const signs=[];
  const count=[4,8,12,16][qualityLevel]||8;
  for(let i=0;i<count;i++){
    const business=BUSINESS_TYPES[i%BUSINESS_TYPES.length],side=i%2?1:-1;
    const material=new T.MeshStandardMaterial({color:business.color,emissive:business.color,emissiveIntensity:.08,roughness:.48});
    const group=new T.Group();group.name=`business_${business.id}_${i}`;
    const sign=new T.Mesh(signGeometry,material);sign.position.y=3.15;sign.name=`${business.id}_sign`;
    const post=new T.Mesh(postGeometry,dark);post.position.y=1.2;
    group.add(sign,post);group.position.set(side*(22+(i%3)*5),0,-65-i*48);group.rotation.y=side>0?-Math.PI/2:Math.PI/2;
    group.userData={business,index:i,material,open:false};root.add(group);signs.push(group);
  }
  let lastHour=-1;
  return {root,signs,update({vehicle,hour=new Date().getHours(),day=new Date().getDay(),settlement="city",ambientRoot}={}){
    const frame=cityLifeFrame({hour,day,settlement});
    if(vehicle)for(const group of signs){if(group.position.z>vehicle.position.z+120)group.position.z-=count*48;else if(group.position.z<vehicle.position.z-count*52)group.position.z+=count*48;}
    if(frame.hour!==lastHour){lastHour=frame.hour;for(const group of signs){const open=isBusinessOpen(group.userData.business,frame.hour);group.userData.open=open;group.userData.material.emissiveIntensity=open&&frame.phase!=="midday"?.72:.08;group.scale.y=open?1:.86;}}
    if(ambientRoot)for(const actor of ambientRoot.children){if(!actor.userData?.pedestrian)continue;actor.userData.dailyRoutine=frame.routine;actor.userData.activityMultiplier=.55+frame.density*.75;actor.visible=actor.visible&&((actor.userData.index%10)/10<Math.max(.2,frame.density));}
    return frame;
  },dispose(){scene.remove(root);signGeometry.dispose();postGeometry.dispose();dark.dispose();for(const group of signs)group.userData.material.dispose();}};
}
