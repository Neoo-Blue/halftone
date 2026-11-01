// Search that reaches past the paper. As you type it offers what the paper already knows, and on the results page it works
// out what the words are, because a stock, a team, a town and a war are each read and followed in their own way.
// Everything printed here came from strangers or from a model that read them, so it all goes through esc, and it stays plain text.
import { $, esc, ago, compact, whole, reading, picture } from '/lib.js';

const POST_WAIT = 75000;
const post = async (path, body) => {
  const r = await fetch(path, { method: 'POST', credentials: 'same-origin', headers: { 'content-type': 'application/json', 'x-paper': '1' }, body: JSON.stringify(body), signal: AbortSignal.timeout(POST_WAIT) }).catch(() => {
    throw new Error('That took too long. Try again.');
  });
  const data = await r.json();
  if (!r.ok) throw new Error(data.error || 'That could not be finished.');
  return data;
};
const local = (key, fallback) => {
  try {
    return JSON.parse(localStorage.getItem(key)) ?? fallback;
  } catch {
    return fallback;
  }
};
const keep = (key, value) => {
  try {
    localStorage.setItem(key, JSON.stringify(value));
  } catch { /* a private window: the feature just forgets */ }
};

// ---------------------------------------------------------------- each kind of thing, in its own way
const money = (v, currency) => new Intl.NumberFormat('en-US', { style: 'currency', currency, maximumFractionDigits: v >= 1000 ? 0 : 2 }).format(v);

function spark(closes, up) {
  if (closes.length < 2) return '';
  const lo = Math.min(...closes), hi = Math.max(...closes), range = hi - lo || 1;
  const points = closes.map((c, i) => `${((i / (closes.length - 1)) * 100).toFixed(1)},${(26 - ((c - lo) / range) * 24).toFixed(1)}`).join(' ');
  return `<svg class="fo-spark ${up ? 'up' : 'down'}" viewBox="0 0 100 28" preserveAspectRatio="none" role="img" aria-label="${esc(closes.length)} days of closing prices"><polyline points="${points}"/></svg>`;
}

const followButton = (c) => (c.key ? `<button type="button" class="ghost text fo-follow" data-track="${esc(JSON.stringify({ kind: c.kind, key: c.key, name: c.name }))}" aria-pressed="${!!c.followed}">${c.followed ? 'Following' : 'Follow'}</button>` : '');

const gameLine = (g) => {
  const when = g.at ? new Date(g.at * 1000).toLocaleString('en-US', { weekday: 'short', hour: 'numeric', minute: '2-digit' }) : '';
  if (g.mine == null) return `${g.home ? 'vs' : 'at'} ${esc(g.vs)}, ${esc(when)}`;
  const n = Number(g.mine) - Number(g.theirs);
  const word = g.state === 'in' ? 'Now' : n > 0 ? 'Won' : n < 0 ? 'Lost' : 'Drew';
  return `<b>${word} ${esc(g.mine)}-${esc(g.theirs)}</b> ${g.home ? 'vs' : 'at'} ${esc(g.vs)}${g.state === 'in' ? `, ${esc(g.status)}` : ''}`;
};

