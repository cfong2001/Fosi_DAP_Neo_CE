// CE builder engine: a browser-side port of patches/framework/build.py.
//
// Every step mirrors the Python framework's behaviour at this revision:
//   * the input is gated on the pinned stock SHA-256 before any byte
//     is interpreted;
//   * byte patches apply in manifest order, each checked against the
//     bytes the previous patches left (patch 0026, the gapless ARM,
//     intentionally rewrites two bytes inside patch 0022's cave and
//     is guarded by its own expect check, exactly as in build.py;
//     byte patches therefore do not refuse each other's ranges);
//   * the vorbis75 transplant applies as the range writes it reduces
//     to (the transplant's output differs from stock in exactly these
//     ranges), refuses any overlap with a byte patch range, and is
//     pinned by a SHA-256 of the transplanted module 75 segments;
//   * a theme config applies with build.py --theme-config semantics:
//     exact pixel counts, guard words refused, non-empty literal_sites
//     refused, runs edits checked against expected bytes, and no
//     overlap with any earlier modification or within the theme;
//   * finalisation stamps the BCD header date (stock + 1 day,
//     2026-10-23), re-syncs the duplicate header from the offset at
//     0x1F4, recomputes the trailer CRC, and validates the package.
//
// tests/builder.test.mjs proves byte equality with build.py's own
// outputs for the supported subsets. Nothing here flashes a device.
import {STOCK_SHA256, ROLES, GUARD_WORDS, rgb565, asWord} from "./theme-core.mjs";

export const BUILD_DATE = "20261023";
export const STOCK_SIZE = 0xD00004;

const MODULE_FIELDS = ["code_load", "code_exec", "code_len",
  "data_load", "data_exec", "data_len", "bss_exec", "bss_len"];

export function hexToBytes(hex) {
  if (typeof hex !== "string" || hex.length % 2 || /[^0-9a-fA-F]/.test(hex))
    throw new Error("invalid hex string");
  const out = new Uint8Array(hex.length / 2);
  for (let i = 0; i < out.length; i++)
    out[i] = parseInt(hex.slice(2 * i, 2 * i + 2), 16);
  return out;
}

export function bytesToHex(bytes) {
  return [...bytes].map(b => b.toString(16).padStart(2, "0")).join("");
}

function u32(bytes, off) {
  return new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength)
    .getUint32(off, true);
}

// Rockchip trailer CRC: MSB-first CRC-32, polynomial 0x04C10DB7,
// init 0, no final XOR (tools/rknano_image.py rk_crc32).
const CRC_TABLE = (() => {
  const table = new Uint32Array(256);
  for (let n = 0; n < 256; n++) {
    let v = (n << 24) >>> 0;
    for (let i = 0; i < 8; i++)
      v = ((v << 1) ^ (v & 0x80000000 ? 0x04C10DB7 : 0)) >>> 0;
    table[n] = v;
  }
  return table;
})();

export function rkCrc32(bytes) {
  let crc = 0;
  for (let i = 0; i < bytes.length; i++)
    crc = (((crc << 8) >>> 0) ^ CRC_TABLE[((crc >>> 24) ^ bytes[i]) & 0xFF]) >>> 0;
  return crc >>> 0;
}

// firmware_patch.bcd_date(): the year and the month/day groups are
// each parsed as hexadecimal and packed as little-endian halfwords.
export function bcdDate(date) {
  const y = parseInt(date.slice(0, 4), 16);
  const rest = parseInt(date.slice(4), 16);
  return new Uint8Array([y & 0xFF, (y >>> 8) & 0xFF,
                         rest & 0xFF, (rest >>> 8) & 0xFF]);
}

export function parseModules(bytes) {
  const view = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
  const base = view.getUint32(0x200, true);
  const count = view.getUint32(0x204, true);
  const modules = [];
  for (let i = 0; i < count; i++) {
    const m = {index: i};
    MODULE_FIELDS.forEach((field, j) =>
      m[field] = view.getUint32(0x208 + i * 32 + j * 4, true));
    modules.push(m);
  }
  return {base, modules};
}

