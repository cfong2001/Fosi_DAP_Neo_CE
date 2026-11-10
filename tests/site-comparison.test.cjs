// Browser regression (requires Node and Playwright):
//   npm install --no-save playwright
//   npx playwright install chromium
//   node --test tests/site-comparison.test.cjs
// To use a system browser, set PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH instead.
const {test} = require('node:test');
const assert = require('node:assert/strict');
const http = require('node:http');
const fs = require('node:fs/promises');
const path = require('node:path');
const {chromium} = require('playwright');

const docs = path.resolve(__dirname, '../docs');
const types = {'.html': 'text/html', '.css': 'text/css', '.js': 'text/javascript', '.mjs': 'text/javascript'};

async function serveDocs(t) {
  const server = http.createServer(async (req, res) => {
    const name = req.url === '/' ? 'index.html' : req.url.slice(1);
    if (!/^[\w.-]+$/.test(name)) { res.writeHead(404).end(); return; }
    try {
      const data = await fs.readFile(path.join(docs, name));
      res.writeHead(200, {'content-type': types[path.extname(name)] || 'application/octet-stream'}).end(data);
    } catch { res.writeHead(404).end(); }
  });
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  t.after(() => server.close());
  const executablePath = process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH || undefined;
  const browser = await chromium.launch({executablePath, headless: true});
  t.after(() => browser.close());
  return {browser, url: `http://127.0.0.1:${server.address().port}/`};
}

test('comparison synchronizes controls and fits desktop and mobile', async t => {
  const {browser, url} = await serveDocs(t);
  const page = await browser.newPage({viewport: {width: 1440, height: 1000}});
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.goto(url);
  // The theme studio and builder sit in the collapsed Advanced section.
  await page.waitForSelector('#stock-screen [data-stock-id=track-title]', {state: 'attached'});
  assert.equal(await page.locator('#advanced[open]').count(), 0);
  await page.locator('#advanced > summary').click();
  await page.waitForSelector('#stock-screen [data-stock-id=track-title]');
  const titles = () => page.locator('#stock-screen [data-stock-id=track-title], #track-title').allTextContents();
  assert.equal(new Set(await titles()).size, 1);
  await page.locator('#next-track').focus();
  await page.keyboard.press('Enter');
  assert.equal(new Set(await titles()).size, 1);
  assert.match((await titles())[0], /Night Drive/);
  await page.locator('#toggle-play').click();
  assert.equal(await page.locator('#toggle-play').getAttribute('aria-label'), 'Resume simulated playback');
  assert.equal(await page.locator('#stock-screen [data-stock-id=play-indicator].is-playing').count(), 0);
  await page.locator('[data-show=library]').click();
  assert.equal(await page.locator('.screen-panel[data-panel=library].active').count(), 2);
  await page.locator('[data-show=playing]').click();
  await page.locator('#theater-preview').check();
  assert.equal(await page.locator('#stock-screen.theater').count(), 0);
  assert.equal(await page.locator('#screen.theater').count(), 1);
  const ids = await page.locator('[id]').evaluateAll(nodes => nodes.map(node => node.id));
  assert.equal(new Set(ids).size, ids.length, 'all IDs are unique');
  for (const width of [1440, 375]) {
    await page.setViewportSize({width, height: 900});
    assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), `no horizontal overflow at ${width}px`);
  }
  assert.deepEqual(errors, []);
});

