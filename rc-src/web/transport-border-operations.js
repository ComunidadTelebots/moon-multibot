const RULES = Object.freeze({
  ES:{name:"España",speed:{urban:50,road:90,motorway:90},currency:"EUR",side:"derecha",toll:"Mixto",adr:"ADR europeo"},
  NL:{name:"Países Bajos",speed:{urban:50,road:80,motorway:80},currency:"EUR",side:"derecha",toll:"Selectivo",adr:"ADR europeo"},
  DE:{name:"Alemania",speed:{urban:50,road:80,motorway:80},currency:"EUR",side:"derecha",toll:"Peaje pesado",adr:"ADR europeo"},
  TR:{name:"Turquía",speed:{urban:50,road:80,motorway:90},currency:"TRY",side:"derecha",toll:"Electrónico",adr:"ADR"},
  US:{name:"Estados Unidos",speed:{urban:48,road:89,motorway:105},currency:"USD",side:"derecha",toll:"Por estado",adr:"HazMat"},
  CA:{name:"Canadá",speed:{urban:50,road:80,motorway:100},currency:"CAD",side:"derecha",toll:"Selectivo",adr:"TDG"},
  MX:{name:"México",speed:{urban:50,road:80,motorway:95},currency:"MXN",side:"derecha",toll:"Cuotas",adr:"Material peligroso"},
  BR:{name:"Brasil",speed:{urban:50,road:80,motorway:90},currency:"BRL",side:"derecha",toll:"Concesiones",adr:"ANTT"},
  AR:{name:"Argentina",speed:{urban:50,road:80,motorway:90},currency:"ARS",side:"derecha",toll:"Concesiones",adr:"Mercancía peligrosa"},
  MA:{name:"Marruecos",speed:{urban:50,road:80,motorway:90},currency:"MAD",side:"derecha",toll:"Autopistas",adr:"ADR adaptado"},
  EG:{name:"Egipto",speed:{urban:50,road:70,motorway:80},currency:"EGP",side:"derecha",toll:"Selectivo",adr:"Permiso especial"},
  AE:{name:"Emiratos Árabes Unidos",speed:{urban:60,road:80,motorway:100},currency:"AED",side:"derecha",toll:"Electrónico",adr:"Permiso emirato"},
  SG:{name:"Singapur",speed:{urban:50,road:70,motorway:80},currency:"SGD",side:"izquierda",toll:"Electrónico",adr:"Licencia HazMat"},
  CN:{name:"China",speed:{urban:50,road:70,motorway:90},currency:"CNY",side:"derecha",toll:"Extensivo",adr:"Permiso peligroso"},
  JP:{name:"Japón",speed:{urban:40,road:60,motorway:80},currency:"JPY",side:"izquierda",toll:"Extensivo",adr:"Permiso peligroso"},
  IN:{name:"India",speed:{urban:40,road:65,motorway:80},currency:"INR",side:"izquierda",toll:"FASTag",adr:"HazChem"},
  AU:{name:"Australia",speed:{urban:50,road:80,motorway:100},currency:"AUD",side:"izquierda",toll:"Por estado",adr:"Dangerous Goods"},
  NZ:{name:"Nueva Zelanda",speed:{urban:50,road:80,motorway:90},currency:"NZD",side:"izquierda",toll:"Selectivo",adr:"Dangerous Goods"},
});
const fallback=code=>({name:code||"Internacional",speed:{urban:50,road:80,motorway:90},currency:"—",side:"derecha",toll:"Según ruta",adr:"Declaración obligatoria"});
const hash=value=>[...String(value)].reduce((total,char)=>(total*31+char.charCodeAt(0))>>>0,17);

export function createBorderOperations({career,eventLog}={}){
  const style=document.createElement("style");style.textContent=`.border-card{margin-top:10px;padding:11px;border:1px solid #315966;border-radius:13px;background:#081a24}.border-head{display:flex;justify-content:space-between;gap:8px}.border-head small{color:#55e6d0;text-transform:uppercase;letter-spacing:.1em}.border-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:7px;margin-top:9px}.border-stat{padding:8px;border-radius:9px;background:#102632;color:#8fa8b2;font-size:10px}.border-stat b{display:block;margin-top:2px;color:#efffff;font-size:12px}.border-status{margin-top:9px;padding:8px;border-radius:9px;background:#13372f;color:#72f0dd;font-size:11px}.border-status.warning{background:#38270f;color:#ffd166}@media(max-width:700px){.border-grid{grid-template-columns:1fr 1fr}}`;document.head.append(style);
  let current=null;
  function inspect(leg,{cargo="Carga general",adr=false}={}){
    if(!leg)return null;const from=RULES[leg.from.countryCode]||fallback(leg.from.countryCode),to=RULES[leg.to.countryCode]||fallback(leg.to.countryCode),international=leg.from.countryCode!==leg.to.countryCode;
    const seed=hash(`${leg.from.id}:${leg.to.id}:${cargo}`),inspection=international&&seed%100<(adr?48:22),fee=international?Math.round(35+leg.distanceKm*.018+(adr?95:0)):0;
    current={leg,from,to,international,inspection,fee,cargo,adr,cleared:!international};return current;
  }
  function render(container,state=current){if(!container||!state)return;container.querySelector(".border-card")?.remove();const card=document.createElement("section");card.className="border-card";card.innerHTML=`<div class="border-head"><div><small>Aduana internacional</small><b>${state.from.name} → ${state.to.name}</b></div><b>${state.international?`${state.fee} €`:"Ruta nacional"}</b></div><div class="border-grid"><div class="border-stat">Circulación destino<b>Por la ${state.to.side}</b></div><div class="border-stat">Límite pesado<b>${state.to.speed.motorway} km/h</b></div><div class="border-stat">Peajes<b>${state.to.toll}</b></div><div class="border-stat">Carga peligrosa<b>${state.to.adr}</b></div></div><div class="border-status ${state.inspection?"warning":""}">${state.cleared?"✓ Despacho autorizado":state.inspection?"Inspección física requerida":"Documentación pendiente"}</div>`;container.append(card)}
  function clear(){if(!current)return true;if(current.cleared)return true;career?.record?.(-current.fee,`Aduana ${current.from.name} → ${current.to.name}`,{kind:"customs",cargo:current.cargo});current.cleared=true;eventLog?.record?.("operations","customs:cleared",{from:current.from.name,to:current.to.name,fee:current.fee,inspection:current.inspection,cargo:current.cargo},{severity:current.inspection?"warning":"info"});return true}
  return{inspect,render,clear,get current(){return current},rules:RULES,dispose(){style.remove()}};
}

export default createBorderOperations;