function moduleRegion(bytes, base, modules, index, kind) {
  const m = modules[index];
  const length = m[kind + "_len"];
  const off = m[kind + "_load"] - base + 0x200;
  if (length && (off < 0 || off + length > bytes.length))
    throw new Error("module " + index + " " + kind + " outside image");
  return {off, length};
}

// firmware_patch.validate() + the RKnanoFW header checks.
export function validatePackage(bytes, growth = 0) {
  const fail = msg => { throw new Error("package validation failed: " + msg); };
  if (bytes.length < 0x400) fail("image too small");
  const ascii = (off, len) =>
    String.fromCharCode(...bytes.subarray(off, off + len));
  if (ascii(0x10, 8) !== "Rockchip" || ascii(0x1F8, 8) !== "RKnanoFW")
    fail("not an RKnanoFW image");
  const {modules} = parseModules(bytes);
  const mirrorOff = u32(bytes, 0x1F4);
  const mirrorValid = bytes.subarray(0, 0x200)
    .every((b, i) => b === bytes[mirrorOff + i]);
  if (!mirrorValid) fail("header mirror mismatch");
  if (mirrorOff % 0x200) fail("header mirror is not sector aligned");
  if (u32(bytes, bytes.length - 4) !== rkCrc32(bytes.subarray(0, bytes.length - 4)))
    fail("trailer CRC mismatch");
  if (bytes.length !== STOCK_SIZE + growth || mirrorOff !== 0xC94000 + growth || modules.length !== 82)
    fail("input is not a V137-layout update package");
  const {base} = parseModules(bytes);
  for (const m of modules) for (const kind of ["code", "data"])
    moduleRegion(bytes, base, modules, m.index, kind);
}

function applyModulePatch(bytes, base, modules, patch) {
  const m = modules[patch.module];
  const region = patch.region;
  const expect = hexToBytes(patch.expect);
  const replace = hexToBytes(patch.replace);
  const rel = patch.address - m[region + "_exec"];
  if (rel < 0 || rel + replace.length > m[region + "_len"])
    throw new Error("patch " + patch.name + ": crosses module boundary");
  const {off: regionOff} = moduleRegion(bytes, base, modules, patch.module, region);
  const off = regionOff + rel;
  for (let i = 0; i < expect.length; i++)
    if (bytes[off + i] !== expect[i])
      throw new Error("patch " + patch.name +
        ": stock byte precondition mismatch at module " + patch.module +
        " " + region + " 0x" + patch.address.toString(16) +
        " (file 0x" + off.toString(16) + "): expected " + patch.expect +
        ", found " + bytesToHex(bytes.subarray(off, off + expect.length)));
  bytes.set(replace, off);
  return [off, off + replace.length - 1];
}

function rangesOverlap(a, b) { return a[0] <= b[1] && b[0] <= a[1]; }

// ---- theme step (port of build.py parse_theme_config + apply_theme)

// build.py CODE_COLOUR_SITES: role -> [stock imm16, [palette routine,
// clock painter]] movw r0 sites in module 0. Both sites or neither.
export const CODE_COLOUR_SITES = {
  accent_light: [0xfb20, [0x030655da, 0x03065f4a]],
  line_light:   [0xef7d, [0x030655e2, 0x03065f52]],
  accent_dark:  [0xf220, [0x030655f0, 0x03065f90]],
  line_dark:    [0x1082, [0x030655f8, 0x03065f98]],
};
export function movwR0(word) {
  const hw1 = 0xf240 | ((word >> 1) & 0x400) | (word >> 12);
  const hw2 = (((word >> 8) & 7) << 12) | (word & 0xff);
  return Uint8Array.of(hw1 & 0xff, hw1 >> 8, hw2 & 0xff, hw2 >> 8);
}
export function movwR0Imm(b) {
  const hw1 = b[0] | (b[1] << 8), hw2 = b[2] | (b[3] << 8);
  if ((hw1 & 0xfbf0) !== 0xf240 || (hw2 & 0x8f00) !== 0) return null;
  return ((hw1 & 0xf) << 12) | (((hw1 >> 10) & 1) << 11) |
    (((hw2 >> 12) & 7) << 8) | (hw2 & 0xff);
}

