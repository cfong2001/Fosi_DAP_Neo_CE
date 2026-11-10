// Preview-only theater color selection. Input is local RGBA image data.
// The resulting ground is quantized to the device's RGB565 colors before
// choosing foreground and stroke, so the reported contrast uses its colors.
import {rgb565, rgb888} from "./theme-core.mjs";

const hex = rgb => "#" + rgb.map(v => v.toString(16).padStart(2, "0")).join("");
const linear = v => {
  const c = v / 255;
  return c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4;
};
export function luminance(rgb) {
  return 0.2126 * linear(rgb[0]) + 0.7152 * linear(rgb[1]) + 0.0722 * linear(rgb[2]);
}
export function contrast(a, b) {
  const x = luminance(a), y = luminance(b);
  return (Math.max(x, y) + 0.05) / (Math.min(x, y) + 0.05);
}

// First third of source rows, rounded up so small images include a row.
export function topThirdRegions(width, height) {
  if (!Number.isSafeInteger(width) || !Number.isSafeInteger(height) ||
      width < 1 || height < 1 || width > 8192 || height > 8192)
    throw new Error("Artwork dimensions must be between 1 and 8192 pixels");
  return [{x: 0, y: 0, width, height: Math.ceil(height / 3)}];
}

function colorsForGround(background, preferred = null) {
  const white = [255, 255, 255], black = [0, 0, 0];
  const whiteContrast = contrast(white, background), blackContrast = contrast(black, background);
  const foreground = preferred === "white" ? white : preferred === "black" ? black :
                     whiteContrast >= blackContrast ? white : black;
  return {background: hex(background), text: hex(foreground),
          stroke: hex(foreground === white ? black : white),
          contrast: foreground === white ? whiteContrast : blackContrast};
}

export function fallbackTheater(background) {
  return colorsForGround(rgb888(rgb565(background)));
}

export function theaterFromSums(totals, weight, light = false) {
  if (!weight) throw new Error("Artwork has no visible pixels");
  const mix = light ? 0.75 : 0.55;
  const target = light ? [242, 237, 230] : [0, 0, 0];
  const mixed = totals.map((sum, c) => Math.round((sum / weight) * (1 - mix) + target[c] * mix));
  return colorsForGround(rgb888(rgb565(hex(mixed))), light ? "black" : "white");
}

export function theaterColors(rgba, light = false) {
  if (!rgba || rgba.length % 4 !== 0) throw new Error("Invalid artwork pixels");
  const totals = [0, 0, 0];
  let weight = 0;
  for (let i = 0; i < rgba.length; i += 4) {
    const a = rgba[i + 3];
    weight += a;
    for (let c = 0; c < 3; c++) totals[c] += rgba[i + c] * a;
  }
  return theaterFromSums(totals, weight, light);
}