const CARD = {
  market(c) {
    const move = c.prev ? (100 * (c.price - c.prev)) / c.prev : null, up = move >= 0;
    return `<span class="fo-kind">${esc(c.key)}${c.where ? `, ${esc(c.where)}` : ''}</span><b class="fo-name">${esc(c.name)}</b>
      <span class="fo-big">${money(c.price, c.currency)}${move == null ? '' : ` <em class="${up ? 'pos' : 'neg'}">${up ? '+' : ''}${move.toFixed(2)}%</em>`}</span>${spark(c.closes || [], (c.closes?.at(-1) ?? 0) >= (c.closes?.[0] ?? 0))}`;
  },
  team(c) {
    return `<span class="fo-kind">${esc([c.standing, c.record].filter(Boolean).join(', '))}</span><b class="fo-name">${c.logo ? `<img src="${esc(picture(c.logo))}" alt="" loading="lazy">` : ''}${esc(c.name)}</b>
      ${c.last ? `<span class="fo-line">${gameLine(c.last)}</span>` : ''}${c.next && c.next.at !== c.last?.at ? `<span class="fo-line">Next: ${gameLine(c.next)}</span>` : ''}`;
  },
  place(c) {
    const day = (d) => new Date(d.t * 1000 + 43200000).toLocaleDateString('en-US', { weekday: 'short', timeZone: c.tz || undefined });
    return `<span class="fo-kind">${esc(c.region || 'Weather')}</span><b class="fo-name">${esc(c.name)}</b><span class="fo-big">${esc(c.now?.temp)}° <em>${esc(c.now?.sky)}</em></span>
      <ul class="fo-days">${(c.days || []).slice(1, 4).map((d) => `<li><b>${esc(day(d))}</b> ${esc(d.hi)}°/${esc(d.lo)}°${d.rain >= 30 ? `, ${esc(d.rain)}% rain` : ''}</li>`).join('')}</ul>`;
  },
  conflict(c) {
    const t = c.tally || {}, camps = (c.camps || []).filter((x) => t.camps?.[x.code]);
    const parts = [...camps.map((x) => [t.camps[x.code], x.label]), [t.outside, 'outside the fight']].filter(([n]) => n);
    const alone = Object.values(c.only || {}).reduce((a, b) => a + b, 0);
    return `<span class="fo-kind">Conflict</span><b class="fo-name">${esc(c.name)}</b><span class="fo-big">${esc(c.esc)} <em>of 100</em></span>
      ${parts.length ? `<span class="fo-line">${parts.map(([n, word]) => `${whole(n)} from ${esc(word)}`).join(', ')}</span>` : ''}${alone ? `<span class="fo-line">${whole(alone)} ${alone === 1 ? 'claim' : 'claims'} only one side is making</span>` : ''}`;
  },
  thing(c) {
    return `${c.img ? `<img class="fo-photo" src="${esc(picture(c.img))}" alt="" loading="lazy">` : ''}<span class="fo-kind">${esc(c.about || 'Wikipedia')}</span><b class="fo-name">${esc(c.name)}</b><p class="fo-text">${esc(c.text)}</p>`;
  },
  topic(c) {
    const rows = c.rows || [], fresh = newFor(c);
    return `<span class="fo-kind">${fresh ? `${whole(fresh)} new` : rows[0]?.ts ? `Latest ${esc(ago(rows[0].ts))}` : 'Following'}</span><b class="fo-name">${esc(c.name)}</b>${rows.slice(0, 2).map((r) => `<span class="fo-line">${esc(r.t)}</span>`).join('')}${rows.length ? '' : '<span class="fo-line">Nothing new yet.</span>'}`;
  },
};

const href = (c) => (c.kind === 'thing' ? reading(c.url) : c.href || `/topic/${encodeURIComponent(c.kind === 'market' || c.kind === 'topic' ? c.key : c.name)}`);
function inside(c) {
  try {
    return (CARD[c.kind] || CARD.topic)(c);
  } catch {  // a card whose source hasn't answered yet, or sent a currency or a time zone nothing can print
    return `<b class="fo-name">${esc(c.name)}</b><span class="fo-line">Waiting for its next update.</span>`;
  }
}

export const card = (c, buttons = true) => `<article class="fo fo-${esc(c.kind)}"><a class="fo-open" href="${esc(href(c))}" data-seen="${esc(c.id || '')}">${inside(c)}</a>${buttons ? followButton(c) : ''}</article>`;

// What's new on a followed subject is counted on this device, from the last time it was opened here.
const SEEN = 'paper-follow-seen';
function newFor(c) {
  const last = local(SEEN, {})[c.id];
  return last ? (c.rows || []).filter((r) => r.ts > last).length : 0;
}

