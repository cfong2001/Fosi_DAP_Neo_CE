// Run: node patches/theme_editor/test_browser.mjs
import assert from "node:assert/strict";
import {
  parseFirmware, frequencies, rgbaPixels, rgb565, rgb888,
  asWord, wordHex, validateTheme, exportConfig, GUARD_WORDS
} from "../../docs/theme-core.mjs";

const bytes = new Uint8Array(0xD00004);
const view = new DataView(bytes.buffer);
function writeText(offset, value) {
  for (let i = 0; i < value.length; i++) bytes[offset + i] = value.charCodeAt(i);
}
writeText(0x10, "Rockchip");
writeText(0x1F8, "RKnanoFW");
const section = 0x900000, count = 456;
const pixelOffset = 0x20 + 16 * count;
view.setUint32(0x14c, section, true);
view.setUint32(0x150, pixelOffset + 2 * count, true);
writeText(section, "ROCK26IMAGERES  ");
view.setUint32(section + 16, count, true);
for (let id = 0; id < count; id++) {
  const at = section + 0x20 + id * 16;
  view.setUint16(at, 1, true);
  view.setUint16(at + 2, 1, true);
  view.setUint16(at + 4, id % 24, true);
  view.setUint16(at + 6, id % 32, true);
  view.setUint32(at + 8, 2, true);
  view.setUint32(at + 12, pixelOffset + id * 2, true);
  view.setUint16(section + pixelOffset + id * 2, 0xA210, true);
}
const firmware = parseFirmware(bytes);
assert.equal(firmware.entries.length, 456);
assert.equal(firmware.entries[6].id, 6);
assert.equal(frequencies(firmware, firmware.entries[6])[0].count, 1);
assert.equal(frequencies(firmware, firmware.entries[6])[0].word, 0xA210);
assert.equal(rgbaPixels(firmware, firmware.entries[6]).length, 4);
assert.equal(rgb565("#FFFFFF"), 65535);
assert.equal(rgb565("#000000"), 0);
assert.deepEqual(rgb888(0xF800), [255, 0, 0]);
assert.equal(wordHex(asWord("0xA210")), "0xA210");
assert.equal(GUARD_WORDS.has(0x0000), true);

const palette = {
  background: "#141821", text: "#FFFFFF", highlight: "#38BDF8",
  icons: "#DCECF8", progress_bar: "#38BDF8"
};
const cfg = exportConfig(palette, [
  {id: 7, role: "icons", source: "0xA210", expected_count: 1},
  {id: 6, role: "highlight", source: "0xA210", expected_count: 1}
]);
assert.deepEqual(cfg.resources.map(x => x.id), [6, 7]);
validateTheme(cfg, firmware.entries);
assert.throws(() => validateTheme({
  ...cfg, resources: [{...cfg.resources[0], source: "0x0000"}]
}, firmware.entries), /Reserved/);
assert.throws(() => validateTheme({
  ...cfg, resources: [{...cfg.resources[0], expected_count: 0}]
}, firmware.entries), /expected_count/);
assert.throws(() => parseFirmware(new Uint8Array(1000)), /size/);
console.log("PASS: browser RGB565 transforms, 456 resources, pixel decoding and theme gates");