function parseThemeConfig(config) {
  if (!config || typeof config !== "object" || config.version !== 1)
    throw new Error("theme: config must be a version 1 theme document");
  const literalSites = config.literal_sites ?? [];
  if (!Array.isArray(literalSites))
    throw new Error("theme: literal_sites must be an array");
  if (literalSites.length)
    throw new Error("theme: literal_sites are not accepted by the build: " +
      "the APPROVED_LITERAL_SITES registry in tools/ui_theme.py is empty " +
      "at this revision, so no literal site is approved for patching");
  const paletteWords = {};
  if (config.palette !== undefined && config.palette !== null) {
    const palette = config.palette;
    const keys = Object.keys(palette);
    if (keys.length !== ROLES.length || !ROLES.every(r => typeof palette[r] === "string"))
      throw new Error("theme: palette must define exactly the five roles " +
        ROLES.join(", "));
    for (const role of ROLES) paletteWords[role] = rgb565(palette[role]);
  }
  const resources = config.resources ?? [];
  if (!Array.isArray(resources))
    throw new Error("theme: resources must be an array");
  const rules = [];
  const seen = new Set();
  for (const rule of resources) {
    if (!rule || typeof rule !== "object")
      throw new Error("theme: resource rule must be an object");
    const rid = rule.id, role = rule.role;
    if (!Number.isInteger(rid) || rid < 0)
      throw new Error("theme: resource id " + rid + " is not a valid id");
    if (!ROLES.includes(role))
      throw new Error("theme: unknown colour role " + role);
    if (!(role in paletteWords))
      throw new Error("theme: resource rule for asset " + rid + " names role " +
        role + " but the config carries no palette");
    const source = asWord(rule.source);
    if (GUARD_WORDS.has(source))
      throw new Error("theme: resource rule for asset " + rid +
        " uses reserved colour 0x" + source.toString(16) +
        "; the guard words 0x0000 and 0x00F8 are blocked as replacement sources");
    const count = rule.expected_count;
    if (!Number.isInteger(count) || count <= 0)
      throw new Error("theme: resource rule for asset " + rid +
        " must specify an exact expected_count");
    const key = rid + ":" + source;
    if (seen.has(key))
      throw new Error("theme: duplicate resource rule for asset " + rid +
        " source 0x" + source.toString(16));
    seen.add(key);
    rules.push({id: rid, role, source, expected_count: count});
  }
  const rawRuns = config.runs ?? [];
  if (!Array.isArray(rawRuns))
    throw new Error("theme: runs must be an array");
  const runs = [];
  for (const run of rawRuns) {
    if (!run || typeof run !== "object")
      throw new Error("theme: run must be an object");
    let off = run.offset;
    if (typeof off === "string" && /^0x[0-9a-fA-F]+$/.test(off))
      off = parseInt(off, 16);
    if (!Number.isInteger(off) || off < 0)
      throw new Error("theme: run offset " + run.offset + " is not a valid file offset");
    const expect = hexToBytes(run.expect);
    const replace = hexToBytes(run.replace);
    if (!expect.length || expect.length !== replace.length)
      throw new Error("theme: run expect/replace must be equal, non-zero length");
    runs.push({offset: off, expect, replace});
  }
  const codeColours = config.code_colours ?? {};
  if (typeof codeColours !== "object" || Array.isArray(codeColours))
    throw new Error("theme: code_colours must be an object");
  const codeWords = {};
  for (const [role, value] of Object.entries(codeColours)) {
    if (!(role in CODE_COLOUR_SITES))
      throw new Error("theme: unknown code colour " + role + "; use " +
        Object.keys(CODE_COLOUR_SITES).join(", "));
    codeWords[role] = rgb565(value);
  }
  return {paletteWords, resources: rules, runs, codeWords};
}

