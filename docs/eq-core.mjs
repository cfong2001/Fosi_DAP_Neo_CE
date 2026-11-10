// AutoEQ and custom curves for the stock 31-band EQ: the browser port of
// patches/eq_presets/eqfit.py. Same grid, same ridge start, same greedy
// refinement, so both produce the same integer gains
// (tests/builder.test.mjs checks this against build.py output).
import {parseModules} from "./builder-core.mjs";

export const ISO = [20, 25, 31.5, 40, 50, 63, 80, 100, 125, 160, 200, 250, 315, 400, 500,
  630, 800, 1000, 1250, 1600, 2000, 2500, 3150, 4000, 5000, 6300, 8000,
  10000, 12500, 16000, 20000];
export const SLOTS = {1: "Pop", 2: "Jazz", 3: "Rock", 4: "Classical", 5: "Bass Boost", 6: "Heavy Metal"};
const TABLE = 0x030489cc, SELECTOR = 0x0308ad08, FS = 48000, RIDGE = 0.1;
const GRID = Array.from({length: 120}, (_, i) => 20 * 2 ** (i / 12));
const TREBLE_HOLD = 16000;  // as eqfit.py: the fit holds the curve level above this

function region(bytes, index, kind) {
  const {base, modules} = parseModules(bytes);
  const m = modules[index];
  return {off: m[kind + "_load"] - base + 0x200, exec: m[kind + "_exec"]};
}

function responseDb([b0, b1, b2, a1, a2], f) {
  const w = 2 * Math.PI * f / FS, zr = Math.cos(w), zi = -Math.sin(w);
  const z2r = zr * zr - zi * zi, z2i = 2 * zr * zi;
  const nr = b0 + b1 * zr + b2 * z2r, ni = b1 * zi + b2 * z2i;
  const dr = 1 - a1 * zr - a2 * z2r, di = -a1 * zi - a2 * z2i;
  return 10 * Math.log10((nr * nr + ni * ni) / (dr * dr + di * di));
}

export function bandTable(bytes) {
  const {off} = region(bytes, 35, "data");
  const v = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
  const R = [];
  for (let b = 0; b < 31; b++) {
    const row = [];
    for (let g = 0; g < 25; g++) {
      let c;
      if (b < 10) {
        const p = off + 4 * 5000 + (b * 25 + g) * 20, q = i => v.getInt32(p + 4 * i, true) / 2 ** 20;
        c = [q(2), q(3), q(4), q(0), q(1)];
      } else {
        const p = off + 25000 + 4 * 5250 + ((b - 10) * 25 + g) * 10, q = i => v.getInt16(p + 2 * i, true) / 8192;
        const k = q(4);
        c = [k, q(2) * k, q(3) * k, q(0), q(1)];
      }
      row.push(GRID.map(f => responseDb(c, f)));
    }
    R.push(row);
  }
  return R;
}

export function parseCurve(text) {
  const m = /GraphicEQ:\s*(.*)/.exec(text);
  if (m) {
    const pts = [];
    for (const pair of m[1].split(";")) {
      const parts = pair.trim().split(/\s+/);
      if (parts.length === 2) pts.push([Number(parts[0]), Number(parts[1])]);
    }
    if (pts.length < 2) throw new Error("GraphicEQ line has fewer than two points");
    return pts.sort((a, b) => a[0] - b[0] || a[1] - b[1]);
  }
  const nums = (text.match(/[-+]?\d+(?:\.\d+)?/g) || []).map(Number);
  if (nums.length !== 31)
    throw new Error("expected an AutoEQ GraphicEQ line or 31 dB values, got " + nums.length + " numbers");
  return ISO.map((f, i) => [f, nums[i]]);
}

function targetAt(pts, f) {
  if (f <= pts[0][0]) return pts[0][1];
  if (f >= pts[pts.length - 1][0]) return pts[pts.length - 1][1];
  for (let i = 0; i + 1 < pts.length; i++) {
    const [f0, g0] = pts[i], [f1, g1] = pts[i + 1];
    if (f0 <= f && f <= f1) {
      const t = (Math.log(f) - Math.log(f0)) / (Math.log(f1) - Math.log(f0));
      return g0 + t * (g1 - g0);
    }
  }
  return pts[pts.length - 1][1];
}

