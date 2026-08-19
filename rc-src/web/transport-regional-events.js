import { resolveRegion } from "./transport-regional-materials.js";

const clamp = (value, min, max) => Math.max(min, Math.min(max, Number(value) || 0));
const monthIn = (month, values) => values.includes(month);
const emptyEffects = () => ({ weather:null, gripMultiplier:1, waterDepth:0, windSpeed:0, speedLimit:null, trafficMultiplier:1, roadClosure:false, wildlifeMigration:false });

export const REGIONAL_EVENT_RULES = Object.freeze([
  { id:"alpine-snow-closure", regions:["western_europe","eastern_europe","northern_europe"], months:[11,12,1,2,3], test:c=>c.elevation>=800&&(c.temperature<=2||c.weather==="snow"), label:"Nieve alpina · puerto condicionado", effects:{weather:"snow",gripMultiplier:.58,speedLimit:45,trafficMultiplier:.58,roadClosure:true} },
  { id:"nordic-black-ice", regions:["northern_europe","polar"], months:[10,11,12,1,2,3,4], test:c=>c.temperature<=1&&!c.precipitation, label:"Hielo nórdico · adherencia crítica", effects:{weather:"snow",gripMultiplier:.48,speedLimit:50,trafficMultiplier:.68} },
  { id:"tropical-monsoon", regions:["south_asia","southeast_asia"], months:[5,6,7,8,9,10], test:c=>c.precipitation>=2||["rain","storm","thunderstorm"].includes(c.weather), label:"Monzón · balsas de agua", effects:{weather:"storm",gripMultiplier:.62,waterDepth:.028,windSpeed:30,speedLimit:45,trafficMultiplier:.54} },
  { id:"desert-sandstorm", regions:["north_africa_middle_east","sub_saharan_africa"], months:[3,4,5,6,7,8,9,10], test:c=>c.windSpeed>=20||c.temperature>=37, label:"Tormenta de arena · visibilidad reducida", effects:{weather:"fog",gripMultiplier:.74,windSpeed:42,speedLimit:55,trafficMultiplier:.62} },
  { id:"mediterranean-wildfire", regions:["mediterranean"], months:[6,7,8,9], test:c=>Boolean(c.wildfire)||c.temperature>=32, label:"Incendio mediterráneo · servicios de emergencia", effects:{weather:"fog",gripMultiplier:.88,speedLimit:40,trafficMultiplier:.45,roadClosure:true} },
  { id:"coastal-cyclone", regions:["southeast_asia","oceania","east_asia","north_america","latin_america"], months:[6,7,8,9,10,11], test:c=>c.coastal&&["storm","thunderstorm"].includes(c.weather)&&c.windSpeed>=45, label:"Ciclón costero · accesos restringidos", effects:{weather:"storm",gripMultiplier:.5,waterDepth:.045,windSpeed:55,speedLimit:35,trafficMultiplier:.34,roadClosure:true} },
  { id:"regional-market", regions:Object.keys({northern_europe:1,western_europe:1,mediterranean:1,eastern_europe:1,north_america:1,latin_america:1,north_africa_middle_east:1,sub_saharan_africa:1,south_asia:1,east_asia:1,southeast_asia:1,oceania:1}), months:[1,2,3,4,5,6,7,8,9,10,11,12], test:c=>[0,6].includes(c.weekday)&&c.hour>=8&&c.hour<18&&c.day%3===0, label:"Mercado regional · corte urbano temporal", effects:{speedLimit:30,trafficMultiplier:.72,roadClosure:true} },
  { id:"wildlife-migration", regions:["northern_europe","western_europe","eastern_europe","north_america","sub_saharan_africa","oceania"], months:[3,4,5,9,10,11], test:c=>(c.hour<=7||c.hour>=18)&&c.day%2===0, label:"Migración de fauna · precaución", effects:{speedLimit:50,trafficMultiplier:.82,wildlifeMigration:true} },
]);

export function evaluateRegionalEvent(input = {}) {
  const date = input.date instanceof Date ? input.date : new Date(input.at ?? Date.now());
  const region = input.region || resolveRegion(input.coordinates || {});
  const context = {
    region, month:date.getUTCMonth()+1, day:date.getUTCDate(), weekday:date.getUTCDay(), hour:date.getUTCHours(),
    elevation:Number(input.elevation)||0, temperature:Number.isFinite(Number(input.temperature))?Number(input.temperature):18,
    precipitation:Math.max(0,Number(input.precipitation)||0), windSpeed:Math.max(0,Number(input.windSpeed)||0),
    weather:String(input.weather||"clear").toLowerCase(), wildfire:input.wildfire||null, coastal:Boolean(input.coastal),
  };
  const candidates = REGIONAL_EVENT_RULES.filter(rule=>rule.regions.includes(region)&&monthIn(context.month,rule.months)&&rule.test(context));
  const selected = input.forceEvent ? REGIONAL_EVENT_RULES.find(rule=>rule.id===input.forceEvent) : candidates[0];
  if (!selected) return { id:null, label:"Sin evento regional", region, calendar:context, effects:emptyEffects() };
  return { id:selected.id, label:selected.label, region, calendar:context, effects:{...emptyEffects(),...selected.effects}, source:input.source||"calendar" };
}

export function createRegionalEventDirector({ eventLog = null } = {}) {
  let current = evaluateRegionalEvent({ at:0 }), previousId = null;
  const update = input => {
    current = evaluateRegionalEvent(input);
    if (current.id !== previousId) {
      if (previousId) eventLog?.record?.("world","regional-event:ended",{id:previousId,region:current.region});
      if (current.id) eventLog?.record?.("world","regional-event:started",{id:current.id,label:current.label,region:current.region,effects:current.effects},{severity:current.effects.roadClosure?"warning":"info",region:current.region});
      previousId = current.id;
    }
    return current;
  };
  return { update, get state(){ return current; } };
}

export default { REGIONAL_EVENT_RULES, evaluateRegionalEvent, createRegionalEventDirector };
