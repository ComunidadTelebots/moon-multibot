import test from "node:test";
import assert from "node:assert/strict";
import { createVehicleJobSystem, VEHICLE_JOBS } from "./transport-vehicle-jobs.js";
import { createTransportEventLog } from "./transport-event-log.js";

const memoryStorage = () => { const values=new Map(); return {getItem:key=>values.get(key)??null,setItem:(key,value)=>values.set(key,value)}; };
const career = () => ({ money:0,xp:0,events:[],record(value){this.money+=value},addXp(value){this.xp+=value},emit(type,detail){this.events.push({type,detail})} });

test("cada profesión tiene objetivos, recompensa y vehículo", () => {
  assert.deepEqual(new Set(VEHICLE_JOBS.map(job=>job.vehicle)),new Set(["bus","ambulance","fire","recovery","cargo_plane","container_ship"]));
  VEHICLE_JOBS.forEach(job=>{assert.ok(job.objectives.length>=3);assert.ok(job.reward.money>0);assert.ok(job.reward.xp>0)});
});

test("un trabajo progresa por eventos, persiste y entrega recompensa", () => {
  const storage=memoryStorage(), log=createTransportEventLog({storage}), progress=career(), selected=[];
  const jobs=createVehicleJobSystem({storage,career:progress,eventLog:log,selectVehicle:type=>selected.push(type)});
  jobs.start("recovery-motorway");
  assert.deepEqual(selected,["recovery"]);
  assert.equal(jobs.activeJob.progress.objectiveIndex,1);
  assert.equal(jobs.performAction(),true);
  assert.equal(jobs.performAction(),true);
  assert.equal(jobs.performAction(),true);
  assert.equal(jobs.activeJob,null);
  assert.equal(progress.money,2100);
  assert.equal(progress.xp,300);
  const restored=createVehicleJobSystem({storage,career:career(),eventLog:createTransportEventLog({storage})});
  assert.ok(restored.runtime.snapshot.completed.includes("recovery-motorway"));
});

test("un trabajo puede fallar y libera la selección", () => {
  const storage=memoryStorage(), progress=career(), jobs=createVehicleJobSystem({storage,career:progress,eventLog:createTransportEventLog({storage})});
  jobs.start("bus-city-line");
  jobs.fail("Fuera de servicio");
  assert.equal(jobs.activeJob,null);
  assert.equal(jobs.runtime.snapshot.missions["bus-city-line"].status,"failed");
  assert.equal(progress.events.at(-1).type,"job:failed");
});