// Python round(): half to even.
function pyRound(x) {
  const r = Math.round(x);
  return (Math.abs(x % 1) === 0.5 && r % 2 !== 0) ? r - 1 : r;
}
const clamp = x => Math.max(-12, Math.min(12, x)) + 0;  // + 0 turns -0 into 0

function ridgeStart(target, R) {
  const n = GRID.length;
  const A = GRID.map((_, i) => R.map(row => (row[24][i] - row[0][i]) / 24));
  const M = [], v = [];
  for (let a = 0; a < 31; a++) {
    const rowM = [];
    for (let b = 0; b < 31; b++) {
      let s = 0;
      for (let i = 0; i < n; i++) s += A[i][a] * A[i][b];
      rowM.push(s + (a === b ? RIDGE : 0));
    }
    M.push(rowM);
    let s = 0;
    for (let i = 0; i < n; i++) s += A[i][a] * target[i];
    v.push(s);
  }
  for (let c = 0; c < 31; c++) {
    let p = c;
    for (let r = c + 1; r < 31; r++) if (Math.abs(M[r][c]) > Math.abs(M[p][c])) p = r;
    [M[c], M[p]] = [M[p], M[c]];
    [v[c], v[p]] = [v[p], v[c]];
    for (let r = 0; r < 31; r++) {
      if (r === c) continue;
      const f = M[r][c] / M[c][c];
      for (let k = c; k < 31; k++) M[r][k] -= f * M[c][k];
      v[r] -= f * v[c];
    }
  }
  return v.map((x, c) => clamp(pyRound(x / M[c][c])));
}

export function fit(pts, R) {
  const target = GRID.map(f => targetAt(pts, Math.min(f, TREBLE_HOLD)));
  const gains = ridgeStart(target, R);
  let total = GRID.map((_, i) => R.reduce((s, row, b) => s + row[gains[b] + 12][i], 0));
  const err = tot => tot.reduce((s, r, i) => s + (target[i] - r) ** 2, 0);
  let best = err(total);
  for (let pass = 0; pass < 60; pass++) {
    let changed = false;
    for (let b = 0; b < 31; b++) {
      for (const step of [1, -1]) {
        const g = gains[b] + step;
        if (g < -12 || g > 12) continue;
        const trial = total.map((t, i) => t - R[b][gains[b] + 12][i] + R[b][g + 12][i]);
        const e = err(trial);
        if (e < best - 1e-9) { best = e; total = trial; gains[b] = g; changed = true; break; }
      }
    }
    if (!changed) break;
  }
  return {gains, rms: Math.sqrt(best / GRID.length), peak: Math.max(...total)};
}

const hex = bytes => [...bytes].map(b => b.toString(16).padStart(2, "0")).join("");
const packGains = gains => {
  const out = new Uint8Array(62);
  gains.forEach((g, i) => { out[2 * i] = g + 12; out[2 * i + 1] = 0; });
  return out;
};

// Byte patches for the builder engine: the selector fix plus one array per
// slot (slots maps 1..6 to 31 integer dB values). Slots left out keep what
// stock applies for that menu item.
export function slotPatches(bytes, slots) {
  const {off, exec} = region(bytes, 33, "data");
  const stock = k => bytes.subarray(off + TABLE + 62 * k - exec, off + TABLE + 62 * k - exec + 62);
  const applied = {1: stock(0), 2: stock(1), 3: stock(2), 4: stock(0), 5: stock(1),
                   6: packGains(new Array(31).fill(0))};
  const patches = [{index: 60, name: "eq-selector-distinct-presets", module: 33, region: "code",
                    address: SELECTOR, expect: "051632", replace: "0b0b0b"}];
  for (let n = 1; n <= 6; n++) {
    let next;
    if (slots[n]) {
      if (slots[n].length !== 31 || slots[n].some(g => !Number.isInteger(g) || g < -12 || g > 12))
        throw new Error("slot " + n + ": need 31 integer gains in -12..12");
      next = packGains(slots[n]);
    } else next = applied[n];
    const old = stock(n - 1);
    if (hex(next) !== hex(old))
      patches.push({index: 60 + n, name: "eq-preset-" + n, module: 33, region: "data",
                    address: TABLE + 62 * (n - 1), expect: hex(old), replace: hex(next)});
  }
  return patches;
}
