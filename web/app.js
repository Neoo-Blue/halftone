import { makeGlobe } from '/globe.js';
import { $, $$, esc, usd, whole, dollars, pct, plural, ago, span, bytes, dayName, dayKey, when, ICON, lineChart, dayBars, look, lookPicker, tight } from '/lib.js';
import { showDock, openDock } from '/dock.js';
import { start, go, reading, picture, eventHref, isFront } from '/detail.js';
import { startPhone, onPhone, phoneCheck } from '/phone.js';

const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
const THEMES = ['morning', 'night', 'cobalt', 'glass'];
const DESKS = [['sports', 'sports'], ['mail', 'mail'], ['business', 'money'], ['usage', 'usage'], ['arts', 'media'], ['systems', 'systems']];
const KIND = { k: 'Conflict', e: 'Economy', h: 'Hazard' };
const NEWS = ['world', 'us', 'business'], TECH = ['tech', 'ai', 'security', 'science'];
const WIRES = {
  world: { el: '#wire', tab: 'all', more: 14, tabs: [['all', 'Latest'], ['world', 'World'], ['us', 'US'], ['business', 'Business'], ['k', 'Conflict']] },
  tech: { el: '#techwire', tab: 'all', more: 14, tabs: [['all', 'Latest'], ['ai', 'AI'], ['tech', 'Tech'], ['security', 'Security'], ['science', 'Science']] },
  sports: { el: '#sportswire', tab: 'all', more: 10, tabs: [['all', 'Latest']] },
};
let league = 'all';

let saving = 0, saves = Promise.resolve();
let paper = null, days = 30, problems = false, drawn = false, globe = null, dotsKey = '', labelsKey = '';
let sort = { key: 'cents', dir: -1 };
const open = new Set(['Proxmox']);
const issueHref = (i) => `/issue/${i.slug}`;

function asof(el, source, s) {
  if (!s) return;
  const stale = s.error ? ` The last try failed, so this is the last good copy.` : '';
  el.textContent = s.as_of ? `${source}, ${ago(s.as_of)}.${stale}` : s.error ? `${source} has not answered yet.` : `Waiting for ${source}.`;
  el.classList.toggle('stale', !!s.error);
}

// ---------------------------------------------------------------- front page

function front(p) {
  const now = new Date(p.now * 1000);
  $('#dateline').textContent = now.toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' });
  $('#edition').innerHTML = `<span class="not-phone">Vol. I, No. ${esc(p.edition)}${p.news.as_of ? '. ' : ''}</span>${p.news.as_of ? `News updated ${esc(ago(p.news.as_of))}` : ''}`;
  $('#note').textContent = p.note || 'The first edition is still on the press.';
  $('#colophon-time').textContent = `Updated ${now.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' })}`;

  const m = p.money, w = p.world.data, pr = (p.probes.data || []).filter((x) => !x.gated), med = p.media.data;
  const bad = p.worries.filter((x) => x.level).length;
  const fresh = (med?.added || []).filter((a) => (a.at || 0) >= p.now - 86400).length;
  const wx = p.weather.data;
  const rows = [
    wx && ['Weather', '/weather', `${wx.now.temp}\u00b0 ${wx.now.sky}`, ''],
    p.on.systems && ['Systems', '/#systems', pr.length ? (bad ? plural(bad, 'issue') : `${pr.length} of ${pr.length} up`) : 'Checking', bad ? 'bad' : 'good'],
    p.on.money && [`${m ? m.days : 30}-day result`, '/#business', m ? `${m.result > 0 && m.missing.length ? 'At most ' : ''}${usd(m.result)}` : 'Counting', m && m.result < 0 ? 'neg' : ''],
    p.on.usage && p.usage.last && ['AI, last day', '/usage', dollars(p.usage.last.worth), ''],
    p.invest.total != null && ['Investments', '/investments', `${dollars(p.invest.total)}${p.invest.gain == null ? '' : ` ${p.invest.gain < 0 ? '-' : '+'}${dollars(Math.abs(p.invest.gain))}`}`, p.invest.gain < 0 ? 'neg' : p.invest.gain > 0 ? 'pos' : ''],
    p.on.mail && ['Mail', '/#mail', (p.mail?.need || []).length ? `${p.mail.need.length} need you` : p.mail_status?.as_of ? 'Nothing urgent' : 'Checking', (p.mail?.need || []).length ? 'bad' : ''],
    p.on.media && ['Plex today', '/#arts', med ? (fresh ? `${fresh} new` : 'Nothing new') : 'Checking', ''],
    p.on.world && ['World tension', '/#world', w ? `${Math.round(w.index?.value ?? w.index ?? 0)} of 100` : 'Waiting', ''],
    p.shelf.saved.length > 0 && ['Saved stories', '/saved', p.shelf.saved.length, ''],
  ].filter(Boolean);
  $('#glance').innerHTML = rows.map(([k, h, v, c]) => `<div><dt><a href="${esc(h)}">${esc(k)}</a></dt><dd class="${c}">${esc(v)}</dd></div>`).join('');

  const next = med?.upcoming?.[0];
  const trouble = p.worries.find((x) => x.level), need = p.mail?.need || [];
  const inside = [
    need[0] && [`/mail/${need[0].id}`, `${need[0].sender}: ${need[0].why || need[0].subject}`],
    trouble && ['/#systems', trouble.text],
    p.brief.data && [issueHref(p.brief.data), `Today's brief: ${p.brief.data.headline}`],
    w?.alerts?.[0] && [w.alerts[0].theater ? `/world/theater/${w.alerts[0].theater}` : '/#world', w.alerts[0].t],
    m && ['/#business', `${plural(m.visitors, 'real visitor')} and ${plural(m.abandoned, 'unfinished checkout')} in ${m.days} days`],
    next && [next.kind === 'movie' ? `/arts/movie/${next.id}` : `/arts/show/${next.id}`, `${next.title} ${next.kind === 'movie' ? 'arrives' : 'airs'} ${when(next)}`],
    !p.on.mail && !p.on.money && !p.on.media && !p.on.systems && ['/settings', 'Add your mail, money, media and servers in Settings'],
  ].filter(Boolean);
  $('#inside').innerHTML = inside.length ? `<h2>Inside</h2><ul>${inside.map(([h, t]) => `<li><a href="${esc(h)}">${esc(t)}</a></li>`).join('')}</ul>` : '';

  const ed = $('#editor');
  ed.hidden = !p.editor.data?.text;
  if (p.editor.data?.text) ed.innerHTML = `<p>${esc(p.editor.data.text)}</p><small>Written by AI from today's wire, ${esc(ago(p.editor.data.at || p.editor.as_of))}. It can be wrong.</small>`;
  $('#trend-tags').innerHTML = (p.news.data?.trending || []).length ? `<h2>Trending</h2>${p.news.data.trending.map((t) => `<a href="/topic/${encodeURIComponent(t.name)}">${esc(t.name)}<b>${t.n}</b></a>`).join('')}` : '';

  const L = p.news.data?.lead;
  if (L) {
    const story = reading(L.via?.u || L.u), also = p.news.data.also || [];
    $('#lead').innerHTML = `
      ${L.img ? `<a class="lead-photo ink only-phone" href="${story}" tabindex="-1" aria-hidden="true"><img src="${esc(picture(L.img))}" alt=""></a>` : ''}
      <h1 class="headline"><a href="${story}">${tight(L.t)}</a></h1>
      ${L.sum ? `<p class="deck">${esc(L.sum)}</p>` : ''}
      ${L.text ? `<div class="lead-body">${L.text}</div>` : ''}
      <p class="byline">${esc(covered(L))}. Updated ${esc(ago(L.ts))}.${L.via && L.via.u !== L.u ? ` Text from ${esc(L.via.src)}.` : ''} <a href="${story}">Read the story</a></p>
      ${also.length ? `<h2 class="also-head">Also in the news</h2><ul class="also">${also.map((n) => `<li><a href="${reading(n.u)}">${esc(n.t)}</a><span>${esc(n.n > 1 ? `${n.src} and ${n.n - 1} more` : n.src)}, ${esc(ago(n.ts))}</span></li>`).join('')}</ul>` : ''}`;
  }
}

