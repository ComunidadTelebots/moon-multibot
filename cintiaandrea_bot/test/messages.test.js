import test from 'node:test';
import assert from 'node:assert/strict';

import { commandFromText, helpText, startText } from '../tgcloud/lib/messages.js';

test('extracts commands with and without bot username', () => {
  assert.equal(commandFromText('/start'), 'start');
  assert.equal(commandFromText('/stats@AndreaBot ahora'), 'stats');
  assert.equal(commandFromText('hola'), null);
});

test('renders useful bot copy', () => {
  assert.match(startText('Andrea'), /Hola, Andrea/);
  assert.match(helpText(), /\/stats/);
});
