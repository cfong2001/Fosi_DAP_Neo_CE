import test from "node:test";
import assert from "node:assert/strict";
import {theaterColors, contrast, topThirdRegions, fallbackTheater} from "../docs/theater-core.mjs";

const rgb = hex => [1, 3, 5].map(i => parseInt(hex.slice(i, i + 2), 16));

test("theater text keeps at least 4.5:1 contrast after RGB565 quantization", () => {
  // These are the worst luminance endpoints for the fixed stock text
  // colors: the lightest dark ground and the darkest light ground.
  assert.ok(theaterColors(new Uint8Array([255, 255, 255, 255]), false).contrast >= 4.5);
  assert.ok(theaterColors(new Uint8Array([0, 0, 0, 255]), true).contrast >= 4.5);
  for (const light of [false, true]) for (let r = 0; r <= 255; r += 17)
    for (let g = 0; g <= 255; g += 17) for (let b = 0; b <= 255; b += 17) {
      const result = theaterColors(new Uint8Array([r, g, b, 255]), light);
      assert.ok(contrast(rgb(result.background), rgb(result.text)) >= 4.5);
      assert.ok(contrast(rgb(result.stroke), rgb(result.text)) >= 4.5);
      assert.equal(result.text, light ? "#000000" : "#ffffff");
    }
});

test("transparent artwork contributes no color and empty artwork is refused", () => {
  const red = theaterColors(new Uint8Array([255, 0, 0, 255]));
  assert.deepEqual(theaterColors(new Uint8Array([255, 0, 0, 255, 0, 255, 0, 0])), red);
  assert.throws(() => theaterColors(new Uint8Array([255, 0, 0, 0])), /no visible pixels/);
  assert.throws(() => theaterColors(new Uint8Array([1, 2, 3])), /Invalid/);
  const fallback = fallbackTheater("#141821");
  assert.ok(contrast(rgb(fallback.background), rgb(fallback.text)) >= 4.5);
});

test("the top third uses complete rows, rounded up", () => {
  const collect = (width, height) => topThirdRegions(width, height).flatMap(r => {
    const cells = [];
    for (let y = r.y; y < r.y + r.height; y++)
      for (let x = r.x; x < r.x + r.width; x++) cells.push(`${x},${y}`);
    return cells;
  });
  for (const [width, height] of [[1, 1], [1, 5], [5, 1], [2, 2], [7, 5]]) {
    const cells = collect(width, height);
    assert.equal(new Set(cells).size, cells.length);
    assert.equal(cells.length, width * Math.ceil(height / 3));
    assert.ok(cells.every(c => {
      const [x, y] = c.split(",").map(Number);
      return x >= 0 && x < width && y >= 0 && y < Math.ceil(height / 3);
    }));
  }
  assert.throws(() => topThirdRegions(0, 1), /dimensions/);
});

test("lower rows do not affect the top-third theater color", () => {
  function topFrom(rgba, width, height) {
    const values = [];
    for (const r of topThirdRegions(width, height))
      for (let y = r.y; y < r.y + r.height; y++)
        for (let x = r.x; x < r.x + r.width; x++)
          values.push(...rgba.slice((y * width + x) * 4, (y * width + x + 1) * 4));
    return new Uint8Array(values);
  }
  const pixels = new Uint8Array(5 * 5 * 4);
  for (let i = 0; i < 25; i++) pixels.set([255, 0, 0, 255], i * 4);
  const original = theaterColors(topFrom(pixels, 5, 5));
  for (let y = 2; y < 5; y++) for (let x = 0; x < 5; x++)
    pixels.set([0, 0, 255, 255], (y * 5 + x) * 4);
  assert.deepEqual(theaterColors(topFrom(pixels, 5, 5)), original);
  pixels.set([0, 255, 0, 255], 0);
  assert.notDeepEqual(theaterColors(topFrom(pixels, 5, 5)), original);
});
