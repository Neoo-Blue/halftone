// Every tap opens here. Each detail is a real address on this paper, so reload, back and open-in-new-tab all work,
// and stories are read inside the paper. The only way off the site is the small "Original" link under a story.
import { $, $$, esc, usd, whole, dollars, compact, ago, span, bytes, dayName, dotPlot, dayBars, lineChart, look, lookPicker, tight } from '/lib.js';
import { makeGlobe } from '/globe.js';
import { dockStory } from '/dock.js';
import { phoneTab, phonePage } from '/phone.js';
import { mountScene } from '/scene.js';

const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
const NAME = document.title;
const ROUTES = [
  [/^\/mail\/([0-9a-f]{24})$/, 'mail', 'Mail'],
  [/^\/issue\/([a-z0-9-]+)$/, 'issue', 'Tech'],
  [/^\/world\/event\/([0-9a-f]+)$/, 'event', 'World'],
  [/^\/world\/theater\/([a-z0-9_]+)$/, 'theater', 'World'],
  [/^\/world\/thread\/(.+)$/, 'thread', 'World'],
  [/^\/world\/hazard\/(.+)$/, 'hazard', 'World'],
  [/^\/world\/market\/([a-z0-9_]+)$/, 'market', 'World'],
  [/^\/arts\/plex\/(\d+)$/, 'plex', 'Arts'],
  [/^\/arts\/show\/(\d+)$/, 'show', 'Arts'],
  [/^\/arts\/movie\/(\d+)$/, 'movie', 'Arts'],
  [/^\/business\/([a-z]+)$/, 'product', 'Business'],
  [/^\/systems\/service\/(.+)$/, 'service', 'Systems'],
  [/^\/systems\/machine\/(.+)$/, 'machine', 'Systems'],
  [/^\/topic\/(.+)$/, 'topic', null],
  [/^\/weather()$/, 'weather', null],
  [/^\/usage()$/, 'usage', null],
  [/^\/investments()$/, 'investments', null],
  [/^\/saved()$/, 'saved', null],
  [/^\/archive\/?([0-9-]*)$/, 'archive', null],
  [/^\/systems\/container\/(\d+)$/, 'container', 'Systems'],
];
const DESK = { Mail: '/#mail', Tech: '/#tech', World: '/#world', Arts: '/#arts', Business: '/#business', Systems: '/#systems' };
const WHEN = { dateStyle: 'medium', timeStyle: 'short' };

const stamp = (ts) => (ts ? new Date(ts * 1000).toLocaleString('en-US', WHEN) : '');
const date = (iso) => (iso ? dayName(/T/.test(iso) ? iso : `${iso}T12:00:00`) : '');
const title = (s) => String(s ?? '').replace(/_/g, ' ').replace(/^./, (c) => c.toUpperCase());
export const reading = (url) => `/read?${new URLSearchParams({ u: url })}`;
export const picture = (url) => `/img/remote?${new URLSearchParams({ u: url })}`;
export const eventHref = (s) => `/world/${s.k === 'h' ? 'hazard' : 'event'}/${encodeURIComponent(s.i)}`;

const km = (a, b) => 6371 * Math.acos(Math.min(1, Math.sin(a.la * Math.PI / 180) * Math.sin(b.la * Math.PI / 180) + Math.cos(a.la * Math.PI / 180) * Math.cos(b.la * Math.PI / 180) * Math.cos((a.lo - b.lo) * Math.PI / 180)));

// A sentence or two of what happened, worked out from the track, so every hazard opens with the point.
function hazardStory(d, t) {
  const seen = t.filter((p) => !p.fc), ahead = t.filter((p) => p.fc);
  if (seen.length < 2) return d.about || d.text || '';
  const peak = seen.reduce((a, b) => ((b.v || 0) > (a.v || 0) ? b : a)), end = seen[seen.length - 1];
  const far = seen.slice(1).reduce((sum, p, i) => sum + km(seen[i], p), 0);
  const unit = d.unit || 'km/h';
  const speed = peak.v ? ` It peaked at ${whole(peak.v)} ${unit} on ${stamp(peak.t)}.` : '';
  const next = ahead.length ? ` It is forecast to go on for another ${whole(ahead.slice(1).reduce((sum, p, i) => sum + km(ahead[i], p), km(end, ahead[0])))} km.` : '';
  return `It was first tracked on ${stamp(seen[0].t)} and has covered ${whole(far)} km.${speed} Its last reported position was on ${stamp(end.t)}${end.label ? `, as a ${end.label.toLowerCase()}` : ''}.${next}`;
}

const impactList = (d) => (d.impact?.length ? `<h3>The impact</h3>${facts(d.impact)}` : '');

function advisories(t, unit = 'km/h') {
  if (t.length < 3) return '';
  return `<details class="log"><summary>Every position, ${t.length} in all</summary><table class="num-table"><thead><tr><th scope="col">When</th><th scope="col">Status</th><th scope="col" class="r">Strength</th><th scope="col" class="r">Exposed</th></tr></thead><tbody>${t.map((p) => `<tr><th scope="row">${esc(stamp(p.t))}</th><td>${esc(p.label || '')}${p.fc ? ' (forecast)' : ''}</td><td class="r">${p.v ? `${whole(p.v)} ${esc(unit)}` : ''}</td><td class="r">${p.gale ? whole(p.gale) : ''}</td></tr>`).join('')}</tbody></table></details>`;
}

const relatedNews = (list) => (list?.length ? `<h3>In the news</h3><ul class="plain">${list.map((n) => `<li><a href="${reading(n.u)}">${esc(n.t)}</a> <span class="small">${esc(n.src)}, ${esc(ago(n.ts))}</span></li>`).join('')}</ul>` : '');

// Reports as time-stamped dots, with the page's subject pulsing among them.
function reportScene(rows, pin, alt) {
  const dots = rows.filter((r) => r.la != null && r.lo != null).map((r) => ({ la: r.la, lo: r.lo, t: r.ts, s: r.s, k: r.k || 'k', label: r.t, href: r.k === 'h' ? eventHref({ k: 'h', i: r.i }) : r.i && r.i !== 'demo' ? eventHref({ k: r.k, i: r.i }) : null }));
  return dots.length || pin ? { dots, pin, span: 8, alt, key: [['k-red', 'Conflict'], ['k-blue', 'Economy'], ['k-orange', 'Hazard']] } : null;
}

const uniqueReports = (rows) => [...new Map(rows.map((r) => [r.i || r.t, r])).values()];
let machine = null, machineRange = '24h';

function machineCharts(d, range) {
  const r = d.series[range] || [], percent = (v) => `${Math.round(v)}%`, rate = (v) => `${bytes(v)}/s`;
  if (r.length < 2) return '<p class="empty">Readings build up from the moment a machine is connected. Check back in a few minutes.</p>';
  const plot = (title, keys, o) => (r.some((x) => keys.some((k) => x[k.key] != null)) ? `<section><h3>${title}</h3>${dotPlot(r, keys, { caption: '', aria: `${title} for ${d.name}, ${range}`, style: look.style, ...o })}</section>` : '');
  return plot('CPU', [{ key: 'cpu', name: 'CPU', cls: 'k1' }, { key: 'io', name: 'Disk wait', cls: 'k3' }], { fmt: percent, lo: 0 })
    + plot('Memory', [{ key: 'mem', name: 'Memory', cls: 'k2' }], { fmt: percent, lo: 0, hi: 100 })
    + plot('Disk used', [{ key: 'disk', name: 'Disk', cls: 'k3' }], { fmt: (v) => `${v.toFixed(1)}%` })
    + plot('Network', [{ key: 'rx', name: 'In', cls: 'k1' }, { key: 'tx', name: 'Out', cls: 'k2' }], { fmt: rate, lo: 0 })
    + plot('Disk activity', [{ key: 'rd', name: 'Read', cls: 'k1' }, { key: 'wr', name: 'Written', cls: 'k2' }], { fmt: rate, lo: 0 })
    + plot('Load', [{ key: 'load', name: 'Load', cls: 'k1' }], { fmt: (v) => v.toFixed(2), lo: 0 })
    + plot('Temperature', [{ key: 'temp', name: 'Temperature', cls: 'k3' }], { fmt: (v) => `${Math.round(v)} C` });
}

const longDate = (s) => {
  const [y, m, d] = s.split('-').map(Number);
  if (!m) return String(y);
  return new Date(Date.UTC(y, m - 1, d || 1)).toLocaleDateString('en-US', { timeZone: 'UTC', year: 'numeric', month: 'short', ...(d ? { day: 'numeric' } : {}) });
};
const hostOf = (url) => { try { return new URL(url).hostname.replace(/^www\./, ''); } catch { return ''; } };

