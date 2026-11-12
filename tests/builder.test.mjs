// Offline proof for the CE builder page engine (docs/builder-core.mjs).
//
// Runs the page's patch engine headlessly against the stock image and
// asserts byte equality with the Python framework's own outputs
// (patches/framework/build.py at this revision, default build date
// 20261023). The expected hashes below are build.py's outputs:
//
//   (a) framework-only build:
//         build.py --no-transplants
//         c71c98c4e47241551634445ffa4ecd418757f030513728edf3be94dfecf4b8ac
//   (b) framework-only plus the example theme:
//         build.py --no-transplants \
//           --theme-config patches/theme_editor/theme.example.json
//         75c8d0a8270028a5ecff1fb81149185240a9461c84f19a42c787e0a0c86f1c77
//   (c) framework-only plus the CE splash mark:
//         build.py --no-transplants \
//           --theme-config patches/theme_editor/ce-mark.json
//         1d2847abd0fe363a29eeee0d3b69eb4429cae722b988e96840ae92b3a9c7d938
//   (d) the default unified build (byte patches plus vorbis75):
//         build.py
//         1cf609559048a02686585a159dab06fa4856954aa647283a50a8b47da33e3c99
//   (k) the theater variant (the default build plus the five
//       theater hook patches and the 676-byte tail payload):
//         build.py --manifest patches/theater/build/manifest.txt \
//           --tail patches/theater/build/theater_tail.bin
//         698c7def8898496f128090f2a4d6666a689c1e1e138851bb2fce7f6ae30c54e0
//   (l) the theater variant plus the title pair (38 patches):
//         3b57f57f4634c797ddad024b737e038953e53ee592e25d45375e3187c81a7989
//   (p) the default unified build with the example EQ presets
//       (patches/eq_presets/example.json: a custom curve in slot 5 and
//       an AutoEQ GraphicEQ in slot 6, fitted in the browser):
//         build.py --eq-presets patches/eq_presets/example.json
//         4981629b659a0c2e5b183f36640d55bb9bc679ad9ec06a0470cf4ae5d99f8664
//   (n) the default unified build with each DAC filter:
//         build.py --dac-filter fast-linear-phase
//           bd7301f0b61a3e7e15b923e372363b200cf9e3c8f8384ac27cd64b04120685ed
//         build.py --dac-filter slow-low-latency
//           ab8f0c3bb4cdf821839f728303db1f3465222d47f081be585d390a016cdca538
//         build.py --dac-filter slow-linear-phase
//           2c859507e7bd8170733b007127c99c6787316d4ba3fedb565943492c4e6c2bfc
//         build.py --dac-filter nos
//           40a13e126ad761cc6b598104da29ce3b6f76a9eaa46c6625b87c74d2337d703a
//   (o) the default unified build with each Bluetooth auto-off option,
//       and with both new options together:
//         build.py --bt-auto-off 10min
//           c92fb4143c732234fd30582b6c11a0e11df46e80475f43779354be5519ff8ace
//         build.py --bt-auto-off never
//           acfa0e0bd40fd7a839172b1f59a82e170acbe4614c429382c86b6d75ee422bd2
//         build.py --bt-auto-off never --dac-filter nos
//           566546aea3b1a9367b54cb1b211a030eef4876ac19de0201d303e17f7cce28a2
//   (m) the everything build (patches/full/: 65 patches, both
//       transplants, two growth insertions, the merged tail and
//       the merged theme runs), with the page's embedded Opus data
//       (docs/builder-opus-data.mjs; DAP_NEO_OPUS_DATA overrides it):
//         build_full.py (one build.py pass)
//         6fb923612567088663bc145fda4812e97a96c1a304d5e25bbb2c5b4bef2baefb
//   standalone lock screen (the embedded 406-byte reference-toolchain
//   routine in a module 31 extension, plus patch 0033):
//         build.py --no-transplants --manifest <framework manifest plus
//           patches/ui_features/lockscreen_build/0033-ui-lockscreen-title.patch>
//           --grow 31:code:lockscreen.bin
//         25e8341a39cd41413042d5e9379bad71eb946bde19fcebebf30a2709ee718068
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
  "6fb923612567088663bc145fda4812e97a96c1a304d5e25bbb2c5b4bef2baefb");
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
   "c71c98c4e47241551634445ffa4ecd418757f030513728edf3be94dfecf4b8ac"],
  ["(b) toggles on plus the example theme",
   {groups: allGroups, patchGroups: PATCH_GROUPS, themeConfig: exampleTheme},
   "75c8d0a8270028a5ecff1fb81149185240a9461c84f19a42c787e0a0c86f1c77"],
  ["(c) toggles on plus the CE splash mark",
   {groups: allGroups, patchGroups: PATCH_GROUPS, ceMarkRuns: CE_MARK_RUNS},
   "1d2847abd0fe363a29eeee0d3b69eb4429cae722b988e96840ae92b3a9c7d938"],
  ["(d) toggles on plus the vorbis75 transplant (unified build)",
   {groups: allGroups, patchGroups: PATCH_GROUPS, vorbis: VORBIS75},
   "1cf609559048a02686585a159dab06fa4856954aa647283a50a8b47da33e3c99"],
  ["(e) gapless off, other feature patches on",
   {groups: new Set([...allGroups].filter(id => id !== "gapless")), patchGroups: PATCH_GROUPS},
   "25c34dafafb155f32911bd40d386792b90ea7c37d6ffabcbfd4637b1b8a367f1"],
  ["(f) module 31 insertion, framework reference",
   {groups: allGroups, patchGroups: PATCH_GROUPS,
    module31Payload: Uint8Array.from({length: 1000}, (_, i) => i % 251)},
   "80d2e24602376eab8515797342d322c7616ae9a2f897c681da1132864f77f923"],
  ["(g) paired player title repair, framework reference",
   {groups: allGroups, patchGroups: PATCH_GROUPS, extraPatches: TITLE_PATCHES},
   "8c39a2e1fcda66cf5d33f6284c94b7a55ab488eb4b5771ae0b2c35a0dde3c98d"],
  ["(k) theater variant: default build plus hooks and tail",
   {groups: allGroups, patchGroups: PATCH_GROUPS, vorbis: VORBIS75,
    extraPatches: THEATER_PATCHES, tailPayload: theaterBytes},
   "698c7def8898496f128090f2a4d6666a689c1e1e138851bb2fce7f6ae30c54e0"],
  ["(l) theater plus title pair (different modules, no overlap)",
   {groups: allGroups, patchGroups: PATCH_GROUPS, vorbis: VORBIS75,
    extraPatches: [...THEATER_PATCHES, ...TITLE_PATCHES],
    tailPayload: theaterBytes},
   "3b57f57f4634c797ddad024b737e038953e53ee592e25d45375e3187c81a7989"],
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
    "4981629b659a0c2e5b183f36640d55bb9bc679ad9ec06a0470cf4ae5d99f8664"]);
  assert.throws(() => parseCurve("1 2 3"), /31 dB values/);
}
for (const [id, hash] of [
  ["fast-linear-phase", "bd7301f0b61a3e7e15b923e372363b200cf9e3c8f8384ac27cd64b04120685ed"],
  ["slow-low-latency", "ab8f0c3bb4cdf821839f728303db1f3465222d47f081be585d390a016cdca538"],
  ["slow-linear-phase", "2c859507e7bd8170733b007127c99c6787316d4ba3fedb565943492c4e6c2bfc"],
  ["nos", "40a13e126ad761cc6b598104da29ce3b6f76a9eaa46c6625b87c74d2337d703a"],
]) cases.push(["(n) unified build with DAC filter " + id,
  {groups: allGroups, patchGroups: PATCH_GROUPS, vorbis: VORBIS75,
   extraPatches: dacFilterPatches(id)}, hash]);
