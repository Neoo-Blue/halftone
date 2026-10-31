// Shared by the front page and the detail pages.
export const $ = (s, el = document) => el.querySelector(s);
export const $$ = (s, el = document) => [...el.querySelectorAll(s)];
export const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

// ---------------------------------------------------------------- formats

export const usd = (c) => `${c < 0 ? '-' : ''}$${(Math.abs(c) / 100).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
export const whole = (n) => Number(n || 0).toLocaleString('en-US');
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

export const ICON = {
  good: '<svg class="st st-good" viewBox="0 0 16 16" aria-hidden="true"><circle cx="8" cy="8" r="5.5"/></svg>',
  warn: '<svg class="st st-warn" viewBox="0 0 16 16" aria-hidden="true"><path d="M8 2 14.5 13.5h-13z"/></svg>',
  note: '<svg class="st st-note" viewBox="0 0 16 16" aria-hidden="true"><circle cx="8" cy="8" r="5"/></svg>',
  bad: '<svg class="st st-bad" viewBox="0 0 16 16" aria-hidden="true"><path d="M3 3l10 10M13 3 3 13" fill="none" stroke-width="3" stroke-linecap="round"/></svg>',
  up: '<svg class="tri" viewBox="0 0 10 10" aria-hidden="true"><path d="M5 1.5 9.5 8.5h-9z"/></svg>',
  down: '<svg class="tri" viewBox="0 0 10 10" aria-hidden="true"><path d="M5 8.5.5 1.5h9z"/></svg>',
};


// The paper's one chart: a run of dots, on a scale fitted to the data, labelled in plain numbers. Hover or tap reads a point.
export function dotPlot(rows, series, { fmt = (v) => String(v), lo, hi, caption = '', aria = '' } = {}) {
  const W = 720, H = 190, n = rows.length;
  const vals = rows.flatMap((r) => series.map((s) => r[s.key])).filter((v) => v != null);
  if (!vals.length) return '<p class="empty">No readings yet.</p>';
  const top = hi ?? Math.max(...vals), low = lo ?? Math.min(...vals), range = top - low || 1;
  const x = (i) => (n > 1 ? 5 + (i / (n - 1)) * (W - 10) : W / 2), y = (v) => H - 6 - ((v - low) / range) * (H - 12);
  const at = (t) => new Date(t * 1000).toLocaleString('en-US', { month: 'short', day: 'numeric', hour: 'numeric' });
  const dots = series.map((s) => `<g class="${s.cls}">${rows.map((r, i) => (r[s.key] == null ? '' : `<circle cx="${x(i).toFixed(1)}" cy="${y(r[s.key]).toFixed(1)}" r="2.4"/>`)).join('')}</g>`).join('');
  const hits = rows.map((r, i) => `<rect x="${(x(i) - W / n / 2).toFixed(1)}" y="0" width="${(W / n + 1).toFixed(1)}" height="${H}" data-tip="${esc(at(r.t))}: ${esc(series.map((s) => `${series.length > 1 ? `${s.name} ` : ''}${fmt(r[s.key])}`).join(', '))}"/>`).join('');
  const legend = series.length > 1 ? series.map((s) => `<i class="${s.cls}"></i>${esc(s.name)}`).join('') : '';
  return `<figure class="plot"><figcaption>${legend}${caption ? `<span>${esc(caption)}</span>` : ''}</figcaption>
    <div class="plot-box"><div class="plot-y" aria-hidden="true"><span>${esc(fmt(top))}</span><span>${esc(fmt((top + low) / 2))}</span><span>${esc(fmt(low))}</span></div>
    <svg viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(aria)}"><path class="grid" d="M0 ${y(top)}H${W}M0 ${y((top + low) / 2)}H${W}M0 ${y(low)}H${W}"/>${dots}${hits}</svg></div>
    <div class="plot-x" aria-hidden="true"><span>${esc(at(rows[0].t))}</span><span>${esc(at(rows[n - 1].t))}</span></div></figure>`;
}

export function lineChart(hist, title = 'Proxmox') {
  if (!hist?.length) return '';
  const most = Math.max(...hist.flatMap((p) => [p.cpu, p.mem, p.io || 0]));
  const last = hist[hist.length - 1];
  return dotPlot(hist, [{ key: 'cpu', name: 'CPU', cls: 'k1' }, { key: 'mem', name: 'Memory', cls: 'k2' }, { key: 'io', name: 'Disk wait', cls: 'k3' }], {
    fmt: (v) => `${Math.round(v * 10) / 10}%`, lo: 0, hi: Math.max(5, Math.ceil(most * 1.15)), caption: 'Last 24 hours',
    aria: `${title} over 24 hours. CPU is now ${last.cpu} percent, memory ${last.mem} percent.`,
  });
}

// A headline must not break inside a name like GPT-6.
export const tight = (text) => esc(text).replace(/\b[A-Za-z]+-\d[\w.]*/g, (m) => `<span class="nb">${m}</span>`);
