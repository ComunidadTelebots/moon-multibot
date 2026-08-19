import assert from "node:assert/strict";
import { evaluateRegionalEvent, createRegionalEventDirector } from "./transport-regional-events.js";

const alpine=evaluateRegionalEvent({region:"western_europe",date:new Date("2026-01-12T09:00:00Z"),elevation:1400,temperature:-4,weather:"snow"});
assert.equal(alpine.id,"alpine-snow-closure"); assert.equal(alpine.effects.roadClosure,true); assert.ok(alpine.effects.gripMultiplier<1);
const monsoon=evaluateRegionalEvent({region:"southeast_asia",date:new Date("2026-08-11T12:00:00Z"),precipitation:12,weather:"rain"});
assert.equal(monsoon.id,"tropical-monsoon"); assert.ok(monsoon.effects.waterDepth>0);
const desert=evaluateRegionalEvent({region:"north_africa_middle_east",date:new Date("2026-07-11T12:00:00Z"),temperature:42,windSpeed:28});
assert.equal(desert.id,"desert-sandstorm");
const quiet=evaluateRegionalEvent({region:"mediterranean",date:new Date("2026-02-11T12:00:00Z"),temperature:15}); assert.equal(quiet.id,null);
const records=[],director=createRegionalEventDirector({eventLog:{record:(...args)=>records.push(args)}});
director.update({region:"mediterranean",date:new Date("2026-08-11T12:00:00Z"),temperature:36});
director.update({region:"mediterranean",date:new Date("2026-08-11T12:01:00Z"),temperature:36});
assert.equal(records.filter(row=>row[1]==="regional-event:started").length,1,"no debe duplicar logs durante el mismo evento");
console.log("transport-regional-events: OK");
