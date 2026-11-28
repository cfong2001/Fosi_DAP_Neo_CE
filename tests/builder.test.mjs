// Offline proof for the CE builder page engine (docs/builder-core.mjs).
//
// Runs the page's patch engine headlessly against the stock image and
// asserts byte equality with the Python framework's own outputs
// (patches/framework/build.py at this revision, default build date
// 20261023). The expected hashes below are build.py's outputs:
//
//   (a) framework-only build:
//         build.py --no-transplants
//         9ef6284c88a48c50966813b88677f789bc3413e9ee18ad88f66ea378d0f5f0bf
//   (b) framework-only plus the example theme:
//         build.py --no-transplants \
//           --theme-config patches/theme_editor/theme.example.json
//         668b2df36fb652959226e8200c6fa53b562e035f3e9aead580a40a5faa900fea
//   (c) framework-only plus the CE splash mark:
//         build.py --no-transplants \
//           --theme-config patches/theme_editor/ce-mark.json
//         8bf4ce635ffdb00fd81a149bf076c5fc420e9064b33e861cbef111062a941c4d
//   (d) the default unified build (byte patches plus vorbis75):
//         build.py
//         43476a08ace9e4fbf942bfcab2bbd5eea2e3554ac7a7c7cf60f9770d29700565
//   (k) the theater variant (the default build plus the five
//       theater hook patches and the 676-byte tail payload):
//         build.py --manifest patches/theater/build/manifest.txt \
//           --tail patches/theater/build/theater_tail.bin
//         4247c28ca74e015c3d8940daa246c8ffd9d3fb52a13e092b0a970be219b2757d
//   (l) the theater variant plus the title pair (40 patches):
//         17bf32725119cef40bbe5188903cf52a5ab14c9a68d6a2401dccf2b20171bc57
//   (p) the default unified build with the example EQ presets
//       (patches/eq_presets/example.json: a custom curve in slot 5 and
//       an AutoEQ GraphicEQ in slot 6 renamed "HD 600", fitted in the browser):
//         build.py --eq-presets patches/eq_presets/example.json
//         5840564ccf4fd754bfe39036f391380ebe05f1409d83b86f21b13b22c2c1f77e
//   (n) the default unified build with each DAC filter:
//         build.py --dac-filter fast-linear-phase
//           83b6f0cff500d09dbcc7e76e0122473c46f320e3998e622bb3cabffae9b958c6
//         build.py --dac-filter slow-low-latency
//           719baedc6500c824474d846068253d25c23daf5687307ffac469b1a1af8b47cf
//         build.py --dac-filter slow-linear-phase
//           2879f65c2a4792238d31b6d0e22aa61009a9e0a380fd7e701888dc515c041bf8
//         build.py --dac-filter nos
//           8f8f3ffe820d6ebbf6ad4c151bd1af2d2d686ee16910fba7fcc23448e283c775
//   (o) the default unified build with each Bluetooth auto-off option,
//       and with both new options together:
//         build.py --bt-auto-off 10min
//           402db2b90a6f2236775e2ef0a98b9ebefcfed70716705795331a4434839c4268
//         build.py --bt-auto-off never
//           9e163264bc63ecd42dea6b662f6409e95f959dd3a823edace0ca4acae6de4c23
//         build.py --bt-auto-off never --dac-filter nos
//           97ff0281eeae8c5a64f28b704a168bf1f4c287d19ecc8da17cfe30b4141f3a3f
//   (m) the everything build (patches/full/: 143 patches, both
//       transplants, two growth insertions, the merged tail and
//       the merged theme runs), with the page's embedded Opus data
//       (docs/builder-opus-data.mjs; DAP_NEO_OPUS_DATA overrides it):
//         build_full.py (one build.py pass)
//         b91485f76ab11d12fd42305f37adf2cca02168f40c831d009ac13099cbca5830
//   standalone lock screen (the embedded 406-byte reference-toolchain
//   routine in a module 31 extension, plus patch 0033):
//         build.py --no-transplants --manifest <framework manifest plus
//           patches/ui_features/lockscreen_build/0033-ui-lockscreen-title.patch>
//           --grow 31:code:lockscreen.bin
//         13f8f3ddbb60edcd2f9354ba880ffe72dccbfb86a557300c532dba637656be0f
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
import {FULL_PATCHES, FULL_TAIL, FULL_GROWTHS, FULL_THEME_RUNS, FULL_IMAGE_SHA256} from "../docs/builder-full.mjs";
import {bandTable, parseCurve, fit, slotPatches, namePatches} from "../docs/eq-core.mjs";
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
const codeColours = JSON.parse(await readFile(
  new URL("../patches/theme_editor/code-colours.example.json", import.meta.url),
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
  .split("\n").map(line => line.split("#")[0].trim()).filter(Boolean);
assert.equal(fullManifest.length, FULL_PATCHES.length);
for (const [patch, path] of fullManifest.map((entry, i) =>
    [FULL_PATCHES[i], "../patches/full/" + entry])) {
  const source = await readFile(new URL(path, import.meta.url), "utf8");
  const field = name => source.match(new RegExp("^" + name + ":\\s*(\\S+)", "m"))?.[1];
  assert.equal(patch.address, Number(field("address")));
  assert.equal(patch.module, Number(field("module")));
  assert.equal(patch.expect, field("expect").toLowerCase());
  assert.equal(patch.replace, field("replace").toLowerCase());
}
assert.equal(FULL_PATCHES.length, 193);
assert.equal(FULL_TAIL.length, 2040);
assert.equal(FULL_TAIL.sha256,
  "794659ecade723737fe5f09fab9efdf904b0b3c1e4336e055a65f08fcf20e0e4");
assert.deepEqual(FULL_GROWTHS.map(g => [g.module, g.length, g.sha256]), [
  [31, 6616, "3f7e09cae9658c4cf21bfc4f9be92a037051f10a74e759f2e7fd8d4c0cac2aa9"],
  [24, 26, "7b80afb308d276a4d0012cd4302f7a5f2a1c5192a1f2e70d3f23867e195a942a"],
  [39, 1052, "f388c301f6ad4f16d00eaf8e10d565998768cb90b1938c4f32ffc7201afbc3b9"],
]);
assert.equal(FULL_THEME_RUNS.length, 2277);
assert.equal(FULL_IMAGE_SHA256,
  "b91485f76ab11d12fd42305f37adf2cca02168f40c831d009ac13099cbca5830");
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
   "9ef6284c88a48c50966813b88677f789bc3413e9ee18ad88f66ea378d0f5f0bf"],
  ["(b) toggles on plus the example theme",
   {groups: allGroups, patchGroups: PATCH_GROUPS, themeConfig: exampleTheme},
   "668b2df36fb652959226e8200c6fa53b562e035f3e9aead580a40a5faa900fea"],
  ["(b2) toggles on plus the code-colour example",
   {groups: allGroups, patchGroups: PATCH_GROUPS, themeConfig: codeColours},
   "d887bfe8967f2179b5eca044c2250b513998b9a29863cf1d74c23203c1c1c160"],
  ["(c) toggles on plus the CE splash mark",
   {groups: allGroups, patchGroups: PATCH_GROUPS, ceMarkRuns: CE_MARK_RUNS},
   "8bf4ce635ffdb00fd81a149bf076c5fc420e9064b33e861cbef111062a941c4d"],
  ["(d) toggles on plus the vorbis75 transplant (unified build)",
   {groups: allGroups, patchGroups: PATCH_GROUPS, vorbis: VORBIS75},
   "43476a08ace9e4fbf942bfcab2bbd5eea2e3554ac7a7c7cf60f9770d29700565"],
  ["(e) gapless off, other feature patches on",
   {groups: new Set([...allGroups].filter(id => id !== "gapless")), patchGroups: PATCH_GROUPS},
   "35d5c0691464b3553103f54464822573aded3a2dfc6699939f3545a2c2a6c2f2"],
  ["(f) module 31 insertion, framework reference",
   {groups: allGroups, patchGroups: PATCH_GROUPS,
    module31Payload: Uint8Array.from({length: 1000}, (_, i) => i % 251)},
   "98ed54f2d4e5812574b999acdaef419b6d76b6e16adbf6face6da5ea4eea1e3c"],
  ["(g) paired player title repair, framework reference",
   {groups: allGroups, patchGroups: PATCH_GROUPS, extraPatches: TITLE_PATCHES},
   "240fe3773054c756a9e341272b90d05d67fcecf96d5900dc2164eea4b9ac9f3d"],
  ["(k) theater variant: default build plus hooks and tail",
   {groups: allGroups, patchGroups: PATCH_GROUPS, vorbis: VORBIS75,
    extraPatches: THEATER_PATCHES, tailPayload: theaterBytes},
   "4247c28ca74e015c3d8940daa246c8ffd9d3fb52a13e092b0a970be219b2757d"],
  ["(l) theater plus title pair (different modules, no overlap)",
   {groups: allGroups, patchGroups: PATCH_GROUPS, vorbis: VORBIS75,
    extraPatches: [...THEATER_PATCHES, ...TITLE_PATCHES],
    tailPayload: theaterBytes},
   "17bf32725119cef40bbe5188903cf52a5ab14c9a68d6a2401dccf2b20171bc57"],
];
{
  const example = JSON.parse(await readFile(new URL("../patches/eq_presets/example.json", import.meta.url), "utf8"));
  const R = bandTable(stock), slots = {}, names = {};
  for (const [n, spec] of Object.entries(example.slots)) {
    if (spec.name) names[n] = spec.name;
    const text = spec.text ?? await readFile(new URL("../patches/eq_presets/" + spec.file, import.meta.url), "utf8");
    slots[n] = fit(parseCurve(text), R).gains;
  }
  assert.deepEqual(slots[6], [-1,0,0,1,0,0,0,-1,-2,-1,-2,-1,-2,0,0,-1,-1,-1,-3,-1,1,0,-3,-1,-2,-2,3,5,-11,-7,-12]);
  cases.push(["(p) unified build with the example EQ presets (browser fit)",
    {groups: allGroups, patchGroups: PATCH_GROUPS, vorbis: VORBIS75,
     extraPatches: [...slotPatches(stock, slots), ...namePatches(stock, names)]},
    "5840564ccf4fd754bfe39036f391380ebe05f1409d83b86f21b13b22c2c1f77e"]);
  assert.throws(() => parseCurve("1 2 3"), /31 dB values/);
  for (const bad of ["", " Warm", "x".repeat(25), "a\nb"])
    assert.throws(() => namePatches(stock, {1: bad}), /slot 1: name/);
}
for (const [id, hash] of [
  ["fast-linear-phase", "83b6f0cff500d09dbcc7e76e0122473c46f320e3998e622bb3cabffae9b958c6"],
  ["slow-low-latency", "719baedc6500c824474d846068253d25c23daf5687307ffac469b1a1af8b47cf"],
  ["slow-linear-phase", "2879f65c2a4792238d31b6d0e22aa61009a9e0a380fd7e701888dc515c041bf8"],
  ["nos", "8f8f3ffe820d6ebbf6ad4c151bd1af2d2d686ee16910fba7fcc23448e283c775"],
]) cases.push(["(n) unified build with DAC filter " + id,
  {groups: allGroups, patchGroups: PATCH_GROUPS, vorbis: VORBIS75,
   extraPatches: dacFilterPatches(id)}, hash]);