// As many extra headlines as the lead column has room for, so it ends level with the globe and never runs past it.
function fitAlso() {
  const list = $('.also');
  if (!list) return;
  const room = Math.max($('#orb').getBoundingClientRect().bottom, $('#inside').getBoundingClientRect().bottom);  // their own heights: the column itself stretches to the tallest
  while (list.lastElementChild && list.getBoundingClientRect().bottom > room) list.lastElementChild.remove();
  if (!list.children.length) { list.previousElementSibling.remove(); list.remove(); }
}

// "BBC, New York Times and 4 more": who carried it, which is also why it ranks where it does.
function covered(s) {
  const names = (s.outlets || [{ src: s.src }]).map((o) => o.src), n = s.n ?? names.length;
  if (n <= 1) return names[0];
  return s.outlets ? `${names.slice(0, 2).join(n === 2 ? ' and ' : ', ')}${n > 2 ? ` and ${n - 2} more` : ''}` : `${names[0]} and ${n - 1} more`;
}

function tech(p) {
  const d = p.news.data, b = p.brief.data, L = d?.tech_lead;
  const earlier = (b?.earlier || []).map((i) => `<li><a href="${issueHref(i)}"><b>${esc(i.title)}</b><span>${esc(i.meta)}</span></a></li>`).join('');
  $('#techbody').classList.toggle('solo', !b && !earlier);
  $('#techbody').innerHTML = `
    <div class="tech-main">
      ${L ? `<a class="tech-lead" href="${reading(L.u)}"><span class="photo"><img src="${picture(L.img)}" alt="" loading="lazy"></span><span><h3 class="sub-head">${tight(L.t)}</h3>${L.sum ? `<span class="tech-sum">${esc(L.sum)}</span>` : ''}<span class="tech-by">${esc(covered(L))}, ${esc(ago(L.ts))}</span></span></a>` : ''}
      <div class="wire" id="techwire"></div>
    </div>
    <aside class="earlier"${!b && !earlier ? ' hidden' : ''}>
      ${b ? `<h3>The daily brief</h3><a class="daily" href="${issueHref(b)}"><b>${tight(b.headline)}</b><span>${esc(b.deck)}</span><span>${esc(b.meta || b.title)}</span></a>` : ''}
      ${earlier ? `<h3>Earlier issues</h3><ul>${earlier}</ul>` : ''}
    </aside>`;
  wireList(p, 'tech');
  const st = p.news;
  $('#asof-tech').textContent = st.as_of ? `Wire updated ${ago(st.as_of)}.` : 'Waiting for the wire.';
}

// ---------------------------------------------------------------- world

function world(p) {
  const w = p.world.data;
  const nd = p.news.data;
  $('#asof-world').textContent = `${nd ? `News from ${nd.feeds} of ${nd.total} feeds, updated ${ago(p.news.as_of)}. ` : ''}${p.on.world ? `WARROOM ${ago(p.world.as_of)}.` : ''}`;
  $('#asof-world').classList.toggle('stale', !!(p.news.error || p.world.error));
  if (!w) {
    $('#worldbody').innerHTML = `<div class="wire" id="wire"></div><div class="world-main"><p class="empty">${p.on.world ? 'WARROOM has not reported yet.' : 'Add WARROOM in Settings for the globe and the conflict desk.'}</p></div>`;
    wireList(p, 'world');
    return;
  }
  const idx = Math.round(w.index?.value ?? w.index ?? 0);
  const assessed = w.assessed != null ? `The analyst's hourly reading, ${ago(w.ts)}, was ${Math.round(w.assessed)}, on a narrower window than the live index. ` : '';
  const fc = w.forecast.map((f) => `<li><span class="odds" style="--v:${Math.round((f.probability || 0) * 100)}"><i></i></span><b>${Math.round((f.probability || 0) * 100)}%</b><span class="fc-t">${esc(f.statement)} <em>${esc(f.horizon)}</em></span></li>`).join('');
  const claim = { confirmed: 'Confirmed', reported: 'Reported', claimed: "One side's claim" };
  const front = (w.front || []).map((s) => {
    const ref = (s.refs || []).find((r) => /^[0-9a-f]{32}$/.test(r));
    return `<li><span class="claim ${esc(s.certainty)}">${esc(claim[s.certainty] || s.certainty)}${s.where ? `, ${esc(s.where)}` : ''}</span>
      <h4>${ref ? `<a href="${eventHref({ k: 'k', i: ref })}">${esc(s.headline)}</a>` : esc(s.headline)}</h4>
      <p class="prose">${esc(s.what_happened)}</p>
      <p class="prose"><b>Why it matters.</b> ${esc(s.why_it_matters)}</p>
      <p class="prose"><b>What to watch.</b> ${esc(s.what_next)}</p></li>`;
  }).join('');
  const alerts = w.alerts.map((a) => `<li><a href="${a.theater ? `/world/theater/${esc(a.theater)}` : '/#world'}">${esc(a.t)}</a><time>${esc(ago(a.ts))}</time></li>`).join('');
  const haz = w.hazards ? `${whole(w.hazards.red)} red and ${whole(w.hazards.orange)} orange disaster alerts are open.` : '';
  const sp = w.space ? ` Space weather: Kp ${esc(w.space.kp)}, ${w.space.g === 'none' ? 'no geomagnetic storm' : esc(w.space.g)}.` : '';
  const as = w.assets ? `Tracking ${whole(w.assets.vessels)} ships, ${whole(w.assets.aircraft)} aircraft and ${whole(w.assets.satellites)} satellites.` : '';
  $('#worldbody').innerHTML = `
    <div class="wire" id="wire"></div>
    <div class="world-main">
      ${front ? `<h3 class="sub-head">What matters today</h3><ol class="world-stories">${front}</ol>` : ''}
      <h3 class="sub-head">The escalation index stands at ${idx}</h3>
      <p class="prose">${esc(assessed)}${esc(w.rationale || w.headline)}</p>
      ${w.most ? `<p class="prose">${esc(w.most)}</p>` : ''}
      <h4>Odds for the next hours</h4>
      <ol class="forecast">${fc}</ol>
    </div>
    <div class="world-side">
      <h4>Surges this week</h4>
      <ul class="plain">${alerts || '<li>Nothing new.</li>'}</ul>
      <p class="small">${esc(haz)}${sp} ${esc(as)}</p>
    </div>
    ${w.markets.length ? `<div class="world-markets">
      <h4>Markets</h4>
      <table class="num-table"><thead><tr><th scope="col">Market</th><th scope="col" class="r">Last</th><th scope="col" class="r">Change</th></tr></thead>
      <tbody>${w.markets.slice(0, 14).map((m) => `<tr title="${esc(m.why)}"><th scope="row"><a href="/world/market/${esc(m.key)}">${esc(m.label)}</a></th><td class="r">${m.last == null ? '' : Number(m.last).toLocaleString('en-US', { maximumFractionDigits: 2 })}</td><td class="r ${(m.pct || 0) < 0 ? 'neg' : 'pos'}">${(m.pct || 0) < 0 ? ICON.down : ICON.up} ${Math.abs(m.pct || 0).toFixed(1)}%</td></tr>`).join('')}</tbody></table>
    </div>` : ''}`;
  wireList(p, 'world');

  $('#theaters').innerHTML = w.theaters.slice(0, 5).map((t) => `<li><a href="/world/theater/${esc(t.id)}">${esc(t.name)}</a><b>${t.esc}</b>${t.lat == null ? '' : `<button type="button" class="locate" data-fly="${esc(t.lat)},${esc(t.lon)}" aria-label="Show ${esc(t.name)} on the globe"><svg viewBox="0 0 16 16" aria-hidden="true"><circle cx="8" cy="8" r="4.2"/><path d="M8 1v3.2M8 11.8V15M1 8h3.2M11.8 8H15"/></svg></button>`}</li>`).join('');
  if (globe) {
    const key = w.dots.length + (w.ts || '');
    if (key !== dotsKey) { dotsKey = key; globe.setDots(w.dots); }
    const placed = w.theaters.filter((t) => t.lat != null).slice(0, 4), lk = placed.map((t) => t.id).join();  // a trade war has no spot on the map, so the next theater takes the label
    if (lk !== labelsKey) { labelsKey = lk; globe.setLabels(placed, $('#labels')); }
  }
}

