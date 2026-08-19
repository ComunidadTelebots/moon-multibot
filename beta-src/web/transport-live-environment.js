const CACHE_KEY = "moon.transport.live-environment.v1";
const haversine = (a, b) => { const r=6371,rad=Math.PI/180,dLat=(b.lat-a.lat)*rad,dLon=(b.lon-a.lon)*rad; const q=Math.sin(dLat/2)**2+Math.cos(a.lat*rad)*Math.cos(b.lat*rad)*Math.sin(dLon/2)**2; return 2*r*Math.asin(Math.sqrt(q)); };
const weatherKind = code => code >= 95 ? "storm" : code >= 71 && code <= 86 ? "snow" : code >= 51 && code <= 67 || code >= 80 && code <= 82 ? "rain" : code === 45 || code === 48 ? "fog" : "clear";
export function createLiveEnvironment({ fetchImpl = fetch, maxFireDistanceKm = 180 } = {}) {
  let location = { lat: 40.4168, lon: -3.7038 }, state = { enabled:false, source:"simulated", weather:"clear", temperature:null, windSpeed:5, windDirection:0, precipitation:0, wildfire:null, updatedAt:0, error:"" };
  function setLocation(value={}) { if(Number.isFinite(Number(value.lat))&&Number.isFinite(Number(value.lon))) location={lat:Number(value.lat),lon:Number(value.lon)}; return location; }
  function cached(){try{const row=JSON.parse(localStorage.getItem(CACHE_KEY)||"null");return row&&Date.now()-row.savedAt<15*60*1000&&haversine(location,row.location)<25?row.state:null}catch{return null}}
  async function load(force=false){
    const saved=!force&&cached(); if(saved){state={...saved,enabled:true,source:"cache"};return state}
    const weatherUrl=`https://api.open-meteo.com/v1/forecast?latitude=${location.lat}&longitude=${location.lon}&current=temperature_2m,precipitation,rain,showers,snowfall,weather_code,wind_speed_10m,wind_direction_10m,wind_gusts_10m&timezone=auto`;
    try{
      const [weatherResult,fireResult]=await Promise.allSettled([fetchImpl(weatherUrl).then(r=>{if(!r.ok)throw new Error(`weather ${r.status}`);return r.json()}),fetchImpl("https://eonet.gsfc.nasa.gov/api/v3/events/geojson?category=wildfires&status=open&days=30&limit=100").then(r=>{if(!r.ok)throw new Error(`fire ${r.status}`);return r.json()})]);
      if(weatherResult.status!=="fulfilled")throw weatherResult.reason;
      const current=weatherResult.value.current||{}, fires=fireResult.status==="fulfilled"?(fireResult.value.features||[]):[];
      const nearest=fires.map(feature=>{const coordinates=feature.geometry?.coordinates||[];const point={lon:Number(coordinates[0]),lat:Number(coordinates[1])};return {...feature,distanceKm:haversine(location,point)}}).filter(row=>Number.isFinite(row.distanceKm)).sort((a,b)=>a.distanceKm-b.distanceKm)[0];
      state={enabled:true,source:"live",weather:weatherKind(Number(current.weather_code||0)),temperature:Number(current.temperature_2m),windSpeed:Number(current.wind_speed_10m||0),windDirection:Number(current.wind_direction_10m||0),windGusts:Number(current.wind_gusts_10m||0),precipitation:Number(current.precipitation||0),wildfire:nearest&&nearest.distanceKm<=maxFireDistanceKm?{id:nearest.id,title:nearest.properties?.title||"Incendio activo",distanceKm:nearest.distanceKm}:null,updatedAt:Date.now(),error:""};
      localStorage.setItem(CACHE_KEY,JSON.stringify({savedAt:Date.now(),location,state}));return state;
    }catch(error){state={...state,enabled:true,source:"fallback",error:String(error?.message||error)};return state}
  }
  function disable(){state={...state,enabled:false,source:"simulated"};return state}
  return {setLocation,load,disable,get state(){return state},get location(){return location}};
}