// The whole story from day one. The rail shows how far through it you are, and fills as you read down.
function arc(h, d) {
  let n = 0;
  const steps = h.eras.map((e, i) => `<section class="arc-era" id="era-${i}">
      <header><h4>${esc(e.name)}<small>${esc(e.from)}${e.to === 'now' ? ' to now' : e.to === e.from ? '' : ` to ${esc(e.to)}`}</small></h4>
      ${e.summary ? `<p class="arc-sum">${esc(e.summary)}</p>` : ''}</header>
      <ol>${e.events.map((x) => `<li class="arc-step" id="step-${n++}">
        <time datetime="${esc(x.date)}">${esc(longDate(x.date))}</time>
        <div><b>${esc(x.title)}</b>${x.detail ? `<p>${esc(x.detail)}</p>` : ''}${x.source ? `<a class="arc-src" href="${esc(x.source)}" target="_blank" rel="noopener noreferrer">${esc(hostOf(x.source))}</a>` : ''}</div></li>`).join('')}</ol>
    </section>`).join('');
  let dot = 0;
  const rail = h.eras.map((e, i) => `<li style="flex:${Math.max(e.events.length, 3)} 1 0"><button type="button" data-era="${i}"><b>${esc(e.name)}</b><small>${esc(e.from)}</small></button>
    <span class="arc-dots">${e.events.map((x) => `<button type="button" data-step="${dot++}" data-tip="${esc(longDate(x.date))}: ${esc(x.title)}" aria-label="${esc(longDate(x.date))}: ${esc(x.title)}"></button>`).join('')}</span></li>`).join('');
  return `<section class="arc" aria-labelledby="arc-head">
    <h3 id="arc-head">How we got here</h3>
    <div class="arc-rail"><ol>${rail}</ol><div class="arc-bar" aria-hidden="true"><i></i></div><p class="arc-where" aria-live="off"></p></div>
    ${steps}
    <p class="arc-now"><b>Today</b> Escalation stands at ${esc(d.esc)} of 100.</p>
  </section>`;
}

let arcWatch = null;
function mountArc() {
  arcWatch?.disconnect();
  const box = $('.arc', sheet());
  if (!box) return;
  const steps = $$('.arc-step', box), eras = $$('.arc-era', box), bar = $('.arc-bar i', box), where = $('.arc-where', box);
  if (!reduce) box.classList.add('live');
  const show = (x) => x.classList.add('seen');
  arcWatch = new IntersectionObserver((seen) => {
    for (const x of seen) {
      if (!x.isIntersecting) continue;
      show(x.target);
      const i = steps.indexOf(x.target), era = eras.indexOf(x.target.closest('.arc-era'));
      bar.style.width = `${(100 * (i + 1)) / steps.length}%`;
      where.textContent = `${$('time', x.target).textContent}, ${$('h4', eras[era]).firstChild.textContent}`;
      $$('[data-era]', box).forEach((b, k) => b.classList.toggle('on', k === era));
      $$('[data-step]', box).forEach((b, k) => b.classList.toggle('past', k <= i));
    }
  }, { rootMargin: '-30% 0px -55% 0px' });
  steps.forEach((s) => arcWatch.observe(s));
  const early = new IntersectionObserver((seen, o) => { for (const x of seen) if (x.isIntersecting) { show(x.target); o.unobserve(x.target); } }, { rootMargin: '0px 0px -8% 0px' });
  steps.forEach((s) => early.observe(s));
}

let held = null;
const signed = (v) => (v == null ? '' : `${v < 0 ? '-' : '+'}${dollars(Math.abs(v))}`);
const moved = (v) => (v == null ? '' : `<span class="${v < 0 ? 'neg' : 'pos'}">${v < 0 ? 'Down' : 'Up'} ${esc(dollars(Math.abs(v)))}</span>`);

function heldBody() {
  const d = held, money = d.show_gain, price = (r) => (r.price == null ? 'No price yet' : `${r.currency === 'USD' ? '$' : `${esc(r.currency)} `}${r.price.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: r.price < 1 ? 6 : 2 })}`);
  const priced = new Set((d.positions || []).map((r) => r.symbol));
  const waiting = d.holdings.filter((h) => !priced.has(h.symbol)).map((h) => ({ symbol: h.symbol, shares: Number(h.shares) || 0, buy: null, price: null, pct: null, value: null, gain: null, source: 'typed' }));
  const rows = [...(d.positions || []), ...waiting].map((r) => `<tr>
    <th scope="row">${esc(r.symbol)}<small>${esc(r.name || (r.price == null ? 'Checking the price' : ''))}${r.stale ? ', last known price' : ''}</small></th>
    <td class="r">${r.shares ? esc(r.shares.toLocaleString('en-US', { maximumFractionDigits: 8 })) : 'Watching'}</td>
    <td class="r">${price(r)}<small class="${(r.pct || 0) < 0 ? 'neg' : 'pos'}">${r.pct == null ? '' : `${r.pct < 0 ? '-' : '+'}${Math.abs(r.pct).toFixed(2)}%`}</small></td>
    <td class="r">${r.value == null ? '' : dollars(r.value)}</td>
    ${money ? `<td class="r">${r.gain == null ? (r.shares ? '<span class="dim">Add a buy price</span>' : '') : moved(r.gain)}${r.buy == null ? '' : `<small>from ${r.currency === 'USD' ? '$' : `${esc(r.currency || '')} `}${r.buy.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 6 })}</small>`}</td>` : ''}
    <td>${r.source === 'typed' ? `<button type="button" class="ghost" data-held-remove="${esc(r.symbol)}" aria-label="Remove ${esc(r.symbol)}"><svg viewBox="0 0 16 16" aria-hidden="true"><path d="M3.5 3.5l9 9M12.5 3.5l-9 9"/></svg></button>` : ''}</td></tr>`).join('');
  const off = new Set(d.tape_off);
  return `${rows ? `<table class="num-table held"><thead><tr><th scope="col">Holding</th><th scope="col" class="r">Shares</th><th scope="col" class="r">Price</th><th scope="col" class="r">Value</th>${money ? '<th scope="col" class="r">Up or down</th>' : ''}<th scope="col"><span class="vh">Remove</span></th></tr></thead><tbody>${rows}</tbody></table>` : '<p class="empty">Add what you hold, or a symbol to watch.</p>'}
    <form class="held-add" id="held-add">
      <label><span>Symbol</span><input name="symbol" required maxlength="15" placeholder="AAPL or BTC-USD" autocapitalize="characters" spellcheck="false"></label>
      <label><span>Shares</span><input name="shares" inputmode="decimal" placeholder="10"></label>
      <label><span>Buy price</span><input name="buy" inputmode="decimal" placeholder="150.25"></label>
      <button type="submit" class="btn">Add</button>
      <label class="held-tape"><input type="checkbox" name="tape" checked> Show on the tape</label>
    </form>
    <p class="small" id="held-note" role="status">${d.error ? 'The last pricing run failed, so these are the last good numbers. ' : ''}${d.feed ? 'Holdings from your portfolio address appear here too. ' : ''}${d.missing?.length ? `${esc(d.missing.join(' and '))}: not counted in full just now. ` : ''}Prices from Yahoo Finance, a little delayed. Leave shares blank to only watch a symbol.</p>
    ${d.markets.length ? `<h3>What the tape shows</h3><ul class="tape-picks">${d.markets.map((m) => `<li><label><input type="checkbox" data-tape="${esc(m.label)}"${off.has(m.label) ? '' : ' checked'}> ${esc(m.label)}</label></li>`).join('')}</ul>` : ''}`;
}

const saveValues = (values) => fetch('/api/settings', { method: 'PUT', credentials: 'same-origin', headers: { 'content-type': 'application/json', 'x-paper': '1' }, body: JSON.stringify({ values }) });

async function refreshHeld() {
  const box = $('#held-body');
  if (!box) return;
  const r = await fetch('/api/detail/investments/', { credentials: 'same-origin' });
  if (!r.ok) return;
  held = await r.json();
  box.innerHTML = heldBody();
  dispatchEvent(new Event('paper:reload'));
}

async function saveHoldings(next) {
  const before = held.holdings;
  held.holdings = next;  // at once, so a second quick change builds on this one
  const r = await saveValues({ HOLDINGS: next });
  if (!r.ok) {
    held.holdings = before;
    $('#held-note').textContent = (await r.json()).error || 'That could not be saved.';
    return false;
  }
  [300, 3000, 12000].forEach((ms) => setTimeout(refreshHeld, ms));  // the price arrives a little after the holding
  return true;
}

let spent = null, spentDays = 30, spentDay = null;