// One running list per desk, newest first: each line is one story, however many outlets carried it.
function wireList(p, name) {
  const W = WIRES[name], el = $(W.el), read = new Set(p.shelf.read);
  if (!el) return;
  const desks = { world: NEWS, tech: TECH, sports: ['sports'] }[name];
  const heads = (p.news.data?.wire || []).filter((n) => n.desks.some((d) => desks.includes(d))).map((n) => ({ t: n.t, href: reading(n.u), u: n.u, by: n.n > 1 ? `${n.src} and ${n.n - 1} more` : n.src, ts: n.ts, tabs: n.desks, wide: n.n >= 3 }));
  const reports = name === 'world' ? (p.world.data?.stories || []).map((s) => ({ t: s.t, href: eventHref(s), by: s.src, ts: s.ts, tabs: s.s >= 0.55 ? [s.k, 'all'] : [s.k] })) : [];
  const rows = [...heads, ...reports].filter((r) => (W.tab === 'all' ? heads.includes(r) || r.tabs.includes('all') : r.tabs.includes(W.tab))).sort((a, b) => (b.ts || 0) - (a.ts || 0));
  el.innerHTML = `<div class="wire-top"><h3 class="sub-head">The wire</h3><div class="seg" role="group" aria-label="Filter the wire"${W.tabs.length > 1 ? '' : ' hidden'}>${W.tabs.map(([k, t]) => `<button type="button" data-wire="${name}:${k}" aria-pressed="${k === W.tab}">${t}</button>`).join('')}</div></div>
    <ul class="wire-list two">${rows.slice(0, W.more).map((r) => `<li class="${r.wide ? 'wide-story' : ''}${read.has(r.u) ? ' read' : ''}"><a href="${esc(r.href)}">${esc(r.t)}</a><span>${esc(r.by)}, ${esc(ago(r.ts))}</span></li>`).join('') || '<li>Nothing on this line yet.</li>'}</ul>
    ${rows.length > W.more ? `<button type="button" class="ghost text" data-more="${name}">Show ${Math.min(20, rows.length - W.more)} more</button>` : ''}`;
}

function tops(p) {
  const n = p.news.data?.tops || [];
  if (n.length < 3) return;
  $('#tops').innerHTML = n.slice(0, 4).map((s) => `<a class="top" href="${reading(s.u)}"><span class="photo"><img src="${picture(s.img)}" alt="" loading="lazy"></span><b>${esc(s.t)}</b><span>${esc(covered(s))}, ${esc(ago(s.ts))}</span></a>`).join('');
}

// ---------------------------------------------------------------- sports

function gameCard(g) {
  const side = (t) => `<span class="${g.state === 'post' && t.won ? 'won' : ''}"><b>${esc(t.name)}</b>${t.record ? `<small>${esc(t.record)}</small>` : ''}<em>${g.state === 'pre' ? '' : esc(t.score)}</em></span>`;
  const clock = g.state === 'pre' ? new Date(g.at * 1000).toLocaleString('en-US', { weekday: 'short', hour: 'numeric', minute: '2-digit' }) : g.status;
  return `<li class="game ${g.state === 'in' ? 'live' : ''}"><a href="/topic/${encodeURIComponent(String(g.home.name).toWellFormed())}"><p class="game-time">${g.state === 'in' ? '<i></i>' : ''}${esc(clock)}</p>${side(g.away)}${side(g.home)}${g.note ? `<p class="game-note">${esc(g.note)}</p>` : ''}</a></li>`;
}

const across = (n) => (n % 4 === 1 ? 3 : 4);  // so no game sits alone on the last row

function sports(p) {
  const all = p.sports.data || [], el = $('#sportsbody');
  asof($('#asof-sports'), 'Scores', p.sports);
  if (league !== 'all' && !all.some((l) => l.key === league)) league = 'all';
  const shown = all.filter((l) => league === 'all' || l.key === league);
  const live = all.reduce((n, l) => n + l.games.filter((g) => g.state === 'in').length, 0);
  const tabs = [['all', 'All'], ...all.filter((l) => l.games.length).map((l) => [l.key, l.name])];
  el.innerHTML = !all.length ? '<p class="empty">The first scores are on their way.</p>' : `
    <div class="wire-top"><h3 class="sub-head">${live ? `${plural(live, 'game')} on now` : 'Scores'}</h3>
      <div class="seg" role="group" aria-label="Filter by league">${tabs.map(([k, t]) => `<button type="button" data-league="${esc(k)}" aria-pressed="${k === league}">${esc(t)}</button>`).join('')}</div></div>
    ${shown.filter((l) => l.games.length).map((l) => `<h4>${esc(l.name)}</h4><ul class="games" style="--cols:${across(Math.min(l.games.length, league === 'all' ? 6 : 20))}">${l.games.slice(0, league === 'all' ? 6 : 20).map(gameCard).join('')}</ul>`).join('') || '<p class="empty">No games today.</p>'}`;
  wireList(p, 'sports');
}

// ---------------------------------------------------------------- mail
const CAT = { money: 'Money', customer: 'Customer', security: 'Security', legal: 'Legal', noise: 'Filtered' };
let mailBox = 'all', mailNoise = false;

function mailRow(m, action) {
  const label = m.sorted ? (CAT[m.cat] || 'Other') : 'Not sorted yet';
  return `<li class="${m.unread ? 'unread' : ''}"><a href="/mail/${esc(m.id)}"><b>${esc(m.why || m.subject)}</b><span>${esc(m.sender)}, ${esc(m.subject)}</span><span>${esc(label)} in ${esc(m.box)}${m.junk ? ', spam folder' : ''}, ${esc(ago(m.at))}</span></a>${action ? `<button type="button" class="ghost text" data-done="${esc(m.id)}">Done</button>` : ''}</li>`;
}

function mail(p) {
  const d = p.mail, st = p.mail_status, el = $('#mailbody'), need = d?.need || [];
  const count = $('#mail-count');
  count.hidden = !need.length;
  count.textContent = need.length || '';
  if (!st?.as_of && !st?.error) {
    el.innerHTML = '<p class="empty">The first mail check is still running.</p>';
    return;
  }
  const boxes = [...new Set((d.rest || []).map((m) => m.box))];
  const inBox = (d.rest || []).filter((m) => mailBox === 'all' || m.box === mailBox);
  const filtered = inBox.filter((m) => m.cat === 'noise').length;
  const rest = mailNoise ? inBox : inBox.filter((m) => m.cat !== 'noise');
  const s = st.data || {};
  const trouble = [s.failed?.length ? `Could not read ${s.failed.join(', ')}.` : '', s.triage_error ? 'Sorting is down, so new mail waits under Not sorted yet.' : ''].filter(Boolean).join(' ');
  $('#asof-mail').textContent = `Reading ${s.read ?? 0} of ${d.boxes.length} mailboxes, ${ago(st.as_of)}. Read only: nothing in your mailboxes changes.`;
  $('#asof-mail').classList.toggle('stale', !!st.error);
  el.innerHTML = `
    <h3 class="sub-head">${need.length ? `${need.length} ${need.length === 1 ? 'email needs' : 'emails need'} you` : 'Nothing needs you'}</h3>
    ${trouble ? `<p class="prose">${esc(trouble)}</p>` : ''}
    ${need.length ? `<ul class="mail-list">${need.map((m) => mailRow(m, true)).join('')}</ul>` : ''}
    ${d.unsorted.length ? `<h4>Not sorted yet</h4><ul class="mail-list">${d.unsorted.map((m) => mailRow(m, true)).join('')}</ul>` : ''}
    <div class="mail-rest"><h4>Everything else</h4>
      <div class="mail-tools"><label class="mail-filter"><input type="checkbox" id="mail-noise"${mailNoise ? ' checked' : ''}> Show ${filtered} filtered</label>
      <label class="mail-filter">Mailbox <select id="mail-box"><option value="all">All</option>${boxes.map((b) => `<option${b === mailBox ? ' selected' : ''}>${esc(b)}</option>`).join('')}</select></label></div>
    </div>
    ${rest.length ? `<ul class="mail-list quiet">${rest.slice(0, mailNoise ? 120 : 24).map((m) => mailRow(m, false)).join('')}</ul>` : '<p class="empty">Nothing else in the last two weeks.</p>'}`;
}

// ---------------------------------------------------------------- business

