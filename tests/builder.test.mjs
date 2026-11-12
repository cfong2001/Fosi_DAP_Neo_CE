// Offline proof for the CE builder page engine (docs/builder-core.mjs).
//
// Runs the page's patch engine headlessly against the stock image and
// asserts byte equality with the Python framework's own outputs
// (patches/framework/build.py at this revision, default build date
// 20261023). The expected hashes below are build.py's outputs:
//
//   (a) framework-only build:
//         build.py --no-transplants
//         dfda863748ce422296be3200dfedf3f235c7baf815dba3993dbf579c396d8fa8
//   (b) framework-only plus the example theme:
//         build.py --no-transplants \
//           --theme-config patches/theme_editor/theme.example.json
//         dc0186d9faabf415c294a8eb442c257ae474ace30fdc2c4ee5d237333ac67dc5
//   (c) framework-only plus the CE splash mark:
//         build.py --no-transplants \
//           --theme-config patches/theme_editor/ce-mark.json
//         963b45f8acc43151e7300c17e033d0729fc54f07f9bb8232c4f9bcc962c641d0
//   (d) the default unified build (byte patches plus vorbis75):
//         build.py
//         4fa813d99d6b84d871635be490f49f3a8d4f17bcb5f7ae2540edfb62d334ad4e
//   (k) the theater variant (the default build plus the five
//       theater hook patches and the 676-byte tail payload):
//         build.py --manifest patches/theater/build/manifest.txt \
//           --tail patches/theater/build/theater_tail.bin
//         f9e324151c78fc5eba3647d60cde8ca2f56dde74de0fafa16b293451214ec2cb
//   (l) the theater variant plus the title pair (39 patches):
//         2448afaed16c053cb0d776f92d626d2c69eaee9381455ac6ac30664db2857fab
//   (p) the default unified build with the example EQ presets
//       (patches/eq_presets/example.json: a custom curve in slot 5 and
//       an AutoEQ GraphicEQ in slot 6, fitted in the browser):
//         build.py --eq-presets patches/eq_presets/example.json
//         7de2ae1b4f9bdf4eab109d7e8ee61fbf3a1e943021c753069687caf720f73704
//   (n) the default unified build with each DAC filter:
//         build.py --dac-filter fast-linear-phase
//           c6794c724cbfe9d8f00b1f7bf439f1da93c08dbbff1a13f5fdc913719543f3b7
//         build.py --dac-filter slow-low-latency
//           bc095da0c9188a022a3fab3a96af55a6a288550c8e0f91b583b55898bea29255
//         build.py --dac-filter slow-linear-phase
//           02a905f69d459250927a3b94c23f92ee1581ef29e3ff598cec0fe1f64107f361
//         build.py --dac-filter nos
//           bfd64bdd756768b87763d2cb42ccd2d0d7144d5c832d5f94693d652a35a67823
//   (o) the default unified build with each Bluetooth auto-off option,
//       and with both new options together:
//         build.py --bt-auto-off 10min
//           f8ec789695c2915d774628e5968b75bac4d5af8fa6bf3140a7eebc6dda6ca9b3
//         build.py --bt-auto-off never
//           64055539485a84426eb3e0be6b694faa1f4ae0647eb1b490658340f32e1136e5
//         build.py --bt-auto-off never --dac-filter nos
//           f6f08c220dd6b33b322df25a807e183d9af744e80122a05f234e73ceb596314c
//   (m) the everything build (patches/full/: 66 patches, both
//       transplants, two growth insertions, the merged tail and
//       the merged theme runs), with the page's embedded Opus data
//       (docs/builder-opus-data.mjs; DAP_NEO_OPUS_DATA overrides it):
//         build_full.py (one build.py pass)
//         a7c7f5c2f04279359fd577f602abece687421776f46860ed6d63a7b7f42d05d6
//   standalone lock screen (the embedded 406-byte reference-toolchain
//   routine in a module 31 extension, plus patch 0033):
//         build.py --no-transplants --manifest <framework manifest plus
//           patches/ui_features/lockscreen_build/0033-ui-lockscreen-title.patch>
//           --grow 31:code:lockscreen.bin
//         a645d045ed1ef5f5ad7cae2ded9bace8fea4d41480f18e53f7e540114c9f24f7
//
// Run:  node tests/builder.test.mjs
// The stock image defaults to the repo-root DP3_V137.img; override
// with DAP_NEO_STOCK=/path/to/DP3_V137.img.
import {readFile} from "node:fs/promises";
import {createHash} from "node:crypto";
import {buildFirmware, hexToBytes} from "../docs/builder-core.mjs";
import {PATCH_GROUPS} from "../docs/builder-data.mjs";
import {VORBIS75} from "../docs/builder-vorbis.mjs";
import {OPUS_PATCHES} from "../docs/builder-opus.mjs";
import {CE_MARK_RUNS} from "../docs/builder-cemark.mjs";
import {THEATER_PATCHES, THEATER_TAIL} from "../docs/builder-theater.mjs";
import {BT_PATCH, LOCK_PATCH, PLAYLIST_PATCHES, TITLE_PATCHES, bluetoothTail, lockscreenPayload, playlistPayloads, combineTails, theaterTail, combineWithTheater} from "../docs/builder-experimental.mjs";
import {OPUS_DATA} from "../docs/builder-opus-data.mjs";
import {BT_PAYLOAD, LOCK_PAYLOAD} from "../docs/builder-payloads.mjs";
import {FULL_EXTRA_PATCHES, FULL_TAIL, FULL_GROWTHS, FULL_THEME_RUNS, FULL_IMAGE_SHA256} from "../docs/builder-full.mjs";
import {bandTable, parseCurve, fit, slotPatches} from "../docs/eq-core.mjs";
import {DAC_FILTERS, dacFilterPatches} from "../docs/builder-dacfilter.mjs";
import {BT_AUTO_OFF, btAutoOffPatches} from "../docs/builder-btautooff.mjs";
import assert from "node:assert/strict";