function usageBody() {
  const d = spent, days = d.days.slice(-spentDays), row = d.days.find((x) => x.day === spentDay) || days[days.length - 1], by = Object.create(null);
  days.forEach((x) => x.rows.forEach((r) => {
    by[r.who] ||= { who: r.who, worth: 0, charged: 0 };
    by[r.who].worth += r.worth || 0;
    by[r.who].charged += r.charged || 0;
  }));
  const used = (r) => (r.unit === 'minutes' ? `${whole(Math.round(r.qty))} min` : r.qty ? compact(r.qty) : '');
  const head = (first) => `<thead><tr><th scope="col">${first}</th>${first === 'Used by' ? '<th scope="col" class="r">Used</th>' : ''}<th scope="col" class="r">Worth</th><th scope="col" class="r">Charged</th></tr></thead>`;
  const rows = row.rows.map((r) => `<tr><th scope="row">${esc(r.who)}<small>${esc(r.model)}</small></th><td class="r">${esc(used(r))}</td><td class="r">${dollars(r.worth)}</td><td class="r">${dollars(r.charged)}</td></tr>`).join('');
  const who = Object.values(by).sort((a, b) => b.worth - a.worth).map((w) => `<tr><th scope="row">${esc(w.who)}</th><td class="r">${dollars(w.worth)}</td><td class="r">${dollars(w.charged)}</td></tr>`).join('');
  const at = d.days.indexOf(row);
  return `<div class="page-cols"><section><h3>Worth at list price</h3>${dayBars(days, 'worth', { picked: row.day })}</section>
    <section><h3>Really charged</h3>${dayBars(days, 'charged', { picked: row.day, label: ' charged', over: 'worth' })}</section></div>
    <div class="use-day"><h3>${esc(dayName(`${row.day}T12:00:00`))}</h3><span>${dollars(row.worth)} worth, ${dollars(row.charged)} charged</span>
      <button type="button" class="ghost text" data-usage-step="-1" ${at ? '' : 'disabled'}>Earlier</button><button type="button" class="ghost text" data-usage-step="1" ${at < d.days.length - 1 ? '' : 'disabled'}>Later</button></div>
    <div class="page-cols"><section><table class="num-table">${head('Used by')}<tbody>${rows}</tbody></table></section>
    <section><h3>Last ${days.length} days, by who used it</h3><table class="num-table">${head('Source')}<tbody>${who}</tbody></table></section></div>`;
}

const around = (lat, lon, deg = 12) => getDots().filter((x) => Math.abs(x.la - lat) < deg && Math.abs(x.lo - lon) < deg * 1.4);

const coverageSpan = (o) => { const ts = o.map((x) => x.ts).filter(Boolean); return [Math.min(...ts), Math.max(...ts)]; };

// Who carried a story, and when, each dot in its place along the day.
function spread(outlets) {
  if (!outlets || outlets.length < 2) return '';
  const [from, to] = coverageSpan(outlets), width = (to - from) || 1;
  return `<section class="spread"><h3>How it spread</h3><p class="small">${outlets.length} outlets over ${esc(span(to - from) || 'moments')}.</p>
    <ol>${outlets.map((o, i) => `<li style="--x:${(((o.ts - from) / width) * 100).toFixed(1)};--i:${i}"><a href="${reading(o.u)}"><i></i><b>${esc(o.src)}</b><span>${esc(o.t || '')}</span><time>${esc(ago(o.ts))}</time></a></li>`).join('')}</ol></section>`;
}

function facts(rows) {
  const list = rows.filter(([, v]) => v !== null && v !== undefined && v !== '' && v !== false);
  return list.length ? `<dl class="facts">${list.map(([k, v]) => `<div><dt>${esc(k)}</dt><dd>${esc(v)}</dd></div>`).join('')}</dl>` : '';
}
// WARROOM's analysts cite events as [hex id]; here each becomes a numbered link to that story.
function cited(text) {
  const seen = [];
  return esc(text).replace(/\s*\[([0-9a-f]{24,40})\]/g, (_, id) => {
    if (!seen.includes(id)) seen.push(id);
    return `<a class="ref" href="/world/event/${id}" aria-label="Source ${seen.indexOf(id) + 1}">${seen.indexOf(id) + 1}</a>`;
  });
}
const bullet = (b) => (typeof b === 'string' ? b : b.text || '').replace(/^\[(high|medium|low)\]\s*/i, '').replace(/\s*\((up|down|flat)[^)]*confidence[^)]*\)/gi, '');  // the analyst's working, not the reader's
const notes = (list) => (list || []).map((n) => `<section class="intel"><h3>${esc(n.headline)}</h3>${n.body ? `<p>${cited(n.body)}</p>` : ''}${n.bullets?.length ? `<ul>${n.bullets.map((b) => `<li>${cited(bullet(b))}</li>`).join('')}</ul>` : ''}<time>${esc(ago(n.ts))}</time></section>`).join('');
const stories = (rows) => `<ul class="wire-list">${rows.map((s) => `<li><a href="${eventHref(s)}">${esc(s.t)}</a><span>${esc([s.src, s.place, ago(s.ts)].filter(Boolean).join(', '))}</span></li>`).join('')}</ul>`;
const onGlobe = (lat, lon) => (lat != null ? `<button type="button" class="ghost text" data-globe="${esc(lat)},${esc(lon)}">Show on the globe</button>` : '');

const rail = (title, rows) => (rows?.length ? `<h3>${title}</h3><ul class="rail-list">${rows.map((s) => `<li><a href="${esc(reading(s.u))}"><b>${esc(s.t)}</b><span>${esc(s.n > 1 ? `${s.src} and ${s.n - 1} more` : s.src)}, ${esc(ago(s.ts))}</span>${s.img ? `<i class="thumb ink"><img src="${esc(picture(s.img))}" alt="" loading="lazy"></i>` : ''}</a></li>`).join('')}</ul>` : '');

// A wide page sets the story in newspaper columns, in blocks short enough that the eye never scrolls back up to find the next column. The first block sits beside the photograph.
let reading_ = null;
const stopReading = () => { window.speechSynthesis?.cancel(); reading_?.(); reading_ = null; };

function readOnDevice(button) {
  const talk = new SpeechSynthesisUtterance($('.page-body', sheet()).textContent), done = () => { button.setAttribute('aria-pressed', 'false'); button.textContent = 'Listen'; };
  talk.voice = speechSynthesis.getVoices().find((v) => v.name === button.dataset.voice) || null;
  talk.onend = done;
  reading_ = done;
  button.setAttribute('aria-pressed', 'true');
  button.textContent = 'Stop';
  speechSynthesis.speak(talk);
}

// One piece at a time, the next fetched while this one plays, so the voice starts quickly and a long story never waits on all of itself.
async function readWithService(button) {
  const audio = new Audio();
  let off = false, skip = () => {};
  const done = () => { off = true; skip(); audio.pause(); button.setAttribute('aria-pressed', 'false'); button.textContent = 'Listen'; };
  reading_ = done;
  button.setAttribute('aria-pressed', 'true');
  button.textContent = 'Loading';
  audio.src = URL.createObjectURL(new Blob([Uint8Array.from(atob('UklGRiQAAABXQVZFZm10IBAAAAABAAEAQB8AAIA+AAACABAAZGF0YQAAAAA='), (c) => c.charCodeAt(0))], { type: 'audio/wav' }));
  audio.play().catch(() => {});  // while the tap still counts, so a phone lets the real audio play
  const piece = async (part) => {
    const r = await fetch('/api/listen', { method: 'POST', credentials: 'same-origin', headers: { 'content-type': 'application/json', 'x-paper': '1' }, body: JSON.stringify({ url: button.dataset.url, part }) });
    if (!r.ok) throw new Error((await r.json().catch(() => ({}))).error || 'no audio');
    return { blob: await r.blob(), parts: Number(r.headers.get('x-parts')) };
  };
  try {
    let next = piece(0);
    for (let part = 0; ; part += 1) {
      const { blob, parts } = await next;
      if (off) return;
      if (part + 1 < parts) next = piece(part + 1);
      URL.revokeObjectURL(audio.src);
      audio.src = URL.createObjectURL(blob);
      await audio.play();
      button.textContent = 'Stop';
      await new Promise((end, fail) => { audio.onended = end; audio.onerror = fail; skip = end; });
      if (off) return;
      if (part + 1 >= parts) break;
    }
    done();
  } catch {
    if (off) return;
    done();
    readOnDevice(button);  // a dead service leaves the story readable, and the button says whose voice this is
    button.textContent = 'Stop device voice';
  }
}