function rock26Resources(bytes) {
  const view = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
  if (bytes.length < 0x154)
    throw new Error("theme: image too small to carry a resource section");
  const start = view.getUint32(0x14C, true);
  const length = view.getUint32(0x150, true);
  const signature = String.fromCharCode(...bytes.subarray(start, start + 16));
  if (length < 0x20 || start + length > bytes.length ||
      signature !== "ROCK26IMAGERES  ")
    throw new Error("theme: ROCK26 image resource section not found");
  const count = view.getUint32(start + 16, true);
  if (0x20 + count * 16 > length)
    throw new Error("theme: ROCK26 resource table overruns its section");
  const entries = [];
  for (let i = 0; i < count; i++) {
    const rec = start + 0x20 + i * 16;
    const w = view.getUint16(rec, true), h = view.getUint16(rec + 2, true);
    const size = view.getUint32(rec + 8, true);
    const off = view.getUint32(rec + 12, true);
    if (size !== w * h * 2 || off + size > length)
      throw new Error("theme: resource " + i +
        " is not a raw RGB565 bitmap inside the section");
    entries.push({id: i, width: w, height: h, size, data_offset: start + off});
  }
  return entries;
}

function applyTheme(bytes, config, claimedRanges) {
  const cfg = parseThemeConfig(config);
  const entries = rock26Resources(bytes);
  const claimed = claimedRanges.map(r => [...r]);
  const taken = new Set();
  for (const [s, e] of claimed)
    for (let b = s; b <= e; b++) taken.add(b);
  const claim = (rng, what) => {
    for (let b = rng[0]; b <= rng[1]; b++) {
      if (taken.has(b))
        throw new Error("theme: " + what + " range 0x" + rng[0].toString(16) +
          "..0x" + rng[1].toString(16) +
          " overlaps an earlier modification at 0x" + b.toString(16));
      taken.add(b);
    }
    claimed.push(rng);
  };
  const recRules = [];
  for (const rule of cfg.resources) {
    if (rule.id >= entries.length)
      throw new Error("theme: resource id " + rule.id + " outside the image's " +
        entries.length + " resources");
    const ent = entries[rule.id];
    const base = ent.data_offset, size = ent.size;
    const srcLo = rule.source & 0xFF, srcHi = (rule.source >>> 8) & 0xFF;
    const target = cfg.paletteWords[rule.role];
    const hits = [];
    for (let i = 0; i < size / 2; i++) {
      const off = base + 2 * i;
      if (bytes[off] === srcLo && bytes[off + 1] === srcHi) hits.push(off);
    }
    if (hits.length !== rule.expected_count)
      throw new Error("theme: resource " + rule.id + ": expected " +
        rule.expected_count + " pixels of 0x" + rule.source.toString(16) +
        ", found " + hits.length + "; refusing (the theme was exported " +
        "against a different image)");
    let start = null, prev = null;
    for (const off of hits) {
      if (start === null) { start = prev = off; }
      else if (off === prev + 2) { prev = off; }
      else { claim([start, prev + 1], "resource " + rule.id + " recolour"); start = prev = off; }
    }
    if (start !== null) claim([start, prev + 1], "resource " + rule.id + " recolour");
    // The source is named little-endian (the studio's convention), but
    // the panel shows stored bytes big-endian, so write the palette
    // colour big-endian, as patches/framework/build.py does.
    for (const off of hits) {
      bytes[off] = (target >>> 8) & 0xFF;
      bytes[off + 1] = target & 0xFF;
    }
    recRules.push({asset: rule.id, role: rule.role, count: hits.length});
  }
  const recCode = [];
  const {base, modules} = parseModules(bytes);
  const mod0 = modules[0];
  const code0 = moduleRegion(bytes, base, modules, 0, "code");
  for (const [role, [stock, sites]] of Object.entries(CODE_COLOUR_SITES)) {
    if (!(role in cfg.codeWords)) continue;
    const word = cfg.codeWords[role];
    for (const addr of sites) {
      const rel = addr - mod0.code_exec;
      if (rel < 0 || rel > code0.length - 4)
        throw new Error("theme: code colour site 0x" + addr.toString(16) +
          " is outside module 0 code");
      const off = code0.off + rel;
      if (movwR0Imm(bytes.subarray(off, off + 4)) !== stock)
        throw new Error("theme: code colour " + role + " at 0x" + addr.toString(16) +
          ": expected movw r0, #0x" + stock.toString(16) + ", found " +
          bytesToHex(bytes.subarray(off, off + 4)) + "; refusing");
      claim([off, off + 3], "code colour " + role);
      bytes.set(movwR0(word), off);
    }
    recCode.push({role, stock, target: word});
  }
  const recRuns = [];
  for (const run of cfg.runs) {
    const {offset: off, expect, replace} = run;
    if (off + expect.length > bytes.length)
      throw new Error("theme: run at 0x" + off.toString(16) + " overruns the image");
    claim([off, off + expect.length - 1], "run");
    for (let i = 0; i < expect.length; i++)
      if (bytes[off + i] !== expect[i])
        throw new Error("theme: run at 0x" + off.toString(16) +
          ": expected bytes mismatch: expected " + bytesToHex(expect) +
          ", found " + bytesToHex(bytes.subarray(off, off + expect.length)));
    bytes.set(replace, off);
    recRuns.push({file_offset: off, bytes: expect.length});
  }
  const record = {
    resources: recRules, runs: recRuns, code_colours: recCode,
    pixels_changed: recRules.reduce((n, r) => n + r.count, 0),
    bytes_changed: 2 * recRules.reduce((n, r) => n + r.count, 0) +
      recRuns.reduce((n, r) => n + r.bytes, 0) + 8 * recCode.length,
  };
  return {record, claimed};
}

