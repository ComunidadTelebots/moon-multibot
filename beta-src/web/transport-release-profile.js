export const RELEASE_PROFILES={
 stable:{label:"Estable · Primera edición",build:"5f4a52e",features:["Camión y autobús","Tres cámaras","Conducción básica","Cuatro ciudades"]},
 rc:{label:"RC · Simulación terrestre",features:["Camión detallado","Cabina y nueve cámaras","Físicas avanzadas","Interfaz Canva","Gráficos escalables"]},
 beta:{label:"Beta · Carrera europea",features:["Todo RC","Rutas OSM","Empresa y contratos","Carga y trabajos","Servicios y emergencias"]},
 alpha:{label:"Alfa · Mundo conectado",features:["Todo Beta","Multijugador y convoy","Campañas narrativas","Eventos regionales","Aire, mar y logística mundial"]}
};
const BETA_ONLY=["contractButton","cargoMonitorButton","academyButton","europeMapButton","eventsButton"];
const ALPHA_ONLY=["convoyButton","worldMapButton","worldPlanButton","fleetVehicle","fleetLivery"];
let gateStyle;
export function releaseProfile(channel="stable"){return RELEASE_PROFILES[channel]||RELEASE_PROFILES.stable}
export function applyReleaseProfile(channel,root=document){
 const active=RELEASE_PROFILES[channel]?channel:"stable",rank={stable:0,rc:1,beta:2,alpha:3}[active];
 if(!gateStyle&&root.head){gateStyle=root.createElement("style");gateStyle.textContent=`body[data-release-profile="rc"] :is(#contractButton,#cargoMonitorButton,#academyButton,#europeMapButton,#eventsButton,#convoyButton,#worldMapButton,#worldPlanButton,#fleetVehicle,#fleetLivery),body[data-release-profile="beta"] :is(#convoyButton,#worldMapButton,#worldPlanButton,#fleetVehicle,#fleetLivery){display:none!important}`;root.head.append(gateStyle)}
 for(const id of BETA_ONLY){const node=root.getElementById?.(id);if(node)node.hidden=rank<2}
 for(const id of ALPHA_ONLY){const node=root.getElementById?.(id);if(node)node.hidden=rank<3}
 root.body?.setAttribute("data-release-profile",active);
 globalThis.dispatchEvent?.(new CustomEvent("moon:release-profile",{detail:{channel:active,profile:releaseProfile(active)}}));
 return releaseProfile(active);
}
export function stableEditionUrl(){return "./transport-stable.html?release=stable"}