const sha256Hex = async bytes =>
  createHash("sha256").update(bytes).digest("hex");

const stockUrl = process.env.DAP_NEO_STOCK
  ? new URL("file://" + process.env.DAP_NEO_STOCK)
  : new URL("../DP3_V137.img", import.meta.url);
const stock = new Uint8Array(await readFile(stockUrl));
const allGroups = new Set(PATCH_GROUPS.map(g => g.id));
const exampleTheme = JSON.parse(await readFile(
  new URL("../patches/theme_editor/theme.example.json", import.meta.url),
  "utf8"));

// Keep the browser's embedded hook preconditions synchronized with the
// source patch files even when local experimental binaries are absent.
for (const [patch, path] of [
  [BT_PATCH, "../patches/m3u/tail_build/patches/0032-ui-bt-dispatcher-hook-tail.patch"],
  [LOCK_PATCH, "../patches/ui_features/lockscreen_build/0033-ui-lockscreen-title.patch"],
  [PLAYLIST_PATCHES[0], "../patches/m3u/compose/patches/0033-ui-lockscreen-title.patch"],
  [PLAYLIST_PATCHES[1], "../patches/m3u/compose/patches/0040-m3u-browser-hook.patch"],
  [PLAYLIST_PATCHES[2], "../patches/m3u/tail_build/patches/0041-resolver-primary-hook.patch"],
  [PLAYLIST_PATCHES[3], "../patches/m3u/tail_build/patches/0042-resolver-companion-hook.patch"],
  [TITLE_PATCHES[0], "../patches/theater/text/title-copy.patch"],
  [TITLE_PATCHES[1], "../patches/theater/text/title-suffix.patch"],
  [THEATER_PATCHES[0], "../patches/theater/build/0100-theater-setup-reset-hook.patch"],
  [THEATER_PATCHES[1], "../patches/theater/build/0101-theater-blit-sync-a.patch"],
  [THEATER_PATCHES[2], "../patches/theater/build/0102-theater-blit-sync-b.patch"],
  [THEATER_PATCHES[3], "../patches/theater/build/0103-theater-blit-painter-a.patch"],
  [THEATER_PATCHES[4], "../patches/theater/build/0104-theater-blit-painter-b.patch"],
  [DAC_FILTERS[1].patch, "../patches/dac_filter/0034-dac-filter-fast-linear-phase.patch"],
  [DAC_FILTERS[2].patch, "../patches/dac_filter/0035-dac-filter-slow-low-latency.patch"],
  [DAC_FILTERS[3].patch, "../patches/dac_filter/0036-dac-filter-slow-linear-phase.patch"],
  [DAC_FILTERS[4].patch, "../patches/dac_filter/0037-dac-filter-nos.patch"],
  [BT_AUTO_OFF[1].patch, "../patches/bt_auto_off/0038-bt-auto-off-10min.patch"],
  [BT_AUTO_OFF[2].patch, "../patches/bt_auto_off/0039-bt-auto-off-never.patch"],
]) {
  const source = await readFile(new URL(path, import.meta.url), "utf8");
  const field = name => source.match(new RegExp("^" + name + ":\\s*(\\S+)", "m"))?.[1];
  assert.equal(patch.address, Number(field("address")));
  assert.equal(patch.module, Number(field("module")));
  assert.equal(patch.expect, field("expect").toLowerCase());
  assert.equal(patch.replace, field("replace").toLowerCase());
}

