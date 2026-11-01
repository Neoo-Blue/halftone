// Shared by the front page and the detail pages.
export const $ = (s, el = document) => el.querySelector(s);
export const $$ = (s, el = document) => [...el.querySelectorAll(s)];
export const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

// ---------------------------------------------------------------- formats

export const usd = (c) => `${c < 0 ? '-' : ''}$${(Math.abs(c) / 100).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
export const whole = (n) => Number(n || 0).toLocaleString('en-US');
export const dollars = (v) => (v == null ? 'No price' : v >= 100 ? `$${whole(Math.round(v))}` : `$${v.toFixed(2)}`);
export const compact = (n) => new Intl.NumberFormat('en-US', { notation: 'compact', maximumFractionDigits: 1 }).format(n);
export const pct = (a, b) => (b ? (100 * a) / b : 0);
export const plural = (n, one, many = `${one}s`) => `${whole(n)} ${n === 1 ? one : many}`;
export function ago(ts) {
  if (!ts) return 'never';
  const s = Math.max(0, Date.now() / 1000 - ts);
  if (s < 90) return 'just now';
  if (s < 5400) return `${Math.round(s / 60)} min ago`;
  if (s < 129600) return `${Math.round(s / 3600)} hours ago`;
  return `${Math.round(s / 86400)} days ago`;
}
export function span(sec) {
  if (!sec) return '';
  if (sec < 3600) return `${Math.round(sec / 60)} min`;
  if (sec < 172800) return `${Math.round(sec / 3600)} hours`;
  return `${Math.round(sec / 86400)} days`;
}
export function bytes(n) {
  if (n == null) return '';
  const u = ['B', 'KB', 'MB', 'GB', 'TB', 'PB'];
  let i = 0;
  while (n >= 1024 && i < u.length - 1) { n /= 1024; i += 1; }
  return `${n >= 100 || i < 3 ? Math.round(n) : n.toFixed(1)} ${u[i]}`;
}
// Episodes carry a real air time, so they land on the reader's own day. A film's date is a calendar date stored as midnight UTC.
export const dayKey = (u) => (u.kind === 'movie' ? u.at.slice(0, 10) : new Date(u.at).toLocaleDateString('en-CA'));
export function when(u) {
  const d = new Date(`${dayKey(u)}T12:00:00`), n = new Date(), days = Math.round((new Date(d).setHours(0, 0, 0, 0) - new Date(n).setHours(0, 0, 0, 0)) / 86400000);
  if (days <= 0) return u.kind !== 'movie' && new Date(u.at).getHours() >= 17 ? 'tonight' : 'today';
  return days === 1 ? 'tomorrow' : `on ${d.toLocaleDateString('en-US', { weekday: 'long' })}`;
}
export const dayName = (iso) => new Date(iso).toLocaleDateString('en-US', { weekday: 'long', month: 'short', day: 'numeric' });

// Who is carrying a story, always said in words as well as drawn. Unrated outlets aren't on the scale, and one rated outlet says nothing about sides.
export function sideWord([left, center, right]) {
  if (left && right) return 'Both sides';
  if (left) return center ? 'Left and center' : 'Left only';
  if (right) return center ? 'Right and center' : 'Right only';
  return center ? 'Center only' : '';
}
export function sideBar(l, big = false) {
  const n = l ? l[0] + l[1] + l[2] : 0;
  if (n < 2) return '';
  const tip = `${l[0]} left, ${l[1]} center, ${l[2]} right`;
  return `<span class="sides${big ? ' big' : ''}" title="${tip}">${big ? '' : `<em>${sideWord(l)}</em>`}<span class="side-bar" role="img" aria-label="${big ? tip : `${sideWord(l)}: ${tip}`}">${[['l', l[0]], ['c', l[1]], ['r', l[2]]].filter(([, x]) => x).map(([k, x]) => `<i class="s-${k}" style="flex:${x}"></i>`).join('')}</span></span>`;
}

export const ICON = {
  good: '<svg class="st st-good" viewBox="0 0 16 16" aria-hidden="true"><circle cx="8" cy="8" r="5.5"/></svg>',
  warn: '<svg class="st st-warn" viewBox="0 0 16 16" aria-hidden="true"><path d="M8 2 14.5 13.5h-13z"/></svg>',
  note: '<svg class="st st-note" viewBox="0 0 16 16" aria-hidden="true"><circle cx="8" cy="8" r="5"/></svg>',
  bad: '<svg class="st st-bad" viewBox="0 0 16 16" aria-hidden="true"><path d="M3 3l10 10M13 3 3 13" fill="none" stroke-width="3" stroke-linecap="round"/></svg>',
  up: '<svg class="tri" viewBox="0 0 10 10" aria-hidden="true"><path d="M5 1.5 9.5 8.5h-9z"/></svg>',
  down: '<svg class="tri" viewBox="0 0 10 10" aria-hidden="true"><path d="M5 8.5.5 1.5h9z"/></svg>',
};


// The paper's one chart: a run of dots, on a scale fitted to the data, labelled in plain numbers. Hover or tap reads a point.
export const look = { style: 'dots' };  // how home server charts are drawn, from the layout settings
export const lookPicker = () => `<div class="seg looks" role="group" aria-label="Chart style">${[['dots', 'Dots'], ['line', 'Lines'], ['area', 'Areas'], ['bars', 'Columns']].map(([k, name]) => `<button type="button" data-look="${k}" aria-pressed="${k === look.style}">${name}</button>`).join('')}</div>`;

export function dotPlot(rows, series, { fmt = (v) => String(v), lo, hi, caption = '', aria = '', style = 'dots' } = {}) {
  const W = 720, H = 190, n = rows.length;
  const vals = rows.flatMap((r) => series.map((s) => r[s.key])).filter((v) => v != null);
  if (!vals.length) return '<p class="empty">No readings yet.</p>';
  const top = hi ?? Math.max(...vals), low = lo ?? Math.min(...vals), range = top - low || 1;
  const x = (i) => (n > 1 ? 5 + (i / (n - 1)) * (W - 10) : W / 2), y = (v) => H - 6 - ((v - low) / range) * (H - 12);
  const at = (t) => new Date(t * 1000).toLocaleString('en-US', { month: 'short', day: 'numeric', hour: 'numeric' });
  const runs = (s) => {  // a gap in the readings stays a gap in the line
    const out = [[]];
    rows.forEach((r, i) => { if (r[s.key] == null) out.push([]); else out[out.length - 1].push(`${x(i).toFixed(1)} ${y(r[s.key]).toFixed(1)}`); });
    return out.filter((p) => p.length);
  };
  const base = y(low).toFixed(1), wide = Math.max(1.5, Math.min(12, ((W / n) * 0.72) / series.length));
  const marks = {
    dots: (s) => rows.map((r, i) => (r[s.key] == null ? '' : `<circle cx="${x(i).toFixed(1)}" cy="${y(r[s.key]).toFixed(1)}" r="2.4"/>`)).join(''),
    line: (s) => runs(s).map((p) => `<path class="m-line" pathLength="1" d="M${p.join('L')}"/>`).join(''),
    area: (s) => runs(s).map((p) => `<path class="m-area" d="M${p[0].split(' ')[0]} ${base}L${p.join('L')}L${p[p.length - 1].split(' ')[0]} ${base}Z"/><path class="m-line" pathLength="1" d="M${p.join('L')}"/>`).join(''),
    bars: (s, j) => `<path class="m-bar" stroke-width="${wide.toFixed(1)}" d="${rows.map((r, i) => (r[s.key] == null ? '' : `M${(x(i) + (j - (series.length - 1) / 2) * wide).toFixed(1)} ${base}V${y(r[s.key]).toFixed(1)}`)).join('')}"/>`,
  };
  const draw = marks[style] || marks.dots;
  const dots = series.map((s, j) => `<g class="${s.cls}">${draw(s, j)}</g>`).join('');
  const hits = rows.map((r, i) => `<rect x="${(x(i) - W / n / 2).toFixed(1)}" y="0" width="${(W / n + 1).toFixed(1)}" height="${H}" data-tip="${esc(at(r.t))}: ${esc(series.map((s) => `${series.length > 1 ? `${s.name} ` : ''}${fmt(r[s.key])}`).join(', '))}"/>`).join('');
  const legend = series.length > 1 ? series.map((s) => `<i class="${s.cls}"></i>${esc(s.name)}`).join('') : '';
  return `<figure class="plot"><figcaption>${legend}${caption ? `<span>${esc(caption)}</span>` : ''}</figcaption>
    <div class="plot-box"><div class="plot-y" aria-hidden="true"><span>${esc(fmt(top))}</span><span>${esc(fmt((top + low) / 2))}</span><span>${esc(fmt(low))}</span></div>
    <svg viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(aria)}"><path class="grid" d="M0 ${y(top)}H${W}M0 ${y((top + low) / 2)}H${W}M0 ${y(low)}H${W}"/>${dots}${hits}</svg></div>
    <div class="plot-x" aria-hidden="true"><span>${esc(at(rows[0].t))}</span><span>${esc(at(rows[n - 1].t))}</span></div></figure>`;
}

// One column a day. With href each opens that day; without it each is a button the page listens for.
export function dayBars(days, key, { href, picked, label = '', over = key } = {}) {
  const top = Math.max(...days.map((d) => d[key]), 0), scale = Math.max(top, ...days.map((d) => d[over])), short = (d) => dayName(`${d.day}T12:00:00`).replace(/^\w+, /, '');
  const bar = (d, i) => {
    const tip = esc(`${dayName(`${d.day}T12:00:00`)}: ${dollars(d[key])}${label}`), fill = `<i style="--h:${scale ? Math.max(d[key] ? 2 : 0, (d[key] / scale) * 100).toFixed(1) : 0}%;--i:${i}"></i>`;
    return `<li>${href ? `<a href="${esc(href(d))}" data-tip="${tip}" aria-label="${tip}">${fill}</a>` : `<button type="button" data-usage-day="${esc(d.day)}" aria-pressed="${d.day === picked}" data-tip="${tip}" aria-label="${tip}">${fill}</button>`}</li>`;
  };
  return `<p class="chart-note">Highest ${dollars(top)}. Each column is one day.</p><ol class="daybars" style="--n:${days.length}">${days.map(bar).join('')}</ol>
    <div class="plot-x" aria-hidden="true"><span>${esc(short(days[0]))}</span><span>${esc(short(days[days.length - 1]))}</span></div>`;
}

// A question for the paper. The answer goes in as text, never as markup: the model has read strangers' words, so nothing it says may become a link or a tag.
export async function askPaper(question, log, { last = false, url } = {}) {
  const entry = document.createElement('article'), head = document.createElement('h2'), reply = document.createElement('p');
  head.textContent = question;
  reply.textContent = 'Reading the paper.';
  reply.className = 'wait';
  entry.append(head, reply);
  if (last) log.append(entry); else log.prepend(entry);
  log.scrollTop = last ? log.scrollHeight : 0;
  try {
    const r = await fetch('/api/ask', { method: 'POST', credentials: 'same-origin', headers: { 'content-type': 'application/json', 'x-paper': '1' }, body: JSON.stringify({ question, url }) });
    if (r.status === 401) { location.assign('/login'); return entry; }
    const body = await r.json();
    reply.textContent = r.ok ? body.answer : body.error;
  } catch {
    reply.textContent = 'The paper did not answer. Check your connection and try again.';
  }
  reply.className = '';
  return entry;
}

export function lineChart(hist, title = 'Proxmox') {
  if (!hist?.length) return '';
  const most = Math.max(...hist.flatMap((p) => [p.cpu, p.mem, p.io || 0]));
  const last = hist[hist.length - 1];
  return dotPlot(hist, [{ key: 'cpu', name: 'CPU', cls: 'k1' }, { key: 'mem', name: 'Memory', cls: 'k2' }, { key: 'io', name: 'Disk wait', cls: 'k3' }], {
    fmt: (v) => `${Math.round(v * 10) / 10}%`, lo: 0, hi: Math.max(5, Math.ceil(most * 1.15)), caption: 'Last 24 hours', style: look.style,
    aria: `${title} over 24 hours. CPU is now ${last.cpu} percent, memory ${last.mem} percent.`,
  });
}

// A headline must not break inside a name like GPT-6.
export const tight = (text) => esc(text).replace(/\b[A-Za-z]+-\d[\w.]*/g, (m) => `<span class="nb">${m}</span>`);
