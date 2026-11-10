#!/usr/bin/env node
// Check recorded component ledgers against the browser's embedded bytes.
// This does not build source, verify overlay lifetimes, or test hardware.
import { createHash } from 'node:crypto';
import { readFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { resolve } from 'node:path';
import { FULL_TAIL, FULL_GROWTHS } from '../docs/builder-full.mjs';

const root = fileURLToPath(new URL('../', import.meta.url));
const hash = bytes => createHash('sha256').update(bytes).digest('hex');
const fail = message => { throw new Error(message); };

function decode(payload, label) {
  if (!payload || typeof payload.hex !== 'string' ||
      payload.hex.length % 2 !== 0 || !/^[0-9a-f]*$/i.test(payload.hex))
    fail(`${label}: invalid hex`);
  const bytes = Buffer.from(payload.hex, 'hex');
  if (!Number.isSafeInteger(payload.length) || bytes.length !== payload.length)
    fail(`${label}: byte length mismatch`);
  if (typeof payload.sha256 !== 'string' || !/^[0-9a-f]{64}$/.test(payload.sha256) || hash(bytes) !== payload.sha256)
    fail(`${label}: payload hash mismatch`);
  return bytes;
}

export function checkFullArtifacts(layout, tailLayout, tailPayload, growths, growthLedger) {
  const tail = decode(tailPayload, 'tail');
  if (tail.length !== tailLayout.tail_bytes || hash(tail) !== tailLayout.tail_sha256)
    fail('tail: embedded bytes disagree with recorded layout');
  if (!Number.isSafeInteger(tailLayout.budget) || tailLayout.budget < tail.length ||
      !Array.isArray(tailLayout.pieces)) fail('tail: invalid recorded budget');
  const base = Number(tailLayout.tail_base);
  if (!Number.isSafeInteger(base) || base < 0) fail('tail: invalid recorded base');
  const spans = [];
  for (const piece of tailLayout.pieces) {
    const label = `tail piece ${piece.name}`;
    if (typeof piece.name !== 'string' || !piece.name ||
        !Number.isSafeInteger(piece.offset) || !Number.isSafeInteger(piece.bytes) ||
        piece.offset < 0 || piece.bytes <= 0 || piece.offset + piece.bytes > tailLayout.budget ||
        Number(piece.address) !== base + piece.offset) fail(`${label}: invalid extent`);
    const end = piece.offset + piece.bytes;
    spans.push([piece.offset, end, piece.name]);
    if (piece.sha256 !== undefined) {
      if (end > tail.length || !/^[0-9a-f]{64}$/.test(piece.sha256) ||
          hash(tail.subarray(piece.offset, end)) !== piece.sha256)
        fail(`${label}: piece hash mismatch`);
    } else if (piece.offset < tail.length) {
      // Unhashed emitted pieces are reserved zero-filled staging space.
      if (end > tail.length || tail.subarray(piece.offset, end).some(byte => byte !== 0))
        fail(`${label}: unhashed emitted bytes are not all zero`);
    }
  }
  spans.sort((a, b) => a[0] - b[0]);
  if (!spans.length || spans[0][0] !== 0 || spans.at(-1)[1] !== tailLayout.budget)
    fail('tail: recorded pieces do not cover the budget');
  for (let i = 1; i < spans.length; i++) {
    if (spans[i][0] < spans[i - 1][1]) fail('tail: recorded pieces overlap');
    if (spans[i][0] !== spans[i - 1][1]) fail('tail: uncovered recorded bytes');
  }
  if (!Array.isArray(growths) || !growths.length) fail('missing growth payloads');
  if (!growthLedger || growthLedger.version !== 1 || !Array.isArray(growthLedger.modules) || !growthLedger.modules.length)
    fail('growth ledger: invalid modules');
  const expected = new Map();
  for (const entry of growthLedger.modules) {
    if (!Number.isSafeInteger(entry.module) || entry.module < 0 || expected.has(entry.module) ||
        !Number.isSafeInteger(entry.length) || entry.length <= 0 ||
        typeof entry.sha256 !== 'string' || !/^[0-9a-f]{64}$/.test(entry.sha256))
      fail('growth ledger: invalid or duplicate module');
    expected.set(entry.module, entry);
  }
  const modules = new Set();
  for (const growth of growths) {
    if (!Number.isSafeInteger(growth.module) || modules.has(growth.module))
      fail('growth: invalid or duplicate module');
    modules.add(growth.module);
    const expectedEntry = expected.get(growth.module);
    if (!expectedEntry) fail(`growth: unexpected module ${growth.module}`);
    const bytes = decode(growth, `module ${growth.module}`);
    if (bytes.length !== expectedEntry.length || hash(bytes) !== expectedEntry.sha256)
      fail(`module ${growth.module}: embedded bytes disagree with growth ledger`);
    if (growth.module === 31 && (bytes.length !== layout.payload_bytes ||
        hash(bytes) !== layout.payload_sha256))
      fail('module 31: embedded bytes disagree with recorded layout');
  }
  for (const module of expected.keys()) {
    if (!modules.has(module)) fail(`growth: missing module ${module}`);
  }
  if (!modules.has(31)) fail('module 31: missing growth');
  return { tailBytes: tail.length, modules: [...modules] };
}

async function main() {
  const layout = JSON.parse(await readFile(resolve(root, 'patches/full/out/layout31.json'), 'utf8'));
  const tail = JSON.parse(await readFile(resolve(root, 'patches/full/out/layout_tail.json'), 'utf8'));
  const growthLedger = JSON.parse(await readFile(resolve(root, 'patches/full/growth-ledger.json'), 'utf8'));
  const result = checkFullArtifacts(layout, tail, FULL_TAIL, FULL_GROWTHS, growthLedger);
  console.log(`Embedded artifacts match recorded hashes: tail ${result.tailBytes} bytes; modules ${result.modules.join(', ')}.`);
  console.log('This does not verify source rebuilds, overlay lifetimes, or device behavior.');
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  main().catch(err => { console.error(err.message); process.exitCode = 1; });
}
