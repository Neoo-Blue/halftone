// Every tap opens here. Each detail is a real address on this paper, so reload, back and open-in-new-tab all work,
// and stories are read inside the paper. The only way off the site is the small "Original" link under a story.
import { $, esc, usd, whole, ago, span, bytes, dayName, dotPlot, lineChart, tight } from '/lib.js';
import { makeGlobe } from '/globe.js';

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
const notes = (list) => (list || []).map((n) => `<section class="intel"><h3>${esc(n.headline)}</h3>${n.body ? `<p>${cited(n.body)}</p>` : ''}${n.bullets?.length ? `<ul>${n.bullets.map((b) => `<li>${cited(typeof b === 'string' ? b : b.text || '')}</li>`).join('')}</ul>` : ''}<time>${esc(ago(n.ts))}</time></section>`).join('');
const stories = (rows) => `<ul class="wire-list">${rows.map((s) => `<li><a href="${eventHref(s)}">${esc(s.t)}</a><span>${esc([s.place, ago(s.ts)].filter(Boolean).join(', '))}</span></li>`).join('')}</ul>`;
const onGlobe = (lat, lon) => (lat != null ? `<button type="button" class="ghost text" data-globe="${esc(lat)},${esc(lon)}">Show on the globe</button>` : '');

function storyBody(s) {
  return `<div class="page-body">${s.body}</div><p class="source">Original at <a href="${esc(s.url)}" target="_blank" rel="noopener noreferrer">${esc(s.site)}</a></p>`;
}

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
      ${onGlobe(d.lat, d.lon)}
      ${d.theater && d.theater !== 'global' ? `<p class="to"><a href="/world/theater/${esc(d.theater)}">This conflict</a></p>` : ''}
      ${d.thread ? `<p class="to"><a href="/world/thread/${esc(d.thread.id)}">${esc(d.thread.title)}</a></p>` : ''}
      ${d.sources.length ? `<h3>Sources</h3><ul class="plain">${d.sources.map((s) => `<li><a href="${reading(s.url)}">${esc(s.title || s.publisher || s.url)}</a>${s.title ? `<time>${esc(s.publisher)}</time>` : ''}</li>`).join('')}</ul>` : ''}`;
    const long = (d.summary || '').length > 220;
    const body = `${long ? `<div class="page-body"><p>${esc(d.summary)}</p></div>` : ''}${d.note ? notes([d.note]) : ''}
      ${d.story ? storyBody(d.story) : `<p class="empty">${d.sources.length ? 'The publisher would not share the full story with the paper. The sources alongside may have more.' : 'WARROOM has no article for this event, only the report itself.'}</p>`}
      ${d.nearby.length ? `<h3>Nearby in the last three days</h3>${stories(d.nearby)}` : ''}`;
    return { head: d.title, deck: long ? '' : d.summary, meta: [place, ago(d.ts)].filter(Boolean).join(', '), body, side, locate: [d.lat, d.lon] };
  },

  theater(d) {
    return {
      head: d.name, deck: `Escalation stands at ${d.esc} of 100.`, meta: `${d.events.length} recent stories`,
      body: `${notes(d.intel)}<h3>Latest</h3>${d.events.length ? stories(d.events) : '<p class="empty">Nothing recent with a real headline.</p>'}`,
      side: onGlobe(d.lat, d.lon), locate: [d.lat, d.lon],
    };
  },

  thread(d) {
    return {
      head: d.title, deck: d.summary, meta: `${whole(d.count)} reports since ${stamp(d.first)}`,
      body: `${notes(d.intel)}<h3>Latest</h3>${stories(d.events)}`,
      side: `${facts([['Status', title(d.status)], ['Last report', ago(d.last)], ['Who', d.actors.join(', ')]])}${onGlobe(d.lat, d.lon)}${d.theater && d.theater !== 'global' ? `<p class="to"><a href="/world/theater/${esc(d.theater)}">This conflict</a></p>` : ''}`,
      locate: [d.lat, d.lon],
    };
  },

  hazard(d) {
    return {
      head: d.title, deck: d.text, meta: [title(d.hkind), d.country].filter(Boolean).join(', '),
      body: `<div class="page-body"><p>${esc(d.about || d.text)}</p></div>`,
      side: `${facts([['Alert', title(d.alert)], ['From', stamp(d.from)], ['Until', stamp(d.to)]])}${onGlobe(d.lat, d.lon)}`, locate: [d.lat, d.lon],
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
      hero: d.image ? picture(d.image) : null,
      side: d.also?.length ? `<h3>Also covered by</h3><ul class="plain">${d.also.map((o) => `<li><a href="${reading(o.u)}">${esc(o.src)}</a></li>`).join('')}</ul>` : '',
      body: d.body ? storyBody(d) : `<p class="empty">${esc(none)}</p>${d.url ? `<p class="source">Original at <a href="${esc(d.url)}" target="_blank" rel="noopener noreferrer">${esc(d.site)}</a></p>` : ''}`,
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

function page(v, m) {
  const back = m.desk ? `<a href="${DESK[m.desk]}">Back to ${m.desk}</a>` : '<a href="/">Back to the paper</a>';
  const art = v.backdrop ? `<div class="backdrop"><img src="${esc(v.backdrop)}" alt=""></div>` : '';
  const hero = v.hero ? `<button type="button" class="hero ink" data-reveal aria-pressed="false" aria-label="Show the photograph in colour"><img src="${esc(v.hero)}" alt=""></button>` : '';
  const left = v.poster ? `<button type="button" class="page-poster ink" data-reveal aria-pressed="false" aria-label="Show the poster in colour"><img src="${esc(v.poster)}" alt=""></button>` : '';
  const where = v.locate?.[0] != null ? `<div class="locator"><canvas data-lat="${esc(v.locate[0])}" data-lon="${esc(v.locate[1])}" tabindex="0" role="img" aria-label="Globe centred on this place. Tap a dot to open that report."></canvas></div>` : '';
  const sub = `${v.deck ? `<p class="deck">${esc(v.deck)}</p>` : ''}${v.meta ? `<p class="byline">${esc(v.meta)}</p>` : ''}`;
  const side = where || v.side ? `<aside class="page-side">${where}${v.side || ''}</aside>` : '';
  return `<nav class="crumb" aria-label="Back">${back}</nav>${art}
    <header class="page-top${v.poster ? ' with-poster' : ''}">${left}<h1 class="page-head" tabindex="-1">${tight(v.head)}</h1><div class="page-sub">${sub}</div></header>${hero}
    <div class="page-grid${side ? '' : ' solo'}"><div class="page-main">${v.body || ''}</div>${side}</div>`;
}

let front = 0, turn = 0, still = null, getDots = () => [];
const sheet = () => $('#page');

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

export async function route() {
  const m = match(), mine = (turn += 1);
  if (!m) {
    still?.destroy();
    still = null;
    if (!sheet().hidden) await swap(false, () => { sheet().replaceChildren(); document.title = NAME; });
    const target = location.hash && $(location.hash);
    if (target) target.scrollIntoView();
    else scrollTo(0, front);
    return;
  }
  if (sheet().hidden) front = scrollY;
  const data = fetch(m.url, { credentials: 'same-origin' }).then(async (r) => ({ ok: r.ok, body: await r.json() })).catch(() => ({ ok: false, body: {} }));
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
  document.title = `${v.head} | ${NAME}`;
  $('.page-head', sheet())?.focus({ preventScroll: true });
}

export function go(href) {
  history.pushState(null, '', href);
  route();
}

export function start(fly, dots) {
  getDots = dots;
  addEventListener('popstate', route);
  document.addEventListener('error', (e) => { if (e.target.matches?.('.hero img, .page-poster img')) e.target.parentNode.remove(); }, true);  // a dead picture leaves no hole
  document.addEventListener('click', (e) => {
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
    if (!a || a.target || a.pathname === '/settings' || e.metaKey || e.ctrlKey || e.shiftKey || e.button) return undefined;
    e.preventDefault();
    go(a.getAttribute('href'));
    return undefined;
  });
  route();
}
