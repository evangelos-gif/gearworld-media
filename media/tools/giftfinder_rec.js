const { chromium } = require('playwright');
const fs = require('fs');
(async () => {
  const b = await chromium.launch();
  const ctx = await b.newContext({ viewport: { width: 432, height: 768 }, deviceScaleFactor: 2.5, isMobile: true, hasTouch: true, userAgent: 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1' });
  const p = await ctx.newPage();
  await p.route(/\/(out|go)\//, r => r.abort());
  await p.goto('https://gearworldhub.com/', { waitUntil: 'networkidle', timeout: 60000 });
  await p.click('#gwhAnalyticsReject').catch(() => {});
  const h = await p.evaluate(() => { const x = [...document.querySelectorAll('h1,h2,h3')].find(e => /Gift finder/.test(e.textContent)); return x.getBoundingClientRect().top + window.scrollY; });
  await p.evaluate(y => window.scrollTo(0, y - 40), h);
  await p.waitForTimeout(600);
  const frames = []; const taps = []; const t0 = Date.now(); let n = 0;
  async function snap() { const buf = await p.screenshot({ type: 'jpeg', quality: 88 }); const t = (Date.now() - t0) / 1000; const f = `rec/f${String(n++).padStart(4, '0')}.jpg`; fs.writeFileSync(f, buf); frames.push({ f, t }); }
  async function hold(ms) { const end = Date.now() + ms; while (Date.now() < end) await snap(); }
  async function tap(loc) { const bb = await loc.boundingBox(); taps.push({ t: (Date.now() - t0) / 1000, x: (bb.x + bb.width / 2) * 2.5, y: (bb.y + bb.height / 2) * 2.5 }); await loc.click(); }
  await hold(700);
  await tap(p.getByRole('button', { name: 'Her', exact: true })); await hold(800);
  await tap(p.getByRole('button', { name: 'Up to £50', exact: true })); await hold(700);
  await tap(p.getByRole('button', { name: 'Perfume', exact: true })); await hold(700);
  await tap(p.locator('#gwh2GiftGo')); await hold(1500);
  for (let i = 0; i < 14; i++) { await p.mouse.wheel(0, 70); await snap(); }
  await hold(900);
  fs.writeFileSync('rec/meta.json', JSON.stringify({ frames, taps }));
  console.log('frames', frames.length, 'dur', frames[frames.length - 1].t, 'taps', JSON.stringify(taps));
  await b.close();
})();
