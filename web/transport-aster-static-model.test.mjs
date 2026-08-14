import assert from "node:assert/strict";
import fs from "node:fs";
const model=JSON.parse(fs.readFileSync(new URL("./models/aster-viento-high.json",import.meta.url),"utf8"));
assert.equal(model.version,1);assert.equal(model.components.length,9);
for(const component of model.components){assert.equal(component.positions.length%3,0);assert.equal(component.uvs.length/2,component.positions.length/3);assert.equal(component.indices.length%3,0);}
assert.ok(model.components.reduce((sum,row)=>sum+row.indices.length/3,0)>1900);
console.log("transport-aster-static-model: OK");
