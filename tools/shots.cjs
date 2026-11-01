// The README's pictures, from tools/demo.py and nothing else, so no real name can reach them.
// Run the demo, then: NODE_PATH=<a folder with playwright-core> CHROME=<a Chrome binary> node tools/shots.cjs [out folder]
const { chromium } = require('playwright-core');
const path = require('path');
const base = 'http://127.0.0.1:8096', out = process.argv[2] || path.join(__dirname, '..', 'docs', 'img');
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const shot = (name) => path.join(out, `${name}.png`);
const noRail = () => document.documentElement.style.setProperty('scroll-behavior', 'auto');

async function opened(b, url, { theme = 'morning', width = 1440, height = 900, scale = 1.5, phone = false, wait = 'body.inked' } = {}) {
  const ctx = await b.newContext({ viewport: { width, height }, deviceScaleFactor: scale, reducedMotion: 'reduce', serviceWorkers: 'block', isMobile: phone, hasTouch: phone });
  await ctx.addInitScript((x) => { try { localStorage.setItem('paper-theme', x); } catch { /* */ } }, theme);
  const p = await ctx.newPage();
  p.on('pageerror', (e) => console.log('page error', url, e.message.slice(0, 160)));
  await p.goto(`${base}${url}`);
  await p.waitForSelector(wait, { timeout: 20000 });
  await sleep(2600);
  await p.evaluate(noRail);
  return p;
}

const toTop = async (p, selector, gap = 16) => {
  await p.evaluate(([s, g]) => { document.querySelector(s).scrollIntoView(); scrollBy(0, -g); }, [selector, gap]);
  await sleep(500);
};

// One part of a page, with room around it, and clear of the bar that stays at the top.
async function crop(p, selector, name, { room = 28, most = Infinity } = {}) {
  const el = await p.$(selector);
  if (!el) return console.log('no', selector);
  await p.addStyleTag({ content: '#dock-btn { display: none !important; }' });
  await p.evaluate(([s]) => { const e = document.querySelector(s); scrollTo(0, e.getBoundingClientRect().top + scrollY - 90); }, [selector]);
  await sleep(700);
  const box = await el.boundingBox(), size = p.viewportSize();
  const x = Math.max(0, box.x - room), y = Math.max(0, box.y - room / 2);
  await p.screenshot({ path: shot(name), clip: { x, y, width: Math.min(size.width - x, box.width + 2 * room), height: Math.min(size.height - y, box.height + room, most) } });
}

// The masthead is on the front page's picture already, and the sticky bar stays.
const pastMasthead = async (p) => {
  await p.evaluate(() => scrollTo(0, 134));
  await sleep(500);
};

// Several pictures on one sheet, for the themes and the phone.
async function sheet(b, name, names, { columns, width, gap = 28, pad = 28, background = '#f6d3bd', radius = 10, flow = false }) {
  const fs = require('fs');
  const imgs = names.map((n) => `<img src="data:image/png;base64,${fs.readFileSync(shot(n)).toString('base64')}">`).join('');
  const p = await (await b.newContext({ viewport: { width, height: 800 }, deviceScaleFactor: 1 })).newPage();
  await p.setContent(`<body style="margin:0;background:${background}"><div id="s" style="${flow ? `columns:${columns};column-gap:${gap}px` : `display:grid;grid-template-columns:repeat(${columns},1fr);gap:${gap}px`};padding:${pad}px;background:${background}">${imgs}</div><style>img{width:100%;display:block;border-radius:${radius}px;break-inside:avoid;${flow ? `margin-bottom:${gap}px` : ''}}</style>`);
  await sleep(600);
  await (await p.$('#s')).screenshot({ path: shot(name) });
  await p.context().close();
  names.forEach((n) => fs.unlinkSync(shot(n)));
}

