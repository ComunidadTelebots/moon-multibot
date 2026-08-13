import { EUROPE_CITIES, EUROPE_ROADS, findShortestRoute } from "./transport-europe-data.js";

export function mountEuropeRoadMap(canvas, output) {
  const ctx = canvas.getContext("2d"), state = { from: null, to: null, route: null, vehicle: null };
  const project = city => ({ x: 34 + ((city.x + 100) / 200) * (canvas.width - 68), y: 28 + ((city.z + 82) / 164) * (canvas.height - 56) });
  const cityById = id => EUROPE_CITIES.find(city => city.id === id);
  const tourIds = ["lisbon","madrid","barcelona","lyon","paris","brussels","amsterdam","hamburg","berlin","prague","vienna","budapest","zagreb","sarajevo","belgrade","sofia","athens"];
  const tourSegments = tourIds.slice(0, -1).map((from, index) => {
    const to = tourIds[index + 1], road = EUROPE_ROADS.find(item => (item.from === from && item.to === to) || (item.from === to && item.to === from));
    return road ? { from, to, distanceKm: road.distanceKm } : null;
  }).filter(Boolean);
  const tourLength = tourSegments.reduce((sum, segment) => sum + segment.distanceKm, 0);
  function locateVehicle(distanceKm = 0) {
    let remaining = ((distanceKm % tourLength) + tourLength) % tourLength;
    for (const segment of tourSegments) {
      if (remaining <= segment.distanceKm) {
        const from = cityById(segment.from), to = cityById(segment.to), progress = remaining / segment.distanceKm;
        state.vehicle = { x: from.x + (to.x - from.x) * progress, z: from.z + (to.z - from.z) * progress, from, to, progress, distanceKm };
        return state.vehicle;
      }
      remaining -= segment.distanceKm;
    }
  }
  function draw() {
    const w=canvas.width,h=canvas.height,g=ctx.createLinearGradient(0,0,0,h);g.addColorStop(0,"#102b3c");g.addColorStop(1,"#07131d");ctx.fillStyle=g;ctx.fillRect(0,0,w,h);
    ctx.fillStyle="#17352e";ctx.beginPath();ctx.moveTo(w*.08,h*.62);ctx.bezierCurveTo(w*.1,h*.2,w*.38,h*.05,w*.5,h*.16);ctx.bezierCurveTo(w*.69,h*.02,w*.94,h*.22,w*.91,h*.62);ctx.bezierCurveTo(w*.83,h*.91,w*.6,h*.94,w*.45,h*.78);ctx.bezierCurveTo(w*.24,h*.98,w*.06,h*.82,w*.08,h*.62);ctx.fill();
    const routeRoads=new Set(state.route?.roads||[]);
    for(const road of EUROPE_ROADS){const a=project(cityById(road.from)),b=project(cityById(road.to)),selected=routeRoads.has(road);ctx.beginPath();ctx.moveTo(a.x,a.y);ctx.lineTo(b.x,b.y);ctx.lineWidth=selected?5:road.roadClass==="motorway"?2.2:1.25;ctx.strokeStyle=selected?"#54f0cf":road.ferry?"#55a8d9":road.toll?"#d9a33f":"#58798b";ctx.setLineDash(road.ferry?[6,5]:[]);ctx.stroke()}ctx.setLineDash([]);
    for(const city of EUROPE_CITIES){const p=project(city),active=city.id===state.from||city.id===state.to;ctx.fillStyle=active?"#ffca52":"#e9f7ff";ctx.beginPath();ctx.arc(p.x,p.y,active?6:3.2,0,Math.PI*2);ctx.fill();if(active||canvas.width>600){ctx.font=active?"700 12px system-ui":"10px system-ui";ctx.fillStyle=active?"#ffdf84":"#b8cad4";ctx.fillText(city.name,p.x+7,p.y-5)}}
    if(state.vehicle){const p=project(state.vehicle);ctx.save();ctx.translate(p.x,p.y);ctx.fillStyle="#52f0cb";ctx.shadowColor="#52f0cb";ctx.shadowBlur=13;ctx.beginPath();ctx.moveTo(0,-11);ctx.lineTo(-8,9);ctx.lineTo(0,5);ctx.lineTo(8,9);ctx.closePath();ctx.fill();ctx.restore();ctx.shadowBlur=0;ctx.font="700 11px system-ui";ctx.fillStyle="#75f5d8";ctx.fillText("TU CAMIÓN",p.x+10,p.y+4)}
    ctx.fillStyle="#d7e6ee";ctx.font="700 13px system-ui";ctx.fillText("EUROPA · RED DE CARRETERAS",16,20);
  }
  function describe(){if(!state.from){output.textContent="Selecciona la ciudad de origen";return}if(!state.to){output.textContent=`Origen: ${cityById(state.from).name} · selecciona destino`;return}if(!state.route){output.textContent="No existe conexión disponible";return}output.textContent=`${state.route.cities.map(c=>c.name).join(" → ")} · ${state.route.distanceKm.toLocaleString("es-ES")} km`;}
  canvas.addEventListener("pointerdown",event=>{const rect=canvas.getBoundingClientRect(),x=(event.clientX-rect.left)*canvas.width/rect.width,y=(event.clientY-rect.top)*canvas.height/rect.height;const nearest=EUROPE_CITIES.map(city=>({city,d:Math.hypot(project(city).x-x,project(city).y-y)})).sort((a,b)=>a.d-b.d)[0];if(!nearest||nearest.d>24)return;if(!state.from||state.to){state.from=nearest.city.id;state.to=null;state.route=null}else if(nearest.city.id!==state.from){state.to=nearest.city.id;state.route=findShortestRoute(state.from,state.to)}describe();draw()});
  draw();describe();return { state, draw, setVehicleProgress(distanceKm){const vehicle=locateVehicle(distanceKm);if(vehicle)output.textContent=`Posición: ${vehicle.from.name} → ${vehicle.to.name} · ${Math.round(vehicle.progress*100)}% · PK ${distanceKm.toFixed(1)}`;draw();return vehicle;} };
}