// The everything build's extra patches must stay synchronized
// with their source patch files (the full build's own copies where
// the merged tail or the composed payload moved a branch target).
const fullManifest = (await readFile(new URL("../patches/full/manifest.txt", import.meta.url), "utf8"))
  .split("\n").map(line => line.split("#")[0].trim()).filter(Boolean)
  .filter(entry => !entry.startsWith("../framework/patches/") && !entry.startsWith("../opus_swap/"));
assert.equal(fullManifest.length, FULL_EXTRA_PATCHES.length);
for (const [patch, path] of fullManifest.map((entry, i) =>
    [FULL_EXTRA_PATCHES[i], "../patches/full/" + entry])) {
  const source = await readFile(new URL(path, import.meta.url), "utf8");
  const field = name => source.match(new RegExp("^" + name + ":\\s*(\\S+)", "m"))?.[1];
  assert.equal(patch.address, Number(field("address")));
  assert.equal(patch.module, Number(field("module")));
  assert.equal(patch.expect, field("expect").toLowerCase());
  assert.equal(patch.replace, field("replace").toLowerCase());
}
assert.equal(FULL_EXTRA_PATCHES.length, 28);
assert.equal(FULL_TAIL.length, 2040);
assert.equal(FULL_TAIL.sha256,
  "6d77b1102cc4a82828ed8c1670eef99de708565e95d585a58dfdeb1d01047a71");
assert.deepEqual(FULL_GROWTHS.map(g => [g.module, g.length, g.sha256]), [
  [31, 6936, "010197e684a8a3e3f1a0937b61fe89a7f620b48c0872e5305f781d42d9b88f05"],
  [24, 26, "7b80afb308d276a4d0012cd4302f7a5f2a1c5192a1f2e70d3f23867e195a942a"],
]);
assert.equal(FULL_THEME_RUNS.length, 1269);
assert.equal(FULL_IMAGE_SHA256,
  "a7c7f5c2f04279359fd577f602abece687421776f46860ed6d63a7b7f42d05d6");
for (const g of FULL_GROWTHS)
  assert.equal(await sha256Hex(hexToBytes(g.hex)), g.sha256);
assert.equal(await sha256Hex(hexToBytes(FULL_TAIL.hex)), FULL_TAIL.sha256);

// The generated theater data must carry the payload pin, and the
// payload itself must pass the pin check before it can be built.
assert.equal(THEATER_TAIL.length, 676);
assert.equal(THEATER_TAIL.sha256,
  "96931a93bd197782f5efda40974ab31731c801e4231f29f44c1dfa7347c0fc78");
const theaterBytes = await theaterTail(
  hexToBytes(THEATER_TAIL.hex), sha256Hex);

