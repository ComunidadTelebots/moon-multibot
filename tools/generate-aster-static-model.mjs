import fs from "node:fs";
import path from "node:path";

const components=[];
function grid(name,material,columns,rows,point){
  const positions=[],uvs=[],indices=[];
  for(let y=0;y<=rows;y++)for(let x=0;x<=columns;x++){const u=x/columns,v=y/rows,p=point(u,v);positions.push(...p);uvs.push(u,v);}
  for(let y=0;y<rows;y++)for(let x=0;x<columns;x++){const a=y*(columns+1)+x,b=a+1,c=a+columns+1,d=c+1;indices.push(a,c,b,b,c,d);}
  components.push({name,material,positions:positions.map(n=>+n.toFixed(4)),uvs:uvs.map(n=>+n.toFixed(4)),indices});
}
// Curved roof and front crown, shaped directly from the Aster Viento Canva views.
grid("aster_static_roof","paint",18,12,(u,v)=>{const x=(u-.5)*4.5,z=-6.2+v*4.55,y=4.53+.34*Math.cos((u-.5)*Math.PI)-.08*v;return[x,y,z];});
grid("aster_static_front_lower","paint",18,8,(u,v)=>{const x=(u-.5)*4.62,y=.78+v*1.78,z=-6.82-.17*Math.cos((u-.5)*Math.PI)+.08*v;return[x,y,z];});
for(const side of[-1,1]){
  grid(`aster_static_lower_side_${side<0?"left":"right"}`,"paint",14,7,(u,v)=>{const z=-6.25+u*4.4,y=.82+v*1.48,x=side*(2.38-.12*Math.sin(u*Math.PI)-.04*Math.sin(v*Math.PI));return[x,y,z];});
  grid(`aster_static_rear_side_${side<0?"left":"right"}`,"paint",8,8,(u,v)=>{const z=-3.68+u*1.83,y=2.28+v*2.05,x=side*(2.32-.06*Math.sin(u*Math.PI)-.06*Math.sin(v*Math.PI));return[x,y,z];});
  grid(`aster_static_pillar_${side<0?"left":"right"}`,"paint",6,12,(u,v)=>{const x=side*(2.13+u*.3),y=2.55+v*1.92,z=-6.62+u*.26+.07*Math.sin(v*Math.PI);return[x,y,z];});
}
grid("aster_static_rear","paint",16,12,(u,v)=>{const x=(u-.5)*4.42,y=.82+v*3.7,z=-1.78+.08*Math.cos((u-.5)*Math.PI);return[x,y,z];});
const output=path.resolve("web/models/aster-viento-high.json");fs.mkdirSync(path.dirname(output),{recursive:true});fs.writeFileSync(output,JSON.stringify({version:1,source:"TodoSobreAllTech Studios Canva pages 74-75",components}));
console.log(output,components.length,components.reduce((sum,row)=>sum+row.indices.length/3,0),"triangles");
