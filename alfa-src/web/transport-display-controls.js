const STORAGE_KEY="moon_transport_display_v1";
export const DISPLAY_RESOLUTIONS=Object.freeze([
  {id:"auto",label:"Automática",height:0},
  {id:"720",label:"HD · 720p",height:720},
  {id:"900",label:"HD+ · 900p",height:900},
  {id:"1080",label:"Full HD · 1080p",height:1080},
  {id:"1440",label:"QHD · 1440p",height:1440},
  {id:"2160",label:"4K · 2160p",height:2160},
]);
export function normalizeDisplayResolution(value){const id=String(value||"auto");return DISPLAY_RESOLUTIONS.some(item=>item.id===id)?id:"auto"}
export function createDisplayControls({trigger,fullscreenRoot=document.documentElement,storage=globalThis.localStorage,onResolution=()=>{}}={}){
  let saved="auto";try{saved=normalizeDisplayResolution(JSON.parse(storage?.getItem(STORAGE_KEY)||"{}").resolution)}catch{}
  const style=document.createElement("style");style.textContent=`.transport-display-panel{position:fixed;z-index:70;right:12px;bottom:76px;width:min(340px,calc(100vw - 24px));padding:16px;border:1px solid #3edfc9;border-radius:18px;background:linear-gradient(145deg,#07141ef8,#0d2834f7);color:#effcfd;box-shadow:0 24px 70px #000d}.transport-display-panel[hidden]{display:none}.transport-display-panel header{display:flex;align-items:center;justify-content:space-between;gap:12px}.transport-display-panel h2{margin:0;font-size:18px}.transport-display-panel small{color:#6fe8d7}.transport-display-panel label{display:grid;gap:6px;margin:15px 0;color:#9db6c0}.transport-display-panel select,.transport-display-panel button{min-height:42px;padding:9px 11px;border:1px solid #315868;border-radius:10px;background:#102936;color:#fff}.transport-display-actions{display:grid;grid-template-columns:1fr 1fr;gap:8px}.transport-display-actions [data-fullscreen]{border-color:#ff9d32;background:#b94f2e;font-weight:800}@media(max-width:600px){.transport-display-panel{right:6px;bottom:70px;width:calc(100vw - 12px);box-sizing:border-box}}`;document.head.append(style);
  const panel=document.createElement("section");panel.className="transport-display-panel";panel.hidden=true;panel.setAttribute("role","dialog");panel.setAttribute("aria-modal","true");panel.setAttribute("aria-label","Pantalla y resolución");panel.innerHTML=`<header><div><small>TODO SOBRE ALLTECH STUDIOS</small><h2>Pantalla y resolución</h2></div><button data-close aria-label="Cerrar">×</button></header><label>Resolución interna<select data-resolution>${DISPLAY_RESOLUTIONS.map(item=>`<option value="${item.id}"${item.id===saved?" selected":""}>${item.label}</option>`).join("")}</select></label><p data-detail></p><div class="transport-display-actions"><button data-fullscreen>Pantalla completa</button><button data-apply>Aplicar resolución</button></div>`;document.body.append(panel);
  const select=panel.querySelector("[data-resolution]"),detail=panel.querySelector("[data-detail]"),fullscreenButton=panel.querySelector("[data-fullscreen]");
  const describe=()=>{const item=DISPLAY_RESOLUTIONS.find(entry=>entry.id===select.value)||DISPLAY_RESOLUTIONS[0];detail.textContent=item.height?`Render máximo ${item.height}p · la interfaz conserva su tamaño`:`El juego ajusta la resolución para mantener los FPS objetivo`};
  const persist=()=>{try{storage?.setItem(STORAGE_KEY,JSON.stringify({resolution:select.value}))}catch{}};
  const syncFullscreen=()=>{fullscreenButton.textContent=document.fullscreenElement?"Salir de pantalla completa":"Pantalla completa"};
  const open=()=>{panel.hidden=false;describe();syncFullscreen();select.focus()};const close=()=>{panel.hidden=true;trigger?.focus?.()};
  trigger?.addEventListener("click",open);panel.querySelector("[data-close]").onclick=close;select.onchange=describe;
  panel.querySelector("[data-apply]").onclick=()=>{persist();const item=DISPLAY_RESOLUTIONS.find(entry=>entry.id===select.value)||DISPLAY_RESOLUTIONS[0];onResolution(item.height);close()};
  fullscreenButton.onclick=async()=>{try{if(document.fullscreenElement)await document.exitFullscreen();else await fullscreenRoot.requestFullscreen();syncFullscreen()}catch(error){detail.textContent=`No se pudo cambiar la pantalla: ${error.message}`}};
  document.addEventListener("fullscreenchange",syncFullscreen);panel.addEventListener("keydown",event=>{if(event.key==="Escape")close()});
  describe();onResolution((DISPLAY_RESOLUTIONS.find(entry=>entry.id===saved)||DISPLAY_RESOLUTIONS[0]).height);
  return{element:panel,open,close,get resolution(){return select.value},dispose(){document.removeEventListener("fullscreenchange",syncFullscreen);style.remove();panel.remove()}};
}
