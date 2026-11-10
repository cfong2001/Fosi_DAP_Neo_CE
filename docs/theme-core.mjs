// Pure V137 parser and color transforms. No network calls or firmware writes.
export const STOCK_SHA256 = "fcc1cd3e35b46f1f8dbcb8da39fcc5eb3f1d469cdfade5e9c6ea3bd71ac6deef";
export const ROLES = ["background", "text", "highlight", "icons", "progress_bar"];
export const GUARD_WORDS = new Set([0x0000, 0x00f8]); // possible colorkeys, not proven
export const KNOWN_LABELS = new Map([
  [0, "startup/spinner artwork"], [1, "QR-code artwork"],
  [6, "battery graphic 1"], [7, "battery graphic 2"],
  [8, "battery graphic 3"], [9, "battery graphic 4"],
  [10, "battery graphic 5"],
]);

const assert = (ok, message) => { if (!ok) throw new Error(message); };
const getU16 = (view, pos) => view.getUint16(pos, true);
const getU32 = (view, pos) => view.getUint32(pos, true);
const asByteArray = (source) => source instanceof Uint8Array ? source : new Uint8Array(source);

export function rgb565(hex) {
  assert(/^#[0-9a-fA-F]{6}$/.test(hex), "Use a #RRGGBB color");
  const r = Number.parseInt(hex.slice(1, 3), 16), g = Number.parseInt(hex.slice(3, 5), 16);
  const b = Number.parseInt(hex.slice(5, 7), 16);
  return ((Math.floor((r * 31 + 127) / 255) << 11)
       | (Math.floor((g * 63 + 127) / 255) << 5)
       | Math.floor((b * 31 + 127) / 255));
}
export function rgb888(value) {
  return [Math.floor(((value >> 11) & 31) * 255 / 31),
          Math.floor(((value >> 5) & 63) * 255 / 63),
          Math.floor((value & 31) * 255 / 31)];
}
export function asWord(value) {
  const word = Number.isInteger(value) ? value :
    /^0x[0-9a-fA-F]{1,4}$/.test(value || "") ? parseInt(value, 16) : NaN;
  assert(Number.isInteger(word) && word >= 0 && word <= 65535,
         "Invalid RGB565 word; expected 0x0000 through 0xFFFF");
  return word;
}
export function wordHex(value) { return "0x" + value.toString(16).toUpperCase().padStart(4, "0"); }

export function parseFirmware(source) {
  const bytes = asByteArray(source);
  assert(bytes.byteLength === 0xD00004, "Wrong file size for stock DP3_V137.img");
  const view = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
  const ascii = (offset, length) => String.fromCharCode(...bytes.subarray(offset, offset + length));
  assert(ascii(0x10, 8) === "Rockchip", "Invalid Rockchip header");
  assert(ascii(0x1f8, 8) === "RKnanoFW", "Invalid RKnanoFW format");
  const start = getU32(view, 0x14c), length = getU32(view, 0x150);
  assert(start + length <= bytes.byteLength && length >= 0x20,
         "Image resource section outside firmware");
  assert(ascii(start, 16) === "ROCK26IMAGERES  ", "Invalid resource signature");
  const count = getU32(view, start + 16);
  assert(count === 456 && 0x20 + count * 16 <= length, "Expected 456 resource records");
  const entries = [];
  for (let id = 0; id < count; id++) {
    const p = start + 0x20 + id * 16;
    const width = getU16(view, p), height = getU16(view, p + 2);
    const x = getU16(view, p + 4), y = getU16(view, p + 6);
    const size = getU32(view, p + 8), offset = getU32(view, p + 12);
    assert(width > 0 && height > 0 && size === width * height * 2,
           "Unsupported non-RGB565 resource #" + id);
    assert(offset + size <= length, "Resource #" + id + " outside section");
    entries.push({id, width, height, x, y, size, data_offset: start + offset,
                  label: KNOWN_LABELS.get(id) || "unclassified"});
  }
  return {bytes, view, entries};
}
export async function sha256(bytes) {
  assert(globalThis.crypto?.subtle, "SHA-256 requires HTTPS or localhost");
  const digest = await crypto.subtle.digest("SHA-256", bytes);
  return Array.from(new Uint8Array(digest), v => v.toString(16).padStart(2, "0")).join("");
}
export function frequencies(firmware, asset) {
  const counts = new Map();
  const {view} = firmware;
  for (let off = asset.data_offset; off < asset.data_offset + asset.size; off += 2) {
    const w = getU16(view, off);
    counts.set(w, (counts.get(w) || 0) + 1);
  }
  return [...counts.entries()].sort((a,b) => b[1] - a[1]).map(([word, count]) =>
    ({word, count, hex: wordHex(word)}));
}
export function validateTheme(config, entries) {
  assert(config && config.version === 1, "Theme must be version 1");
  assert(config.palette && typeof config.palette === "object", "Missing palette");
  assert(Object.keys(config.palette).length === ROLES.length &&
         ROLES.every(role => typeof config.palette[role] === "string"),
         "Palette must define exactly five known roles");
  for (const role of ROLES) rgb565(config.palette[role]);
  assert(Array.isArray(config.resources) && Array.isArray(config.literal_sites),
         "resources and literal_sites must be arrays");
  const keys = new Set();
  for (const rule of config.resources) {
    assert(Number.isInteger(rule.id) && rule.id >= 0 && rule.id < entries.length,
           "Resource ID outside firmware");
    assert(ROLES.includes(rule.role), "Unknown color role");
    const source = asWord(rule.source);
    assert(Number.isInteger(rule.expected_count) && rule.expected_count > 0,
           "Resource rule must specify exact expected_count");
    assert(!GUARD_WORDS.has(source),
           "Reserved color " + wordHex(source) + " requires offline evidence and explicit opt-in");
    const key = rule.id + ":" + source;
    assert(!keys.has(key), "Duplicate resource source selection");
    keys.add(key);
  }
  return config;
}
export function rgbaPixels(firmware, asset, replacements = new Map()) {
  const arr = new Uint8ClampedArray(asset.width * asset.height * 4);
  for (let px = 0; px < asset.width * asset.height; px++) {
    const w = getU16(firmware.view, asset.data_offset + px * 2);
    const [r,g,b] = rgb888(replacements.has(w) ? replacements.get(w) : w);
    const p = px * 4;
    arr[p] = r; arr[p+1] = g; arr[p+2] = b; arr[p+3] = 255;
  }
  return arr;
}
export function exportConfig(palette, rules) {
  const resources = [...rules].sort((a,b) => a.id - b.id || asWord(a.source) - asWord(b.source));
  return {version: 1, palette: {...palette}, resources, literal_sites: []};
}
