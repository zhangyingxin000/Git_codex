const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const { chromium } = require('playwright');

const [url, outputDir, profileDir] = process.argv.slice(2);
if (!url || !outputDir || !profileDir) process.exit(2);
fs.mkdirSync(outputDir, { recursive: true });
fs.mkdirSync(profileDir, { recursive: true });

(async () => {
  const context = await chromium.launchPersistentContext(profileDir, {
    headless: false,
    executablePath: 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe',
    viewport: { width: 1440, height: 960 },
    args: ['--start-maximized']
  });
  const page = context.pages()[0] || await context.newPage();
  const networkData = [];
  const responseTasks = [];
  page.on('response', response => {
    if (networkData.length >= 100) return;
    const task = (async () => {
      try {
        const headers = await response.allHeaders();
        const type = (headers['content-type'] || '').toLowerCase();
        const length = Number(headers['content-length'] || 0);
        if (!/(json|text|javascript)/.test(type) || length > 2000000) return;
        const responseUrl = response.url();
        if (!responseUrl.startsWith('http')) return;
        const body = await response.text();
        if (!body || body.length > 2000000) return;
        networkData.push({ url: responseUrl, status: response.status(), contentType: type, body });
      } catch (_) {}
    })();
    responseTasks.push(task);
  });
  await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 60000 });
  const deadline = Date.now() + 180000;
  const openedAt = Date.now();
  while (Date.now() < deadline) {
    const state = await page.evaluate(() => ({ url: location.href, text: (document.body?.innerText || '').length, title: document.title, images: document.images.length, canvases: document.querySelectorAll('canvas').length }));
    const publicVisualPage = Date.now() - openedAt > 10000 && state.text > 20 && (state.images > 0 || state.canvases > 0);
    if (!/login|signin|auth/i.test(state.url) && (state.text > 500 || publicVisualPage)) break;
    await page.waitForTimeout(2000);
  }
  for (let i = 0; i < 30; i++) {
    const before = await page.evaluate(() => document.documentElement.scrollHeight);
    await page.evaluate(() => window.scrollTo(0, document.documentElement.scrollHeight));
    await page.waitForTimeout(700);
    const after = await page.evaluate(() => document.documentElement.scrollHeight);
    if (after === before) break;
  }
  await page.evaluate(() => window.scrollTo(0, 0));
  const result = await page.evaluate(() => ({
    title: document.title,
    url: location.href,
    text: document.body?.innerText || '',
    headings: [...document.querySelectorAll('h1,h2,h3,h4')].map(x => x.innerText.trim()).filter(Boolean),
    tables: [...document.querySelectorAll('table')].map(t => t.innerText.trim()).filter(Boolean),
    images: [...document.images].map((img, i) => ({ index: i, src: img.currentSrc || img.src, alt: img.alt || '', width: img.naturalWidth, height: img.naturalHeight })).filter(x => x.src),
    links: [...document.querySelectorAll('a[href]')].map(a => ({ text: a.innerText.trim(), href: a.href })).filter(x => x.text)
  }));
  result.frames = [];
  for (const frame of page.frames()) {
    try {
      const frameText = await frame.locator('body').innerText({ timeout: 3000 });
      if (frameText.trim()) result.frames.push({ url: frame.url(), text: frameText });
    } catch (_) {}
  }
  await page.screenshot({ path: path.join(outputDir, 'full-page.png'), fullPage: true });
  const scrollInfo = await page.evaluate(() => {
    const candidates = [...document.querySelectorAll('*')].map((el, index) => ({
      index, scrollHeight: el.scrollHeight, clientHeight: el.clientHeight,
      overflowY: getComputedStyle(el).overflowY
    })).filter(x => x.scrollHeight - x.clientHeight > 300 && ['auto', 'scroll'].includes(x.overflowY));
    return candidates.sort((a, b) => (b.scrollHeight - b.clientHeight) - (a.scrollHeight - a.clientHeight))[0] || null;
  });
  const viewportShots = [];
  if (scrollInfo) {
    const step = Math.max(400, scrollInfo.clientHeight - 120);
    for (let top = 0, n = 0; top < scrollInfo.scrollHeight && n < 30; top += step, n++) {
      await page.evaluate(({ index, top }) => { const el = [...document.querySelectorAll('*')][index]; if (el) el.scrollTop = top; }, { index: scrollInfo.index, top });
      await page.waitForTimeout(500);
      const file = `viewport-${String(n).padStart(3, '0')}.png`;
      await page.screenshot({ path: path.join(outputDir, file) });
      viewportShots.push(file);
    }
  } else {
    await page.mouse.move(900, 500);
    let previousHash = '';
    let unchanged = 0;
    for (let n = 0; n < 30; n++) {
      const file = `viewport-${String(n).padStart(3, '0')}.png`;
      const buffer = await page.screenshot({ path: path.join(outputDir, file) });
      viewportShots.push(file);
      const hash = crypto.createHash('sha1').update(buffer).digest('hex');
      unchanged = hash === previousHash ? unchanged + 1 : 0;
      if (unchanged >= 2) break;
      previousHash = hash;
      await page.mouse.wheel(0, 420);
      await page.waitForTimeout(500);
    }
  }
  result.scroll_capture = scrollInfo ? { ...scrollInfo, screenshots: viewportShots } : { mode: 'wheel', screenshots: viewportShots };
  await Promise.allSettled(responseTasks);
  let prototypeManifestCount = 0;
  let prototypeResourceCount = 0;
  for (const item of networkData) {
    try {
      const parsed = JSON.parse(item.body);
      if (parsed && parsed.images && typeof parsed.images === 'object') {
        prototypeManifestCount++;
        prototypeResourceCount += Object.keys(parsed.images).length;
      }
    } catch (_) {}
  }
  result.network = networkData.map(x => ({ url: x.url, status: x.status, contentType: x.contentType, bodyLength: x.body.length }));
  result.completeness = {
    domTextLength: result.text.length,
    frameCount: result.frames.length,
    headingCount: result.headings.length,
    tableCount: result.tables.length,
    imageCount: result.images.length,
    linkCount: result.links.length,
    networkDocumentCount: networkData.length,
    prototypeManifestCount,
    prototypeResourceCount,
    screenshotCount: viewportShots.length + 1,
    suspectedCanvasDocument: result.text.length < 200 && viewportShots.length > 3
  };
  fs.writeFileSync(path.join(outputDir, 'page.json'), JSON.stringify(result, null, 2), 'utf8');
  fs.writeFileSync(path.join(outputDir, 'network.json'), JSON.stringify(networkData, null, 2), 'utf8');
  await context.close();
})().catch(e => { fs.writeFileSync(path.join(outputDir, 'error.txt'), String(e.stack || e)); process.exit(1); });
