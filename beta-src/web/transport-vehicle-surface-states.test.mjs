import assert from"node:assert/strict";import test from"node:test";import{VEHICLE_STATE_TEXTURES}from"./transport-vehicle-surface-states.js";
test("static vehicle states cover motion and weather",()=>{assert.deepEqual(Object.keys(VEHICLE_STATE_TEXTURES),["tyre","motion","rain","mud","grime"]);for(const url of Object.values(VEHICLE_STATE_TEXTURES))assert.match(url,/\.png$/)});
