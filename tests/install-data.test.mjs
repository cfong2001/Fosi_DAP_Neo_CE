// The install flow's pins (docs/install-data.mjs) must describe the
// committed release set exactly: same files, lengths and SHA-256 values
// as release/SHA256SUMS and the images themselves.
//   node --test tests/install-data.test.mjs
import {test} from "node:test";
import assert from "node:assert/strict";
import {readFile, stat} from "node:fs/promises";
import {createHash} from "node:crypto";
import {fileURLToPath} from "node:url";
import path from "node:path";
import {IMAGES, UPDATE_NAME, RELEASE_DIR} from "../docs/install-data.mjs";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const release = path.join(root, RELEASE_DIR);

async function sums() {
  const text = await readFile(path.join(release, "SHA256SUMS"), "utf8");
  const map = new Map();
  for (const line of text.trim().split("\n")) {
    const [hash, name] = line.trim().split(/\s+\*?/);
    map.set(name, hash);
  }
  return map;
}

test("install pins match release/SHA256SUMS one for one", async () => {
  const pinned = await sums();
  assert.deepEqual(new Set(IMAGES.map(i => i.file)), new Set(pinned.keys()));
  for (const image of IMAGES) assert.equal(image.sha256, pinned.get(image.file), image.file);
});

test("install pins match the committed images", async () => {
  for (const image of IMAGES) {
    const file = path.join(release, image.file);
    assert.equal((await stat(file)).size, image.length, image.file + " length");
    const hash = createHash("sha256").update(await readFile(file)).digest("hex");
    assert.equal(hash, image.sha256, image.file + " SHA-256");
  }
});

test("image ids are unique and the update name encodes the stock FAT short name", () => {
  assert.equal(new Set(IMAGES.map(i => i.id)).size, IMAGES.length);
  assert.ok(!IMAGES.some(i => i.id === "custom"), "custom is reserved for builds");
  const [base, extension] = UPDATE_NAME.split(".");
  assert.equal(base.length, 8);
  assert.equal(extension.length, 3);
  assert.equal(base + extension, "RKNANOFWIMG");
});