export function followed(p) {
  const band = $('#followed'), cards = p.following || [];
  band.hidden = !cards.length;
  if (cards.length) $('#fo-row').innerHTML = cards.slice(0, 12).map((c) => card(c, false)).join('');
}

// ---------------------------------------------------------------- the search box
const DESKS = [['Weather', '/weather'], ['Investments', '/investments'], ['Both sides', '/#sides'], ['Saved stories', '/saved'], ['Back issues', '/archive'], ['Following', '/following'], ['AI use', '/#usage'], ['Settings', '/settings']];
const RECENT = 'paper-find-recent';
let paper = null, go = () => {};

export const findData = (p) => { paper = p; };

const remembered = (q) => keep(RECENT, [q, ...local(RECENT, []).filter((x) => x.toLowerCase() !== q.toLowerCase())].slice(0, 6));

function offers(q) {
  const low = q.toLowerCase(), hit = (t) => String(t || '').toLowerCase().includes(low);
  const topic = (name) => `/topic/${encodeURIComponent(name)}`;
  if (!q) {
    return [...local(RECENT, []).map((t) => ({ t, kind: 'Recent', href: topic(t) })), ...(paper?.following || []).slice(0, 4).map((c) => ({ t: c.name, kind: 'Following', href: href(c) }))];
  }
  const games = (paper?.sports?.data || []).flatMap((l) => l.games || []).flatMap((g) => [g.home?.name, g.away?.name]);
  return [
    ...(paper?.following || []).filter((c) => hit(c.name)).map((c) => ({ t: c.name, kind: 'Following', href: href(c) })),
    ...(paper?.world?.data?.all_theaters || paper?.world?.data?.theaters || []).filter((t) => hit(t.name)).slice(0, 3).map((t) => ({ t: t.name, kind: 'Conflict', href: `/world/theater/${t.id}` })),
    ...[...new Set(games.filter(hit))].slice(0, 2).map((t) => ({ t, kind: 'Team', href: topic(t) })),
    ...DESKS.filter(([t]) => hit(t)).map(([t, to]) => ({ t, kind: 'In the paper', href: to })),
    ...(paper?.news?.data?.wire || []).filter((s) => hit(s.t)).slice(0, 4).map((s) => ({ t: s.t, kind: s.src, href: reading(s.u) })),
  ].slice(0, 8);
}

function searchBox(form, box, list, leave = () => {}) {
  let picked = -1, rows = [];
  const close = () => {
    list.hidden = true;
    picked = -1;
    box.setAttribute('aria-expanded', 'false');
    box.removeAttribute('aria-activedescendant');
  };
  const draw = () => {
    const q = box.value.trim();
    rows = offers(q);
    if (q) rows.push({ t: q, kind: 'Search everywhere', href: `/topic/${encodeURIComponent(q)}`, all: true });
    list.innerHTML = rows.map((r, i) => `<li role="option" id="${list.id}-${i}" aria-selected="${i === picked}"><a href="${esc(r.href)}" tabindex="-1"><span>${esc(r.t)}</span><small>${esc(r.kind)}</small></a></li>`).join('');
    list.hidden = !rows.length;
    box.setAttribute('aria-expanded', String(!!rows.length));
    box.setAttribute('aria-activedescendant', picked >= 0 ? `${list.id}-${picked}` : '');
  };
  const leaveWith = (to, q) => {
    close();
    box.value = '';
    box.blur();
    leave();
    if (q) remembered(q);
    go(to);
  };
  box.addEventListener('input', () => { picked = -1; draw(); });
  box.addEventListener('focus', draw);
  box.addEventListener('blur', () => setTimeout(close, 120));  // long enough for a tap on a row to land
  box.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') return close();
    if (e.key !== 'ArrowDown' && e.key !== 'ArrowUp') return undefined;
    e.preventDefault();
    if (list.hidden) return draw();
    picked = (picked + (e.key === 'ArrowDown' ? 1 : -1) + rows.length + 1) % (rows.length + 1);
    if (picked === rows.length) picked = -1;
    return draw();
  });
  list.addEventListener('pointerdown', (e) => e.preventDefault());  // the box keeps focus until the row has been read
  list.addEventListener('click', (e) => {
    const a = e.target.closest('a');
    if (!a) return;
    e.preventDefault();
    const r = rows[[...list.children].indexOf(a.closest('li'))];
    leaveWith(a.getAttribute('href'), r?.all || r?.kind === 'Recent' ? r.t : '');
  });
  form.addEventListener('submit', (e) => {
    e.preventDefault();
    const q = box.value.trim();
    if (picked >= 0 && rows[picked]) leaveWith(rows[picked].href, rows[picked].all ? q : '');
    else if (q) leaveWith(`/topic/${encodeURIComponent(q)}`, q);
  });
}

