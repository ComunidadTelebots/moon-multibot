const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const assert = require('node:assert/strict');
for (const name of ['hub.html', 'hub-estable.html', 'hub-new.html', 'hub-clasico.html']) {
  const html = fs.readFileSync(path.join(__dirname, '../web', name), 'utf8');
  assert.equal((html.match(/<!doctype html>/gi) || []).length, 1, name + ': one document');
  let count = 0;
  for (const match of html.matchAll(/<script\b[^>]*>([\s\S]*?)<\/script\s*>/gi)) {
    new vm.Script(match[1], {filename: name + ':script-' + (++count)});
  }
  assert(count > 0);
}
const hub = fs.readFileSync(path.join(__dirname, '../web/hub.html'), 'utf8');
assert(hub.includes('let curTheme="original"'));
assert(hub.includes("frame.title = 'Diseño histórico del Hub'"));
assert(hub.includes('back.onclick = () => panel.remove()'));
assert(!hub.includes('Ã') && !hub.includes('â€') && !hub.includes('ðŸ'));
console.log('PASS: four separate HTML documents, valid inline scripts, original default, historical return and repaired encoding.');