// Append to a module's code segment after the stock-layout patches
// have been applied. This preserves their stock file offsets while
// shifting the resulting bytes and metadata exactly as the
// framework's insertion step (tools/insert_rebuild.py) does.
// Multiple growths compose by applying this once per module; each
// call re-reads the module table the previous calls updated.
export function growModule(bytes, index, payload, maxPayload = 0x10000) {
  if (!(payload instanceof Uint8Array) || !payload.length || payload.length > maxPayload)
    throw new Error("module " + index + " extension must contain 1 to " +
      maxPayload + " bytes");
  const {base, modules} = parseModules(bytes);
  const target = modules[index];
  const address = target.code_load + target.code_len;
  const pos = address - base + 0x200;
  if (pos < 0x208 + modules.length * 32 || pos > bytes.length - 4)
    throw new Error("module " + index + " insertion outside payload area");
  const out = new Uint8Array(bytes.length + payload.length);
  out.set(bytes.subarray(0, pos));
  out.set(payload, pos);
  out.set(bytes.subarray(pos), pos + payload.length);
  const view = new DataView(out.buffer);
  for (const m of modules) {
    for (const [field, offset] of [["code_load", 0], ["data_load", 12]]) {
      if (m.index === index && field === "code_load") continue;
      if (m[field] >= address)
        view.setUint32(0x208 + m.index * 32 + offset, m[field] + payload.length, true);
    }
  }
  view.setUint32(0x208 + index * 32 + 8, target.code_len + payload.length, true);
  for (const off of [0x70, 0x78, 0x80, 0xCC, 0xF8, 0x14C, 0x1F4]) {
    const value = view.getUint32(off, true);
    if (value >= pos) view.setUint32(off, value + payload.length, true);
  }
  return out;
}

// Pad zeros just before the duplicate header so its offset is a
// multiple of 512, as tools/insert_rebuild.py's align_mirror does. The
// boot validator reads the mirror at sector (u32 @ 0x1F4) >> 9 and
// compares a whole sector. The pad sits in the zero run before the
// mirror, which no field addresses; only 0x1F4 moves.
export function alignMirror(bytes) {
  const fwLen = u32(bytes, 0x1F4);
  const pad = (0x200 - fwLen % 0x200) % 0x200;
  if (!pad) return bytes;
  if (bytes.subarray(fwLen - 64, fwLen).some(b => b !== 0))
    throw new Error("bytes before the duplicate header are not zero");
  const out = new Uint8Array(bytes.length + pad);
  out.set(bytes.subarray(0, fwLen));
  out.set(bytes.subarray(fwLen), fwLen + pad);
  new DataView(out.buffer).setUint32(0x1F4, fwLen + pad, true);
  return out;
}