// Release files are served from the local checkout in place of
// raw.githubusercontent.com, and the drive picker is replaced by the
// browser's origin-private file system, a real FileSystemDirectoryHandle.
test('install flow verifies, copies and downloads release images', async t => {
  const {browser, url} = await serveDocs(t);
  const release = path.resolve(__dirname, '../release');
  const context = await browser.newContext({acceptDownloads: true, viewport: {width: 1280, height: 900}});
  t.after(() => context.close());
  const fetched = [];
  let tamper = false;
  await context.route('https://raw.githubusercontent.com/**', async route => {
    const name = new URL(route.request().url()).pathname.split('/').pop();
    fetched.push(route.request().url());
    try {
      const body = await fs.readFile(path.join(release, name));
      if (tamper) body[body.length - 1] ^= 1;
      await route.fulfill({status: 200, body, headers: {'access-control-allow-origin': '*', 'content-type': 'application/octet-stream'}});
    } catch { await route.fulfill({status: 404, body: 'not found'}); }
  });
  await context.addInitScript(() => {
    window.showDirectoryPicker = async () => {
      const root = await navigator.storage.getDirectory();
      return root.getDirectoryHandle('player', {create: true});
    };
  });
  const page = await context.newPage();
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.goto(url);
  const radios = page.locator('#image-choices input[type=radio]');
  assert.equal(await radios.count(), 3);
  assert.ok(await page.locator('#image-choices input[value=standard]').isChecked());
  assert.ok(await page.locator('#copy-to-player').isVisible());
  assert.equal(await page.locator('#direct-links a').count(), 4);

  // Copy the standard image to the "player".
  await page.locator('#copy-to-player').click();
  await page.waitForSelector('#install-status.good, #install-status.bad', {timeout: 60000});
  const status = await page.locator('#install-status').textContent();
  assert.match(status, /Copied DP3_V137_CE\.img .* as RKNANOFWIMG .*SHA-256 matches/);
  assert.match(fetched[0], /^https:\/\/raw\.githubusercontent\.com\/cfong2001\/Fosi_DAP_Neo_CE\/main\/release\/DP3_V137_CE\.img$/);
  const written = await page.evaluate(async () => {
    const dir = await (await navigator.storage.getDirectory()).getDirectoryHandle('player');
    const file = await (await dir.getFileHandle('RKNANOFWIMG')).getFile();
    const digest = await crypto.subtle.digest('SHA-256', await file.arrayBuffer());
    return {size: file.size, hash: Array.from(new Uint8Array(digest), b => b.toString(16).padStart(2, '0')).join('')};
  });
  assert.deepEqual(written, {size: 13638454, hash: '4d993e89bb3cdd22befb28efab0998f18acb2f56d7c0019c5dfa672c9f4de50d'});

  // Download the minimal image under the update name.
  await page.locator('#image-choices input[value=minimal]').check();
  const [download] = await Promise.all([
    page.waitForEvent('download'),
    page.locator('#download-update-name').click(),
  ]);
  assert.equal(download.suggestedFilename(), 'RKNANOFWIMG');
  const saved = await fs.readFile(await download.path());
  assert.equal(require('node:crypto').createHash('sha256').update(saved).digest('hex'),
    '623214370755053ed69dc53f0c7ae5ec0504bcb3e9ca6f2766cc9e9049101090');

  // A tampered recovery image is refused and nothing new is written.
  tamper = true;
  await page.locator('#image-choices input[value=recovery]').check();
  await page.locator('#download-image').click();
  await page.waitForSelector('#install-status.bad', {timeout: 60000});
  assert.match(await page.locator('#install-status').textContent(), /DP3_V137_CE_recovery\.img has SHA-256 [0-9a-f]{64}, expected aff851b3.*refused/);

  // A build from the Advanced section becomes a fourth, selected choice.
  await page.evaluate(async () => {
    const bytes = new Uint8Array([1, 2, 3, 4]);
    const digest = await crypto.subtle.digest('SHA-256', bytes);
    const sha256 = Array.from(new Uint8Array(digest), b => b.toString(16).padStart(2, '0')).join('');
    window.dispatchEvent(new CustomEvent('ce-build', {detail: {name: 'DP3_V137_CE_builder.img', bytes, sha256}}));
  });
  assert.ok(await page.locator('#image-choices input[value=custom]').isChecked());
  await page.locator('#copy-to-player').click();
  await page.waitForFunction(() => /Copied DP3_V137_CE_builder\.img/.test(document.querySelector('#install-status').textContent));
  assert.equal(await page.evaluate(async () => {
    const dir = await (await navigator.storage.getDirectory()).getDirectoryHandle('player');
    return (await (await dir.getFileHandle('RKNANOFWIMG')).getFile()).size;
  }), 4);

  // Links into the builder open the Advanced section.
  await page.evaluate(() => { location.hash = 'firmware-features'; });
  await page.waitForSelector('#advanced[open]');
  for (const width of [1280, 375]) {
    await page.setViewportSize({width, height: 900});
    assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), `no horizontal overflow at ${width}px`);
  }
  assert.deepEqual(errors, []);
});

test('without a drive picker the page offers downloads only', async t => {
  const {browser, url} = await serveDocs(t);
  const context = await browser.newContext();
  t.after(() => context.close());
  await context.addInitScript(() => { delete window.showDirectoryPicker; });
  const page = await context.newPage();
  await page.goto(url);
  await page.waitForSelector('#image-choices input');
  assert.ok(await page.locator('#copy-to-player').isHidden());
  assert.ok(await page.locator('#download-update-name').isVisible());
  assert.match(await page.locator('#copy-support').textContent(), /cannot write to a drive directly/);
});
