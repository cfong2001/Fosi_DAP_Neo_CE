import { test } from 'node:test';
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFile } from 'node:fs/promises';
import { checkFullArtifacts } from '../tools/check_full_artifacts.mjs';
import { FULL_TAIL, FULL_GROWTHS } from '../docs/builder-full.mjs';

const layout = JSON.parse(await readFile(new URL('../patches/full/out/layout31.json', import.meta.url)));
const recordedTail = JSON.parse(await readFile(new URL('../patches/full/out/layout_tail.json', import.meta.url)));
const growthLedger = JSON.parse(await readFile(new URL('../patches/full/growth-ledger.json', import.meta.url)));
const check = (layout, tail, payload, growths) => checkFullArtifacts(layout, tail, payload, growths, growthLedger);
const copy = value => structuredClone(value);
const hash = bytes => createHash('sha256').update(bytes).digest('hex');
const hashedPiece = recordedTail.pieces.find(piece => piece.sha256);
const zeroPiece = recordedTail.pieces.find(piece => !piece.sha256 && piece.offset < recordedTail.tail_bytes);

test('current embedded bytes agree with the recorded composition', () => {
  const result = check(layout, recordedTail, FULL_TAIL, FULL_GROWTHS);
  assert.equal(result.tailBytes, recordedTail.tail_bytes);
  assert.deepEqual([...result.modules].sort((a, b) => a - b),
                   growthLedger.modules.map(growth => growth.module).sort((a, b) => a - b));
});

test('rejects modified tail even when the embedded hash is also changed', () => {
  const tail = copy(FULL_TAIL);
  const altered = Buffer.from(tail.hex, 'hex');
  altered[hashedPiece.offset] ^= 1;
  tail.hex = altered.toString('hex');
  tail.sha256 = hash(altered);
  assert.throws(() => check(layout, recordedTail, tail, FULL_GROWTHS), /recorded layout/);
});

test('rejects a modified component even when both whole-tail hashes are changed', () => {
  const tail = copy(FULL_TAIL), ledger = copy(recordedTail);
  const altered = Buffer.from(tail.hex, 'hex');
  altered[hashedPiece.offset] ^= 1;
  tail.hex = altered.toString('hex');
  ledger.tail_sha256 = tail.sha256 = hash(altered);
  assert.throws(() => check(layout, ledger, tail, FULL_GROWTHS), /piece hash mismatch/);
});

test('rejects nonzero reserved staging even if whole-tail hashes are changed', () => {
  const tail = copy(FULL_TAIL), ledger = copy(recordedTail);
  const altered = Buffer.from(tail.hex, 'hex');
  altered[zeroPiece.offset] = 1;
  tail.hex = altered.toString('hex');
  ledger.tail_sha256 = tail.sha256 = hash(altered);
  assert.throws(() => check(layout, ledger, tail, FULL_GROWTHS), /not all zero/);
});

test('rejects growth inconsistencies, duplicate modules, and malformed hex', () => {
  const growths = copy(FULL_GROWTHS);
  const index31 = growths.findIndex(growth => growth.module === 31);
  growths[index31].length--;
  assert.throws(() => check(layout, recordedTail, FULL_TAIL, growths), /length mismatch/);
  const alteredLayout = copy(layout);
  alteredLayout.payload_sha256 = '0'.repeat(64);
  assert.throws(() => check(alteredLayout, recordedTail, FULL_TAIL, FULL_GROWTHS), /recorded layout/);
  growths[index31] = copy(FULL_GROWTHS[index31]);
  growths.push(copy(growths[index31]));
  assert.throws(() => check(layout, recordedTail, FULL_TAIL, growths), /duplicate/);
  growths.pop();
  growths[index31].hex = 'gg';
  assert.throws(() => check(layout, recordedTail, FULL_TAIL, growths), /invalid hex/);
});

test('rejects overlapping or out-of-bounds recorded tail pieces', () => {
  const bad = copy(recordedTail);
  bad.pieces[1].offset = bad.pieces[0].offset;
  bad.pieces[1].address = bad.pieces[0].address;
  delete bad.pieces[1].sha256;
  assert.throws(() => check(layout, bad, FULL_TAIL, FULL_GROWTHS), /overlap/);
  const beyond = copy(recordedTail);
  beyond.pieces[1].bytes = beyond.budget + 1;
  assert.throws(() => check(layout, beyond, FULL_TAIL, FULL_GROWTHS), /invalid extent/);
});

test('rejects missing or unexpected growth modules against the independent ledger', () => {
  const without24 = FULL_GROWTHS.filter(growth => growth.module !== 24);
  assert.throws(() => check(layout, recordedTail, FULL_TAIL, without24), /missing module 24/);
  const unexpected = [...copy(FULL_GROWTHS), {...copy(FULL_GROWTHS[0]), module: 99}];
  assert.throws(() => check(layout, recordedTail, FULL_TAIL, unexpected), /unexpected module 99/);
});

test('rejects a self-consistent replacement growth against the independent ledger', () => {
  const growths = copy(FULL_GROWTHS);
  const other = growths.find(growth => growth.module === 24);
  const bytes = Buffer.from(other.hex, 'hex');
  bytes[0] ^= 1;
  other.hex = bytes.toString('hex');
  other.sha256 = hash(bytes);
  assert.throws(() => check(layout, recordedTail, FULL_TAIL, growths), /growth ledger/);
});