function verdict(m) {
  const blanks = m.missing.length;
  const also = blanks ? ` ${plural(blanks, 'cost')} still ${blanks === 1 ? 'has' : 'have'} no amount, so the true figure is lower.` : '';
  if (m.result > 0 && blanks) return [`At most ${usd(m.result)} ahead over ${m.days} days.`, also];
  if (m.result > 0) return [`Yes. You are ${usd(m.result)} ahead over ${m.days} days.`, also];
  if (m.result === 0) return [`Even over the last ${m.days} days.`, also];
  return [`Not yet. You are ${usd(-m.result)} down over ${m.days} days.`, also];
}

function dotChart(daily) {
  const max = Math.max(...daily.map((d) => d.cents), 1), rows = 7, n = daily.length, w = Math.max(10, 560 / n), r = Math.min(3.2, w * 0.3);
  let out = '';
  daily.forEach((d, i) => {
    const on = d.cents ? Math.max(1, Math.round((d.cents / max) * rows)) : 0, x = i * w + w / 2;
    for (let j = 0; j < Math.max(on, 1); j += 1) out += `<circle cx="${x}" cy="${86 - j * 12}" r="${r}" class="${on ? 'on' : 'off'}"/>`;
    out += `<rect x="${i * w}" y="0" width="${w}" height="100" data-tip="${esc(dayName(`${d.day}T12:00:00`))}: ${esc(d.cents ? usd(d.cents) : 'no sales')}"/>`;
  });
  const best = Math.max(...daily.map((d) => d.cents));
  return `<p class="chart-note">${best ? `Best day ${usd(best)}. Each column is one day.` : 'No sales in this period.'}</p><svg class="dotchart" viewBox="0 0 ${n * w} 100" role="img" aria-label="Sales per day for the last ${n} days. The highest day was ${usd(Math.max(...daily.map((d) => d.cents)))}.">${out}</svg>`;
}

const COLS = [['name', 'Product'], ['cents', 'Sales', 1], ['orders', 'Orders', 1], ['mrr', 'Monthly', 1], ['visitors', 'Visitors', 1], ['abandoned', 'Left checkout', 1]];

function productsTable(m, probes) {
  const up = Object.fromEntries((probes || []).map((p) => [p.name, p]));
  const rows = [...m.products].sort((a, b) => {
    const x = a[sort.key], y = b[sort.key];
    return (typeof x === 'string' ? x.localeCompare(y) : x - y) * sort.dir || b.visitors - a.visitors;
  });
  const head = COLS.map(([k, t, r]) => `<th scope="col" class="${r ? 'r' : ''} ${k === 'abandoned' || k === 'orders' ? 'wide' : ''}" aria-sort="${sort.key === k ? (sort.dir < 0 ? 'descending' : 'ascending') : 'none'}"><button type="button" data-sort="${k}">${t}</button></th>`).join('');
  const body = rows.map((r) => {
    const st = up[r.name];
    const dot = st ? `${st.up ? ICON.good : ICON.bad}<span class="vh">${st.up ? 'Up' : 'Down'}</span>` : '';
    return `<tr><th scope="row">${dot}${r.host ? `<a href="/business/${esc(r.site)}">${esc(r.name)}</a>` : esc(r.name)}</th>
      <td class="r">${r.cents ? usd(r.cents) : '<span class="nil">0</span>'}</td><td class="r wide">${r.orders || '<span class="nil">0</span>'}</td>
      <td class="r">${r.mrr ? usd(r.mrr) : '<span class="nil">0</span>'}</td><td class="r">${r.visitors ? whole(r.visitors) : '<span class="nil">0</span>'}</td>
      <td class="r wide">${r.abandoned || '<span class="nil">0</span>'}</td></tr>`;
  }).join('');
  return `<table class="num-table products"><caption>Every product, ${m.days} days</caption><thead><tr>${head}</tr></thead><tbody>${body}</tbody></table>`;
}

function ledger(m) {
  const line = (t, c, cls = '') => `<tr class="${cls}"><th scope="row">${esc(t)}</th><td class="r">${c}</td></tr>`;
  const minus = (c) => (c ? `-${usd(c)}` : usd(0));
  const missing = m.missing.length ? `<tr class="gap"><th scope="row">No amount yet</th><td class="r">${esc(m.missing.join(', '))}</td></tr>` : '';
  return `<table class="ledger"><caption>The last ${m.days} days</caption><tbody>
    ${line('Sales', usd(m.gross))}
    ${line('Refunds', minus(m.refunds))}
    ${line('Stripe fees, estimated', minus(m.fees))}
    ${line('Marketing and AI', minus(m.spend))}
    ${m.known.map((k) => line(k.name, minus(k.cents))).join('')}
    ${missing}
    ${line('Result', usd(m.result), `total ${m.result < 0 ? 'neg' : ''}`)}
  </tbody></table>`;
}

function costRow(c = { name: '', cents: null, per: 'month' }) {
  if (c.note) return `<li class="cost-row cost-auto"><span>${esc(c.name)}</span><b>${usd(c.cents)} a ${esc(c.per)}</b><small>${esc(c.note)}</small></li>`;
  return `<li class="cost-row">
    <input class="c-name" aria-label="Cost name" value="${esc(c.name)}" maxlength="60" placeholder="Name">
    ${c.connect ? `<a class="c-connect" href="/settings#set-${esc(c.connect)}">Connect</a><input class="c-amount" type="hidden" value="">` : `<input class="c-amount" aria-label="Amount in dollars" inputmode="decimal" value="${c.cents == null ? '' : (c.cents / 100).toFixed(2)}" placeholder="Amount">`}
    <select class="c-per" aria-label="How often"><option value="month"${c.per === 'month' ? ' selected' : ''}>a month</option><option value="year"${c.per === 'year' ? ' selected' : ''}>a year</option></select>
    <button type="button" class="ghost" data-remove aria-label="Remove ${esc(c.name || 'this cost')}"><svg viewBox="0 0 16 16" aria-hidden="true"><path d="M3.5 3.5l9 9M12.5 3.5l-9 9"/></svg></button>
  </li>`;
}

function business(p) {
  const m = p.money, el = $('#bizbody');
  asof($('#asof-biz'), 'The money report', { as_of: p.money_as_of, error: p.money_error });
  if (!m) {
    el.innerHTML = '<p class="empty">The money report has not come in yet.</p>';
    return;
  }
  const [head, also] = verdict(m);
  const sales = m.gross ? `${usd(m.gross)} in sales, ${plural(m.orders, 'new order')},` : 'No product has sold anything';
  const first = m.lifetime.earlier[0];
  const month = first ? new Date(`${first.day}T12:00:00`).toLocaleDateString('en-US', { month: 'long' }) : '';
  const story = `${sales} in ${m.days} days. ${plural(m.visitors, 'real person', 'real people')} visited, and ${plural(m.abandoned, 'checkout')} started without finishing.${also} All-time income is ${usd(m.lifetime.cents)}${m.lifetime.reported || !first ? '' : `, one ${first.label} in ${month}`}.`;
  if (!$('#biz-head', el)) {
    el.innerHTML = `
      <div class="biz-top">
        <div id="biz-head"></div>
        <div class="seg" role="group" aria-label="Period">${[7, 30, 90].map((d) => `<button type="button" data-days="${d}">${d} days</button>`).join('')}</div>
      </div>
      <div class="biz-grid">
        <div id="biz-ledger"></div>
        <div class="biz-mid"><h4>Sales per day</h4><div id="biz-chart"></div>
          <h4>What it costs to run</h4>
          <ul class="costs" id="costs"></ul>
          <div class="cost-foot"><button type="button" class="ghost text" id="add-cost">Add a cost</button><span id="cost-state" role="status"></span></div>
        </div>
      </div>
      <div id="biz-products"></div>`;
  }
  $('#biz-head').innerHTML = `<h3 class="sub-head">${esc(head)}</h3><p class="prose">${esc(story)}</p>`;
  $('#biz-ledger').innerHTML = ledger(m);
  $('#biz-chart').innerHTML = dotChart(m.daily);
  $('#biz-products').innerHTML = productsTable(m, p.probes.data);
  $$('[data-days]', el).forEach((b) => b.setAttribute('aria-pressed', String(Number(b.dataset.days) === days)));
  const list = $('#costs');
  if (!saving && !list.contains(document.activeElement)) list.innerHTML = p.costs.map(costRow).join('');
}