for (const [id, extra, hash] of [
  ["10min", [], "402db2b90a6f2236775e2ef0a98b9ebefcfed70716705795331a4434839c4268"],
  ["never", [], "9e163264bc63ecd42dea6b662f6409e95f959dd3a823edace0ca4acae6de4c23"],
  ["never", dacFilterPatches("nos"), "97ff0281eeae8c5a64f28b704a168bf1f4c287d19ecc8da17cfe30b4141f3a3f"],
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
    "127e011ebc6fe9c8c713815845d6669d974e4da726c2b609d9d1c9118d76479c"]);
  cases.push(["(m) everything build: all features in one image",
    {groups: new Set(), patchGroups: [], vorbis: VORBIS75,
     opus, opusPatches: [],
     themeConfig: {version: 1, runs: FULL_THEME_RUNS},
     tailPayload: hexToBytes(FULL_TAIL.hex),
     extraPatches: FULL_PATCHES,
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
    "6cb7e797e38fff7d69bd35a07737b5a19f157a6e87aed7a71660ade6062ab6a8"]);
}
{
  const payload = await lockscreenPayload(process.env.DAP_NEO_LOCK_DATA
    ? new Uint8Array(await readFile(process.env.DAP_NEO_LOCK_DATA)) : hexToBytes(LOCK_PAYLOAD.hex), sha256Hex);
  cases.push(["standalone lock-screen extension, framework reference",
    {groups: allGroups, patchGroups: PATCH_GROUPS, module31Payload: payload, extraPatches: [LOCK_PATCH]},
    "13f8f3ddbb60edcd2f9354ba880ffe72dccbfb86a557300c532dba637656be0f"]);
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

// A code colour must name a known role, and a run that claims one of
// its movw sites is refused as an overlap, as in build.py.
await assert.rejects(buildFirmware(stock, {
  groups: allGroups, patchGroups: PATCH_GROUPS,
  themeConfig: {version: 1, code_colours: {background: "#000000"}},
}, sha256Hex), /unknown code colour/);
await assert.rejects(buildFirmware(stock, {
  groups: allGroups, patchGroups: PATCH_GROUPS,
  themeConfig: {version: 1, code_colours: {accent_light: "#0284C7"},
                runs: [{offset: "0x3ec86", expect: "4ff62030", replace: "4ff62030"}]},
}, sha256Hex), /overlaps an earlier modification/);
console.log("PASS code colours: unknown roles and overlapping runs are refused");
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
