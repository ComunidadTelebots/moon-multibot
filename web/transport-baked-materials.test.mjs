import assert from "node:assert/strict";
import {atlasTileTransform} from "./transport-baked-materials.js";
assert.deepEqual(atlasTileTransform(0,0),{repeat:[.25,.25],offset:[0,.75]});
assert.deepEqual(atlasTileTransform(3,3),{repeat:[.25,.25],offset:[.75,0]});
console.log("transport-baked-materials: OK");