const cases = [
  ["(a) toggles on, no theme, no mark",
   {groups: allGroups, patchGroups: PATCH_GROUPS},
   "dfda863748ce422296be3200dfedf3f235c7baf815dba3993dbf579c396d8fa8"],
  ["(b) toggles on plus the example theme",
   {groups: allGroups, patchGroups: PATCH_GROUPS, themeConfig: exampleTheme},
   "dc0186d9faabf415c294a8eb442c257ae474ace30fdc2c4ee5d237333ac67dc5"],
  ["(c) toggles on plus the CE splash mark",
   {groups: allGroups, patchGroups: PATCH_GROUPS, ceMarkRuns: CE_MARK_RUNS},
   "963b45f8acc43151e7300c17e033d0729fc54f07f9bb8232c4f9bcc962c641d0"],
  ["(d) toggles on plus the vorbis75 transplant (unified build)",
   {groups: allGroups, patchGroups: PATCH_GROUPS, vorbis: VORBIS75},
   "4fa813d99d6b84d871635be490f49f3a8d4f17bcb5f7ae2540edfb62d334ad4e"],
  ["(e) gapless off, other feature patches on",
   {groups: new Set([...allGroups].filter(id => id !== "gapless")), patchGroups: PATCH_GROUPS},
   "25c34dafafb155f32911bd40d386792b90ea7c37d6ffabcbfd4637b1b8a367f1"],
  ["(f) module 31 insertion, framework reference",
   {groups: allGroups, patchGroups: PATCH_GROUPS,
    module31Payload: Uint8Array.from({length: 1000}, (_, i) => i % 251)},
   "60a4bd2df3ebb2be8b6732edddee0a747211ed8f2a79ce353f90347fa193697c"],
  ["(g) paired player title repair, framework reference",
   {groups: allGroups, patchGroups: PATCH_GROUPS, extraPatches: TITLE_PATCHES},
   "70fa5ecb9ba6cc775071da2632090ebaf6415f821e692401f85897e1061f347b"],
  ["(k) theater variant: default build plus hooks and tail",
   {groups: allGroups, patchGroups: PATCH_GROUPS, vorbis: VORBIS75,
    extraPatches: THEATER_PATCHES, tailPayload: theaterBytes},
   "f9e324151c78fc5eba3647d60cde8ca2f56dde74de0fafa16b293451214ec2cb"],
  ["(l) theater plus title pair (different modules, no overlap)",
   {groups: allGroups, patchGroups: PATCH_GROUPS, vorbis: VORBIS75,
    extraPatches: [...THEATER_PATCHES, ...TITLE_PATCHES],
    tailPayload: theaterBytes},
   "2448afaed16c053cb0d776f92d626d2c69eaee9381455ac6ac30664db2857fab"],
];
{
  const example = JSON.parse(await readFile(new URL("../patches/eq_presets/example.json", import.meta.url), "utf8"));
  const R = bandTable(stock), slots = {};
  for (const [n, spec] of Object.entries(example.slots)) {
    const text = spec.text ?? await readFile(new URL("../patches/eq_presets/" + spec.file, import.meta.url), "utf8");
    slots[n] = fit(parseCurve(text), R).gains;
  }
  assert.deepEqual(slots[6], [-1,0,0,1,0,0,0,-1,-2,-1,-2,-1,-2,0,0,-1,-1,-1,-3,-1,1,0,-3,-1,-2,-2,3,5,-11,-7,-12]);
  cases.push(["(p) unified build with the example EQ presets (browser fit)",
    {groups: allGroups, patchGroups: PATCH_GROUPS, vorbis: VORBIS75,
     extraPatches: slotPatches(stock, slots)},
    "7de2ae1b4f9bdf4eab109d7e8ee61fbf3a1e943021c753069687caf720f73704"]);
  assert.throws(() => parseCurve("1 2 3"), /31 dB values/);
}
for (const [id, hash] of [
  ["fast-linear-phase", "c6794c724cbfe9d8f00b1f7bf439f1da93c08dbbff1a13f5fdc913719543f3b7"],
  ["slow-low-latency", "bc095da0c9188a022a3fab3a96af55a6a288550c8e0f91b583b55898bea29255"],
  ["slow-linear-phase", "02a905f69d459250927a3b94c23f92ee1581ef29e3ff598cec0fe1f64107f361"],
  ["nos", "bfd64bdd756768b87763d2cb42ccd2d0d7144d5c832d5f94693d652a35a67823"],
]) cases.push(["(n) unified build with DAC filter " + id,
  {groups: allGroups, patchGroups: PATCH_GROUPS, vorbis: VORBIS75,
   extraPatches: dacFilterPatches(id)}, hash]);
