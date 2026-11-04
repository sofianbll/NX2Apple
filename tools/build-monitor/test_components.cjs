const {test} = require('node:test');
const assert = require('node:assert/strict');
const {readFileSync} = require('node:fs');
const {join} = require('node:path');

const source = readFileSync(join(__dirname, 'nx-components.js'), 'utf8');
const load = () => import(`data:text/javascript;base64,${Buffer.from(source).toString('base64')}`);

test('legacy build counter keeps its done/total percentage', async () => {
  const {formatBuildProgress} = await load();
  const progress = formatBuildProgress('1670', 29651);
  assert.equal(progress.percent, 5);
  assert.equal(progress.count, `${(1670).toLocaleString('fr-FR')} / ${(29651).toLocaleString('fr-FR')}`);
  assert.equal(formatBuildProgress(99, 100).percent, 99);
  assert.equal(formatBuildProgress(5, 0).percent, 0);
});

test('stage progress is a floored percent for a valid 0..1 fraction', async () => {
  const {formatStageProgress} = await load();
  assert.equal(formatStageProgress(0), 0);
  assert.equal(formatStageProgress('0.425'), 42);
  assert.equal(formatStageProgress(0.29), 29);
  assert.equal(formatStageProgress(0.999), 99);
  assert.equal(formatStageProgress(1 - Number.EPSILON), 99);
  assert.equal(formatStageProgress(1), 100);
});

test('stage progress is null when unknown or invalid', async () => {
  const {formatStageProgress} = await load();
  // '50' = percent-scale value, rejected as out of the 0..1 range.
  for (const value of ['', '  ', null, undefined, 'abc', NaN, Infinity, -0.1, 1.01, '50']) {
    assert.equal(formatStageProgress(value), null, String(value));
  }
});

test('standard pad mapping: d-pad, left stick past the dead zone, bottom/right face buttons', async () => {
  const {padState} = await load();
  const pad = (pressed = [], axes = [0, 0]) => ({mapping: 'standard', buttons: Array.from({length: 17}, (_, i) => ({pressed: pressed.includes(i)})), axes});
  assert.deepEqual([...padState(pad([0, 1, 12, 13, 14, 15]))].sort(), ['back', 'confirm', 'down', 'left', 'right', 'up']);
  assert.deepEqual([...padState(pad([], [0.8, -0.9]))].sort(), ['right', 'up']);
  assert.deepEqual([...padState(pad([], [0.3, 0.4]))], []);
  assert.deepEqual([...padState(pad([2, 3, 7]))], [], 'X, Y and ZR do nothing');
  assert.deepEqual([...padState(null)], []);
  assert.deepEqual([...padState({...pad([0, 15], [0.9, 0.9]), mapping: ''})], [], 'unknown pad: raw buttons and motion axes ignored');
});

test('only new presses count, so a held button never repeats', async () => {
  const {padPresses} = await load();
  assert.deepEqual(padPresses(new Set(), new Set(['confirm'])), ['confirm']);
  assert.deepEqual(padPresses(new Set(['confirm']), new Set(['confirm'])), []);
  assert.deepEqual(padPresses(new Set(['right']), new Set(['right', 'back'])), ['back']);
});