for (const [id, extra, hash] of [
  ["10min", [], "c92fb4143c732234fd30582b6c11a0e11df46e80475f43779354be5519ff8ace"],
  ["never", [], "acfa0e0bd40fd7a839172b1f59a82e170acbe4614c429382c86b6d75ee422bd2"],
  ["never", dacFilterPatches("nos"), "566546aea3b1a9367b54cb1b211a030eef4876ac19de0201d303e17f7cce28a2"],
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
    "2c17dde9101c5a8b61e2400b166c4bcf7f47d2f820bfe25db9a1683e3cec2996"]);
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
    "525c54d1da01fa3916179d135af2262ebc047e2897b2a4a3add6d69020a13861"]);
}
{
  const payload = await lockscreenPayload(process.env.DAP_NEO_LOCK_DATA
    ? new Uint8Array(await readFile(process.env.DAP_NEO_LOCK_DATA)) : hexToBytes(LOCK_PAYLOAD.hex), sha256Hex);
  cases.push(["standalone lock-screen extension, framework reference",
    {groups: allGroups, patchGroups: PATCH_GROUPS, module31Payload: payload, extraPatches: [LOCK_PATCH]},
    "25e8341a39cd41413042d5e9379bad71eb946bde19fcebebf30a2709ee718068"]);
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
