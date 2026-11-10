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

test('comparison synchronizes controls and fits desktop and mobile', async t => {
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
  const page = await browser.newPage({viewport: {width: 1440, height: 1000}});
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.goto(`http://127.0.0.1:${server.address().port}/`);
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
