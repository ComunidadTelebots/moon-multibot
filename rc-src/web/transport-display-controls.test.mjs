import test from"node:test";import assert from"node:assert/strict";import{DISPLAY_RESOLUTIONS,normalizeDisplayResolution}from"./transport-display-controls.js";
test("ofrece resoluciones desde automática hasta 4K",()=>{assert.deepEqual(DISPLAY_RESOLUTIONS.map(item=>item.height),[0,720,900,1080,1440,2160])});
test("normaliza valores de resolución no admitidos",()=>{assert.equal(normalizeDisplayResolution("1440"),"1440");assert.equal(normalizeDisplayResolution("8000"),"auto")});