function storyBody(s, photo = '') {
  const src = document.createElement('template'), blocks = [{ html: [], words: 0 }];
  src.innerHTML = s.body;
  const same = (a, b) => a?.replace(/\s+/g, ' ').trim().slice(0, 80) === b?.replace(/\s+/g, ' ').trim().slice(0, 80);
  if (same(src.content.firstElementChild?.textContent, s.deck)) src.content.firstElementChild.remove();  // a feed's summary is often the story's first line, and the deck has just said it
  const close = () => {  // a scrap left before a heading joins the block above rather than being spread over the columns
    const [last, prev] = [blocks.at(-1), blocks.at(-2)];
    if (prev && last.words < 90 && !/^<h\d/.test(last.html[0])) {
      prev.html.push(...last.html);
      prev.words += last.words;
      blocks.pop();
    }
  };
  for (const el of src.content.children) {
    const now = blocks.at(-1);
    if (now.words >= (blocks.length === 1 ? 150 : 420) || (/^H\d$/.test(el.tagName) && now.words)) {  // a heading always opens a block, so it can sit over all its columns
      close();
      blocks.push({ html: [], words: 0 });
    }
    blocks.at(-1).html.push(el.outerHTML);
    blocks.at(-1).words += el.textContent.split(/\s+/).length;
  }
  close();
  const [first, ...rest] = blocks;
  return `<div class="page-body story-body"><div class="story-chunk story-lead">${photo}<div>${first.html.join('')}</div></div>${rest.map((b) => `<div class="story-chunk${b.words < 90 ? ' short' : ''}">${b.html.join('')}</div>`).join('')}</div>
    <p class="source">Original at <a href="${esc(s.url)}" target="_blank" rel="noopener noreferrer">${esc(s.site)}</a></p>`;
}
const photograph = (url) => (url ? `<button type="button" class="hero ink" data-reveal aria-pressed="false" aria-label="Show the photograph in colour"><img src="${esc(picture(url))}" alt=""></button>` : '');