function readCosts() {
  const rows = [];
  for (const li of $$('#costs .cost-row:not(.cost-auto)')) {
    const name = $('.c-name', li).value.trim(), raw = $('.c-amount', li).value.replace(/[$,\s]/g, '');
    const amount = $('.c-amount', li);
    const bad = raw !== '' && !/^\d+(\.\d{0,2})?$/.test(raw);
    amount.setAttribute('aria-invalid', String(bad));
    if (bad) return { error: 'Use an amount like 12.50.' };
    if (name) rows.push({ name, cents: raw === '' ? null : Math.round(Number(raw) * 100), per: $('.c-per', li).value });
  }
  return { rows };
}

// Saves run one at a time, each carrying the list as it stood when you acted, and the list only redraws once they have all landed.
// Without this, an edit followed quickly by a delete sent two saves and the older one could bring the row back.
function saveCosts() {
  const state = $('#cost-state'), { rows, error } = readCosts();
  if (error) { state.textContent = error; return; }
  state.textContent = 'Saving';
  saving += 1;
  saves = saves.then(async () => {
    try {
      const r = await fetch('/api/costs', { method: 'PUT', headers: { 'content-type': 'application/json', 'x-paper': '1' }, body: JSON.stringify({ rows }) });
      if (!r.ok) throw new Error((await r.json()).error);
      state.textContent = 'Saved';
    } catch (e) {
      state.textContent = e.message && !e.message.includes('fetch') ? e.message : 'Could not save. Check your connection and try again.';
    }
    saving -= 1;
    if (!saving) await load();
  });
}

// ---------------------------------------------------------------- arts

function poster(a, big = false) {
  const img = a.art ? `<img src="${esc(a.art)}" alt="" loading="lazy" decoding="async">` : '';
  const badge = a.res === '4k' ? '<b class="res">4K</b>' : '';
  const inner = `<span class="poster">${img}${badge}</span><span class="p-t">${esc(a.title)}</span><span class="p-s">${esc(a.sub)}</span>`;
  return `<li class="${big ? 'big' : ''}"><a href="/arts/plex/${esc(a.key)}" title="${esc(a.about || a.title)}">${inner}</a></li>`;
}

function arts(p) {
  const med = p.media.data, el = $('#artsbody');
  asof($('#asof-arts'), 'Your library', p.media);
  if (!med) {
    el.innerHTML = '<p class="empty">Plex has not reported yet.</p>';
    return;
  }
  const playing = (p.playing.data || []).map((s) => `<li>${ICON.good}<b>${esc(s.title)}</b> <span>${esc(s.who)} on ${esc(s.device)}${s.pct != null ? `, ${s.pct}% in` : ''}, ${esc(s.mode)}</span></li>`).join('');
  const days_ = {};
  for (const u of med.upcoming) {
    const list = (days_[dayKey(u)] ||= []), same = list.find((x) => x.title === u.title);
    if (same) same.sub = `${(same.n = (same.n || 1) + 1)} episodes`;
    else list.push({ ...u });
  }
  const agenda = Object.entries(days_).sort(([a], [b]) => a.localeCompare(b)).slice(0, 7).map(([d, list]) => `<li class="day"><h5>${esc(dayName(`${d}T12:00:00`))}</h5><ul>${list.map((u) => `<li><a href="/arts/${u.kind === 'movie' ? 'movie' : 'show'}/${esc(u.id)}">${u.art ? `<img src="${esc(u.art)}" alt="" loading="lazy">` : ''}<div><b>${esc(u.title)}</b><span>${esc(u.sub)}</span></div></a></li>`).join('')}</ul></li>`).join('');
  const libs = med.libraries.map((l) => `${whole(l.count)} ${l.title.toLowerCase()}`).join(' and ');
  const req = med.requests ? ` Seerr shows ${whole(med.requests.processing)} requests in progress and ${whole(med.requests.pending)} waiting for approval.` : '';
  el.innerHTML = `
    ${playing ? `<div class="playing"><h4>Playing now</h4><ul class="plain">${playing}</ul></div>` : ''}
    <h3 class="sub-head">Just added</h3>
    ${med.added.length ? `<ul class="rail">${med.added.map((a) => poster(a)).join('')}</ul>` : '<p class="empty">Nothing new has landed.</p>'}
    <h3 class="sub-head">Coming up</h3>
    ${agenda ? `<ol class="agenda">${agenda}</ol>` : '<p class="empty">Nothing is scheduled in the next two weeks.</p>'}
    <p class="small">The library holds ${esc(libs)}.${esc(req)}</p>`;
}

// ---------------------------------------------------------------- systems

function meter(v, warn = 80, bad = 92) {
  const cls = v >= bad ? 'bad' : v >= warn ? 'warn' : '';
  return `<span class="meter ${cls}" style="--v:${Math.min(100, v).toFixed(1)}"><i></i></span><b>${Math.round(v)}%</b>`;
}

function guestsTable(guests) {
  return `<table class="num-table guests"><thead><tr><th scope="col">Container</th><th scope="col">State</th><th scope="col" class="r">CPU</th><th scope="col" class="r">Memory</th><th scope="col" class="r wide">Disk</th><th scope="col" class="r wide">Up</th></tr></thead><tbody>
    ${guests.map((g) => `<tr class="${g.status === 'running' ? '' : 'off'}"><th scope="row"><a href="/systems/container/${g.id}">${g.id} ${esc(g.name)}</a></th><td>${g.status === 'running' ? 'Running' : 'Stopped'}</td><td class="r">${g.status === 'running' ? `${g.cpu}%` : ''}</td><td class="r">${g.status === 'running' ? `${bytes(g.mem)} of ${bytes(g.maxmem)}` : ''}</td><td class="r wide">${bytes(g.maxdisk)}</td><td class="r wide">${span(g.uptime)}</td></tr>`).join('')}
  </tbody></table>`;
}

const machineHref = (h) => `/systems/machine/${encodeURIComponent(h.name)}`;

function hostRow(h, m) {
  const isOpen = open.has(h.name);
  if (!h.ok) return `<tr class="host down"><th scope="row">${ICON.bad}${esc(h.name)}<small>${esc(h.role)}</small></th><td colspan="5">Not answering</td></tr>`;
  const extra = h.name === 'Proxmox' ? `<tr class="more"><td colspan="6">${lookPicker()}<p class="small"><a href="${machineHref(h)}">History, volumes and backups</a></p>${lineChart(m.history)}${guestsTable(m.guests)}</td></tr>`
    : `<tr class="more"><td colspan="6"><p class="small"><a href="${machineHref(h)}">History, processes and volumes</a>. ${esc(h.cores)} cores${h.temp ? `, ${esc(h.temp)} C` : ''}. Largest volume ${esc(h.disk_mount)}: ${bytes(h.disk_used)} of ${bytes(h.disk_total)}.${h.failed_units?.length ? ` Failed: ${esc(h.failed_units.join(', '))}.` : ''}</p></td></tr>`;
  return `<tr class="host"><th scope="row"><button type="button" class="expander" data-host="${esc(h.name)}" aria-expanded="${isOpen}">${ICON.good}${esc(h.name)}<small>${esc(h.role)}</small></button></th>
    <td data-label="CPU">${meter(h.cpu)}</td><td data-label="Memory">${meter(pct(h.mem_used, h.mem_total), 85)}</td><td data-label="Disk">${meter(pct(h.disk_used, h.disk_total), 85, 93)}</td><td class="r" data-label="Load">${h.load[0].toFixed(2)}</td><td class="r" data-label="Up">${span(h.uptime)}</td></tr>${isOpen ? extra : ''}`;
}

