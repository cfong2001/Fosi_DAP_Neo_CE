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
    const name = req.url === '/' ? 'index.html' : req.url.slice(1).split(/[?#]/)[0];
    // Files in docs/ and one level of folders (stage/stage.js), nothing else.
    if (!/^(?:[\w-]+\/)?[\w.-]+$/.test(name) || name.includes('..')) { res.writeHead(404).end(); return; }
    try {
      const data = await fs.readFile(path.join(docs, name));
      res.writeHead(200, {'content-type': types[path.extname(name)] || 'application/octet-stream'}).end(data);
    } catch { res.writeHead(404).end(); }
  });
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  t.after(() => server.close());
  const executablePath = process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH || undefined;
  const browser = await chromium.launch({executablePath, headless: true, args: ['--enable-unsafe-swiftshader']});
  t.after(() => browser.close());
  return {browser, url: `http://127.0.0.1:${server.address().port}/`};
}

// Files from raw.githubusercontent.com/<owner>/<repo>/main/<path> are
// served from the checkout, honouring single byte ranges as GitHub does.
async function serveRaw(context, onRequest = () => {}) {
  const repoRoot = path.resolve(__dirname, '..');
  await context.route('https://raw.githubusercontent.com/**', async route => {
    const url = new URL(route.request().url());
    const rel = decodeURIComponent(url.pathname).split('/').slice(4).join('/');
    const range = route.request().headers()['range'];
    onRequest({url: url.href, rel, range});
    let body;
    try { body = await fs.readFile(path.join(repoRoot, rel)); }
    catch { await route.fulfill({status: 404, body: 'not found'}); return; }
    const headers = {'access-control-allow-origin': '*', 'content-type': 'application/octet-stream'};
    const m = range && /^bytes=(\d+)-(\d+)$/.exec(range);
    if (m) {
      const a = Number(m[1]), b = Math.min(Number(m[2]), body.length - 1);
      headers['content-range'] = `bytes ${a}-${b}/${body.length}`;
      await route.fulfill({status: 206, body: body.subarray(a, b + 1), headers});
    } else await route.fulfill({status: 200, body, headers});
  });
}

const word = ([r, g, b]) => (r << 16) | (g << 8) | b;

// No horizontal page scroll; on failure, name what sticks out.
async function assertNoOverflow(page, width) {
  const report = await page.evaluate(() => {
    if (document.documentElement.scrollWidth <= innerWidth) return null;
    const out = [];
    for (const el of document.querySelectorAll('body *')) {
      const r = el.getBoundingClientRect();
      if (r.right > innerWidth + 1 && r.width > 0 && !el.parentElement?.closest('.ss-stage'))
        out.push((el.id ? '#' + el.id : el.tagName.toLowerCase() + '.' + [...el.classList].join('.')) + ' right ' + Math.round(r.right));
    }
    const first = [...document.querySelectorAll('.ss-stage')].find(el => el.getBoundingClientRect().right > innerWidth + 1);
    const chain = [];
    for (let el = first; el && el !== document.body; el = el.parentElement)
      chain.push((el.id ? '#' + el.id : el.tagName.toLowerCase() + '.' + [...el.classList].join('.')) + '[' + getComputedStyle(el).overflowX + ' ' + Math.round(el.getBoundingClientRect().right) + ']');
    return document.documentElement.scrollWidth + 'px wide: ' + out.slice(0, 8).join(', ') + ' | ' + chain.join(' < ');
  });
  assert.equal(report, null, `no horizontal overflow at ${width}px`);
}