export function growModule31(bytes, payload) {
  return growModule(bytes, 31, payload, 7436);
}

function applyTail(bytes, payload, claimed) {
  if (!(payload instanceof Uint8Array) || !payload.length || payload.length > 0x7fc)
    throw new Error("tail payload must contain 1 to 2044 bytes");
  const {base, modules} = parseModules(bytes);
  const code = modules[0];
  const gapOff = code.code_load - base + 0x200 + code.code_len;
  const gapExec = code.code_exec + code.code_len;
  const span = 0x0307c7b0 - gapExec;
  const tailOffset = 0x0307bfb4 - gapExec;
  if (code.code_len !== 0x29c14 || span <= 0 || tailOffset < 0 ||
      tailOffset + 0x7fc !== span || gapOff + span > bytes.length)
    throw new Error("tail: unexpected module 0 gap geometry");
  if (claimed.some(r => rangesOverlap(r, [gapOff, gapOff + span - 1]) ||
                        rangesOverlap(r, [0x210, 0x213])))
    throw new Error("tail overlaps an earlier modification");
  if (bytes.subarray(gapOff, gapOff + span).some(b => b !== 0))
    throw new Error("tail: package gap is not zero");
  bytes.set(payload, gapOff + tailOffset);
  new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength)
    .setUint32(0x210, code.code_len + span, true);
}

function finalize(bytes, date, growth = 0) {
  const out = new Uint8Array(bytes);
  out.set(bcdDate(date), 0);
  const mirrorOff = u32(out, 0x1F4);
  out.set(out.subarray(0, 0x200), mirrorOff);
  const crc = rkCrc32(out.subarray(0, out.length - 4));
  new DataView(out.buffer).setUint32(out.length - 4, crc, true);
  validatePackage(out, growth);
  return out;
}

