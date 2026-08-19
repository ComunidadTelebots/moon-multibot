import assert from "node:assert/strict";
import {BUSINESS_TYPES,cityLifeFrame,isBusinessOpen} from "./transport-city-life.js";

assert.equal(BUSINESS_TYPES.length,8);
assert.equal(isBusinessOpen("bakery",7),true);
assert.equal(isBusinessOpen("bakery",18),false);
assert.equal(isBusinessOpen("restaurant",23),true);
assert.equal(cityLifeFrame({hour:8,settlement:"city",day:2}).routine,"colegio y trabajo");
assert.ok(cityLifeFrame({hour:3,settlement:"village",day:2}).density<cityLifeFrame({hour:18,settlement:"city",day:2}).density);
console.log("transport-city-life: OK");
