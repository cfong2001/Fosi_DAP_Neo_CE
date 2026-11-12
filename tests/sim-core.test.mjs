// The simulator's renderer (docs/sim-core.mjs) must reproduce the
// emulated painter framebuffers recorded by tools/gen_sim_data.py, and
// its pins must match the committed images.
//   node --test tests/sim-core.test.mjs
import {test} from "node:test";
import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";
import {createHash} from "node:crypto";
import {fileURLToPath} from "node:url";
import path from "node:path";
import {SECTIONS, PAINTER} from "../docs/sim-data.mjs";
import {
  WIDTH, HEIGHT, parseResourceSection, resourceSectionOf, fill, paintPlayer,
  paintProgress, resourceWords, theaterGround, sampleCover, rgb565, framebufferBytes,
  rgbaToWords
} from "../docs/sim-core.mjs";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const sha = bytes => createHash("sha256").update(bytes).digest("hex");
const fixture = JSON.parse(await readFile(path.join(root, "tests/fixtures/sim-painter.json"), "utf8"));

const images = {};
for (const [name, pin] of Object.entries(SECTIONS)) {
  const image = new Uint8Array(await readFile(path.join(root, pin.file)));
  images[name] = {image, pin};
}

test("section pins match the committed images", () => {
  for (const {image, pin} of Object.values(images)) {
    assert.equal(sha(image), pin.image_sha256, pin.file);
    const section = image.subarray(pin.offset, pin.offset + pin.length);
    assert.equal(sha(section), pin.sha256, pin.file + " section");
    assert.deepEqual(resourceSectionOf(image), section);
  }
});

test("painter replay equals every emulated framebuffer", () => {
  assert.equal(fixture.cases.length, 24);
  for (const c of fixture.cases) {
    const {image, pin} = images[c.image];
    const res = parseResourceSection(image.subarray(pin.offset, pin.offset + pin.length));
    const fb = new Uint16Array(WIDTH * HEIGHT);
    fill(fb, 0, 0, WIDTH - 1, HEIGHT - 1, c.ground);
    paintPlayer(fb, res, c.image, {page: c.b, playing: c.play === 1, light: c.theme === 1, ground: c.ground});
    assert.equal(sha(framebufferBytes(fb)), c.sha256,
      `${c.image} theme ${c.theme} B=${c.b} play=${c.play} ground 0x${c.ground.toString(16)}`);
  }
});

test("every state has painter data for both images", () => {
  for (const name of ["stock", "ce"])
    for (const key of ["0:1", "0:0", "1:1", "2:1"]) assert.ok(PAINTER[name][key].length > 0);
});

// Same arithmetic as port_derived in patches/full/build/tests/test_theater_full.py.
function portDerived(words, width, height, light) {
  const rows = Math.ceil(height / 3), sums = [0, 0, 0];
  for (let i = 0; i < rows * width; i++) {
    const w = words[i];
    sums[0] += Math.floor(((w >> 11) & 31) * 255 / 31);
    sums[1] += Math.floor(((w >> 5) & 63) * 255 / 63);
    sums[2] += Math.floor((w & 31) * 255 / 31);
  }
  const n = rows * width, avg = sums.map(s => Math.floor((s + Math.floor(n / 2)) / n));
  const mixed = light ? avg.map((a, i) => Math.floor((a * 25 + [242, 237, 230][i] * 75 + 50) / 100))
                      : avg.map(a => Math.floor((a * 45 + 50) / 100));
  return rgb565(...mixed);
}

test("theater ground equals the Python port on synthetic art", () => {
  assert.equal(fixture.theater.length, 8);
  for (const t of fixture.theater) {
    const words = new Uint16Array(t.width * t.height);
    for (let y = 0; y < t.height; y++)
      for (let x = 0; x < t.width; x++) words[y * t.width + x] = (x * t.mx + y * t.my + t.c) & 0xFFFF;
    assert.equal(theaterGround(words, t.width, t.height, t.light), t.ground, JSON.stringify(t));
  }
});

test("theater ground follows the firmware port", () => {
  const art = sampleCover();
  assert.equal(theaterGround(art, 144, 144, false), portDerived(art, 144, 144, false));
  assert.equal(theaterGround(art, 144, 144, true), portDerived(art, 144, 144, true));
  // A flat cover averages to itself before the theme mix.
  const flat = new Uint16Array(144 * 144).fill(rgb565(200, 100, 50));
  assert.equal(theaterGround(flat, 144, 144, false), portDerived(flat, 144, 144, false));
  // Only the top third counts.
  const split = new Uint16Array(144 * 144).fill(0xFFFF);
  split.fill(0, 0, 48 * 144);
  assert.equal(theaterGround(split, 144, 144, false), 0);
  assert.equal(rgbaToWords(new Uint8ClampedArray([255, 255, 255, 0]))[0], 0);
});

