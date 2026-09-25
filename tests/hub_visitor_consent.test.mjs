import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
const html = fs.readFileSync(new URL('../web/hub.html', import.meta.url), 'utf8');
const script = html.match(/<script>\s*const HUB_GA_ID[\s\S]*?<\/script>/)[0].replace(/^<script>|<\/script>$/g,'');
function run(saved, privacy={}) {
  let calls=0;
  const context={navigator:{language:'en-US',...privacy}, localStorage:{getItem:()=>JSON.stringify(saved)},
    addEventListener:()=>{}, crypto:{randomUUID:()=> 'test'}, fetch:()=>{calls++;return Promise.resolve();}, Intl};
  context.window=context;
  vm.createContext(context); vm.runInContext(script,context); vm.runInContext('hubTrackVisit(); hubTrackVisit();',context);
  return calls;
}
test('Hub first-party visits require stored explicit consent',()=>{
  assert.equal(run(null),0); assert.equal(run({analytics:false}),0); assert.equal(run({analytics:true}),1);
});
test('Hub respects DNT and GPC even after consent',()=>{
  assert.equal(run({analytics:true},{doNotTrack:'1'}),0);
  assert.equal(run({analytics:true},{globalPrivacyControl:true}),0);
});
