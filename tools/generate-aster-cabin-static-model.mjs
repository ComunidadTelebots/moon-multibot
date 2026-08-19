import fs from"node:fs";import path from"node:path";
const components=[];
function grid(name,source,columns,rows,point){const positions=[],uvs=[],indices=[];for(let y=0;y<=rows;y++)for(let x=0;x<=columns;x++){const u=x/columns,v=y/rows;positions.push(...point(u,v));uvs.push(u,v);}for(let y=0;y<rows;y++)for(let x=0;x<columns;x++){const a=y*(columns+1)+x,b=a+1,c=a+columns+1,d=c+1;indices.push(a,c,b,b,c,d);}components.push({name,source,positions:positions.map(n=>+n.toFixed(4)),uvs:uvs.map(n=>+n.toFixed(4)),indices});}
const front=-5.79;
grid("cabin_static_dashboard","dashboard_swept_shell",32,12,(u,v)=>{const x=(u-.5)*4.48,y=1.86+v*.78+.12*Math.cos((u-.5)*Math.PI),z=front-.39+v*.78+.16*Math.cos((u-.5)*Math.PI*2);return[x,y,z];});
grid("cabin_static_upper_pad","dashboard_upper_pad",32,8,(u,v)=>{const x=(u-.5)*4.58,y=2.55+.18*Math.cos((u-.5)*Math.PI)-v*.12,z=front-.38+v*1.3;return[x,y,z];});
grid("cabin_static_driver_wrap","wraparound_driver_console",20,10,(u,v)=>{const angle=(-.18+u*.95),radius=1.45+v*.48,x=-1.03+Math.sin(angle)*radius,y=1.56+v*.48+.05*Math.sin(u*Math.PI),z=front+.15+Math.cos(angle)*radius;return[x,y,z];});
grid("cabin_static_passenger_wrap","wraparound_passenger_console",20,10,(u,v)=>{const angle=(.18-u*.88),radius=1.5+v*.44,x=1.05-Math.sin(angle)*radius,y=1.55+v*.44+.04*Math.sin(u*Math.PI),z=front+.2+Math.cos(angle)*radius;return[x,y,z];});
grid("cabin_static_centre_tunnel","floor_height_centre_console",16,12,(u,v)=>{const x=(u-.5)*(1.14-.18*Math.sin(v*Math.PI)),y=.48+v*1.22+.08*Math.cos((u-.5)*Math.PI),z=front+.42+v*2.08;return[x,y,z];});
grid("cabin_static_floor","rubber_floor",24,22,(u,v)=>{const x=(u-.5)*4.25,y=.36+.035*Math.cos((u-.5)*Math.PI*2),z=front+.45+v*4.35;return[x,y,z];});
grid("cabin_static_headliner","curved_cab_headliner",28,22,(u,v)=>{const x=(u-.5)*4.35,y=4.39+.28*Math.cos((u-.5)*Math.PI)-.06*v,z=front+.25+v*4.25;return[x,y,z];});
for(const side of[-1,1])grid(`cabin_static_side_${side<0?"left":"right"}`,"contoured_sleeper_side_liner",18,18,(u,v)=>{const z=front+.15+u*4.1,y=.62+v*3.7,x=side*(2.14-.1*Math.sin(u*Math.PI)-.08*Math.sin(v*Math.PI));return[x,y,z];});
grid("cabin_static_rear_wall","sculpted_cab_rear_shell",24,18,(u,v)=>{const x=(u-.5)*4.25,y=.55+v*3.75+.22*Math.sin(v*Math.PI)*Math.cos((u-.5)*Math.PI),z=front+4.38+.11*Math.cos((u-.5)*Math.PI);return[x,y,z];});
const output=path.resolve("web/models/aster-cabin-high.json");fs.mkdirSync(path.dirname(output),{recursive:true});fs.writeFileSync(output,JSON.stringify({version:1,source:"TodoSobreAllTech Studios Canva cabin specification",components}));console.log(output,components.length,components.reduce((n,c)=>n+c.indices.length/3,0),"triangles");