for (const [id, extra, hash] of [
  ["10min", [], "f8ec789695c2915d774628e5968b75bac4d5af8fa6bf3140a7eebc6dda6ca9b3"],
  ["never", [], "64055539485a84426eb3e0be6b694faa1f4ae0647eb1b490658340f32e1136e5"],
  ["never", dacFilterPatches("nos"), "f6f08c220dd6b33b322df25a807e183d9af744e80122a05f234e73ceb596314c"],
]) cases.push(["(o) unified build with Bluetooth auto-off " + id + (extra.length ? " and DAC filter nos" : ""),
  {groups: allGroups, patchGroups: PATCH_GROUPS, vorbis: VORBIS75,
   extraPatches: [...btAutoOffPatches(id), ...extra]}, hash]);
assert.deepEqual(btAutoOffPatches("stock"), []);
assert.throws(() => btAutoOffPatches("bogus"), /unknown Bluetooth auto-off/);
assert.deepEqual(dacFilterPatches("stock"), []);
assert.throws(() => dacFilterPatches("bogus"), /unknown DAC filter/);
// The page embeds the Opus data and both payloads; DAP_NEO_*_DATA still
// override them with local files.
{
  const opus = process.env.DAP_NEO_OPUS_DATA
    ? JSON.parse(await readFile(process.env.DAP_NEO_OPUS_DATA, "utf8")) : OPUS_DATA;
  cases.push(["(g) unified build plus the Opus variant",
    {groups: allGroups, patchGroups: PATCH_GROUPS, vorbis: VORBIS75, opus, opusPatches: OPUS_PATCHES},
    "a1c08a819a0edb0954b3a4c0cb73e3b1f725b16663acb441527b244593f94cd7"]);
  cases.push(["(m) everything build: all features in one image",
    {groups: allGroups, patchGroups: PATCH_GROUPS, vorbis: VORBIS75,
     opus, opusPatches: OPUS_PATCHES,
     themeConfig: {version: 1, runs: FULL_THEME_RUNS},
     tailPayload: hexToBytes(FULL_TAIL.hex),
     extraPatches: FULL_EXTRA_PATCHES,
     growths: FULL_GROWTHS.map(g => ({module: g.module,
                                      payload: hexToBytes(g.hex)}))},
    FULL_IMAGE_SHA256]);
}
{
  const bt = process.env.DAP_NEO_BT_DATA
    ? new Uint8Array(await readFile(process.env.DAP_NEO_BT_DATA)) : hexToBytes(BT_PAYLOAD.hex);
  const tailPayload = await bluetoothTail(bt, sha256Hex);
  cases.push(["(h) Bluetooth tail and hook, framework reference",
    {groups: allGroups, patchGroups: PATCH_GROUPS, tailPayload, extraPatches: [BT_PATCH]},
    "a14219b97ea5626a8e37cfe16fb22cd5d0d417c64037646d2ef0113f3f5730cd"]);
}
{
  const payload = await lockscreenPayload(process.env.DAP_NEO_LOCK_DATA
    ? new Uint8Array(await readFile(process.env.DAP_NEO_LOCK_DATA)) : hexToBytes(LOCK_PAYLOAD.hex), sha256Hex);
  cases.push(["standalone lock-screen extension, framework reference",
    {groups: allGroups, patchGroups: PATCH_GROUPS, module31Payload: payload, extraPatches: [LOCK_PATCH]},
    "a645d045ed1ef5f5ad7cae2ded9bace8fea4d41480f18e53f7e540114c9f24f7"]);
}
if (process.env.DAP_NEO_PLAYLIST_OVERLAY && process.env.DAP_NEO_PLAYLIST_RESOLVER) {
  const overlay = new Uint8Array(await readFile(process.env.DAP_NEO_PLAYLIST_OVERLAY));
  const resolver = new Uint8Array(await readFile(process.env.DAP_NEO_PLAYLIST_RESOLVER));
  const playlist = await playlistPayloads(overlay, resolver, sha256Hex);
  cases.push(["(i) playlist and lock-screen with Vorbis",
    {groups: allGroups, patchGroups: PATCH_GROUPS, vorbis: VORBIS75,
     module31Payload: playlist.overlay, tailPayload: playlist.resolver,
     extraPatches: PLAYLIST_PATCHES},
    "5084d954d24c446a6cdaa3cf85b90728de1bee4c28bbd647d4415a4b0e4be16e"]);
  if (process.env.DAP_NEO_BT_DATA) {
    const bt = new Uint8Array(await readFile(process.env.DAP_NEO_BT_DATA));
    cases.push(["(j) combined playlist, lock-screen and Bluetooth with Vorbis",
    {groups: allGroups, patchGroups: PATCH_GROUPS, vorbis: VORBIS75,
     module31Payload: playlist.overlay,
     tailPayload: combineTails(playlist.resolver, await bluetoothTail(bt, sha256Hex)),
     extraPatches: [BT_PATCH, ...PLAYLIST_PATCHES]},
    "a417b4aa6e47be23192bcb333e48ca8260b19e999d3a563435c9f2a43c515bb3"]);
  }
}

