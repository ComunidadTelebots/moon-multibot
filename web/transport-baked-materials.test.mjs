import assert from "node:assert/strict";
import {atlasTileTransform,hasTileSafeUv} from "./transport-baked-materials.js";
assert.deepEqual(atlasTileTransform(0,0),{repeat:[.25,.25],offset:[0,.75]});
assert.deepEqual(atlasTileTransform(3,3),{repeat:[.25,.25],offset:[.75,0]});
assert.equal(hasTileSafeUv({geometry:{attributes:{uv:{array:new Float32Array([0,0,1,1,.5,.25])}}}}),true);
assert.equal(hasTileSafeUv({geometry:{attributes:{uv:{array:new Float32Array([0,0,4.2,1])}}}}),false);
console.log("transport-baked-materials: OK");
