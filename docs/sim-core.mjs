// Screen renderer for the simulator (simulator.js). Pure: no DOM, no
// network. Works on 240x320 framebuffers of RGB565 words.
//
// Pixels are real: resources are decoded from a firmware image's resource
// section, and the player's status icon and transport row are drawn by
// replaying what the firmware's own painter draws (PAINTER in
// sim-data.mjs, recorded under emulation by tools/gen_sim_data.py).
// tests/sim-core.test.mjs checks the replay against the emulated
// framebuffers word for word.
import {LIGHT_OFFSET, DEFAULT_GROUND, PAINTER} from "./sim-data.mjs";

export const WIDTH = 240, HEIGHT = 320;
export const KEY = 0xF800;          // keyed draws skip this word
export const ART = {x: 48, y: 36, size: 144};   // approximate cover box

const SIGNATURE = "ROCK26IMAGERES  ";

// Parse a resource section (the bytes at the image header's 0x14C/0x150
// offset and length). Offsets in the result are relative to the section.
export function parseResourceSection(section) {
  const bytes = section instanceof Uint8Array ? section : new Uint8Array(section);
  const view = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
  if (String.fromCharCode(...bytes.subarray(0, 16)) !== SIGNATURE)
    throw new Error("not a resource section (bad signature)");
  const count = view.getUint32(16, true);
  if (0x20 + count * 16 > bytes.length) throw new Error("resource table outside section");
  const entries = [];
  for (let id = 0; id < count; id++) {
    const p = 0x20 + id * 16;
    const width = view.getUint16(p, true), height = view.getUint16(p + 2, true);
    const size = view.getUint32(p + 8, true), offset = view.getUint32(p + 12, true);
    if (offset + size > bytes.length) throw new Error("resource #" + id + " outside section");
    entries.push({id, width, height, x: view.getUint16(p + 4, true),
                  y: view.getUint16(p + 6, true), size, offset});
  }
  return {bytes, view, entries};
}

// The section of a whole image, located through the image header.
export function resourceSectionOf(image) {
  const view = new DataView(image.buffer, image.byteOffset, image.byteLength);
  const start = view.getUint32(0x14C, true), length = view.getUint32(0x150, true);
  if (start + length > image.length) throw new Error("resource section outside image");
  return image.subarray(start, start + length);
}

// Resource pixels as the panel shows them: stored bytes read big-endian.
export function resourceWords(res, id) {
  const e = res.entries[id];
  if (!e || e.size !== e.width * e.height * 2) throw new Error("resource #" + id + " is not RGB565");
  const out = new Uint16Array(e.width * e.height);
  for (let i = 0; i < out.length; i++) out[i] = res.view.getUint16(e.offset + i * 2, false);
  return out;
}

export function fill(fb, x0, y0, x1, y1, word) {
  for (let y = Math.max(0, y0); y <= Math.min(HEIGHT - 1, y1); y++)
    fb.fill(word, y * WIDTH + Math.max(0, x0), y * WIDTH + Math.min(WIDTH - 1, x1) + 1);
}

export function draw(fb, res, id, x, y, keyed = false) {
  const e = res.entries[id];
  const words = resourceWords(res, id);
  for (let r = 0; r < e.height; r++) {
    const fy = y + r;
    if (fy < 0 || fy >= HEIGHT) continue;
    for (let c = 0; c < e.width; c++) {
      const fx = x + c, w = words[r * e.width + c];
      if (fx < 0 || fx >= WIDTH || (keyed && w === KEY)) continue;
      fb[fy * WIDTH + fx] = w;
    }
  }
}

export function blit(fb, words, width, height, x, y) {
  for (let r = 0; r < height; r++)
    for (let c = 0; c < width; c++) {
      const fx = x + c, fy = y + r;
      if (fx >= 0 && fx < WIDTH && fy >= 0 && fy < HEIGHT) fb[fy * WIDTH + fx] = words[r * width + c];
    }
}

export const groundFor = light => light ? DEFAULT_GROUND.light : DEFAULT_GROUND.dark;

// The painter's status icon and transport row for one state, over a
// framebuffer already holding the ground (and anything drawn before it).
export function paintPlayer(fb, res, image, {page = 0, playing = true, light = false, ground}) {
  const ops = PAINTER[image]?.[page + ":" + (playing ? 1 : 0)];
  if (!ops) throw new Error("no painter data for " + image + " state " + page);
  const g = ground ?? groundFor(light);
  for (const op of ops) {
    if (op[0] === "fill") fill(fb, op[1], op[2], op[3], op[4], g);
    else draw(fb, res, op[1] + (light ? LIGHT_OFFSET : 0), op[2], op[3], op[4]);
  }
}