let failed = 0;
for (const [label, options, expected] of cases) {
  const out = await buildFirmware(stock, options, sha256Hex);
  const ok = out.sha256 === expected;
  if (!ok) failed++;
  console.log((ok ? "PASS" : "FAIL") + " " + label);
  console.log("     page engine " + out.sha256);
  console.log("     build.py    " + expected);
  console.log("     patches applied: " + out.patchesApplied +
    ", bytes changed vs stock: " + out.bytesChanged);
}
if (failed) {
  console.error(failed + " builder equality case(s) failed");
  process.exit(1);
}
// A theme run must survive when the splash mark is enabled, and an
// overlapping run must be refused instead of being silently discarded.
const mark = CE_MARK_RUNS[0];
await assert.rejects(buildFirmware(stock, {
  groups: allGroups, patchGroups: PATCH_GROUPS,
  themeConfig: {version: 1, runs: [mark]}, ceMarkRuns: CE_MARK_RUNS,
}, sha256Hex), /overlaps an earlier modification/);
console.log("PASS overlapping theme and mark runs are refused");
await assert.rejects(buildFirmware(stock, {
  groups: allGroups, patchGroups: PATCH_GROUPS, opusPatches: OPUS_PATCHES,
  opus: {ranges: [{offset: 0, replace: "00"}]},
}, sha256Hex), /range outside module 72/);
console.log("PASS Opus data cannot write outside its module");
await assert.rejects(bluetoothTail(new Uint8Array(436), sha256Hex), /does not match/);
await assert.rejects(lockscreenPayload(new Uint8Array(406), sha256Hex), /does not match/);
await assert.rejects(playlistPayloads(new Uint8Array(7168), new Uint8Array(1602), sha256Hex), /does not match/);
await assert.rejects(theaterTail(new Uint8Array(676), sha256Hex), /does not match/);
console.log("PASS experimental payload hashes reject altered data");
// Theater takes the tail outright: the wiring refuses it combined
// with a Bluetooth-shaped tail, a playlist resolver tail, or the
// lock screen, and passes payloads through untouched otherwise.
assert.throws(() => combineWithTheater(
  theaterBytes, new Uint8Array(2044), false), /cannot be combined/);
assert.throws(() => combineWithTheater(
  theaterBytes, new Uint8Array(1602), false), /cannot be combined/);
assert.throws(() => combineWithTheater(
  theaterBytes, null, true), /cannot be combined/);
assert.equal(combineWithTheater(theaterBytes, null, false), theaterBytes);
assert.equal(combineWithTheater(null, theaterBytes, false), theaterBytes);
console.log("PASS theater tail exclusivity is enforced");
console.log("All builder byte-equality cases match build.py.");