const VIEWS = {
  mail: (d) => ({
    head: d.subject, deck: d.why, meta: `${d.sender}, ${stamp(d.at)}`,
    body: `<div class="page-body mailtext">${esc(d.text) || 'This message has no text.'}</div>`,
    side: `${facts([['From', d.addr], ['To', d.to.join(', ')], ['Mailbox', d.box], ['Folder', d.junk ? 'Spam' : ''], ['Attachments', d.attachments ? 'Yes, open it in Outlook' : '']])}
      <button type="button" class="ghost text" data-mail-done="${esc(d.id)}" data-state="${d.done ? 'open' : 'done'}">${d.done ? 'Mark as not done' : 'Mark as done'}</button>
      <p class="small">Links and images are off here, so nothing in this mail can track you or run. Marking done changes the paper only.</p>
      ${d.open ? `<p class="source"><a href="${esc(d.open)}" target="_blank" rel="noopener noreferrer">Open in Outlook</a></p>` : ''}`,
  }),

  issue: (d) => ({
    head: d.slug.startsWith('brief-') ? d.headline : d.title, deck: d.deck, meta: d.slug.startsWith('brief-') ? d.title : '',
    body: `<div class="page-body wide-body">${d.sections.map((s) => `<section><h2>${esc(s.title)}</h2>${s.html}</section>`).join('')}</div>`,
  }),

  event(d) {
    const place = [...new Set([d.place, d.admin1].filter(Boolean).flatMap((x) => x.split(', ')).filter((x) => !/^[A-Z]{2}\d*$/.test(x)))].join(', ') || d.country;
    const side = `${facts([['Kind', title(d.category)], ['Place', place], ['When', stamp(d.ts)], ['Who', d.actors.join(', ')], ['Fatalities', d.fatalities], ['Severity', d.severity != null ? `${Math.round(d.severity * 100)} of 100` : ''], ['Confidence', d.confidence != null ? `${Math.round(d.confidence * 100)}%` : '']])}
      ${d.lat == null ? '' : onGlobe(d.lat, d.lon)}
      ${d.theater && d.theater !== 'global' ? `<p class="to"><a href="/world/theater/${esc(d.theater)}">This conflict</a></p>` : ''}
      ${d.thread ? `<p class="to"><a href="/world/thread/${esc(d.thread.id)}">${esc(d.thread.title)}</a></p>` : ''}
      ${d.sources.length ? `<h3>Sources</h3><ul class="plain">${d.sources.map((s) => `<li><a href="${reading(s.url)}">${esc(s.title || s.publisher || s.url)}</a>${s.title ? `<time>${esc(s.publisher)}</time>` : ''}</li>`).join('')}</ul>` : ''}
      ${d.nearby.length ? `<h3>Nearby in the last three days</h3>${stories(d.nearby)}` : ''}${rail('On the same subject', d.related)}${rail('Top stories', d.top)}`;
    const long = (d.summary || '').length > 220;
    const body = `${long ? `<div class="page-body"><p>${esc(d.summary)}</p></div>` : ''}${d.note ? notes([d.note]) : ''}
      ${d.story ? storyBody(d.story) : `<p class="empty">${d.sources.length ? 'The publisher would not share the full story with the paper. The sources alongside may have more.' : 'WARROOM has no article for this event, only the report itself.'}</p>`}`;
    return {
      scene: d.lat != null ? reportScene(uniqueReports([...(d.nearby || []), ...around(d.lat, d.lon)]), [d.lat, d.lon], `Where this happened, and what else was reported nearby`) : null, head: (d.title || '').length > 140 ? `${d.title.slice(0, 137).replace(/\s+\S*$/, '')}...` : d.title, deck: `${d.confidence != null && d.confidence < 0.4 ? "Unconfirmed: one side's account, not yet checked against another. " : ''}${long ? '' : d.summary || ''}`, meta: [place, ago(d.ts)].filter(Boolean).join(', '), body, side, locate: [d.lat, d.lon] };
  },

  theater(d) {
    const h = d.history, turns = h ? h.eras.reduce((n, e) => n + e.events.length, 0) : 0, years = h?.began ? new Date().getFullYear() - Number(h.began.slice(0, 4)) : 0;
    return {
      head: d.name, deck: h?.summary || `Escalation stands at ${d.esc} of 100.`, meta: `${whole(d.events.length)} recent ${d.events.length === 1 ? 'story' : 'stories'}`,
      scene: reportScene(uniqueReports([...d.events, ...getDots().filter((x) => x.w === d.id)]), null, `Reports in ${d.name}, over time`),
      wide: h ? arc(h, d) : '',
      body: `<div class="page-cols"><section><h3>What's happening now</h3>${notes(d.intel.slice(0, 1))}${d.intel.length > 1 ? `<details class="older"><summary>Earlier notes</summary>${notes(d.intel.slice(1))}</details>` : ''}</section><section><h3>Latest</h3>${d.events.length ? stories(d.events) : '<p class="empty">Nothing recent with a real headline.</p>'}</section></div>`,
      side: `${facts([['Escalation', `${d.esc} of 100`], ['Began', h?.began ? longDate(h.began) : ''], ['Running for', years ? `${whole(years)} years` : ''], ['Turning points', turns || '']])}${h?.began_note ? `<p class="small">${esc(h.began_note)}</p>` : ''}${d.lat == null ? '<p class="small">This one is about what two sides do, not one place, so it has no spot on the globe.</p>' : onGlobe(d.lat, d.lon)}`,
      locate: [d.lat, d.lon],
    };
  },

  thread(d) {
    return {
      head: d.title, deck: d.summary, meta: `${whole(d.count)} reports since ${stamp(d.first)}`,
      scene: reportScene(d.events, d.events.some((e) => e.la != null) ? null : d.lat != null ? [d.lat, d.lon] : null, `How ${d.title} developed`),
      body: `<div class="page-cols">${d.intel?.length ? `<section>${notes(d.intel)}</section>` : ''}<section><h3>Latest</h3>${stories(d.events)}</section></div>`,
      side: `${facts([['Status', title(d.status)], ['Last report', ago(d.last)], ['Who', d.actors.join(', ')]])}${onGlobe(d.lat, d.lon)}${d.theater && d.theater !== 'global' ? `<p class="to"><a href="/world/theater/${esc(d.theater)}">This conflict</a></p>` : ''}`,
      locate: [d.lat, d.lon],
    };
  },

  hazard(d) {
    const t = d.track || [], quake = d.hkind === 'earthquake', moved = t.length > 1;
    const key = { cyclone: [['k-solid', 'Track'], ['k-dash', 'Forecast'], ['k-red', 'Strongest winds'], ['k-orange', 'Storm winds'], ['k-faint', 'Possible path']], earthquake: [['k-red', 'Violent shaking'], ['k-orange', 'Strong shaking'], ['k-faint', 'Felt']] }[d.hkind];
    const scene = (moved || d.areas?.length || d.lat != null) ? { track: moved ? t : [], areas: d.areas || [], pin: moved ? null : [d.lat, d.lon], ripple: quake && d.areas?.length ? true : null, unit: d.unit || 'km/h', key, span: quake ? 6 : 4, rippleText: 'The shaking spreading from the epicentre', alt: `Map of ${d.title}` } : null;
    return {
      head: d.title, deck: d.text, meta: [title(d.hkind), (d.countries?.length ? d.countries.join(', ') : d.country)].filter(Boolean).join(', '), scene,
      body: `<div class="page-body"><p>${esc(hazardStory(d, t))}</p></div>${impactList(d)}${d.about && d.about !== d.text ? `<div class="page-body"><p>${esc(d.about)}</p></div>` : ''}${advisories(t, d.unit)}`,
      side: `${facts([['Alert', title(d.alert)], ['From', stamp(d.from)], ['Until', stamp(d.to)], ['Reported by', d.source]])}${d.report ? `<p class="source"><a href="${esc(d.report)}" target="_blank" rel="noopener noreferrer">Full report</a></p>` : ''}${onGlobe(d.lat, d.lon)}${relatedNews(d.related)}`,
    };
  },

  topic(d) {
    const list = d.stories.map((s) => `<li class="${s.n >= 3 ? 'wide-story' : ''}"><a href="${reading(s.u)}">${esc(s.t)}</a><span>${esc(s.n > 1 ? `${s.src} and ${s.n - 1} more` : s.src)}, ${esc(ago(s.ts))}</span></li>`).join('');
    const reports = d.reports.filter((r) => r.la != null);
    return {
      head: d.q, deck: d.stories.length || d.reports.length ? `${d.stories.length} ${d.stories.length === 1 ? 'story' : 'stories'} in the paper and ${d.reports.length} on the world desk.` : 'Nothing in the paper on that right now.',
      scene: reports.length ? reportScene(reports, null, `Where ${d.q} is being reported`) : null,
      body: `${list ? `<ul class="wire-list">${list}</ul>` : '<p class="empty">Try a shorter word, or a name.</p>'}${d.earlier?.length ? `<h3>Earlier editions</h3><ul class="wire-list">${d.earlier.map((s) => `<li><a href="${esc(reading(s.u))}">${esc(s.t)}</a><span>${esc([s.src, s.day].join(', '))}</span></li>`).join('')}</ul>` : ''}`,
      side: `<div class="story-tools"><button type="button" class="ghost text" data-follow="${esc(d.q)}">Follow</button><button type="button" class="ghost text" data-mute="${esc(d.q)}">Mute</button></div>${d.outlets.length ? `<h3>Who is covering it</h3>${facts(d.outlets)}` : ''}`,
    };
  },

  weather(d) {
    const clock = (t, o) => new Date(t * 1000).toLocaleString('en-US', { timeZone: d.tz, ...o });
    const hour = { hour: 'numeric' }, deg = (v) => `${Math.round(v)}\u00b0`;
    const rain = d.rain_at ? ` Rain likely by ${clock(d.rain_at, hour)}.` : ' No rain likely in the next two days.';
    const lo = Math.min(...d.days.map((x) => x.lo)), hi = Math.max(...d.days.map((x) => x.hi)), range = (hi - lo) || 1;
    const days = d.days.map((x, i) => `<li style="--i:${i};--a:${((x.lo - lo) / range) * 100}%;--b:${((hi - x.hi) / range) * 100}%"><b>${esc(i ? clock(x.t + 43200, { weekday: 'short' }) : 'Today')}</b><span>${esc(x.sky)}${x.rain >= 30 ? `, ${esc(x.rain)}% rain` : ''}</span><em>${deg(x.lo)}</em><i></i><em>${deg(x.hi)}</em></li>`).join('');
    const rows = d.hours.map((h) => ({ t: h.t, temp: h.temp, rain: h.rain }));
    return {
      head: d.place, deck: `${d.now.temp}\u00b0${d.units}, ${d.now.sky.toLowerCase()}. Feels like ${d.now.feels}\u00b0.${rain}`, meta: [d.region, d.country].filter(Boolean).join(', '),
      scene: { pin: [d.lat, d.lon], span: 5, alt: `Map of ${d.place}` },
      body: `<h3>The week</h3><ol class="days">${days}</ol><h3>Temperature, next 48 hours</h3>${dotPlot(rows, [{ key: 'temp', name: 'Temperature', cls: 'k2' }], { fmt: deg, caption: `Degrees ${d.units}`, aria: `Temperature for the next 48 hours in ${d.place}` })}<h3>Chance of rain</h3>${dotPlot(rows, [{ key: 'rain', name: 'Rain', cls: 'k1' }], { fmt: (v) => `${Math.round(v)}%`, lo: 0, hi: 100, caption: 'Next 48 hours', aria: `Chance of rain for the next 48 hours in ${d.place}` })}`,
      side: facts([['Wind', `${d.now.wind} ${d.speed}`], ['Humidity', `${d.now.humidity}%`], ['Sunrise', clock(d.days[0].rise, { hour: 'numeric', minute: '2-digit' })], ['Sunset', clock(d.days[0].set, { hour: 'numeric', minute: '2-digit' })]]),
    };
  },

  machine(d) {
    machine = d;
    machineRange = '24h';
    if (!d.ok) return { head: d.name, deck: 'Not answering right now.', meta: d.role };
    const load = `${d.load[0].toFixed(2)} on ${d.cores} cores`;
    const fills = d.full_in == null ? 'Not filling up' : `In about ${whole(Math.round(d.full_in))} days`;
    const volumes = (d.volumes || []).map((v) => { const share = (100 * v.used) / (v.total || 1); return `<tr><th scope="row">${esc(v.mount)}</th><td><span class="meter ${share >= 93 ? 'bad' : share >= 85 ? 'warn' : ''}" style="--v:${share.toFixed(1)}"><i></i></span> <b>${Math.round(share)}%</b></td><td class="r">${bytes(v.used)} of ${bytes(v.total)}</td></tr>`; }).join('');
    const top = (d.top || []).map((t) => `<tr><th scope="row">${esc(t.name)}</th><td class="r">${t.cpu.toFixed(1)}%</td><td class="r">${t.mem.toFixed(1)}%</td></tr>`).join('');
    const pools = (d.storage?.pools || []).map((z) => `<li>${esc(z.name)}: ${bytes(z.alloc)} of ${bytes(z.size)}, ${esc(z.health.toLowerCase())}</li>`).join('');
    const docker = [...(d.containers || [])].sort((a, b) => sick(b) - sick(a)).map((c) => `<tr><th scope="row">${esc(c.name)}</th><td class="r${sick(c) ? ' bad' : ''}">${esc(c.status)}</td></tr>`).join('');
    const guests = (d.guests || []).map((g) => `<li><a href="/systems/container/${g.id}">${esc(g.id)} ${esc(g.name)}</a> <span class="small">${esc(g.status)}, ${g.cpu ?? 0}% CPU</span></li>`).join('');
    return {
      head: d.name, deck: `CPU ${Math.round(d.cpu)}%, memory ${Math.round((100 * d.mem_used) / (d.mem_total || 1))}%, disk ${Math.round((100 * d.disk_used) / (d.disk_total || 1))}%.`, meta: `${d.role}, up ${span(d.uptime)}`,
      body: `<div class="plot-tools"><div class="seg ranges" role="group" aria-label="Time range">${['1h', '24h', '7d', '30d'].map((r) => `<button type="button" data-range="${r}" aria-pressed="${r === '24h'}">${r}</button>`).join('')}</div>${lookPicker()}</div>
        <div id="machine-charts">${machineCharts(d, '24h')}</div>
        <div class="page-cols">${volumes ? `<section><h3>Volumes</h3><table class="num-table"><tbody>${volumes}</tbody></table></section>` : ''}
        ${pools ? `<section><h3>Storage pools</h3><ul class="plain">${pools}</ul></section>` : ''}
        ${top ? `<section><h3>Using the most right now</h3><table class="num-table"><thead><tr><th scope="col">Process</th><th scope="col" class="r">CPU</th><th scope="col" class="r">Memory</th></tr></thead><tbody>${top}</tbody></table></section>` : ''}
        ${guests ? `<section><h3>Containers</h3><ul class="plain">${guests}</ul></section>` : ''}
        ${docker ? `<section><h3>Docker</h3><table class="num-table"><tbody>${docker}</tbody></table></section>` : ''}</div>`,
      side: facts([['Docker', docker ? `${d.containers.filter((c) => c.state === 'running').length} of ${d.containers.length} running` : ''], ['Load', load], ['Memory', `${bytes(d.mem_used)} of ${bytes(d.mem_total)}`], ['Disk fills', fills], ['Temperature', d.temp ? `${d.temp} C` : ''], ['Kernel', d.kernel]]),
    };
  },

  usage(d) {
    if (!d.days.length) return { head: 'AI use', deck: 'Nothing counted yet.', body: '<p class="empty">The paper counts its own AI calls from the moment you add a provider. Settings can add the rest.</p>' };
    spent = d;
    spentDays = 30;
    const done = d.days.filter((x) => x.day < d.today), last = done[done.length - 1] || d.days[d.days.length - 1], month = d.days.slice(-30);
    spentDay = d.days.some((x) => x.day === location.hash.slice(1)) ? location.hash.slice(1) : last.day;
    const sum = (key) => month.reduce((n, x) => n + x[key], 0);
    return {
      head: 'AI use', deck: `${dollars(last.worth)} of AI on ${dayName(`${last.day}T12:00:00`)}, at list price. ${dollars(last.charged)} of it was really charged.`, meta: `Counted ${ago(d.as_of)}`,
      body: `${d.error ? '<p class="small">The last count failed, so these are the last good numbers.</p>' : ''}${d.missing.length ? `<p class="small">${esc(d.missing.join(' and '))} did not answer this time, so their days may be behind.</p>` : ''}
        <div class="seg ranges" role="group" aria-label="Period">${[7, 30, 90].map((n) => `<button type="button" data-usage-days="${n}" aria-pressed="${n === 30}">${n} days</button>`).join('')}</div>
        <div id="usage-body">${usageBody()}</div>
        <p class="small">Worth is what the same use would cost at public list prices, so a plan or credit still shows what it saved. Charged is what left your account: the Anthropic bill when it is connected, otherwise the paper's estimate of its own and Commons' API calls. Days run midnight to midnight UTC.${d.unpriced.length ? ` No list price here for ${esc(d.unpriced.join('; '))}, so those count as tokens only.` : ''}</p>`,
      side: facts([['Last 30 days', dollars(sum('worth'))], ['Really charged', dollars(sum('charged'))], ['Tokens', compact(sum('tokens'))]]),
    };
  },

  investments(d) {
    held = d;
    const line = d.total == null ? 'Add what you hold, or a symbol to watch, and it shows on the front page and the tape.' : `Worth ${dollars(d.total)}${d.show_gain && d.gain != null ? `, ${d.gain < 0 ? 'down' : 'up'} ${dollars(Math.abs(d.gain))} (${Math.abs(d.gain_pct || 0).toFixed(1)}%) from what you paid` : ''}.`;
    return {
      head: 'Investments', deck: line, meta: d.as_of ? `Priced ${ago(d.as_of)}` : '',
      body: `${d.total == null ? '' : facts([['Total', dollars(d.total)], ['Today', signed(d.day)], ['You paid', d.show_gain && d.cost != null ? dollars(d.cost) : ''], ['Up or down', d.show_gain ? signed(d.gain) : ''], ['No buy price', d.show_gain && d.no_buy ? d.no_buy : '']])}<div id="held-body">${heldBody()}</div>`,
    };
  },

  archive(d) {
    if (d.day) {
      return { head: longDate(d.day), deck: `The ${d.stories.length} most widely carried stories that day.`, body: `<p class="to"><a href="/archive">Every edition</a></p><ul class="wire-list">${d.stories.map((s) => `<li><a href="${esc(reading(s.u))}">${esc(s.t)}</a><span>${esc(s.n > 1 ? `${s.src} and ${s.n - 1} more` : s.src)}</span></li>`).join('')}</ul>` };
    }
    return { head: 'Back issues', deck: d.days.length ? `${whole(d.days.length)} editions kept.` : 'Each day is kept here from today on.', body: `<ul class="wire-list">${d.days.map((x) => `<li><a href="/archive/${esc(x.day)}">${esc(longDate(x.day))}</a><span>${esc(x.top || '')}</span></li>`).join('')}</ul>` };
  },

  saved(d) {
    return {
      head: 'Saved stories', deck: d.saved.length ? `${whole(d.saved.length)} to read, on every device.` : 'Stories you save show here, on every device.',
      body: d.saved.length ? `<ul class="wire-list">${d.saved.map((s) => `<li><a href="${esc(reading(s.url))}">${esc(s.title || s.url)}</a><span>${esc([s.site, ago(s.saved)].filter(Boolean).join(', '))}</span></li>`).join('')}</ul>` : '<p class="empty">Open a story and press Save.</p>',
    };
  },

  market(d) {
    const num = (n) => Number(n).toLocaleString('en-US', { maximumFractionDigits: 2 });
    return {
      head: d.label, deck: d.why, meta: `${num(d.last)} ${d.unit || ''}, ${(d.pct || 0) >= 0 ? 'up' : 'down'} ${Math.abs(d.pct || 0).toFixed(1)}%`,
      body: dotPlot(d.series, [{ key: 'v', name: d.label, cls: 'k1' }], { fmt: num, caption: `${d.series.length} readings`, aria: `${d.label} price history` }),
    };
  },

  read(d) {
    const none = d.why === 'not a public page' ? 'The paper only opens public web pages.' : d.why ? 'That site did not answer.' : `${d.site} would not share the full story with the paper.`;
    return {
      head: d.title || d.site, deck: d.deck, meta: [d.site, d.author, d.published ? stamp(d.published) : ''].filter(Boolean).join(', '),
      side: `${d.homes?.length ? `<p class="small">Carried in ${esc(d.homes.map(([home, n]) => `${home} ${n}`).join(', '))}.${d.homes.length === 1 && d.homes[0][1] > 2 ? ` So far only ${esc(d.homes[0][0])} outlets.` : ''}</p>` : ''}${spread(d.spread)}${rail('On the same subject', d.related)}${rail('Top stories', d.top)}`,
      body: d.body ? `<div class="story-tools"><button type="button" class="ghost text" data-save="${esc(d.url)}" data-title="${esc(d.title || d.site)}" data-site="${esc(d.site)}" aria-pressed="${!!d.saved}">${d.saved ? 'Saved' : 'Save'}</button>${d.listen !== 'browser' || 'speechSynthesis' in window ? `<button type="button" class="ghost text" data-listen="${esc(d.listen)}" data-voice="${esc(d.voice || '')}" data-url="${esc(d.url)}" aria-pressed="false">Listen</button>` : ''}</div>${storyBody(d, photograph(d.image))}` : `${photograph(d.image)}<p class="empty">${esc(none)}</p>${d.url ? `<p class="source">Original at <a href="${esc(d.url)}" target="_blank" rel="noopener noreferrer">${esc(d.site)}</a></p>` : ''}`,
    };
  },

  plex(d) {
    return {
      head: d.title, deck: d.tagline, meta: [d.year, d.content, d.minutes ? `${d.minutes} min` : '', d.rating ? `${d.rating} of 10` : ''].filter(Boolean).join(', '),
      backdrop: d.art, poster: d.poster,
      body: `<div class="page-body"><p>${esc(d.summary)}</p></div>
        ${d.seasons.length ? `<h3>Seasons</h3><ul class="plain">${d.seasons.map((s) => `<li>${esc(s.title)}<time>${esc(s.n)} episodes${s.watched ? `, ${esc(s.watched)} watched` : ''}</time></li>`).join('')}</ul>` : ''}
        ${d.cast.length ? `<h3>Cast</h3><ul class="cast">${d.cast.map((c) => `<li><b>${esc(c.name)}</b><span>${esc(c.role)}</span></li>`).join('')}</ul>` : ''}`,
      side: `${facts([['Genre', d.genres.join(', ')], ['Director', d.directors.join(', ')], ['Studio', d.studio], ['Video', d.video], ['Audio', d.audio], ['Added', stamp(d.added)]])}${d.open ? `<p class="source"><a href="${esc(d.open)}" target="_blank" rel="noopener noreferrer">Play in Plex</a></p>` : ''}`,
    };
  },

  show(d) {
    return {
      head: d.title, deck: d.summary, meta: [d.year, d.network, d.rating ? `${d.rating} of 10` : '', title(d.status)].filter(Boolean).join(', '), poster: d.poster,
      body: d.next.length ? `<h3>Next episodes</h3><ul class="plain">${d.next.map((e) => `<li><b>${esc(e.code)}: ${esc(e.title)}</b><time>${esc(new Date(e.at).toLocaleString('en-US', WHEN))}</time>${e.about ? `<p>${esc(e.about)}</p>` : ''}</li>`).join('')}</ul>` : '<p class="empty">No episodes scheduled.</p>',
      side: facts([['Genre', d.genres.join(', ')], ['Seasons', d.seasons], ['In the library', d.total ? `${d.have} of ${d.total} episodes` : ''], ['Length', d.minutes ? `${d.minutes} min` : '']]),
    };
  },

  movie(d) {
    return {
      head: d.title, deck: d.summary, meta: [d.year, d.studio, d.rating ? `${d.rating} of 10` : ''].filter(Boolean).join(', '), poster: d.poster,
      body: '',
      side: facts([['Genre', d.genres.join(', ')], ['Length', d.minutes ? `${d.minutes} min` : ''], ['Cinemas', date(d.cinemas)], ['Digital', date(d.digital)], ['Disc', date(d.disc)], ['In the library', d.have ? 'Yes' : 'Not yet']]),
    };
  },

  product(d) {
    const r = d.report, seen = Object.fromEntries(d.visitors.map((v) => [v.day, v.n])), rows = [];
    if (d.visitors.length) {  // every day since the first visitor, so a quiet day reads as zero and not as a gap
      for (let t = Date.parse(`${d.visitors[0].day}T12:00:00`); t <= Date.now(); t += 86400000) {
        const day = new Date(t).toLocaleDateString('en-CA');
        rows.push({ t: t / 1000, n: seen[day] || 0 });
      }
    }
    const most = Math.max(1, ...rows.map((x) => x.n));
    return {
      head: d.name, deck: r?.cents ? `${usd(r.cents)} in sales over 90 days.` : 'No sales yet.', meta: `${d.host}${d.up ? `, ${d.up.up ? `up, ${d.up.ms} ms` : 'down'}` : ''}`,
      body: `<h3>Real visitors per day</h3>${rows.length ? dotPlot(rows, [{ key: 'n', name: 'Visitors', cls: 'k1' }], { fmt: (v) => String(Math.round(v * 10) / 10), lo: 0, hi: most, aria: `Real visitors per day for ${d.name}` }) : '<p class="empty">Nobody has visited yet.</p>'}
        ${d.sales.length ? `<h3>Sales</h3><ul class="plain">${d.sales.map((s) => `<li>${esc(usd(s.cents))}, ${esc(s.item || 'order')}${s.city ? `, ${esc(s.city)}` : ''}<time>${esc(stamp(s.created))}</time></li>`).join('')}</ul>` : ''}`,
      side: `${r ? facts([['Sales, 90 days', usd(r.cents)], ['Orders', r.orders], ['Monthly recurring', usd(r.mrr)], ['Subscribers', r.subs], ['Visitors, 90 days', whole(r.visitors)], ['Left checkout, 30 days', r.abandoned], ['Refunds', usd(r.refunds)]]) : ''}<p class="source">Live at <a href="https://${esc(d.host)}/" target="_blank" rel="noopener noreferrer">${esc(d.host)}</a></p>`,
    };
  },

  service(d) {
    const hour = Math.floor(Date.now() / 3600000) * 3600, seen = Object.fromEntries(d.hours.map((h) => [h.h, h]));
    const cells = Array.from({ length: 168 }, (_, i) => {
      const t = hour - (167 - i) * 3600, h = seen[t];
      return h ? `<span class="${h.up >= 100 ? 'ok' : h.up > 0 ? 'part' : 'out'}" data-tip="${esc(stamp(t))}: ${esc(h.up)}% up, ${esc(h.ms)} ms"></span>` : `<span class="none" data-tip="${esc(stamp(t))}: not measured"></span>`;
    }).join('');
    const all = d.hours.length ? (d.hours.reduce((a, h) => a + h.up, 0) / d.hours.length).toFixed(2) : null;
    return {
      head: d.name, deck: d.up == null ? 'Not checked yet.' : d.up ? `Up, answering in ${d.ms} ms.` : 'Not answering.', meta: `${d.host}, checked ${ago(d.checked)}`,
      body: `<h3>The last seven days, one dot an hour</h3><div class="hours">${cells}</div><p class="small">${d.hours.length} of 168 hours measured so far.</p>`,
      side: facts([['Group', d.group], ['Uptime, measured hours', all ? `${all}%` : '']]),
    };
  },

  container(d) {
    return {
      head: `${d.id} ${d.name}`, meta: `${title(d.status)}${d.uptime ? `, up ${span(d.uptime)}` : ''}`,
      body: `${lineChart(d.history, d.name)}${d.about.length ? `<h3>Notes</h3><ul class="plain">${d.about.map((x) => `<li>${esc(x)}</li>`).join('')}</ul>` : ''}`,
      side: facts([['Cores', d.cores], ['Memory', `${bytes(d.mem)} of ${bytes(d.maxmem)}`], ['Disk', d.maxdisk ? `${bytes(d.disk)} of ${bytes(d.maxdisk)}` : ''], ['Starts on boot', d.autostart ? 'Yes' : 'No'], ['Traffic in', bytes(d.netin)], ['Traffic out', bytes(d.netout)]]),
    };
  },
};

