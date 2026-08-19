import assert from "node:assert/strict";import test from "node:test";import{releaseProfile,stableEditionUrl}from"./transport-release-profile.js";
test("estable apunta a la primera edición real",()=>{assert.equal(releaseProfile("stable").build,"5f4a52e");assert.match(stableEditionUrl(),/transport-stable\.html/)});
test("cada canal amplía el alcance",()=>{assert.ok(releaseProfile("alpha").features.length>=releaseProfile("rc").features.length);assert.match(releaseProfile("beta").label,/Carrera europea/)});
