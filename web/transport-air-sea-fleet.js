export const AIR_FLEET = [
  {id:"helicopter",name:"Altair H4",kind:"helicopter",color:0xf1ad32},
  {id:"rescue_helicopter",name:"Nerea Rescue 8",kind:"helicopter",color:0xe95b43},
  {id:"cargo_helicopter",name:"Bruma Lift 12",kind:"helicopter",color:0x4d8b78},
  {id:"glider",name:"Céfiro G2",kind:"glider",color:0xf0f4f4},
  {id:"turboprop",name:"Auralis T90",kind:"turboprop",color:0x3b8fc2},
  {id:"airliner",name:"Nortia Aster 220",kind:"airliner",color:0xe6eaeb},
  {id:"widebody",name:"Orbe Atlas 480",kind:"widebody",color:0xd8e2e5},
  {id:"cargo_plane",name:"Mercurio C70",kind:"cargo_plane",color:0xb9c5c7},
];
export const SEA_FLEET = [
  {id:"ship",name:"Marina Senda",kind:"ferry",color:0xe8eceb},
  {id:"container_ship",name:"Océano Vector",kind:"container",color:0x2c6780},
  {id:"tanker",name:"Boreal Tank 9",kind:"tanker",color:0x424b50},
  {id:"rescue_boat",name:"Nerea Guard",kind:"rescue",color:0xf1b23c},
  {id:"tugboat",name:"Puerto Firme",kind:"tug",color:0xb84b3d},
];
export const FLEET_LIVERIES=[
  {id:"cinematic",name:"Canva · Cinemática",base:"#ecf2f2",stripe:"#e38b2f",dark:"#17252b"},
  {id:"global",name:"Canva · Global",base:"#dcebed",stripe:"#23b8aa",dark:"#153747"},
  {id:"materials",name:"Canva · Materiales",base:"#c3cdd1",stripe:"#ffb13b",dark:"#202c32"},
  {id:"fleet",name:"Canva · Flota",base:"#eef4f4",stripe:"#318aaa",dark:"#13232b"},
];
function canvasTexture(T,size=256,liveryVariant=0){const l=FLEET_LIVERIES[liveryVariant%FLEET_LIVERIES.length],c=document.createElement("canvas");c.width=c.height=size;const x=c.getContext("2d"),g=x.createLinearGradient(0,0,size,size);g.addColorStop(0,l.base);g.addColorStop(.34,"#91a3aa");g.addColorStop(.56,"#f8fbfb");g.addColorStop(1,l.dark);x.fillStyle=g;x.fillRect(0,0,size,size);x.fillStyle=l.stripe;for(let y=30;y<size;y+=42)x.fillRect(0,y,size,8);x.strokeStyle="rgba(255,255,255,.42)";for(let y=12;y<size;y+=24){x.beginPath();x.moveTo(0,y);x.lineTo(size,y);x.stroke()}const t=new T.CanvasTexture(c);t.colorSpace=T.SRGBColorSpace;t.wrapS=t.wrapT=T.RepeatWrapping;t.repeat.set(2,2);return t}
export function createFleetVehicle({THREE:T,descriptor,qualityLevel=2,liveryVariant=0}){
  const root=new T.Group();root.name=`original_fleet_${descriptor.id}`;const texture=canvasTexture(T,[128,256,512,1024][qualityLevel]||256,liveryVariant),body=new T.MeshPhysicalMaterial({color:descriptor.color,map:texture,roughness:.34,metalness:.28,clearcoat:.55}),dark=new T.MeshStandardMaterial({color:0x172126,roughness:.68,metalness:.36}),glass=new T.MeshPhysicalMaterial({color:0x79b8d0,transparent:true,opacity:.42,depthWrite:false,roughness:.08,metalness:.22});const resources=[texture,body,dark,glass];const add=(g,m,p=[0,0,0],r=[0,0,0],s=[1,1,1])=>{const o=new T.Mesh(g,m);o.position.set(...p);o.rotation.set(...r);o.scale.set(...s);o.castShadow=true;root.add(o);resources.push(g);return o};
  if(descriptor.kind==="helicopter"){add(new T.SphereGeometry(1.35,qualityLevel>1?24:14,12),body,[0,.8,0],[],[1,.72,1.55]);add(new T.CylinderGeometry(.18,.38,5,10),body,[0,.8,3],[Math.PI/2,0,0]);const mainRotor=add(new T.BoxGeometry(7,.08,.3),dark,[0,2.1,0]);const tailRotor=add(new T.BoxGeometry(.1,3,.25),dark,[0,.8,5.4]);add(new T.SphereGeometry(1.05,18,10),glass,[0,.95,-1.35],[],[1,.62,.6]);root.userData.updateAircraft=({dt,speed,airborne})=>{mainRotor.rotation.y+=(airborne?18:5+speed*.08)*dt;tailRotor.rotation.z+=(airborne?24:7+speed*.1)*dt};}
  else {const wide=descriptor.kind==="widebody"?1.25:1,length=descriptor.kind==="glider"?5.5:descriptor.kind==="airliner"?8:descriptor.kind==="widebody"?10:7;add(new T.CylinderGeometry(.62*wide,.82*wide,length,qualityLevel>1?24:14),body,[0,.8,0],[Math.PI/2,0,0]);add(new T.ConeGeometry(.82*wide,2.2,18),body,[0,.8,-length/2-1.05],[-Math.PI/2,0,0]);add(new T.BoxGeometry(descriptor.kind==="glider"?13:9*wide,.13,1.4),body,[0,.8,0]);add(new T.BoxGeometry(3.3,.12,1),body,[0,1.05,length/2-1]);add(new T.BoxGeometry(.14,1.8,1.2),body,[0,1.65,length/2-.8]);if(descriptor.kind!=="glider")for(const x of[-1,1])add(new T.CylinderGeometry(.32,.4,1.7,14),dark,[x*2.2,-.05,.4],[Math.PI/2,0,0]);}
  root.userData.dispose=()=>resources.forEach(r=>r.dispose?.());return root;
}
export function createSeaVehicle({THREE:T,descriptor,qualityLevel=2,liveryVariant=0}){const root=new T.Group(),texture=canvasTexture(T,[128,256,512,1024][qualityLevel]||256,liveryVariant),hull=new T.MeshPhysicalMaterial({color:descriptor.color,map:texture,roughness:.42,metalness:.24,clearcoat:.28}),deck=new T.MeshStandardMaterial({color:0x29383e,roughness:.72}),add=(g,m,p)=>{const o=new T.Mesh(g,m);o.position.set(...p);o.castShadow=true;root.add(o);return o};root.name=`original_fleet_${descriptor.id}`;add(new T.BoxGeometry(descriptor.kind==="rescue"?3:5,1,descriptor.kind==="container"?14:10),hull,[0,.4,0]);add(new T.BoxGeometry(3.8,2.4,3),deck,[0,2,2]);if(descriptor.kind==="container")for(let z=-5;z<5;z+=2.2)for(const x of[-1.4,0,1.4])add(new T.BoxGeometry(1.2,1.1,2),new T.MeshStandardMaterial({color:[0xc74d42,0x3675a5,0xd9a538][Math.abs((z+x|0))%3]}),[x,1.45,z]);root.userData.dispose=()=>{texture.dispose();root.traverse(o=>{o.geometry?.dispose?.();o.material?.dispose?.()})};return root}