test("progress bar is the image's own columns and knob at the player's coordinates", () => {
  const res = parseResourceSection(resourceSectionOf(images.ce.image));
  const ground = 0x7222;
  for (const light of [false, true]) {
    const off = light ? 166 : 0;
    const fb = new Uint16Array(WIDTH * HEIGHT);
    paintProgress(fb, res, {fraction: 0.5, light, ground});
    const filled = Math.round(0.5 * 147);
    const on = resourceWords(res, 187 + off), offc = resourceWords(res, 188 + off);
    for (const i of [0, filled - 10, filled + 20, 147]) {   // clear of the knob
      const col = i < filled ? on : offc;
      for (let r = 0; r < 6; r++) assert.equal(fb[(258 + r) * WIDTH + 46 + i], col[r], `col ${i} row ${r}`);
    }
    const knob = resourceWords(res, 220 + off), kx = Math.min(filled + 42, 196);
    assert.equal(fb[(254 + 7) * WIDTH + kx + 7], knob[7 * 14 + 7]);
    assert.equal(fb[254 * WIDTH + 40], ground, "ground fill at the bar's corner");
    assert.equal(fb[253 * WIDTH + 40], 0, "nothing above the bar area");
  }
});

// Same arithmetic as artwork.c (gain, inset) for the CE cover treatment.
test("CE cover treatment follows the artwork compositor", async () => {
  const {artContrast, artInset, blitCover, paintBadge, BADGE, ART} = await import("../docs/sim-core.mjs");
  const cGain = (v, top) => { const n = 120 * v - 10 * top + 50; const q = n < 0 ? -Math.floor(-n / 100) : Math.floor(n / 100); return Math.max(0, Math.min(top, q)); };
  for (let w = 0; w < 0x10000; w += 97)
    assert.equal(artContrast(w), (cGain(w >> 11, 31) << 11) | (cGain((w >> 5) & 63, 63) << 5) | cGain(w & 31, 31));
  assert.equal(artContrast(0), 0);
  assert.equal(artContrast(0xFFFF), 0xFFFF);
  assert.deepEqual([0, 1, 9, 10, 72, 134, 143].map(r => artInset(r, 144)), [7, 5, 0, 0, 0, 0, 7]);
  const fb = new Uint16Array(WIDTH * HEIGHT), ground = 0x1234;
  blitCover(fb, new Uint16Array(144 * 144).fill(0x8410), 144, ART.x, ART.y, ground);
  assert.equal(fb[ART.y * WIDTH + ART.x + 6], ground, "masked corner");
  assert.equal(fb[ART.y * WIDTH + ART.x + 7], artContrast(0x8410), "first pixel inside the mask");
  assert.equal(fb[(ART.y + 143) * WIDTH + ART.x + 143 - 6], ground, "symmetric bottom-right corner");
  assert.equal(fb[(ART.y + 143) * WIDTH + ART.x + 143 - 7], artContrast(0x8410), "inside at the mirror");
  paintBadge(fb, 0x10A2);
  assert.equal(fb[BADGE.y * WIDTH + BADGE.x + 7], 0x10A2);
  assert.notEqual(fb[BADGE.y * WIDTH + BADGE.x + 6], 0x10A2);
  assert.equal(fb[(BADGE.y + 10) * WIDTH + BADGE.x + 55], 0x10A2);
});

test("CE progress bar is the inverse of the ground, as bar_recolor draws it", async () => {
  const {paintProgress, barColumns} = await import("../docs/sim-core.mjs");
  const res = parseResourceSection(resourceSectionOf(images.ce.image));
  const half = (a, b) => ((a & 0xF7DE) >> 1) + ((b & 0xF7DE) >> 1);
  for (const ground of [0x61A1, 0x10A2, 0xBE9A, 0xFFFF]) {
    const inv = ~ground & 0xFFFF;
    const fb = new Uint16Array(WIDTH * HEIGHT);
    paintProgress(fb, res, {fraction: 0.5, ground, inverse: true});
    const filled = Math.round(0.5 * 147), {played, unplayed} = barColumns(ground);
    assert.deepEqual(played, [half(inv, ground), inv, inv, inv, inv, half(inv, ground)]);
    for (let r = 0; r < 6; r++) {
      assert.equal(fb[(258 + r) * WIDTH + 46], played[r]);
      assert.equal(fb[(258 + r) * WIDTH + 46 + 147], unplayed[r]);
    }
    assert.equal(fb[254 * WIDTH + 40], ground);
  }
});