function systems(p) {
  const el = $('#sysbody'), pr = p.probes.data, m = p.machines.data, s = p.storage.data;
  asof($('#asof-sys'), 'The probes', p.probes);
  if (!pr && !m) {
    el.innerHTML = '<p class="empty">The first check is still running.</p>';
    return;
  }
  const hard = p.worries.filter((w) => w.level), direct = (pr || []).filter((x) => !x.gated), up = direct.filter((x) => x.up).length, total = direct.length, gate = (pr || []).length - total;
  const head = !hard.length ? `All ${total} services are up` : hard[0].level > 1 ? `${hard[0].text}` : `${plural(hard.length, 'thing')} to look at`;
  const list = p.worries.map((w) => `<li>${w.level > 1 ? ICON.bad : w.level ? ICON.warn : ICON.note}${esc(w.text)}</li>`).join('');
  const slow = (pr || []).filter((x) => x.up && !x.gated).sort((a, b) => b.ms - a.ms)[0];
  const groups = [...new Set((pr || []).map((x) => x.group))].map((g) => {
    const rows = (pr || []).filter((x) => x.group === g && (!problems || !x.up));
    if (!rows.length) return '';
    return `<div class="svc-group"><h4>${esc(g)}</h4><ul class="svc">${rows.map((r) => `<li class="${r.up ? '' : 'down'}" data-tip="${esc(r.name)}: ${r.up ? `${r.ms} ms` : esc(r.error || `status ${r.status}`)}${r.day != null ? `. ${r.day}% up in 24 hours, ${r.week}% in 7 days` : ''}">${r.up ? ICON.good : ICON.bad}<a href="/systems/service/${encodeURIComponent(r.name)}">${esc(r.name)}</a><small>${r.gated ? 'gate only' : r.up ? `${r.ms} ms` : 'down'}</small></li>`).join('')}</ul></div>`;
  }).join('');
  const backup = s?.backups?.length ? [...s.backups].sort((a, b) => b.at - a.at)[0] : null;
  const pools = (s?.pools || []).map((z) => `<li>${z.health === 'ONLINE' ? ICON.good : ICON.bad}ZFS ${esc(z.name)}: ${bytes(z.alloc)} of ${bytes(z.size)}, ${esc(z.health.toLowerCase())}, ${esc(z.frag)}% fragmented</li>`).join('');
  const disks = (s?.disks || []).map((d) => `<li>${d.health === 'PASSED' || d.health === 'OK' ? ICON.good : ICON.warn}${esc(d.model)}: ${esc((d.health || 'unknown').toLowerCase())}${d.wear != null ? `, ${esc(d.wear)}% life left` : ''}</li>`).join('');
  const bk = backup ? `<li>${backup.ok ? ICON.good : ICON.bad}Last Proxmox backup ${esc(ago(backup.at))}, ${backup.ok ? 'finished cleanly' : esc(backup.status)}. ${s.backups.filter((b) => b.ok).length} of the last ${s.backups.length} runs were clean.</li>` : '';
  const tasks = (s?.failed_tasks || []).slice(0, 3).map((t) => `<li>${ICON.warn}${esc(t.what)} on ${esc(t.id)} failed ${esc(ago(t.at))}</li>`).join('');
  const toggle = `<button type="button" class="ghost text" id="problems" aria-pressed="${problems}">${problems ? 'Show everything' : 'Show only problems'}</button>`;
  el.innerHTML = `
    <div class="sys-top">
      <div><h3 class="sub-head">${esc(head)}</h3>
      <p class="prose">${total ? `${up} of ${total} answered, ${esc(ago(p.probes.as_of))}.` : ''}${slow ? ` Slowest: ${esc(slow.name)} at ${whole(slow.ms)} ms.` : ''}${gate ? ` ${plural(gate, 'more sits', 'more sit')} behind a login, so only the gate is checked.` : ''}</p></div>
      ${toggle}
    </div>
    ${list ? `<ul class="worries">${list}</ul>` : ''}
    ${(pr || []).length ? `<ul class="launch" aria-label="Open a service">${pr.map((r) => `<li><a href="${esc(r.url)}" target="_blank" rel="noopener noreferrer">${esc(r.name)}</a></li>`).join('')}</ul>` : ''}
    <div class="svc-wrap">${groups || '<p class="empty">No problems to show.</p>'}</div>
    ${m ? `<table class="machines"><caption>Machines</caption><thead><tr><th scope="col">Machine</th><th scope="col">CPU</th><th scope="col">Memory</th><th scope="col">Disk</th><th scope="col" class="r">Load</th><th scope="col" class="r">Up</th></tr></thead><tbody>${m.hosts.map((h) => hostRow(h, m)).join('')}</tbody></table>` : ''}
    <div class="store"><h4>Storage and backups</h4><ul class="plain">${bk}${pools}${disks}${tasks}</ul></div>`;
}

// ---------------------------------------------------------------- AI use

function aiUse(p) {
  const u = p.usage, el = $('#usebody'), key = JSON.stringify(u.days);
  asof($('#asof-use'), 'The count', u);
  if (el.dataset.key === key) return;
  el.dataset.key = key;
  if (!u.days.length) {
    el.innerHTML = '<p class="empty">Nothing counted yet. The paper counts its own AI calls, and Settings can add the rest.</p>';
    return;
  }
  const last = u.last || u.days[u.days.length - 1], most = u.who[0]?.[1] || 1;
  el.innerHTML = `<div class="use-grid">
      <div><a class="use-big" href="/usage">${dollars(last.worth)}</a>
        <p>of AI on ${esc(dayName(`${last.day}T12:00:00`))}, at list price. ${dollars(last.charged)} of it was really charged.</p>
        <p class="small">${dollars(u.month)} worth in ${plural(u.days.length, 'day')}, ${dollars(u.charged)} charged.</p></div>
      <div>${dayBars(u.days, 'worth', { href: (d) => `/usage#${d.day}`, label: ' of AI' })}</div>
      <ul class="use-who">${u.who.map(([who, v]) => `<li style="--w:${((100 * v) / most).toFixed(1)}%"><span>${esc(who)}</span><b>${dollars(v)}</b></li>`).join('')}</ul>
    </div>${u.missing.length ? `<p class="small">${esc(u.missing.join(' and '))} did not answer this time, so their days may be behind.</p>` : ''}`;
}

// ---------------------------------------------------------------- the tape

function tape(p) {
  const markets = p.world.data?.markets?.length ? p.world.data.markets : p.tape_quotes;
  const off = new Set(p.tape_off), run = [...p.invest.tape, ...markets.filter((m) => !off.has(m.label)).slice(0, 12)];
  const items = run.map((m) => `<span class="${(m.pct || 0) < 0 ? 'neg' : 'pos'}">${esc(m.label)} ${(m.pct || 0) < 0 ? ICON.down : ICON.up} ${Math.abs(m.pct || 0).toFixed(1)}%</span>`).join('');
  $('#tape').innerHTML = items ? `<div class="tape-run">${items}</div><div class="tape-run" aria-hidden="true">${items}</div>` : '';
}

// ---------------------------------------------------------------- arranging the page

const USUAL = ['world', 'tech', 'sports', 'mail', 'business', 'usage', 'arts', 'systems'];
const screenForm = () => (innerWidth < 860 ? 'phone' : 'wide');
const saveLayout = (body) => fetch('/api/layout', { method: 'PUT', credentials: 'same-origin', headers: { 'content-type': 'application/json', 'x-paper': '1' }, body: JSON.stringify(body) });
let order = null, arranging = false;

function place(next, animate) {
  const put = () => {
    const nav = $('.desks'), end = $('.desks a[href="/investments"]').parentNode;
    let at = $('#arrange-note');
    for (const id of next) {
      at.after($(`#${id}`));
      at = $(`#${id}`);
      nav.insertBefore($(`.desks a[href="/#${id}"]`).parentNode, end);
    }
  };
  order = [...next];
  if (animate && document.startViewTransition && !reduce) return document.startViewTransition(put).updateCallbackDone;
  return put();
}

function arrange(on) {
  arranging = on;
  document.documentElement.classList.toggle('arranging', on);
  $('#arrange').textContent = on ? 'Done' : 'Arrange';
  $('#arrange').setAttribute('aria-pressed', String(on));
  $('#arrange-note').hidden = !on;
  $('#arrange-text').textContent = `Move sections up or down. Each screen size keeps its own order${paper.layout.learn ? ', and learning starts again from what you choose.' : '.'}`;
  $$('.desk').forEach((d) => { d.style.viewTransitionName = on ? `desk-${d.id}` : ''; });
  if (on) $('#arrange-note').scrollIntoView();
}

function choose(next) {
  paper.layout.order[screenForm()] = next;
  saveLayout({ form: screenForm(), order: next });
  return place(next, true);
}