export function startFind(navigate) {
  go = navigate;
  searchBox($('#find'), $('#find-q'), $('#find-list'));
  searchBox($('#sheet-find-form'), $('#sheet-q'), $('#sheet-list'), () => $('#sheet-find').close());
  document.addEventListener('click', async (e) => {
    const opened = e.target.closest('[data-seen]');
    if (opened?.dataset.seen) keep(SEEN, { ...local(SEEN, {}), [opened.dataset.seen]: Math.floor(Date.now() / 1000) });
    const b = e.target.closest('[data-track]');
    if (!b) return;
    const on = b.getAttribute('aria-pressed') !== 'true';
    b.disabled = true;
    try {
      await post('/api/follow', { ...JSON.parse(b.dataset.track), on });
      b.setAttribute('aria-pressed', String(on));
      b.textContent = on ? 'Following' : 'Follow';
    } catch (err) {
      b.textContent = err.message;
    }
    b.disabled = false;
  });
}

// ---------------------------------------------------------------- the results page
const when = (ts) => (ts ? ago(ts) : '');
const line = (r) => `<li><a href="${esc(reading(r.u))}">${esc(r.t)}</a><span>${esc([r.src, when(r.ts)].filter(Boolean).join(', '))}</span>${r.sum ? `<p>${esc(r.sum)}</p>` : ''}</li>`;
const section = (title, rows, note = '') => (rows?.length ? `<section class="find-part"><h3>${esc(title)}</h3>${note ? `<p class="small">${esc(note)}</p>` : ''}<ul class="wire-list find-rows">${rows.map(line).join('')}</ul></section>` : '');
const waiting = (lines) => `<div class="find-wait" aria-hidden="true">${'<i></i>'.repeat(lines)}</div>`;

function oddsPart(rows) {
  if (!rows?.length) return '';
  return `<section class="find-part"><h3>What the betting markets expect</h3><p class="small">Prices on Polymarket, not facts. They move on what people will bet.</p><ul class="bets">${rows.map((e) => `<li><a href="${esc(e.u)}" target="_blank" rel="noopener noreferrer">${esc(e.t)}</a><span class="bets-sum">$${compact(e.volume)} traded</span>${e.lines.map((l) => `<div class="bets-row"><span>${esc(l.t)}</span><i style="--p:${Math.min(100, Number(l.pct) || 0)}%"></i><b>${esc(Math.round(l.pct))}%</b></div>`).join('')}</li>`).join('')}</ul></section>`;
}

function codeRows(rows) {
  return (rows || []).map((r) => ({ ...r, src: `${r.src}, ${compact(r.stars)} stars` }));
}

// [3] in an answer goes to that source, in the reader. Nothing else in the text can become markup: it was escaped first.
function cited(text, sources) {
  return esc(text).replace(/\[(\d{1,3})\]/g, (m, n) => {
    const s = sources.find((x) => x.n === Number(n));
    return s ? `<a class="ref" href="${esc(reading(s.u))}" title="${esc(s.t)}">${n}</a>` : '';
  });
}

function nextQuestions(next, box) {
  box.innerHTML = (next || []).map((q) => `<button type="button" class="ghost text" data-next>${esc(q)}</button>`).join('');
}

