export const RELEASE_PROFILES={
 stable:{label:"Estable \u2014 Primera edici\u00f3n",build:"5f4a52e",features:["Cami\u00f3n y autob\u00fas","Tres c\u00e1maras","Conducci\u00f3n b\u00e1sica","Cuatro ciudades"]},
 rc:{label:"RC \u2014 Simulaci\u00f3n terrestre",features:["Cami\u00f3n detallado","Cabina y nueve c\u00e1maras","F\u00edsicas avanzadas","Interfaz Canva","Gr\u00e1ficos escalables"]},
 beta:{label:"Beta \u2014 Carrera europea",features:["Todo RC","Rutas OSM","Empresa y contratos","Carga y trabajos","Servicios y emergencias"]},
 alpha:{label:"Alfa \u2014 Mundo conectado",features:["Todo Beta","Multijugador y convoy","Campa\u00f1as narrativas","Eventos regionales","Aire, mar y log\u00edstica mundial"]},
 prealpha:{label:"Pre-Alfa \u2014 Laboratorio I+D",features:["Todo Alfa","Nuevos prototipos mec\u00e1nicos","F\u00edsicas experimentales","M\u00f3dulos sin optimizar"]}
};
const BETA_ONLY=["contractButton","cargoMonitorButton","academyButton","europeMapButton","eventsButton"];
const ALPHA_ONLY=["convoyButton","worldMapButton","worldPlanButton","fleetVehicle","fleetLivery"];
const PREALPHA_ONLY=["toolButton","interactButton"]; // traspaleta y recoger
let gateStyle;
export function releaseProfile(channel="stable"){return RELEASE_PROFILES[channel]||RELEASE_PROFILES.stable}
export function applyReleaseProfile(channel,root=document){
 const active=RELEASE_PROFILES[channel]?channel:"stable",rank={stable:0,rc:1,beta:2,alpha:3,prealpha:4,prealpha:4}[active];
 if(!gateStyle&&root.head){gateStyle=root.createElement("style");gateStyle.textContent=`body[data-release-profile="rc"] :is(#contractButton,#cargoMonitorButton,#academyButton,#europeMapButton,#eventsButton,#convoyButton,#worldMapButton,#worldPlanButton,#fleetVehicle,#fleetLivery),body[data-release-profile="beta"] :is(#convoyButton,#worldMapButton,#worldPlanButton,#fleetVehicle,#fleetLivery){display:none!important}`;root.head.append(gateStyle)}
 for(const id of BETA_ONLY){const node=root.getElementById?.(id);if(node)node.hidden=rank<2}
 for(const id of ALPHA_ONLY){const node=root.getElementById?.(id);if(node)node.hidden=rank<3}
 for(const id of PREALPHA_ONLY){const node=root.getElementById?.(id);if(node)node.hidden=rank<4}
 root.body?.setAttribute("data-release-profile",active);
 globalThis.dispatchEvent?.(new CustomEvent("moon:release-profile",{detail:{channel:active,profile:releaseProfile(active)}}));
 return releaseProfile(active);
}
export function stableEditionUrl(){return "./transport-stable.html?release=stable"}