// Build one image. Options:
//   groups       Set of PATCH_GROUPS ids to apply (the fixture group
//                is always applied, as build.py's manifest does)
//   patchGroups  the PATCH_GROUPS data (docs/builder-data.mjs)
//   vorbis       null, or the VORBIS75 data (docs/builder-vorbis.mjs)
//   themeConfig  null, or a version 1 theme config object
//   ceMarkRuns   null, or the CE_MARK_RUNS data (docs/builder-cemark.mjs);
//                applied as the runs of the build's one theme config,
//                merged with themeConfig when both are given, matching
//                the single --theme-config a build.py build takes
//   growths      null, or an array of {module, payload} code-segment
//                insertions applied after the tail, mirroring
//                build.py's repeatable --grow (module31Payload is
//                the legacy single-growth form of this option)
//   sha256Hex    async (bytes) => hex digest (crypto.subtle in the
//                browser, node:crypto in the offline test)
export async function buildFirmware(stockBytes, options, sha256Hex) {
  const digest = await sha256Hex(stockBytes);
  if (digest !== STOCK_SHA256)
    throw new Error("input SHA-256 " + digest + " does not match pinned stock " +
      STOCK_SHA256 + "; refusing to build");
  validatePackage(stockBytes);
  const bytes = new Uint8Array(stockBytes);
  const {base, modules} = parseModules(bytes);

  const selected = [];
  for (const group of options.patchGroups) {
    if (group.id === "fixture" || options.groups.has(group.id))
      selected.push(...group.patches);
  }
  if (options.opus) selected.push(...options.opusPatches);
  if (options.extraPatches) selected.push(...options.extraPatches);
  selected.sort((x, y) => x.index - y.index);
  let claimed = [];
  for (const patch of selected)
    claimed.push(applyModulePatch(bytes, base, modules, patch));

  let vorbisRecord = null;
  if (options.vorbis) {
    const data = options.vorbis;
    const runRanges = [];
    for (const kind of ["code", "data"]) {
      const {off, length} = moduleRegion(bytes, base, modules, 75, kind);
      const rng = [off, off + length - 1];
      if (claimed.some(other => rangesOverlap(rng, other)))
        throw new Error("transplant vorbis75 overlaps an earlier modification");
      claimed.push(rng);
    }
    for (const run of data.ranges) {
      const replace = hexToBytes(run.replace);
      const rng = [run.offset, run.offset + replace.length - 1];
      bytes.set(replace, run.offset);
      runRanges.push(rng);
    }
    const seg = [];
    for (const kind of ["code", "data"]) {
      const {off, length} = moduleRegion(bytes, base, modules, 75, kind);
      seg.push(bytes.subarray(off, off + length));
    }
    const joined = new Uint8Array(seg[0].length + seg[1].length);
    joined.set(seg[0], 0);
    joined.set(seg[1], seg[0].length);
    const moduleHash = await sha256Hex(joined);
    if (moduleHash !== data.module75_sha256)
      throw new Error("transplant vorbis75: transplanted module 75 does not " +
        "match its pinned SHA-256; refusing to build");
    vorbisRecord = {bytes_changed: data.bytes_changed,
                    ranges: runRanges.length};
  }

  if (options.opus) {
    const data = options.opus;
    const regions = ["code", "data"].map(kind => moduleRegion(bytes, base, modules, 72, kind));
    const opusRanges = regions.map(({off, length}) => [off, off + length - 1]);
    for (const rng of opusRanges) {
      if (claimed.some(other => rangesOverlap(rng, other)))
        throw new Error("transplant opus72 overlaps an earlier modification");
      claimed.push(rng);
    }
    if (!Array.isArray(data.ranges)) throw new Error("transplant opus72: invalid range data");
    for (const run of data.ranges) {
      const replacement = hexToBytes(run.replace);
      const end = run.offset + replacement.length - 1;
      if (!Number.isSafeInteger(run.offset) || !replacement.length ||
          !opusRanges.some(([s, e]) => run.offset >= s && end <= e))
        throw new Error("transplant opus72: range outside module 72");
      bytes.set(replacement, run.offset);
    }
    const parts = regions;
    const joined = new Uint8Array(parts[0].length + parts[1].length);
    joined.set(bytes.subarray(parts[0].off, parts[0].off + parts[0].length));
    joined.set(bytes.subarray(parts[1].off, parts[1].off + parts[1].length), parts[0].length);
    if (await sha256Hex(joined) !== "6a7d50d2647c6623181e3cbbc16a13d2bd9a8724559d62c84f25b83ae8cbb07d")
      throw new Error("transplant opus72: module hash mismatch; refusing to build");
  }

  let themeRecord = null;
  let themeConfig = options.themeConfig ?? null;
  if (options.ceMarkRuns) {
    themeConfig = {...(themeConfig ?? {version: 1}),
                   runs: [...(themeConfig?.runs ?? []), ...options.ceMarkRuns]};
  }
  if (themeConfig) {
    const applied = applyTheme(bytes, themeConfig, claimed);
    themeRecord = applied.record;
    claimed = applied.claimed;
  }

  if (options.tailPayload) applyTail(bytes, options.tailPayload, claimed);
  const growths = options.growths ??
    (options.module31Payload ? [{module: 31, payload: options.module31Payload}] : []);
  let grown = bytes;
  for (const g of growths) grown = growModule(grown, g.module, g.payload);
  grown = alignMirror(grown);
  const growthTotal = grown.length - bytes.length;
  const out = finalize(grown, BUILD_DATE, growthTotal);
  let bytesChanged = growths.length ? null : 0;
  if (bytesChanged !== null)
    for (let i = 0; i < out.length; i++)
      if (out[i] !== stockBytes[i]) bytesChanged++;
  return {bytes: out,
          sha256: await sha256Hex(out),
          bytesChanged,
          patchesApplied: selected.length,
          vorbis: vorbisRecord,
          theme: themeRecord};
}
