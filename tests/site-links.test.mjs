// The site's links into this repository (docs/index.html [data-repo-path]
// and the builder checklist's `patch` paths) must name files and folders that
// exist, and every linked folder must have a README so GitHub shows its
// documentation rather than a bare file list.
//   node --test tests/site-links.test.mjs
import {test} from "node:test";
import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";
import {existsSync, statSync} from "node:fs";
import {fileURLToPath} from "node:url";
import path from "node:path";
import {githubUrl, repoFromLocation} from "../docs/repo.mjs";
import {DEFAULT_REPO, RELEASE_REF} from "../docs/install-data.mjs";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const html = await readFile(path.join(root, "docs/index.html"), "utf8");
const builder = await readFile(path.join(root, "docs/builder.js"), "utf8");

const pageLinks = [...html.matchAll(/<a\s[^>]*?href="([^"]*)"[^>]*?data-repo-path="([^"]*)"[^>]*>/g)]
  .map(([, href, repoPath]) => ({href, repoPath}));
const featurePaths = [...builder.matchAll(/\bpatch: "([^"]+)"/g)].map(m => m[1]);

test("the page and the builder link the repository", () => {
  assert.ok(pageLinks.length >= 20, `page links: ${pageLinks.length}`);
  assert.ok(featurePaths.length >= 12, `feature links: ${featurePaths.length}`);
});

test("every linked path exists, and every linked folder has a README", () => {
  for (const p of [...pageLinks.map(l => l.repoPath), ...featurePaths]) {
    if (!p) continue;
    const full = path.join(root, p);
    assert.ok(existsSync(full), `${p} does not exist`);
    if (statSync(full).isDirectory())
      assert.ok(existsSync(path.join(full, "README.md")), `${p} has no README.md`);
  }
});

test("no repository link is hard-coded past the resolver", () => {
  const anchors = [...html.matchAll(/<a\s[^>]*href="https:\/\/github\.com\/[^"]*"[^>]*>/g)].map(m => m[0]);
  const repoAnchors = anchors.filter(a => a.includes(`github.com/${DEFAULT_REPO}`));
  for (const a of repoAnchors) assert.match(a, /data-repo-path=/, a);
  // The static href is the no-script fallback: the resolver's own answer.
  for (const {href, repoPath} of pageLinks) assert.equal(href, githubUrl(DEFAULT_REPO, repoPath), repoPath);
});

test("links follow the site's repository and ref", () => {
  const fork = repoFromLocation({hostname: "someone.github.io", pathname: "/my-fork/"});
  assert.equal(fork, "someone/my-fork");
  assert.equal(githubUrl(fork, "patches/sort_keys/"), `https://github.com/someone/my-fork/tree/${RELEASE_REF}/patches/sort_keys`);
  assert.equal(githubUrl(fork, "patches/gapless"), `https://github.com/someone/my-fork/tree/${RELEASE_REF}/patches/gapless`);
  assert.equal(githubUrl(fork, "patches/vorbis_swap/DEPENDENCY.md"), `https://github.com/someone/my-fork/blob/${RELEASE_REF}/patches/vorbis_swap/DEPENDENCY.md`);
  assert.equal(githubUrl(fork, ""), "https://github.com/someone/my-fork");
  assert.equal(repoFromLocation({hostname: "127.0.0.1", pathname: "/"}), DEFAULT_REPO);
});