function match() {
  const path = location.pathname;
  if (path === '/read') {
    const u = new URLSearchParams(location.search).get('u');
    return u ? { kind: 'read', url: `/api/read?${new URLSearchParams({ u })}`, desk: null } : null;
  }
  for (const [re, kind, desk] of ROUTES) {
    const hit = path.match(re);
    if (hit) return { kind, desk, url: `/api/detail/${kind}/${hit[1]}` };  // already encoded, and encoding twice breaks ids like gdacs:EQ:1
  }
  return null;
}

// The rail runs out before a long story does, so it scrolls until its end is showing and then stays, and the right of the page is never empty.
let side = null;
const fitSide = () => side?.style.setProperty('--stick', `${Math.min(64, innerHeight - side.offsetHeight - 16)}px`);
const sideGrew = new ResizeObserver(fitSide);
addEventListener('resize', fitSide);

function page(v, m) {
  const back = m.desk ? `<a href="${DESK[m.desk]}">Back to ${m.desk}</a>` : '<a href="/">Back to the paper</a>';
  const art = v.backdrop ? `<div class="backdrop"><img src="${esc(v.backdrop)}" alt=""></div>` : '';
  const left = v.poster ? `<button type="button" class="page-poster ink" data-reveal aria-pressed="false" aria-label="Show the poster in colour"><img src="${esc(v.poster)}" alt=""></button>` : '';
  const stage = v.scene ? '<div class="scene-host" data-scene></div>' : '';
  const where = !v.scene && v.locate?.[0] != null ? `<div class="locator"><canvas data-lat="${esc(v.locate[0])}" data-lon="${esc(v.locate[1])}" tabindex="0" role="img" aria-label="Globe centred on this place. Tap a dot to open that report."></canvas></div>` : '';
  const sub = `${v.deck ? `<p class="deck">${esc(v.deck)}</p>` : ''}${v.meta ? `<p class="byline">${esc(v.meta)}</p>` : ''}`;
  const side = where || v.side ? `<aside class="page-side">${where}${v.side || ''}</aside>` : '';
  return `<nav class="crumb" aria-label="Back">${back}</nav>${art}
    <header class="page-top${v.poster ? ' with-poster' : ''}">${left}<h1 class="page-head" tabindex="-1">${tight(v.head)}</h1><div class="page-sub">${sub}</div></header>${stage}
    ${v.wide || ''}<div class="page-grid${side ? '' : ' solo'}"><div class="page-main">${v.body || ''}</div>${side}</div>`;
}

