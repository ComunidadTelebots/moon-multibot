const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const source = fs.readFileSync(path.join(__dirname, '../web/script.js'), 'utf8');
const polling = source.slice(source.indexOf('let statusPending'), source.indexOf('// --- Bot Management ---'));

function setup(fetch) {
  let now = 0;
  const context = vm.createContext({ fetch, updateHeroStats() {}, authToken: 'test', document: { hidden: false, getElementById: () => null },
    window: { MOON_CONFIG: { currentTab: 'dashboard' } }, AbortSignal,
    Date: { now: () => now }, Math: { ...Math, min: Math.min, random: () => 0 }, console: { error() {} } });
  vm.runInContext(polling, context);
  return { context, load: () => context.fetchData(), advance: ms => { now += ms; } };
}
test('dashboard skips hidden/inactive tabs and never overlaps requests', async () => {
  let calls = 0, release;
  const gate = new Promise(resolve => { release = resolve; });
  const t = setup(async () => { calls++; await gate; return { ok: true, json: async () => ({ ok: true }) }; });
  t.context.document.hidden = true;
  await t.load(); assert.equal(calls, 0);
  t.context.document.hidden = false;
  t.context.window.MOON_CONFIG.currentTab = 'chat';
  await t.load(); assert.equal(calls, 0);
  t.context.window.MOON_CONFIG.currentTab = 'dashboard';
  const first = t.load();
  await t.load(); assert.equal(calls, 1);
  release(); await first;
  await t.load(); assert.equal(calls, 1);
  t.advance(2000); await t.load(); assert.equal(calls, 2);
});
test('failed responses back off and a successful response resets the delay', async () => {
  let calls = 0;
  const t = setup(async () => ({ ok: ++calls > 1, json: async () => ({ ok: true }) }));
  await t.load();
  t.advance(2000); await t.load(); assert.equal(calls, 1);
  t.advance(2000); await t.load(); assert.equal(calls, 2);
  t.advance(2000); await t.load(); assert.equal(calls, 3);
});
