#!/usr/bin/env node
// Reproduce the existing browser-pinned binary. This does not compile source.
import {readFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {buildFirmware, hexToBytes} from '../docs/builder-core.mjs';
import {PATCH_GROUPS} from '../docs/builder-data.mjs';
import {VORBIS75} from '../docs/builder-vorbis.mjs';
import {OPUS_PATCHES} from '../docs/builder-opus.mjs';
import {FULL_EXTRA_PATCHES, FULL_TAIL, FULL_GROWTHS, FULL_THEME_RUNS, FULL_IMAGE_SHA256} from '../docs/builder-full.mjs';
import {writeNewOutput} from './exclusive_output.mjs';

const args = process.argv.slice(2);
if (args.length !== 3) {
  console.error('Usage: node ci/build_cached_full.mjs STOCK.img OPUS-RANGES.json NEW-OUTPUT.img');
  process.exit(2);
}
const [stockPath, opusPath, outputPath] = args;
console.error('Reproducing a cached experimental image with known unresolved feature defects. Do not treat its hash as evidence of safe device operation.');
const sha256 = async bytes => createHash('sha256').update(bytes).digest('hex');
const stock = new Uint8Array(await readFile(stockPath));
const opus = JSON.parse(await readFile(opusPath, 'utf8'));
const tail = hexToBytes(FULL_TAIL.hex);
if (tail.length !== FULL_TAIL.length || await sha256(tail) !== FULL_TAIL.sha256)
  throw new Error('cached tail payload failed its pin');
const growths = [];
for (const growth of FULL_GROWTHS) {
  const payload = hexToBytes(growth.hex);
  if (payload.length !== growth.length || await sha256(payload) !== growth.sha256)
    throw new Error(`cached module ${growth.module} payload failed its pin`);
  growths.push({module: growth.module, payload});
}
const result = await buildFirmware(stock, {
  groups: new Set(PATCH_GROUPS.map(group => group.id)),
  patchGroups: PATCH_GROUPS,
  vorbis: VORBIS75,
  opus,
  opusPatches: OPUS_PATCHES,
  themeConfig: {version: 1, runs: FULL_THEME_RUNS},
  tailPayload: tail,
  extraPatches: FULL_EXTRA_PATCHES,
  growths,
}, sha256);
if (result.sha256 !== FULL_IMAGE_SHA256)
  throw new Error(`combined image does not match its pin: ${result.sha256}`);
await writeNewOutput(outputPath, result.bytes);
console.log(`Reproduced cached combined image: ${result.sha256}`);
console.log('This does not rebuild the firmware patches from source or validate the image on hardware.');
