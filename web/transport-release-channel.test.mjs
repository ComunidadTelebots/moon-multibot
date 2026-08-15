import assert from "node:assert/strict";import test from "node:test";
import{channelIncludes,normalizeReleaseChannel,resolveReleaseChannel,RELEASE_STORAGE_KEY}from"./transport-release-channel.js";
test("normaliza canales desconocidos a estable",()=>{assert.equal(normalizeReleaseChannel("BETA"),"beta");assert.equal(normalizeReleaseChannel("nightly"),"stable")});
test("la URL prevalece sobre el canal guardado",()=>{const storage={getItem:key=>key===RELEASE_STORAGE_KEY?"stable":null};assert.equal(resolveReleaseChannel({query:"?channel=alpha",storage}),"alpha")});
test("los canales incluyen funciones según su madurez",()=>{assert.equal(channelIncludes("alpha","beta"),true);assert.equal(channelIncludes("rc","beta"),false);assert.equal(channelIncludes("stable","stable"),true)});
