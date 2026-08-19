export const TRANSPORT_EVENT_STORAGE_KEY = "moon.transport.events.v1";
const clone = value => {
  try { return structuredClone(value); }
  catch {
    try { return JSON.parse(JSON.stringify(value, (_key, item) => typeof item === "bigint" ? String(item) : item)); }
    catch { return {}; }
  }
};
const safe = (value, fallback = "") => String(value ?? fallback).slice(0, 240);
const normalizeDetail = value => {
  const detail = value && typeof value === "object" && !Array.isArray(value) ? clone(value) : {};
  let encoded = "";
  try { encoded = JSON.stringify(detail); } catch { return {}; }
  if (encoded.length <= 12000) return detail;
  return { truncated:true, preview:encoded.slice(0, 11900) };
};
const normalizeEvent = event => event && typeof event === "object" && Number.isFinite(Number(event.at)) ? {
  id:safe(event.id,`evt_${Number(event.at).toString(36)}`), at:Number(event.at),
  category:safe(event.category,"technical"), type:safe(event.type,"event"),
  severity:["info","warning","critical"].includes(event.severity) ? event.severity : "info",
  player:safe(event.player,"Jugador local"), company:safe(event.company,"Rutas Moon"),
  region:safe(event.region,"Europa"), detail:normalizeDetail(event.detail),
} : null;
export function createTransportEventLog(options = {}) {
  const storage = options.storage ?? globalThis.localStorage ?? null, key = options.storageKey || TRANSPORT_EVENT_STORAGE_KEY;
  const limit = Math.max(100, Number(options.limit) || 2500), listeners = new Set(); let rows = [];
  try { rows = JSON.parse(storage?.getItem(key) || "[]"); } catch { rows = []; }
  if (!Array.isArray(rows)) rows = [];
  rows = rows.map(normalizeEvent).filter(Boolean).slice(-limit);
  const save = () => { try { storage?.setItem(key, JSON.stringify(rows.slice(-limit))); } catch {} };
  const record = (category, type, detail = {}, options = {}) => {
    const safeDetail = normalizeDetail(detail);
    const event = { id:`evt_${Date.now().toString(36)}_${Math.random().toString(36).slice(2,7)}`, at:Date.now(), category:safe(category,"technical"), type:safe(type,"event"), severity:["info","warning","critical"].includes(options.severity)?options.severity:"info", player:safe(options.player||safeDetail.player||"Jugador local"), company:safe(options.company||safeDetail.company||"Rutas Moon"), region:safe(options.region||safeDetail.region||"Europa"), detail:safeDetail };
    rows.push(event); if(rows.length>limit) rows=rows.slice(-limit); save(); listeners.forEach(fn=>fn(clone(event))); return clone(event);
  };
  const query = (filters={}) => rows.filter(e=>(!filters.category||filters.category==="all"||e.category===filters.category)&&(!filters.severity||filters.severity==="all"||e.severity===filters.severity)&&(!filters.search||JSON.stringify(e).toLowerCase().includes(String(filters.search).toLowerCase()))).slice().reverse();
  const summary = () => { const today=rows.filter(e=>e.at>=Date.now()-86400000); return {total:rows.length,today:today.length,completed:today.filter(e=>e.type==="contract:completed").length,pending:today.filter(e=>/accepted|pending|created/.test(e.type)).length,critical:today.filter(e=>e.severity==="critical").length}; };
  const subscribe = fn => { listeners.add(fn); return () => listeners.delete(fn); };
  return {record,query,summary,subscribe,exportJson:()=>JSON.stringify({schema:1,exportedAt:Date.now(),events:clone(rows)},null,2),get events(){return clone(rows);}};
}