let front = 0, turn = 0, still = null, stage = null, getDots = () => [];
const sheet = () => $('#page');

function mountStage(v) {
  stage?.destroy();
  stage = null;
  const host = $('[data-scene]', sheet());
  if (host && v.scene) stage = mountScene(host, v.scene, { open: go });
}

function mountLocator() {
  still?.destroy();
  still = null;
  const c = $('.locator canvas', sheet());
  if (!c) return;
  still = makeGlobe(c, { still: [Number(c.dataset.lat), Number(c.dataset.lon)], onPick() {}, onOpen: (dot) => go(eventHref(dot.k === 'h' ? { k: 'h', i: dot.i } : dot)) });
  still?.setDots(getDots());
}

function swap(show, paint) {
  const done = () => {
    paint();
    $('main#paper').hidden = show;
    sheet().hidden = !show;
  };
  if (!document.startViewTransition || reduce) return done();
  document.documentElement.classList.add('turn');
  const vt = document.startViewTransition(done);
  vt.finished.finally(() => document.documentElement.classList.remove('turn'));
  return vt.ready.catch(() => {});  // a second tap cancels the animation, never the page
}

export function isFront() {
  return !match();
}

const sick = (c) => c.state === 'restarting' || c.status.includes('unhealthy');

export async function route() {
  const m = match(), mine = (turn += 1);
  stopReading();
  dockStory(null);  // set again below if this page is a story: a question on the front page isn't about the last one you read
  if (!m) {
    still?.destroy();
    still = null;
    stage?.destroy();
    stage = null;
    if (!sheet().hidden) await swap(false, () => { sheet().replaceChildren(); document.title = NAME; });
    phonePage(null);
    if (phoneTab(location.hash.slice(1), front)) return;
    const target = location.hash && $(location.hash);
    if (target) target.scrollIntoView();
    else scrollTo(0, front);
    return;
  }
  if (sheet().hidden) front = scrollY;
  const data = fetch(m.url, { credentials: 'same-origin' }).then(async (r) => { const body = await r.json(); look.style = body.look || look.style; return { ok: r.ok, body }; }).catch(() => ({ ok: false, body: {} }));
  await swap(true, () => {
    sheet().innerHTML = '<p class="going">Turning the page</p>';
    scrollTo(0, 0);
  });
  const { ok, body } = await data;
  if (mine !== turn) return;  // a later tap already won
  if (!ok) {
    sheet().innerHTML = `<nav class="crumb"><a href="/">Back to the paper</a></nav><h1 class="page-head">${esc(body.error || 'That page did not load')}</h1><p class="deck">Check your connection, or sign in again if your session ended.</p><button type="button" class="ghost text" data-retry>Try again</button>`;
    return;
  }
  let v;
  try {
    v = VIEWS[m.kind](body);
  } catch {
    v = { head: 'This page came back in a shape the paper could not print', deck: 'The source sent something unexpected. The rest of the paper is fine.' };
  }
  sheet().innerHTML = page(v, m);
  mountLocator();
  mountStage(v);
  mountArc();
  dockStory(m.kind === 'read' && body.body ? body.url : null);
  phonePage(m.kind);
  document.title = `${v.head} | ${NAME}`;
  $('.page-head', sheet())?.focus({ preventScroll: true });
  sideGrew.disconnect();
  side = $('.page-side', sheet());
  if (side) sideGrew.observe(side);
}