// The player's progress bar as module 27 draws it: a ground fill over
// (40, 254)..(201, 268), one 1x6 column per position at (46 + i, 258) for
// 148 positions (resource 187 up to the filled fraction of 147, then 188),
// and the knob (220) at (min(filled + 42, 196), 254). Light: ids + 166.
export function paintProgress(fb, res, {fraction = 0, light = false, ground}) {
  const off = light ? LIGHT_OFFSET : 0;
  fill(fb, 40, 254, 201, 268, ground ?? groundFor(light));
  const filled = Math.round(Math.min(1, Math.max(0, fraction)) * 147);
  for (let i = 0; i < 148; i++) draw(fb, res, (i < filled ? 187 : 188) + off, 46 + i, 258);
  // keyed: CE draws the knob through the keyed helper (patch 0118); the
  // stock knob has no 0xF800 pixels, so this is exact for both images
  draw(fb, res, 220 + off, Math.min(filled + 42, 196), 254, true);
}

// Theater mode: the port tested against the firmware's own trampoline
// (patches/full/build/tests/test_theater_full.py port_average and
// port_derived), over the first ceil(height / 3) rows of the art.
export const rgb565 = (r, g, b) =>
  (Math.floor((r * 31 + 127) / 255) << 11) | (Math.floor((g * 63 + 127) / 255) << 5) |
  Math.floor((b * 31 + 127) / 255);
export const rgb888 = w => [Math.floor(((w >> 11) & 31) * 255 / 31),
  Math.floor(((w >> 5) & 63) * 255 / 63), Math.floor((w & 31) * 255 / 31)];

export function theaterAverage(words, width, height) {
  const rows = Math.ceil(height / 3), sums = [0, 0, 0];
  for (let i = 0; i < rows * width; i++) {
    const [r, g, b] = rgb888(words[i]);
    sums[0] += r; sums[1] += g; sums[2] += b;
  }
  const count = rows * width;
  return sums.map(s => Math.floor((s + Math.floor(count / 2)) / count));
}

export function theaterGround(words, width, height, light = false) {
  const avg = theaterAverage(words, width, height);
  const paper = [242, 237, 230];
  const mixed = light ? avg.map((a, i) => Math.floor((a * 25 + paper[i] * 75 + 50) / 100))
                      : avg.map(a => Math.floor((a * 45 + 50) / 100));
  return rgb565(...mixed);
}

// RGBA bytes (any size) to RGB565 words, composited over black.
export function rgbaToWords(rgba) {
  const out = new Uint16Array(rgba.length / 4);
  for (let i = 0; i < out.length; i++) {
    const a = rgba[i * 4 + 3] / 255;
    out[i] = rgb565(Math.round(rgba[i * 4] * a), Math.round(rgba[i * 4 + 1] * a),
                    Math.round(rgba[i * 4 + 2] * a));
  }
  return out;
}

export function toRGBA(fb) {
  const out = new Uint8ClampedArray(fb.length * 4);
  for (let i = 0; i < fb.length; i++) {
    const [r, g, b] = rgb888(fb[i]);
    out[i * 4] = r; out[i * 4 + 1] = g; out[i * 4 + 2] = b; out[i * 4 + 3] = 255;
  }
  return out;
}

// A sample cover (the README's "ember" art): a warm vertical gradient
// with a pale sun, as RGB565 words.
export function sampleCover(size = ART.size) {
  const out = new Uint16Array(size * size);
  for (let y = 0; y < size; y++) {
    const t = y / (size - 1);
    const row = rgb565(Math.trunc(245 - 170 * t), Math.trunc(140 - 115 * t), Math.trunc(30 - 10 * t));
    out.fill(row, y * size, (y + 1) * size);
  }
  const sun = rgb565(246, 200, 140), cx = 110 * size / 144, cy = 86 * size / 144, rad = 26 * size / 144;
  for (let y = 0; y < size; y++)
    for (let x = 0; x < size; x++)
      if ((x + 0.5 - cx) ** 2 + (y + 0.5 - cy) ** 2 <= rad * rad) out[y * size + x] = sun;
  return out;
}

// Little-endian bytes of a framebuffer, the layout the emulator hashes.
export function framebufferBytes(fb) {
  const out = new Uint8Array(fb.length * 2);
  for (let i = 0; i < fb.length; i++) { out[i * 2] = fb[i] & 0xFF; out[i * 2 + 1] = fb[i] >> 8; }
  return out;
}