(async () => {
  const b = await chromium.launch({ executablePath: process.env.CHROME || undefined, args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });

  // the front page, and the same page in each theme
  let p = await opened(b, '/', { height: 1300 });
  await p.setViewportSize({ width: 1440, height: 900 });
  await sleep(600);
  await p.screenshot({ path: shot('front-morning') });
  await p.setViewportSize({ width: 1440, height: 1500 });
  await crop(p, '#elections', 'elections', { most: 1120 });
  for (const [id, name, most] of [['followed', 'following'], ['sides', 'both-sides'], ['usage', 'ai-use'], ['business', 'business'], ['mail', 'mail'], ['systems', 'systems', 575], ['arts', 'arts']]) await crop(p, `#${id}`, name, { most });
  await p.context().close();
  await sheet(b, 'desks', ['mail', 'arts', 'business', 'systems'], { columns: 2, width: 1800, gap: 24, pad: 12, radius: 0, flow: true });
  const themes = ['morning', 'night', 'cobalt', 'glass'];
  for (const t of themes) {
    p = await opened(b, '/', { theme: t, scale: 1 });
    await p.screenshot({ path: shot(`theme-${t}`) });
    await p.context().close();
  }
  await sheet(b, 'themes', themes.map((t) => `theme-${t}`), { columns: 2, width: 1600, background: '#ffffff', gap: 16, pad: 0, radius: 0 });

  // a story, the case on each side, and the page around it
  const rent = 'https://demo.invalid/story/2/northern-post';
  p = await opened(b, `/read?u=${encodeURIComponent(rent)}`, { height: 1000 });
  await sleep(1200);
  await pastMasthead(p);
  await p.screenshot({ path: shot('story') });
  await p.context().close();

  // a place, a conflict and a machine
  p = await opened(b, '/world/hazard/gdacs:TC:1001', { height: 820 });
  await pastMasthead(p);
  await p.screenshot({ path: shot('scene') });
  await p.context().close();
  p = await opened(b, '/world/theater/north_strait', { height: 1300 });
  await crop(p, '.arc', 'history');
  await crop(p, '.who-reporting', 'who-reporting');
  await p.context().close();
  p = await opened(b, '/systems/machine/NAS', { height: 1000 });
  await pastMasthead(p);
  await p.screenshot({ path: shot('machine') });
  await p.context().close();

  // a race
  const race = await (await fetch(`${base}/api/paper`)).json();
  p = await opened(b, `/elections/race/${race.elections.us.closest[0].key}`, { height: 1500, wait: '.el-verdict' });
  await sleep(1400);
  await pastMasthead(p);
  await p.screenshot({ path: shot('race') });
  await p.context().close();

  // search
  p = await opened(b, '/topic/Northern%20Strait', { height: 1250, wait: '.find-said p' });
  await pastMasthead(p);
  await p.screenshot({ path: shot('search') });
  await p.context().close();

  // settings
  p = await opened(b, '/settings', { wait: '#set-plex', height: 1000 });
  await p.evaluate(() => { document.getElementById('set-plex').scrollIntoView(); scrollBy(0, 96); });
  await sleep(500);
  await p.screenshot({ path: shot('settings') });
  await p.context().close();

  // the phone
  const phone = { width: 390, height: 844, scale: 2, phone: true };
  p = await opened(b, '/', phone);
  await p.screenshot({ path: shot('phone-1') });
  await p.context().close();
  p = await opened(b, `/read?u=${encodeURIComponent(rent)}`, phone);
  await p.screenshot({ path: shot('phone-2') });
  await p.context().close();
  p = await opened(b, '/topic/Northern%20Strait', { ...phone, wait: '.find-said p' });
  await p.screenshot({ path: shot('phone-3') });
  await p.context().close();
  await sheet(b, 'phone', ['phone-1', 'phone-2', 'phone-3'], { columns: 3, width: 1400, background: '#e7bfa5', gap: 44, pad: 44, radius: 22 });

  await b.close();
})().catch((e) => { console.error(e); process.exit(1); });