function movedNote(p) {
  const m = p.layout.moved[screenForm()], up = m ? m.to.filter((id, i) => m.from.indexOf(id) > i && !$(`#${id}`).hidden) : [];
  $('#moved').hidden = !up.length;
  if (up.length) $('#moved-text').textContent = `${new Intl.ListFormat('en').format(up.map((id) => $(`#${id} .desk-name`).textContent))} moved up, after 2 hours of reading.`;
}

// What's new since the last visit, worked out here and kept in this browser.
let lastVisit = null;
const SEEN = 'paper-last-visit', stamp = () => { try { localStorage.setItem(SEEN, String(Math.floor(Date.now() / 1000))); } catch {} };

function sinceLast(p) {
  if (lastVisit === null) {
    try { lastVisit = Number(localStorage.getItem(SEEN)) || 0; } catch { lastVisit = 0; }
  }
  const el = $('#since'), away = Date.now() / 1000 - lastVisit;
  el.hidden = !lastVisit || away < 3600;
  if (el.hidden) return;
  const stories = (p.news.data?.wire || []).filter((s) => s.ts > lastVisit).length, alerts = (p.world.data?.alerts || []).filter((a) => a.ts > lastVisit).length;
  const added = (p.media.data?.added || []).filter((a) => a.at > lastVisit).length;
  const parts = [stories && plural(stories, 'new story', 'new stories'), alerts && plural(alerts, 'new alert'), added && `${whole(added)} added to Plex`].filter(Boolean);
  el.hidden = !parts.length;
  el.textContent = `Since you were here ${ago(lastVisit)}: ${new Intl.ListFormat('en').format(parts)}.`;
}

function following(p) {
  const rows = p.news.data?.following || [];
  $('#following').hidden = !rows.length;
  $('#following').innerHTML = rows.length ? `<h2>Following</h2><ul>${rows.map((s) => `<li><a href="${esc(reading(s.u))}">${esc(s.t)}</a></li>`).join('')}</ul>` : '';
}

// ---------------------------------------------------------------- loading

function render() {
  const p = paper;
  showDock(p);
  look.style = p.layout.chart;
  const want = p.layout.order[screenForm()];
  if (!arranging && String(want) !== String(order)) place(want, drawn);
  for (const [id, key] of DESKS) {
    $(`#${id}`).hidden = !p.on[key];
    $(`.desks a[href="/#${id}"]`).parentNode.hidden = !p.on[key];
  }
  const desk = (draw) => { try { draw(p); } catch (e) { console.error(e); } };  // one desk's odd data leaves the others standing
  [front, tops, world, tech, tape].forEach(desk);
  desk(p.on.sports ? sports : (x) => wireList(x, 'sports'));
  if (p.on.mail) desk(mail);
  if (p.on.money) desk(business);
  if (p.on.usage) desk(aiUse);
  if (p.on.media) desk(arts);
  if (p.on.systems) desk(systems);
  desk(movedNote);
  desk(sinceLast);
  desk(following);
  fitAlso();
  phoneCheck();
  if (!drawn) {
    drawn = true;
    document.body.classList.add('inked');
  }
}

async function load() {
  try {
    const r = await fetch(`/api/paper?days=${days}`, { cache: 'no-store', credentials: 'same-origin' });
    if (r.status === 401) { location.assign('/login'); return; }
    if (!r.ok) throw new Error(String(r.status));
    paper = await r.json();
    $('#banner').hidden = !r.headers.get('x-paper-offline');  // the last edition, kept by the service worker
    render();
  } catch {
    $('#banner').hidden = false;
  }
}

// ---------------------------------------------------------------- behaviour

const chosen = () => { try { return localStorage.getItem('paper-theme'); } catch { return null; } };
const deviceTheme = () => (matchMedia('(prefers-color-scheme: dark)').matches || new Date().getHours() < 6 || new Date().getHours() >= 18 ? 'night' : 'morning');

function markTheme() {
  const t = document.documentElement.dataset.theme, mine = chosen();
  $$('[data-theme-pick]').forEach((b) => {
    const on = b.closest('.phone-sheet') ? b.dataset.themePick === (mine || 'auto') : b.dataset.themePick === t;
    b.setAttribute('aria-checked', String(on));
    b.tabIndex = on ? 0 : -1;
  });
  const bg = getComputedStyle(document.documentElement).getPropertyValue('--bg').trim();
  document.querySelector('meta[name=theme-color]').content = bg;
}

function setTheme(pick, e) {
  const t = pick === 'auto' ? deviceTheme() : pick;
  const apply = () => {
    document.documentElement.dataset.theme = t;
    try {
      if (pick === 'auto') localStorage.removeItem('paper-theme');
      else localStorage.setItem('paper-theme', t);
    } catch { /* private window: it just won't stick */ }
    markTheme();
  };
  if (!document.startViewTransition || reduce) {
    apply();
    globe?.recolor();
    return;
  }
  const x = e?.clientX || innerWidth - 40, y = e?.clientY || 40, r = Math.hypot(Math.max(x, innerWidth - x), Math.max(y, innerHeight - y));
  const vt = document.startViewTransition(apply);
  vt.ready.then(() => document.documentElement.animate({ clipPath: [`circle(0px at ${x}px ${y}px)`, `circle(${r}px at ${x}px ${y}px)`] }, { duration: 760, easing: 'cubic-bezier(.16,1,.3,1)', pseudoElement: '::view-transition-new(root)' })).catch(() => {});
  vt.finished.then(() => globe?.recolor());
}

document.addEventListener('click', (e) => {
  const t = e.target.closest('button');
  if (!t) return;
  if (t.dataset.themePick) setTheme(t.dataset.themePick, e);
  else if (t.dataset.text) {
    document.documentElement.style.setProperty('--text', t.dataset.text);
    try { localStorage.setItem('paper-text', t.dataset.text); } catch { /* it just won't stick */ }
    $$('[data-text]').forEach((b) => b.setAttribute('aria-pressed', String(b === t)));
  } else if (t.hasAttribute('data-arrange')) {
    $('#sheet-more').close();
    arrange(true);
  }
  else if (t.dataset.fly) {
    const [lat, lon] = t.dataset.fly.split(',').map(Number);
    globe?.fly(lat, lon);
    if (t.closest('#worldbody')) $('#orb').scrollIntoView({ behavior: reduce ? 'auto' : 'smooth', block: 'center' });
  } else if (t.dataset.layer) {
    const on = t.getAttribute('aria-pressed') !== 'true';
    t.setAttribute('aria-pressed', String(on));
    globe?.filter(Number(t.dataset.layer), on);
  } else if (t.dataset.done) {
    fetch(`/api/mail/${t.dataset.done}/done`, { method: 'PUT', headers: { 'x-paper': '1' } }).then(load);
  } else if (t.dataset.wire) {
    const [name, tab] = t.dataset.wire.split(':');
    Object.assign(WIRES[name], { tab, more: 14 });
    wireList(paper, name);
  } else if (t.dataset.more) {
    WIRES[t.dataset.more].more += 20;
    wireList(paper, t.dataset.more);
  } else if (t.dataset.league) {
    league = t.dataset.league;
    sports(paper);
  } else if (t.dataset.days) {
    days = Number(t.dataset.days);
    load();
  } else if (t.dataset.sort) {
    const k = t.dataset.sort;
    sort = sort.key === k ? { key: k, dir: -sort.dir } : { key: k, dir: k === 'name' ? 1 : -1 };
    $('#biz-products').innerHTML = productsTable(paper.money, paper.probes.data);
  } else if (t.dataset.host) {
    if (open.has(t.dataset.host)) open.delete(t.dataset.host); else open.add(t.dataset.host);
    const name = t.dataset.host;
    systems(paper);
    $(`[data-host="${CSS.escape(name)}"]`)?.focus();
  } else if (t.id === 'problems') {
    problems = !problems;
    systems(paper);
    $('#problems')?.focus();
  } else if (t.id === 'reload') {
    location.reload();
  } else if (t.id === 'add-cost') {
    $('#costs').insertAdjacentHTML('beforeend', costRow());
    $('#costs .cost-row:last-child .c-name').focus();
  } else if (t.hasAttribute('data-remove')) {
    t.closest('.cost-row').remove();
    saveCosts();
  }
});
document.addEventListener('change', (e) => {
  if (e.target.closest('#costs')) saveCosts();
  if (e.target.id === 'mail-box') {
    mailBox = e.target.value;
    mail(paper);
  }
  if (e.target.id === 'mail-noise') {
    mailNoise = e.target.checked;
    mail(paper);
  }
});
$('.plates').addEventListener('keydown', (e) => {
  const step = { ArrowRight: 1, ArrowDown: 1, ArrowLeft: -1, ArrowUp: -1 }[e.key];
  if (!step) return;
  e.preventDefault();
  const next = THEMES[(THEMES.indexOf(document.documentElement.dataset.theme) + step + THEMES.length) % THEMES.length];
  setTheme(next);
  $(`[data-theme-pick=${next}]`).focus();
});
document.addEventListener('keydown', (e) => {
  if (e.metaKey || e.ctrlKey || e.altKey || e.target.closest('input,select,textarea')) return;
  if (e.key === 't') setTheme(THEMES[(THEMES.indexOf(document.documentElement.dataset.theme) + 1) % THEMES.length]);
  if (!isFront()) return;
  if (e.key === '/') {
    e.preventDefault();
    $('#find-q').focus();
  }
  if (e.key === 'a' && paper?.on.ai) {
    e.preventDefault();
    openDock();
  }
});