export function go(href) {
  history.pushState(null, '', href);
  route();
}

export function start(fly, dots) {
  getDots = dots;
  document.addEventListener('submit', async (e) => {
    if (e.target.id !== 'held-add') return;
    e.preventDefault();
    const f = new FormData(e.target), symbol = String(f.get('symbol')).trim().toUpperCase();
    const row = { symbol, shares: String(f.get('shares')).trim(), buy: String(f.get('buy')).trim(), tape: f.get('tape') ? 'yes' : 'no' };
    if (await saveHoldings([...held.holdings, row])) e.target.reset();  // another lot of the same stock adds up, at the average price
  });
  document.addEventListener('change', (e) => {
    if (!e.target.matches('[data-tape]')) return;
    saveValues({ TAPE_OFF: $$('[data-tape]').filter((b) => !b.checked).map((b) => b.dataset.tape).join(',') }).then(() => dispatchEvent(new Event('paper:reload')));
  });
  addEventListener('popstate', route);
  document.addEventListener('error', (e) => { if (e.target.matches?.('.hero img, .page-poster img, .thumb img')) e.target.parentNode.remove(); }, true);  // a dead picture leaves no hole
  document.addEventListener('click', (e) => {
    const range = e.target.closest('[data-range]');
    if (range && machine) {
      $$('[data-range]', sheet()).forEach((b) => b.setAttribute('aria-pressed', String(b === range)));
      machineRange = range.dataset.range;
      $('#machine-charts').innerHTML = machineCharts(machine, machineRange);
      return undefined;
    }
    const gone = e.target.closest('[data-held-remove]');
    if (gone && held) {
      saveHoldings(held.holdings.filter((r) => r.symbol !== gone.dataset.heldRemove));
      return undefined;
    }
    const jump = e.target.closest('[data-era], [data-step]');
    if (jump) {
      $(jump.dataset.era ? `#era-${jump.dataset.era}` : `#step-${jump.dataset.step}`, sheet())?.scrollIntoView({ behavior: reduce ? 'auto' : 'smooth', block: jump.dataset.era ? 'start' : 'center' });
      return undefined;
    }
    const pin = e.target.closest('[data-follow], [data-mute]');
    if (pin) {
      const key = pin.dataset.follow ? 'FOLLOW' : 'MUTE', word = pin.dataset.follow || pin.dataset.mute;
      fetch('/api/settings', { credentials: 'same-origin', headers: { 'x-paper': '1' } }).then((r) => r.json()).then((page) => {
        const now = page.sections.flatMap((s) => s.fields).find((f) => f.key === key)?.value || '';
        return saveValues({ [key]: [...new Set([...now.split(',').map((x) => x.trim()).filter(Boolean), word])].join(', ') });
      }).then((r) => {
        if (!r.ok) throw new Error('refused');
        pin.textContent = key === 'FOLLOW' ? 'Following' : 'Muted';
        pin.disabled = true;
        dispatchEvent(new Event('paper:reload'));
      }).catch(() => { pin.textContent = 'Try again'; });
      return undefined;
    }
    const keep = e.target.closest('[data-save]');
    if (keep) {
      const on = keep.getAttribute('aria-pressed') !== 'true';
      keep.setAttribute('aria-pressed', String(on));
      keep.textContent = on ? 'Saved' : 'Save';
      fetch('/api/saved', { method: 'PUT', credentials: 'same-origin', headers: { 'content-type': 'application/json', 'x-paper': '1' }, body: JSON.stringify({ url: keep.dataset.save, title: keep.dataset.title, site: keep.dataset.site, saved: on }) }).then(() => dispatchEvent(new Event('paper:reload')));
      return undefined;
    }
    const listen = e.target.closest('[data-listen]');
    if (listen) {
      const on = listen.getAttribute('aria-pressed') !== 'true';
      stopReading();
      if (on) (listen.dataset.listen === 'browser' ? readOnDevice : readWithService)(listen);
      return undefined;
    }
    const pick = e.target.closest('[data-look]');
    if (pick) {
      look.style = pick.dataset.look;
      $$('[data-look]').forEach((b) => b.setAttribute('aria-pressed', String(b.dataset.look === look.style)));
      if ($('#machine-charts')) $('#machine-charts').innerHTML = machineCharts(machine, machineRange);
      fetch('/api/layout', { method: 'PUT', credentials: 'same-origin', headers: { 'content-type': 'application/json', 'x-paper': '1' }, body: JSON.stringify({ chart: look.style }) }).then(() => dispatchEvent(new Event('paper:reload')));
      return undefined;
    }
    const usePick = e.target.closest('[data-usage-days], [data-usage-day], [data-usage-step]');
    if (usePick && spent) {
      if (usePick.dataset.usageDays) {
        spentDays = Number(usePick.dataset.usageDays);
        $$('[data-usage-days]', sheet()).forEach((b) => b.setAttribute('aria-pressed', String(b === usePick)));
      }
      if (usePick.dataset.usageDay) spentDay = usePick.dataset.usageDay;
      if (usePick.dataset.usageStep) spentDay = spent.days[spent.days.findIndex((x) => x.day === spentDay) + Number(usePick.dataset.usageStep)]?.day ?? spentDay;
      const box = $('#usage-body');
      box.classList.add('still');
      box.innerHTML = usageBody();
      return undefined;
    }
    const retry = e.target.closest('[data-retry]'), globeBtn = e.target.closest('[data-globe]'), reveal = e.target.closest('[data-reveal]');
    if (retry) return route();
    const done = e.target.closest('[data-mail-done]');
    if (done) {
      fetch(`/api/mail/${done.dataset.mailDone}/${done.dataset.state}`, { method: 'PUT', headers: { 'x-paper': '1' } }).then(() => { dispatchEvent(new Event('paper:reload')); go('/#mail'); });
      return undefined;
    }
    if (reveal) {
      reveal.setAttribute('aria-pressed', String(reveal.classList.toggle('clear')));
      return undefined;
    }
    if (globeBtn) {
      const [lat, lon] = globeBtn.dataset.globe.split(',').map(Number);
      history.pushState(null, '', '/#orb');
      route().then(() => fly(lat, lon));
      return undefined;
    }
    const a = e.target.closest('a[href^="/"]');
    if (!a || a.target || ['/settings', '/ask'].includes(a.pathname) || e.metaKey || e.ctrlKey || e.shiftKey || e.button) return undefined;
    e.preventDefault();
    go(a.getAttribute('href'));
    return undefined;
  });
  route();
}
