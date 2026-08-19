import assert from"node:assert/strict";import test from"node:test";import{worldTileId,worldPolygonProfile,buildWorldPolygonPlan}from"./transport-world-polygon-mesh.js";
test("global tile ids cover both hemispheres",()=>assert.notEqual(worldTileId(-3.7,40.4),worldTileId(151.2,-33.8)));
test("legacy uses fewer polygons than ultra",()=>assert.ok(worldPolygonProfile("LEGACY").sampleStep>worldPolygonProfile("ULTRA").sampleStep));
test("routes split into streamable tiles",()=>{const geo=Array.from({length:30},(_,i)=>[-3+i*.03,40+i*.01]),world=geo.map((_,i)=>({x:i*15,y:0,z:-i*90})),tiles=buildWorldPolygonPlan(geo,world,"ULTRA");assert.ok(tiles.length>1);assert.equal(tiles.reduce((n,t)=>n+t.segments.length,0),29);});
