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