test('simulator draws real firmware pixels for both images', async t => {
  const core = await import('../docs/sim-core.mjs');
  const {SECTIONS} = await import('../docs/sim-data.mjs');
  const images = {};
  for (const [name, pin] of Object.entries(SECTIONS)) {
    const image = await fs.readFile(path.resolve(__dirname, '..', pin.file));
    images[name] = core.parseResourceSection(new Uint8Array(image.subarray(pin.offset, pin.offset + pin.length)));
  }
  // What the page should show, composed in Node from the same images.
  const expected = (side, opts) => {
    const fb = new Uint16Array(240 * 320);
    if (opts.tab === 'splash') { core.draw(fb, images[side], 127 + (opts.light ? 166 : 0), 0, 0); return fb; }
    const art = core.sampleCover();
    const ground = side === 'ce' && opts.theater ? core.theaterGround(art, 144, 144, opts.light) : core.groundFor(opts.light);
    core.fill(fb, 0, 0, 239, 319, ground);
    core.blit(fb, art, 144, 144, 48, 36);
    core.paintPlayer(fb, images[side], side, {page: opts.page || 0, playing: opts.playing !== false, light: opts.light, ground});
    return fb;
  };
  const {browser, url} = await serveDocs(t);
  const context = await browser.newContext({viewport: {width: 1440, height: 1000}});
  t.after(() => context.close());
  const requests = [];
  await serveRaw(context, r => requests.push(r));
  const page = await context.newPage();
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.goto(url);
  // The simulator sits in the collapsed Advanced section and loads on open.
  assert.equal(await page.locator('#advanced[open]').count(), 0);
  assert.equal(requests.length, 0, 'nothing is fetched before Advanced opens');
  await page.locator('#advanced > summary').click();
  await page.waitForSelector('#sim-status.good, #sim-status.bad', {timeout: 60000});
  assert.match(await page.locator('#sim-status').textContent(), /real pixels/);
  assert.deepEqual(requests.map(r => [r.rel, r.range]).sort(), Object.values(SECTIONS).map(p =>
    [p.file, `bytes=${p.offset}-${p.offset + p.length - 1}`]).sort());

  // Rows y0..y1 of a canvas as 0xRRGGBB values; text is drawn above y = 266.
  const rows = (side, y0, y1) => page.evaluate(([id, a, b]) => {
    const d = document.getElementById(id).getContext('2d').getImageData(0, a, 240, b - a + 1).data;
    const out = [];
    for (let i = 0; i < d.length; i += 4) out.push((d[i] << 16) | (d[i + 1] << 8) | d[i + 2]);
    return out;
  }, [side + '-canvas', y0, y1]);
  const want = (fb, y0, y1) => Array.from(fb.subarray(y0 * 240, (y1 + 1) * 240), w => word(core.rgb888(w)));
  const check = async (opts, label) => {
    for (const side of ['stock', 'ce']) {
      const fb = expected(side, opts);
      // Below the progress area (rows 254..268): the knob moves with
      // simulated playback time; paintProgress has its own exact test in
      // tests/sim-core.test.mjs.
      const [y0, y1] = opts.tab === 'splash' ? [0, 319] : [269, 319];
      assert.deepEqual(await rows(side, y0, y1), want(fb, y0, y1), `${label}: ${side} pixels`);
      // A pixel beside the cover shows the ground (or the splash).
      assert.equal((await rows(side, 100, 100))[2], word(core.rgb888(fb[100 * 240 + 2])), `${label}: ${side} ground`);
    }
  };
  await check({theater: true}, 'dark, playing, theater');
  const ceGround = (await rows('ce', 100, 100))[2], stockGround = (await rows('stock', 100, 100))[2];
  assert.equal(stockGround, word(core.rgb888(0x10A2)));
  assert.notEqual(ceGround, stockGround, 'theater changes the CE ground');
  assert.match(await page.locator('#theater-status').textContent(), /CE background 0x[0-9A-F]{4}/);

  await page.locator('#toggle-play').click();
  assert.equal(await page.locator('#toggle-play').getAttribute('aria-label'), 'Resume simulated playback');
  await check({theater: true, playing: false}, 'paused');
  await page.locator('#toggle-play').click();
  await page.locator('#sim-page').selectOption('1');
  await check({theater: true, page: 1}, 'second page');
  await page.locator('#sim-page').selectOption('0');
  await page.locator('#sim-theme').selectOption('light');
  await check({theater: true, light: true}, 'light');
  await page.locator('#theater-preview').uncheck();
  await check({theater: false, light: true}, 'light, theater off');
  await page.locator('[data-show=splash]').click();
  await check({tab: 'splash', light: true}, 'light splash');
  await page.locator('#sim-theme').selectOption('dark');
  await check({tab: 'splash', light: false}, 'dark splash');
  await page.locator('[data-show=playing]').click();

  const ids = await page.locator('[id]').evaluateAll(nodes => nodes.map(node => node.id));
  assert.equal(new Set(ids).size, ids.length, 'all IDs are unique');
  for (const width of [1440, 375]) {
    await page.setViewportSize({width, height: 900});
    await assertNoOverflow(page, width);
  }
  assert.deepEqual(errors, []);
});

