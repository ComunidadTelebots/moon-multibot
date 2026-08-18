import assert from "node:assert/strict";import fs from "node:fs";import test from "node:test";
const source=fs.readFileSync(new URL("./transport-emergency-fleet.js",import.meta.url),"utf8");
test("emergency fleet uses authored materials in high quality",()=>{for(const name of["land-ambulance-exterior","land-ambulance-interior","land-fire-exterior","land-fire-compartment","land-recovery-exterior","land-recovery-flatbed","land-tyre-sidewall"])assert.match(source,new RegExp(name));assert.match(source,/qualityLevel>=2\?loadAuthored/);});