$('#find').addEventListener('submit', (e) => {
  e.preventDefault();
  const q = $('#find-q').value.trim();
  if (q) go(`/topic/${encodeURIComponent(q)}`);
});

$('#tape').addEventListener('pointerup', (e) => {
  if (e.pointerType !== 'mouse') e.currentTarget.classList.toggle('held');  // touch has no hover: a tap stops the tape, another starts it
});

const tip = $('#tip');
const showTip = (e) => {
  const hit = e.target.closest?.('[data-tip]');
  if (!hit) { tip.hidden = true; return; }
  tip.textContent = hit.dataset.tip;
  tip.hidden = false;
  tip.style.transform = `translate(${Math.max(8, Math.min(e.clientX + 14, innerWidth - tip.offsetWidth - 10))}px,${Math.max(8, e.clientY - tip.offsetHeight - 12)}px)`;
};
document.addEventListener('pointermove', showTip);
document.addEventListener('pointerdown', showTip);  // a tap has no hover, so it reads the point it lands on

$$('.desk').forEach((d) => {
  const name = $('.desk-name', d);
  name.insertAdjacentHTML('afterend', `<div class="desk-move">${[['-1', 'up', 'M8 13V3.5M3.5 8 8 3.5 12.5 8'], ['1', 'down', 'M8 3v9.5M3.5 8 8 12.5 12.5 8']].map(([step, way, path]) => `<button type="button" data-move="${step}" aria-label="Move ${esc(name.textContent)} ${way}"><svg viewBox="0 0 16 16" aria-hidden="true"><path d="${path}"/></svg></button>`).join('')}</div>`);
});
$('#arrange').addEventListener('click', () => arrange(!arranging));
$('#arrange-reset').addEventListener('click', () => choose(USUAL));
$('#arrange-done').addEventListener('click', () => arrange(false));
$('#paper').addEventListener('click', (e) => {
  const b = e.target.closest('[data-move]');
  if (!b) return;
  const id = b.closest('.desk').id, shown = order.filter((d) => !$(`#${d}`).hidden), other = shown[shown.indexOf(id) + Number(b.dataset.move)];
  if (!other) return;
  const next = [...order], from = next.indexOf(id), to = next.indexOf(other);
  [next[from], next[to]] = [next[to], next[from]];
  Promise.resolve(choose(next)).then(() => b.focus({ preventScroll: true }));  // moving a button drops its focus, and the next press needs it
});
$('#moved-keep').addEventListener('click', async () => { await saveLayout({ form: screenForm(), seen: true }); load(); });
$('#moved-undo').addEventListener('click', async () => { await saveLayout({ form: screenForm(), order: paper.layout.moved[screenForm()].from }); load(); });

// Time on each section, for the layout setting. It counts only while the page is on screen and someone is there.
let inView = null, lastInput = Date.now(), watched = {};
['pointerdown', 'pointermove', 'keydown', 'wheel', 'touchmove'].forEach((t) => addEventListener(t, () => { lastInput = Date.now(); }, { passive: true }));
const watchedTotal = () => Object.values(watched).reduce((a, b) => a + b, 0);
function sendViews() {
  if (!watchedTotal()) return;
  fetch('/api/views', { method: 'POST', keepalive: true, credentials: 'same-origin', headers: { 'content-type': 'application/json', 'x-paper': '1' }, body: JSON.stringify({ form: screenForm(), seconds: watched }) }).catch(() => {});
  watched = {};
}
setInterval(() => {
  if (!paper?.layout.learn || document.hidden || Date.now() - lastInput > 60000) return;
  const page = location.pathname.split('/')[1], where = isFront() ? (scrollY < innerHeight * 0.6 ? 'front' : inView) : USUAL.includes(page) && page;
  if (!where) return;
  watched[where] = (watched[where] || 0) + 1;
  if (watchedTotal() >= 60) sendViews();
}, 1000);
addEventListener('pagehide', () => { sendViews(); stamp(); });
document.addEventListener('visibilitychange', () => { if (document.hidden) stamp(); });

let shrunk = false;
addEventListener('scroll', () => {  // on a phone the bar and the Ask button give the page back once you're reading
  const next = shrunk ? scrollY > 300 : scrollY > 460;
  if (next === shrunk) return;
  shrunk = next;
  $('.bar').classList.toggle('compact', next);
  $('#dock').classList.toggle('small', next);
}, { passive: true });

const here = new IntersectionObserver((en) => {
  for (const x of en) {
    if (x.isIntersecting && !onPhone()) {
      inView = x.target.id;
      const link = $(`.desks a[href="/#${x.target.id}"]`), nav = $('.desks');
      if (link && nav.scrollWidth > nav.clientWidth) nav.scrollTo({ left: link.offsetLeft - nav.clientWidth / 2 + link.offsetWidth / 2, behavior: reduce ? 'auto' : 'smooth' });
      $$('.desks a').forEach((a) => (a.getAttribute('href') === `/#${x.target.id}` ? a.setAttribute('aria-current', 'true') : a.removeAttribute('aria-current')));
    }
  }
}, { rootMargin: '-40% 0px -55% 0px' });
$$('.desk').forEach((s) => here.observe(s));

if ('serviceWorker' in navigator) navigator.serviceWorker.register('/sw.js').catch(() => {});

markTheme();
matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => { if (!chosen()) setTheme('auto'); });
try {
  const text = localStorage.getItem('paper-text');
  if (text) $$('[data-text]').forEach((b) => b.setAttribute('aria-pressed', String(b.dataset.text === text)));
} catch { /* the usual size */ }

function startGlobe() {
  if (globe || $('#orb').classList.contains('flat')) return;
  try {
    globe = makeGlobe($('#globe'), {
      onOpen(dot) {
        go(eventHref({ k: dot.k, i: dot.i }));
      },
      onPick(hit) {
        const box = $('#pick');
        box.hidden = !hit;
        if (!hit) return;
        box.innerHTML = `<b>${esc(KIND[hit.dot.k])}</b> ${esc(hit.dot.t)}${hit.dot.ts ? ` <time>${esc(ago(hit.dot.ts))}</time>` : ''}`;
        box.style.setProperty('--x', `${hit.x}px`);
        box.style.setProperty('--y', `${hit.y}px`);
      },
    });
  } catch (e) {
    console.warn('globe off', e);
  }
  if (!globe) $('#orb').classList.add('flat');
  else if (paper) world(paper);
}

// A phone shows the globe on the World tab, and doesn't spin it up until that tab opens.
function seatGlobe(phone) {
  if (phone) $('#worldbody').before($('#orb'));
  else {
    $('#front').append($('#orb'));
    startGlobe();
  }
}
startPhone({ go, onTab: (id) => { if (id === 'world') startGlobe(); }, onForm: seatGlobe });

addEventListener('paper:reload', load);
start((lat, lon) => globe?.fly(lat, lon), () => paper?.world.data?.dots || []);
load();
setInterval(load, 60000);
document.addEventListener('visibilitychange', () => { if (!document.hidden) load(); });