test('simulator refuses resources that do not match their pins', async t => {
  const {browser, url} = await serveDocs(t);
  const context = await browser.newContext();
  t.after(() => context.close());
  await context.route('https://raw.githubusercontent.com/**', route =>
    route.fulfill({status: 206, body: Buffer.alloc(4086176), headers: {'access-control-allow-origin': '*'}}));
  const page = await context.newPage();
  await page.goto(url);
  await page.locator('#advanced > summary').click();
  await page.waitForSelector('#sim-status.bad', {timeout: 60000});
  assert.match(await page.locator('#sim-status').textContent(), /do not match their pinned SHA-256; refused/);
  assert.ok(await page.locator('#sim-retry').isVisible());
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
  assert.deepEqual(written, {size: 13638660, hash: '148446d95dfcb85afbaa2b8c13310aed4ea97db80b849f7bb4bb10612e1fa5e1'});

  // Download the minimal image under the update name.
  await page.locator('#image-choices input[value=minimal]').check();
  const [download] = await Promise.all([
    page.waitForEvent('download'),
    page.locator('#download-update-name').click(),
  ]);
  assert.equal(download.suggestedFilename(), 'RKNANOFWIMG');
  const saved = await fs.readFile(await download.path());
  assert.equal(require('node:crypto').createHash('sha256').update(saved).digest('hex'),
    '92c446066e715d74a719671d3ee643ed4b7587c94801eb6dc3893f2271ed944d');

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
    await assertNoOverflow(page, width);
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

// Section 4 end to end: stock fetched from the repository, then builds
// that must equal the release images, all without local files.
test('builder needs no local files and reproduces the release images', async t => {
  const {browser, url} = await serveDocs(t);
  const context = await browser.newContext({acceptDownloads: true, viewport: {width: 1280, height: 900}});
  t.after(() => context.close());
  await serveRaw(context);
  const page = await context.newPage();
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.goto(url);
  await page.locator('#advanced > summary').click();
  await page.locator('#firmware-fetch').click();
  await page.waitForSelector('#firmware-status.good, #firmware-status.bad', {timeout: 60000});
  assert.match(await page.locator('#firmware-status').textContent(), /Verified stock V137/);
  const sha = buf => require('node:crypto').createHash('sha256').update(buf).digest('hex');
  const build = async () => {
    const [download] = await Promise.all([
      page.waitForEvent('download', {timeout: 120000}),
      page.locator('#build-button').click(),
    ]);
    await page.waitForSelector('#build-status.good', {timeout: 120000});
    return sha(await fs.readFile(await download.path()));
  };
  // Sound settings come before the feature choice.
  const order = await page.evaluate(() => ['#opt-dac-filter', '#eq-presets', '.base-choices']
    .map(sel => document.querySelector(sel).getBoundingClientRect().top));
  assert.ok(order[0] < order[2] && order[1] < order[2], 'EQ and DAC filter sit above the features');
  // All CE features: the Standard image, Opus data loaded on demand.
  assert.ok(await page.locator('#feature-list').isHidden());
  assert.equal(await build(), '148446d95dfcb85afbaa2b8c13310aed4ea97db80b849f7bb4bb10612e1fa5e1');
  // Pick features starts as the Minimal image.
  await page.locator('input[name=build-base][value=custom]').check();
  assert.ok(await page.locator('#feature-list').isVisible());
  assert.equal(await build(), '92c446066e715d74a719671d3ee643ed4b7587c94801eb6dc3893f2271ed944d');
  // Theater excludes the Bluetooth shortcut and the lock screen, and says why.
  const box = id => page.locator(`#feature-list input[data-feature="${id}"]`);
  await box('theater').check();
  assert.ok(await box('bt').isDisabled());
  assert.ok(await box('lock').isDisabled());
  assert.match(await page.locator('#feature-list label:has(input[data-feature="bt"]) .why').textContent(), /Not with Theater mode/);
  assert.equal(await build() !== '', true);
  await box('theater').uncheck();
  assert.ok(await box('bt').isEnabled());
  // Opus, the Bluetooth shortcut and the lock screen from embedded data.
  await box('opus').check();
  await box('bt').check();
  await box('lock').check();
  assert.ok(await box('theater').isDisabled());
  await build();
  assert.match(await page.locator('#build-status').textContent(), /Opus playback, .*Lock-screen track info.*Bluetooth shortcut/);
  assert.ok(await box('playlists').isDisabled());
  for (const width of [1280, 375]) {
    await page.setViewportSize({width, height: 900});
    await assertNoOverflow(page, width);
  }
  assert.deepEqual(errors, []);
});

// The Stageshow pictures (site/, built into docs/stage/) mount in both
// color schemes without errors: the hero demo and the four feature tiles.
test('stage pictures mount in light and dark', async t => {
  const {browser, url} = await serveDocs(t);
  for (const colorScheme of ['light', 'dark']) {
    const context = await browser.newContext({colorScheme, viewport: {width: 1280, height: 900}});
    t.after(() => context.close());
    const page = await context.newPage();
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    page.on('console', message => { if (message.type() === 'error') errors.push(message.text()); });
    await page.goto(url);
    await page.waitForSelector('#ce-hero-stage .ss-stage');
    assert.equal(await page.locator('#ce-hero-stage .ss-stage').getAttribute('data-theme'), colorScheme);
    await page.locator('#features').scrollIntoViewIfNeeded();
    for (const name of ['theater', 'eq', 'sort', 'bluetooth'])
      await page.waitForSelector(`[data-picture="${name}"] .ss-stage`);
    await page.locator('[data-stat="vorbis"]').scrollIntoViewIfNeeded();
    // Count exposes its figure as an aria-label (its digits are rolling strips)
    await page.waitForFunction(() => document.querySelector('[data-stat="vorbis"] .ss-count')?.getAttribute('aria-label') === '40', null, {timeout: 10000});
    assert.equal(await page.locator('[data-stat="vorbis"] .ft-stat-number').count(), 1, 'the static fallback gave way');
    assert.deepEqual(errors, [], colorScheme);
  }
});

test('device previews require a sustained hold and update their visible screens', async t => {
  const {browser, url} = await serveDocs(t);
  for (const width of [1280, 390]) {
    const context = await browser.newContext({viewport: {width, height: 950}, reducedMotion: 'reduce'});
    t.after(() => context.close());
    const page = await context.newPage();
    await page.goto(url);
    const bt = page.locator('[data-mode="bluetooth"]');
    await bt.scrollIntoViewIfNeeded();
    const power = bt.getByRole('button', {name: /Hold Power/});
    const box = await power.boundingBox();
    await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2);
    await page.mouse.down();
    await page.waitForTimeout(150);
    await page.mouse.up();
    assert.equal(await bt.getAttribute('data-on'), 'true', 'an early release must not toggle Bluetooth');
    await page.mouse.down();
    await page.waitForFunction(() => document.querySelector('[data-mode="bluetooth"]')?.dataset.on === 'false');
    await page.mouse.up();
    await power.focus();
    await page.keyboard.down('Space');
    await page.waitForFunction(() => document.querySelector('[data-mode="bluetooth"]')?.dataset.on === 'true');
    await page.keyboard.up('Space');
    const eq = page.locator('[data-mode="eq"]');
    await eq.getByRole('button', {name: 'Stock preset', exact: true}).click();
    await page.waitForTimeout(750);
    const stock = await eq.locator('canvas').evaluate(el => el.toDataURL());
    await eq.getByRole('button', {name: 'HD 600 curve', exact: true}).click();
    await page.waitForTimeout(750);
    const fitted = await eq.locator('canvas').evaluate(el => el.toDataURL());
    assert.notEqual(stock, fitted, 'changing the preset must change the rendered screen');
    assert.equal(await page.locator('.player-model[data-unavailable]').count(), 0, '3D previews render successfully');
    await assertNoOverflow(page, width);
    await context.close();
  }
});