function drawAnswer(root, q, a) {
  const said = [{ q, a: a.answer }];
  root.hidden = false;
  root.innerHTML = `<div class="find-said"><p>${cited(a.answer, a.sources)}</p></div><small>Written by AI from ${whole(a.sources.length)} ${a.sources.length === 1 ? 'source' : 'sources'}. It can be wrong, so follow the numbers.</small>
    <div class="find-next" id="find-next"></div>
    <form class="find-ask" id="find-ask"><input type="text" id="find-more-q" maxlength="300" placeholder="Ask about this" aria-label="Ask a follow-up question" autocomplete="off" enterkeyhint="send"><button type="submit" class="ghost text">Ask</button></form>`;
  const list = $('.find-said', root), chips = $('#find-next', root), form = $('#find-ask', root), input = $('#find-more-q', root);
  nextQuestions(a.next, chips);
  let busy = false;
  const ask = async (question) => {
    if (busy) return;
    busy = true;
    const turn = document.createElement('div');
    turn.className = 'find-turn';
    turn.innerHTML = `<h4>${esc(question)}</h4>${waiting(2)}`;
    list.append(turn);
    turn.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    try {
      const got = await post('/api/find/answer', { q, ask: question, said });
      turn.innerHTML = `<h4>${esc(question)}</h4><p>${cited(got.answer, got.sources)}</p>`;
      said.push({ q: question, a: got.answer });
      nextQuestions(got.next, chips);
    } catch (err) {
      turn.innerHTML = `<h4>${esc(question)}</h4><p class="small">${esc(err.message)}</p>`;
    }
    busy = false;
  };
  chips.addEventListener('click', (e) => {
    const b = e.target.closest('[data-next]');
    if (b) ask(b.textContent);
  });
  form.addEventListener('submit', (e) => {
    e.preventDefault();
    const question = input.value.trim();
    if (question.length < 2) return;
    input.value = '';
    ask(question);
  });
}

export async function fillFind(d) {
  const page = $('#find-page');
  if (!page) return;
  const top = $('#find-top', page), cards = $('#find-cards', page), web = $('#find-web', page), more = $('#find-more', page);
  const gone = () => !page.isConnected;
  if (d.reach.ai) {
    top.hidden = false;
    top.innerHTML = waiting(3);
  }
  if (d.reach.outside) {
    cards.innerHTML = waiting(2);
    more.innerHTML = waiting(4);
  }
  try {
    const near = await post('/api/find', { q: d.q });
    if (gone()) return;
    if (near.following) {
      const b = $('.find-tools [data-track]', page);
      b.setAttribute('aria-pressed', 'true');
      b.textContent = 'Following';
    }
    cards.innerHTML = near.cards.map((c) => card(c)).join('');
    more.innerHTML = `${oddsPart(near.odds)}${section('More reporting', near.news)}${section('What people are saying', near.talk)}${section('Research', near.papers)}${section('Code', codeRows(near.code))}`;
    if (!near.cards.length && !near.news.length && !d.stories.length && !d.reports.length) more.innerHTML = '<p class="empty">Nothing anywhere yet. Try a shorter word, or a name.</p>';
  } catch {
    if (gone()) return;
    cards.innerHTML = '';
    more.innerHTML = '';
  }
  const said = await post('/api/find/answer', { q: d.q }).catch(() => null);  // after: it reads what the first call found
  if (gone()) return;
  if (said?.web?.length) web.innerHTML = section('From the web', said.web);
  if (said?.answer) drawAnswer(top, d.q, said);
  else top.hidden = true;
}

export const followingPage = (d) => ({
  head: 'Following', deck: d.cards.length ? 'Each one the way it is best read. Press Following to stop.' : 'Search for anything and press Follow. A stock, a team, a town, a war or a subject each gets its own place here and on the front page.',
  body: `<div class="fo-grid">${d.cards.map((c) => card({ ...c, followed: true })).join('')}</div>`,
});
