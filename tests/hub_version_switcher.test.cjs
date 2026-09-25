const test=require('node:test'),assert=require('node:assert/strict'),vm=require('node:vm'),fs=require('node:fs'),path=require('node:path');
const code=fs.readFileSync(path.join(__dirname,'../web/hub-version-switcher.js'),'utf8');
async function run(isMaster){
 const nodes=[];let requests=0,navigation;
 function element(tag){const e={tag,children:[],append(...x){this.children.push(...x)},showModal(){this.open=true},close(){this.open=false}};nodes.push(e);return e;}
 const context={AbortSignal,window:{Telegram:{WebApp:{initData:'signed-test'}},location:{hash:'#telegram-context',assign(url){navigation=url}}},document:{currentScript:{dataset:{hubVersion:'stable-deployed'}},createElement:element,head:element('head'),body:element('body')},fetch:async()=>{requests++;return {ok:true,json:async()=>requests===1?{ok:true,is_master:isMaster}:{backendVersion:'test',versions:[{id:'stable-deployed',label:'Stable',url:'/hub.html',available:true},{id:'dev',label:'Dev',url:'/hub-releases/dev/hub.html',available:true},{id:'bad',url:'https://external.invalid',available:true}]}}}};
 vm.runInNewContext(code,context);await new Promise(r=>setImmediate(r));return {nodes,context,requests,navigation:()=>navigation};
}
test('only a server-verified master sees selector',async()=>{const r=await run(false);assert.equal(r.requests,1);assert.equal(r.context.document.body.children.length,0)});
test('shows stable identity, blocks external destinations, preserves Telegram context',async()=>{const r=await run(true);const b=r.nodes.find(n=>n.id==='moonVersionButton');assert.match(b.textContent,/Stable/);const options=r.nodes.filter(n=>n.tag==='article');assert.equal(options[0].children[2].disabled,true);assert.equal(options[2].children[2].disabled,true);options[1].children[2].onclick();assert.equal(r.navigation(),'/hub-releases/dev/hub.html#telegram-context')});
