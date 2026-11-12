import {test} from 'node:test';
import assert from 'node:assert/strict';
import {mkdtemp, readFile, writeFile, symlink, link, copyFile, rm} from 'node:fs/promises';
import {existsSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join, resolve} from 'node:path';
import {spawnSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {fileURLToPath} from 'node:url';
import {writeNewOutput} from '../ci/exclusive_output.mjs';

const root = resolve(fileURLToPath(new URL('..', import.meta.url)));
const cli = join(root, 'ci/build_cached_full.mjs');
const stock = process.env.DAP_NEO_STOCK || join(root, 'DP3_V137.img');
const opus = process.env.DAP_NEO_OPUS_DATA;
const run = (...args) => spawnSync(process.execPath, [cli, ...args], {encoding: 'utf8'});
const sha = data => createHash('sha256').update(data).digest('hex');

test('exclusive output preserves existing files and links without optional inputs', async t => {
  const dir = await mkdtemp(join(tmpdir(), 'ce-cached-exclusive-'));
  t.after(() => rm(dir, {recursive: true, force: true}));
  const input = join(dir, 'stock.img');
  const symbolicLink = join(dir, 'symbolic.img');
  const hardlink = join(dir, 'hardlink.img');
  const dangling = join(dir, 'dangling.img');
  await writeFile(input, 'original');
  await symlink(input, symbolicLink);
  await link(input, hardlink);
  await symlink(join(dir, 'missing.img'), dangling);
  for (const output of [input, symbolicLink, hardlink, dangling])
    await assert.rejects(writeNewOutput(output, Buffer.from('replacement')), {code: 'EEXIST'});
  assert.equal(await readFile(input, 'utf8'), 'original');
  const fresh = join(dir, 'new.img');
  await writeNewOutput(fresh, Buffer.from('new'));
  assert.equal(await readFile(fresh, 'utf8'), 'new');
});

test('rejects unpinned stock without creating output', async t => {
  const dir = await mkdtemp(join(tmpdir(), 'ce-cached-reject-'));
  t.after(() => rm(dir, {recursive: true, force: true}));
  const bad = join(dir, 'bad.img'), ranges = join(dir, 'opus.json'), out = join(dir, 'output.img');
  await writeFile(bad, 'not a stock image');
  await writeFile(ranges, '{"ranges":[]}');
  const result = run(bad, ranges, out);
  assert.notEqual(result.status, 0);
  assert.match(result.stderr, /does not match pinned stock/);
  assert.equal(existsSync(out), false);
  assert.equal((await readFile(bad, 'utf8')), 'not a stock image');
});

test('reproduces the pin and refuses existing output and aliases',
  {skip: !opus || !existsSync(stock) ? 'pinned stock and local Opus ranges required' : false}, async t => {
    const dir = await mkdtemp(join(tmpdir(), 'ce-cached-build-'));
    t.after(() => rm(dir, {recursive: true, force: true}));
    const out = join(dir, 'output.img');
    const sourceBefore = sha(await readFile(stock));
    const result = run(stock, opus, out);
    assert.equal(result.status, 0, result.stderr);
    const outputBefore = sha(await readFile(out));
    assert.equal(outputBefore, '66d79d648bee93d71c3adfdf229434bed57b337c6f9448d3c90d82a4a10df8bf');
    assert.notEqual(run(stock, opus, out).status, 0);
    assert.equal(sha(await readFile(out)), outputBefore);
    assert.notEqual(run(stock, opus, stock).status, 0);
    assert.equal(sha(await readFile(stock)), sourceBefore);
    const stockCopy = join(dir, 'stock-copy.img');
    await copyFile(stock, stockCopy);
    const symbolicLink = join(dir, 'input-alias.img');
    await symlink(stockCopy, symbolicLink);
    assert.notEqual(run(stockCopy, opus, symbolicLink).status, 0);
    const hardlink = join(dir, 'input-hardlink.img');
    await link(stockCopy, hardlink);
    assert.notEqual(run(stockCopy, opus, hardlink).status, 0);
    assert.equal(sha(await readFile(stockCopy)), sourceBefore);
    assert.equal(sha(await readFile(stock)), sourceBefore);
    const corruptOpus = JSON.parse(await readFile(opus, 'utf8'));
    const first = corruptOpus.ranges[0];
    first.replace = (first.replace[0] === '0' ? '1' : '0') + first.replace.slice(1);
    const corruptFile = join(dir, 'corrupt-opus.json');
    const rejectedOutput = join(dir, 'rejected.img');
    await writeFile(corruptFile, JSON.stringify(corruptOpus));
    const rejected = run(stock, corruptFile, rejectedOutput);
    assert.notEqual(rejected.status, 0);
    assert.match(rejected.stderr, /module hash mismatch/);
    assert.equal(existsSync(rejectedOutput), false);
  });
