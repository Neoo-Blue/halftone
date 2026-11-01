// Election watch. The map and the chambers are printed like the rest of the paper: a state's dots grow with how sure its
// race is, so a safe seat reads solid and a toss-up barely prints. Names and numbers come from WARROOM through the server,
// which keeps only known fields, and everything still goes through esc.
import { $, $$, esc, ago, plural, sideBar, reading } from '/lib.js';
import { answerInto } from '/find.js';
import { openMap, going, shut } from '/usmap.js';

const pct = (p) => `${Math.round(p * 100)}%`;
const PARTY = { D: 'Democrats', R: 'Republicans', I: 'Independents' };
const SHORT = { D: 'D', R: 'R', I: 'I' };
const clock = (ts, tz) => new Date(ts * 1000).toLocaleString('en-US', { weekday: 'short', hour: 'numeric', minute: '2-digit', timeZone: tz || undefined });

// ---------------------------------------------------------------- a chamber, as seats in a half circle
function seatsOf(c) {
  const count = (o, k) => o?.[k] || 0, row = (kind, n) => Array(n).fill(kind);
  const held = c.held || {};
  return [
    ...row('dw', count(c.won, 'D')), ...row('dh', count(held, 'D')), ...row('ih', count(held, 'I')), ...row('da', count(c.ahead, 'D')), ...row('dl', count(c.lean, 'D')),
    ...row('tt', count(c.lean, 'T') + count(c.ahead, 'I') + count(c.won, 'I') + count(c.won, 'O') + count(c.ahead, 'O')),
    ...row('rl', count(c.lean, 'R')), ...row('ra', count(c.ahead, 'R')), ...row('rh', count(held, 'R')), ...row('rw', count(c.won, 'R')),
  ];
}

function arc(c) {
  const seats = seatsOf(c), n = seats.length;
  if (!n) return '';
  const rows = Math.max(2, Math.round(Math.sqrt(n / 2.4))), inner = 34, outer = 96, gap = (outer - inner) / (rows - 1 || 1);
  const radii = Array.from({ length: rows }, (_, i) => inner + i * gap), total = radii.reduce((a, b) => a + b, 0);
  const spots = [];
  let placed = 0;
  radii.forEach((r, i) => {
    const here = i === rows - 1 ? n - placed : Math.round((n * r) / total);
    placed += here;
    for (let j = 0; j < here; j++) {
      const a = Math.PI * (1 - (here === 1 ? .5 : j / (here - 1)));
      spots.push([a, 100 + r * Math.cos(a), 100 - r * Math.sin(a)]);
    }
  });
  spots.sort((a, b) => b[0] - a[0]);
  const size = Math.min(4.4, 1.05 * Math.sqrt(9000 / n) / 3);
  const dots = spots.map(([, x, y], i) => `<circle class="seat ${seats[i]}" cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="${size.toFixed(2)}" style="--i:${i}"/>`).join('');
  return `<svg class="el-arc" viewBox="0 0 200 106" role="img" aria-label="${esc(tallyWords(c))}">${dots}</svg>`;
}

function sumOf(c) {
  const held = c.held || {}, of = (o, k) => o?.[k] || 0;
  const d = of(c.won, 'D') + of(c.ahead, 'D') + of(c.lean, 'D') + (held.D || 0) + (held.I || 0);
  const r = of(c.won, 'R') + of(c.ahead, 'R') + of(c.lean, 'R') + (held.R || 0);
  return { d, r, t: of(c.lean, 'T') };
}

// Once the count starts, the big numbers are only what's been called. The half circle still shows who's ahead.
function calledOf(c) {
  const held = c.held || {}, won = c.won || {};
  return { d: (won.D || 0) + (held.D || 0) + (held.I || 0), r: (won.R || 0) + (held.R || 0), open: c.up - c.called };
}

function tallyWords(c) {
  const { d, r, t } = sumOf(c);
  return `Democrats ${d}, Republicans ${r}${t ? `, ${t} too close to call` : ''}${c.majority ? `. ${c.majority} to win` : ''}.`;
}

function chamberCard(c) {
  const counting = c.called || Object.keys(c.ahead || {}).length, { d, r, t, open } = counting ? calledOf(c) : sumOf(c);
  const odds = c.md != null ? `<span class="el-odds" aria-label="Betting markets: Democrats ${pct(c.md)}"><i style="width:${(c.md * 100).toFixed(1)}%"></i></span><small>Markets: Democrats ${pct(c.md)}, Republicans ${100 - Math.round(c.md * 100)}%</small>` : '';
  return `<div class="el-house"><h3>${esc(c.name)}${c.majority ? ` <small>${esc(c.majority)} to win</small>` : ` <small>${esc(c.seats)} on the ballot</small>`}</h3>${arc(c)}
    <p class="el-sum"><b class="s-l-text">${esc(d)}</b>${counting ? `<span>${esc(open)} still open</span>` : t ? `<span>${esc(t)} close</span>` : ''}<b class="s-r-text">${esc(r)}</b></p>${odds}</div>`;
}

// ---------------------------------------------------------------- the printed map
const STATES = { AL: 'Alabama', AK: 'Alaska', AZ: 'Arizona', AR: 'Arkansas', CA: 'California', CO: 'Colorado', CT: 'Connecticut', DE: 'Delaware', DC: 'District of Columbia', FL: 'Florida', GA: 'Georgia', HI: 'Hawaii', ID: 'Idaho', IL: 'Illinois', IN: 'Indiana', IA: 'Iowa', KS: 'Kansas', KY: 'Kentucky', LA: 'Louisiana', ME: 'Maine', MD: 'Maryland', MA: 'Massachusetts', MI: 'Michigan', MN: 'Minnesota', MS: 'Mississippi', MO: 'Missouri', MT: 'Montana', NE: 'Nebraska', NV: 'Nevada', NH: 'New Hampshire', NJ: 'New Jersey', NM: 'New Mexico', NY: 'New York', NC: 'North Carolina', ND: 'North Dakota', OH: 'Ohio', OK: 'Oklahoma', OR: 'Oregon', PA: 'Pennsylvania', RI: 'Rhode Island', SC: 'South Carolina', SD: 'South Dakota', TN: 'Tennessee', TX: 'Texas', UT: 'Utah', VT: 'Vermont', VA: 'Virginia', WA: 'Washington', WV: 'West Virginia', WI: 'Wisconsin', WY: 'Wyoming' };

let mapView = 'senate';
const mapBlock = (us) => {
  const views = us.chambers.filter((c) => us.map[c.kind]);
  if (!views.some((c) => c.kind === mapView)) mapView = views[0]?.kind;
  return `<figure class="el-map"><div class="el-map-top"><div class="seg" role="group" aria-label="What the map shows">${views.map((c) => `<button type="button" data-el-view="${esc(c.kind)}" aria-pressed="${c.kind === mapView}">${esc(c.name)}</button>`).join('')}</div>
    <label class="el-find">Find a state <select data-el-state><option value="">Choose</option>${Object.entries(STATES).map(([k, n]) => `<option value="${k}">${n}</option>`).join('')}</select></label></div>
    <div class="el-canvas"><canvas role="img" aria-label="A map of the United States. Each state is printed in dots, blue for Democrats and red for Republicans, and the dots grow with how sure the race is. Choose a state to go into its districts and counties."></canvas><div class="el-tip" hidden></div><nav class="el-crumbs" aria-label="Where you are on the map" hidden></nav><aside class="el-panel" hidden></aside></div>
    <figcaption><span class="el-key"><i class="s-l"></i>Democratic</span><span class="el-key"><i class="s-r"></i>Republican</span><span>A bigger dot means a surer race. Faint dots have nothing on the ballot. Click a state to go in.</span></figcaption></figure>`;
};

function mountMap(root, us, pick, races) {
  const host = $('.el-map', root);
  if (!host) return null;
  const opts = { pick, states: STATES, row: raceRow, seat: seatText, names: nameLine, state: raceState, bar, races: races || (async () => (await (await fetch('/api/detail/elections/', { credentials: 'same-origin' })).json()).races) };
  const opening = openMap(host, us.map, mapView, opts);
  host.onclick = (e) => {
    const b = e.target.closest('[data-el-view]');
    if (!b) return;
    mapView = b.dataset.elView;
    $$('[data-el-view]', host).forEach((x) => x.setAttribute('aria-pressed', String(x === b)));
    shut(host);
    openMap(host, us.map, mapView, opts);
  };
  $('[data-el-state]', host).onchange = (e) => { if (e.target.value) going(host, e.target.value); };
  return opening;
}

// ---------------------------------------------------------------- races
const seatText = (r) => r.seat.replace(/ US (Senate|House)( Special General)?/, ' $1').replace(/ House (\d+)$/, ' $1');
const seatName = (r) => esc(seatText(r));
const bar = (p) => (p == null ? '' : `<span class="el-odds" role="img" aria-label="Democrats ${pct(p)}"><i style="width:${(p * 100).toFixed(1)}%"></i></span>`);
const nameLine = (r) => ['D', 'R', 'I'].filter((k) => r.noms?.[k]).map((k) => `${r.noms[k]} (${SHORT[k]})`).join(' vs ');
const names = (r) => esc(nameLine(r));

function raceState(r) {
  if (r.won) return `<b>${esc(r.won.n)} wins</b>`;
  if (r.lead) return `${esc(r.lead.n)} ahead, ${esc(r.lead.pct)}%. ${Math.round(r.rep)}% counted`;
  return [r.rating, r.pd != null && `model D ${pct(r.pd)}`, r.md != null && `market D ${pct(r.md)}`, r.poll && `polls ${r.poll.d}-${r.poll.r}`].filter(Boolean).map(esc).join(', ');
}

const raceRow = (r) => `<li><a href="/elections/race/${esc(r.key)}">${seatName(r)}</a><span>${names(r)}</span><span>${r.note ? esc(r.note) : raceState(r)}</span>${r.won ? '' : bar(r.pd)}</li>`;
const raceList = (rows) => `<ul class="wire-list el-races">${rows.map(raceRow).join('')}</ul>`;

// ---------------------------------------------------------------- abroad
function daysTo(iso) {
  return Math.round((new Date(`${iso}T12:00:00Z`) - Date.now()) / 864e5);
}

function stage(e) {
  if (e.phase === 'voting') return 'Voting now';
  if (e.phase === 'counting') return 'Counting';
  if (e.phase === 'results') return e.line || 'Results';
  const n = daysTo(e.start);
  return n <= 0 ? 'Today' : n === 1 ? 'Tomorrow' : `In ${n} days`;
}

const abroadRow = (e) => `<li><a href="/elections/world/${esc(e.id)}">${esc(e.country)}</a><span>${esc(e.offices.join(', '))}, ${esc(new Date(`${e.start}T12:00:00Z`).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }))}</span><span class="el-stage ${esc(e.phase)}">${esc(stage(e))}</span></li>`;
const abroad = (rows, title = 'Voting around the world') => (rows?.length ? `<section class="el-part"><h3>${esc(title)}</h3><ul class="wire-list el-world">${rows.map(abroadRow).join('')}</ul></section>` : '');

// ---------------------------------------------------------------- what the numbers add up to
const steps = (l) => (l.steps.length ? `<ol class="el-steps" aria-label="Every race from surest Democratic to surest Republican">${l.steps.map((s, i) => `<li class="${s.v >= 0 ? 'el-d' : 'el-r'}${i === l.need - 1 ? ' el-tipping' : ''}" style="--v:${Math.round(Math.abs(s.v) * 100)}%"><a href="/elections/race/${esc(s.key)}" aria-label="${esc(STATES[s.state] || s.state)}${i === l.need - 1 ? ', the tipping point' : ''}">${esc(s.state)}</a></li>`).join('')}</ol>` : '');

function tipCard(c) {
  const l = c.ladder;
  if (!l) return '';
  const why = l.start ? `Democrats hold ${l.start} seats that aren't on the ballot and need ${l.need} of these ${l.of}.` : `Democrats need ${l.need} of ${l.of}.`;
  return `<section class="el-card"><h3>The seat that decides the ${esc(c.name)}</h3><a class="el-seat" href="/elections/race/${esc(l.tip.key)}">${seatName(l.tip)}</a>
    <p>${esc(why)} Rank every race by how likely Democrats are to win it, and that's the one that gets them there, at ${pct(l.chance)}. If every likelier result holds, it decides the chamber.</p>${steps(l)}</section>`;
}

function gainsCard(us) {
  const line = (c) => {
    const d = c.gains.D, r = c.gains.R, list = (rows) => (rows.length ? (rows.length <= 6 ? rows.map((x) => x.state).join(', ') : `${rows.length} seats`) : 'none');
    return `<li><b>${esc(c.name)}</b><span class="s-l-text">Democrats gain ${esc(list(d))}</span><span class="s-r-text">Republicans gain ${esc(list(r))}</span></li>`;
  };
  return `<section class="el-card"><h3>Seats likely to change hands</h3><p>Races leaning away from the party that holds them now.</p><ul class="el-gains">${us.chambers.map(line).join('')}</ul></section>`;
}

function signalsCard(s) {
  const gap = (g) => `<li><a href="/elections/race/${esc(g.key)}">${seatName(g)}</a><span>Bettors ${pct(g.md)} Democratic, the model ${pct(g.pd)}</span></li>`;
  const against = (g) => `<li><a href="/elections/race/${esc(g.key)}">${seatName(g)}</a><span>Rated ${esc(g.rating)}, but polls have it ${esc(g.poll.d)} to ${esc(g.poll.r)}</span></li>`;
  const rows = [...s.against.map(against), ...s.gaps.map(gap)];
  return rows.length ? `<section class="el-card"><h3>Where the signals disagree</h3><p>Where models, polls and money don't tell one story, the race is less settled than a single number makes it look.${s.splits ? ` Forecasters are split on ${esc(s.splits)} Senate and governor races.` : ''}</p><ul class="wire-list el-gaps">${rows.slice(0, 5).join('')}</ul></section>` : '';
}

function night(us, tz) {
  if (!us.hours?.length || us.phase === 'final') return '';
  const now = Date.now() / 1000, next = us.hours.find((h) => h.at > now);
  const row = (h) => `<li class="${h.at <= now ? 'el-gone' : h === next ? 'el-next' : ''}"><time>${esc(new Date(h.at * 1000).toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', timeZone: tz || undefined }))}</time><div><b>${esc(h.states.map((s) => STATES[s] || s).join(', '))}</b>${h.watch.length ? `<span>Watch ${h.watch.map((w) => `<a href="/elections/race/${esc(w.key)}">${seatName(w)}</a>`).join(', ')}</span>` : ''}</div></li>`;
  return `<section class="el-part"><h3>How the night will go</h3><p class="small">When the last polls close in each state, in your time, and the closest races that come with them. Some states count far faster than others.</p><ol class="el-night">${us.hours.map(row).join('')}</ol></section>`;
}

// ---------------------------------------------------------------- the desk
function schedule(us, tz) {
  const s = us.schedule, marks = [['Polls open', s.polls_open], ['First polls close', s.first_close], ['Last polls close', s.last_close]].filter(([, t]) => t);
  return us.phase === 'final' ? '' : `<dl class="el-times">${marks.map(([k, t]) => `<div><dt>${esc(k)}</dt><dd>${esc(clock(t, tz))}</dd></div>`).join('')}</dl>`;
}

// While votes are counted. WARROOM reads every race every 30 seconds, so a read this old means something on the way has stopped.
const LATE = 180;
const secs = (ts) => new Date(ts * 1000).toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', second: '2-digit' });
function liveLine(o) {
  if (!o.live) return '';
  const late = o.read && Date.now() / 1000 - o.read > LATE;
  return `<p class="el-live${late ? ' late' : ''}"><i aria-hidden="true"></i>${late ? `The count hasn't been reached since ${esc(secs(o.read))}. This is what it last said.` : `Live. Every race updates every 30 seconds.${o.read ? ` Count read at ${esc(secs(o.read))}.` : ''}`}</p>`;
}

// Whether two copies differ in anything but when they were read: a time alone isn't worth a redraw.
const stampOf = (o) => JSON.stringify(o, (k, v) => (k === 'as_of' || k === 'read' ? 0 : v));

// An open page keeps up by itself. It asks nothing while nobody's looking, asks at once when they're back, and stops once the count is over or the page has gone.
function keepUp(o, root, url, draw) {
  const over = (x) => !x || (!x.live && x.phase === 'final');
  if (!root || over(o)) return;
  let held = o;
  const stop = () => { clearInterval(timer); document.removeEventListener('visibilitychange', beat); };
  const beat = async () => {
    if (!root.isConnected) { stop(); return; }
    if (document.hidden) return;
    const fresh = await fetch(url, { cache: 'no-store', credentials: 'same-origin' }).then((r) => (r.ok ? r.json() : null)).catch(() => null);
    if (!root.isConnected) return;
    if (!fresh) { $('.el-now', root).innerHTML = liveLine(held); return; }  // once this is old enough the line says so
    draw(fresh);
    held = fresh.kind === 'elections' ? fresh.us : fresh;
    if (over(held)) stop();
  };
  const timer = setInterval(beat, 30000);
  document.addEventListener('visibilitychange', beat);
}

function usBlock(us, tz) {
  const calls = us.calls?.length ? `<section class="el-part"><h3>Latest calls</h3>${raceList(us.calls)}</section>` : '';
  const said = us.note?.text ? `<p class="el-note">${esc(us.note.text)}</p><small class="el-by">Written by AI from these numbers and today's stories, ${esc(ago(us.note.at))}. It can be wrong.</small>` : '';
  const house = us.chambers.find((c) => c.kind === 'house')?.ladder;
  return `<div class="el-now">${liveLine(us)}</div><div class="el-lead"><div><p class="el-title">${esc(us.title)}</p><p class="el-line">${esc(us.line)}</p>${said}${schedule(us, tz)}${us.ballot ? `<p class="small">Generic ballot: Democrats ${esc(us.ballot.d)}, Republicans ${esc(us.ballot.r)}.</p>` : ''}</div>
    <div class="el-houses">${us.chambers.map(chamberCard).join('')}</div></div>
    <div class="el-insights">${tipCard(us.chambers.find((c) => c.kind === 'senate') || {})}${gainsCard(us)}${signalsCard(us.signals)}</div>
    ${house ? `<p class="el-more">In the House, Democrats need ${esc(house.need)} seats. Counted the same way, the tipping point is <a href="/elections/race/${esc(house.tip.key)}">${seatName(house.tip)}</a>, at ${pct(house.chance)}.</p>` : ''}
    ${mapBlock(us)}${calls}${night(us, tz)}`;
}

let printed = '';
export function electionDesk(p) {
  const v = p.elections;
  if (!v) { printed = ''; return; }
  const body = $('#electionsbody'), us = v.us, stamp = stampOf(v);
  if (stamp !== printed) {
    printed = stamp;
    body.classList.toggle('el-fresh', !body.dataset.seen);
    body.dataset.seen = '1';
    body.innerHTML = `${us ? usBlock(us, p.tz) : ''}<div class="page-cols">${us ? `<section class="el-part"><h3>Closest Senate and governor races</h3>${raceList(us.closest)}</section><section class="el-part"><h3>House races to watch</h3>${raceList(us.house)}</section>` : ''}${abroad(v.world)}</div>${us ? '<p class="el-all"><a href="/elections">Every race</a></p>' : ''}`;
    if (us) mountMap(body, us);
  }
  const now = $('.el-now', body), age = Date.now() / 1000 - (v.as_of || 0), foot = $('#asof-elections');
  if (now) now.innerHTML = liveLine(us);
  foot.textContent = `${v.as_of ? `Updated ${ago(v.as_of)}. ` : ''}From WARROOM. ${us ? `Sources: ${us.sources.join(', ')}.` : 'Calendar: IFES ElectionGuide.'}`;
  foot.classList.toggle('stale', age > 600);
}

// ---------------------------------------------------------------- the pages
const storyRow = (s) => `<li><a href="${esc(reading(s.u))}">${esc(s.t)}</a><span>${esc(s.src)}${s.ts ? `, ${esc(ago(s.ts))}` : ''} ${sideBar(s.lean)}</span></li>`;
const stories = (rows, title = 'In the paper') => (rows?.length ? `<section class="el-part"><h3>${esc(title)}</h3><ul class="wire-list">${rows.map(storyRow).join('')}</ul></section>` : '');

export function electionsView(d) {
  const us = d.us;
  return {
    head: us ? us.name : 'Election watch', deck: us ? `${us.title}. ${us.line}` : 'Votes around the world this month.', meta: '',
    body: `<div id="el-page">${us ? `<div class="el-now">${liveLine(us)}</div><div class="el-houses wide">${us.chambers.map(chamberCard).join('')}</div>${mapBlock(us)}
      <section class="el-part"><h3>Every race</h3><div class="el-filter"><input type="search" id="el-q" placeholder="A state, a name or a seat" aria-label="Filter the races" autocomplete="off"><div class="seg" role="group" aria-label="Which races">${['all', ...us.chambers.map((c) => c.kind)].map((k, i) => `<button type="button" data-el-kind="${esc(k)}" aria-pressed="${i === 0}">${esc(k === 'all' ? 'All' : us.chambers.find((c) => c.kind === k).name)}</button>`).join('')}</div></div><ul class="wire-list el-races two" id="el-list"></ul></section>` : ''}${abroad(d.world)}</div>`,
    side: stories(d.stories, 'The latest'),
  };
}

export function fillElections(d) {
  const root = $('#el-page');
  if (!root || !d.us) return;
  let kind = 'all';
  const list = $('#el-list', root), q = $('#el-q', root);
  const show = () => {
    const words = q.value.toLowerCase().trim();
    const rows = d.races.filter((r) => (kind === 'all' || r.kind === kind) && (!words || `${r.seat} ${r.where} ${Object.values(r.noms).join(' ')}`.toLowerCase().includes(words)));
    list.innerHTML = rows.slice(0, 120).map(raceRow).join('') || '<li class="empty">No race matches that.</li>';
  };
  const state = (st) => history.replaceState(null, '', st ? `/elections?state=${st}` : '/elections');  // the address follows the map
  q.oninput = show;
  root.onclick = (e) => {
    const b = e.target.closest('[data-el-kind]');
    if (!b) return;
    kind = b.dataset.elKind;
    $$('[data-el-kind]', root).forEach((x) => x.setAttribute('aria-pressed', String(x === b)));
    show();
  };
  show();
  const races = async () => d.races;
  const wanted = new URLSearchParams(location.search).get('state');
  mountMap(root, d.us, state, races)?.then(() => { if (wanted && STATES[wanted]) going($('.el-map', root), wanted); });
  keepUp(d.us, root, '/api/detail/elections/', (fresh) => {  // whatever the reader has typed or opened stays as it was
    if (!fresh.us) return;
    const moved = stampOf(fresh.us) !== stampOf(d.us) || stampOf(fresh.races) !== stampOf(d.races);
    d = fresh;
    $('.el-now', root).innerHTML = liveLine(d.us);
    if (!moved) return;
    $('.page-sub .deck').textContent = `${d.us.title}. ${d.us.line}`;
    $('.el-houses', root).innerHTML = d.us.chambers.map(chamberCard).join('');
    mountMap(root, d.us, state, races);
    if (!list.contains(document.activeElement)) show();  // someone moving through the list by keyboard keeps their place
  });
}

const followBox = (kind, key, name, on) => `<div class="story-tools"><button type="button" class="ghost text" data-track="${esc(JSON.stringify({ kind, key, name }))}" aria-pressed="${!!on}">${on ? 'Following' : 'Follow'}</button></div>`;

// Where each signal puts a race, on one scale from surely Republican to surely Democratic. Agreement and disagreement show at a glance.
const SCALE = { 'Safe R': 3, 'Likely R': 15, 'Lean R': 30, 'Tilt R': 42, Tossup: 50, 'Tilt D': 58, 'Lean D': 70, 'Likely D': 85, 'Safe D': 97 };

function signalScale(d) {
  const rows = [['The model', d.pd != null ? d.pd * 100 : null, d.pd != null && `Democrats ${pct(d.pd)}`], ['Betting markets', d.md != null ? d.md * 100 : null, d.md != null && `Democrats ${pct(d.md)}${d.volume ? `, $${Math.round(d.volume / 1000).toLocaleString('en-US')}K traded` : ''}`],
    ['Poll average', d.poll ? Math.max(2, Math.min(98, 50 + (d.poll.d - d.poll.r) * 4)) : null, d.poll && `${d.poll.d} to ${d.poll.r}, ${d.poll.n} polls`], ...d.calls.map((c) => [c.who, SCALE[c.rating] ?? null, c.rating.replace('Tossup', 'Toss-up')])].filter(([, at]) => at != null);
  return rows.length ? `<section class="el-part"><h3>What each signal says</h3><div class="el-scale-key"><span>Surely Republican</span><span>Even</span><span>Surely Democratic</span></div><ul class="el-scale">${rows.map(([k, at, v]) => `<li><span>${esc(k)}</span><div><i class="${at > 50 ? 's-l' : at < 50 ? 's-r' : 's-c'}" style="left:${at.toFixed(1)}%"></i></div><b>${esc(v)}</b></li>`).join('')}</ul></section>` : '';
}

function pollTrail(d) {
  const rows = d.polls || [];
  if (!rows.length) return '';
  const short = (k) => (d.noms[k] || k).split(' ').pop();
  const days = rows.map((p) => new Date(p.end).getTime()), lo = Math.min(...days), hi = Math.max(...days), span = hi - lo || 1;
  const reach = Math.max(6, ...rows.map((p) => Math.abs(p.d - p.r)));
  const dots = rows.map((p, i) => `<circle class="${p.d >= p.r ? 'seat dw' : 'seat rw'}${p.partisan ? ' hollow' : ''}" cx="${(14 + 372 * (days[i] - lo) / span).toFixed(1)}" cy="${(60 - ((p.d - p.r) / reach) * 50).toFixed(1)}" r="4"/>`).join('');
  const line = (p) => `<li><time>${esc(new Date(`${p.end}T12:00:00Z`).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }))}</time><span>${p.url ? `<a href="${esc(p.url)}" target="_blank" rel="noopener noreferrer">${esc(p.who)}</a>` : esc(p.who)}${p.partisan ? ` <em>${esc(p.partisan)} sponsor</em>` : ''}</span><b>${esc(short('D'))} ${esc(p.d)}, ${esc(short('R'))} ${esc(p.r)}</b></li>`;
  return `<section class="el-part"><h3>The polls</h3>${rows.length > 1 ? `<svg class="el-trail" viewBox="0 0 400 120" role="img" aria-label="Each poll's margin over time"><line x1="0" x2="400" y1="60" y2="60"/>${dots}</svg><p class="small">Each dot is a poll. Above the line, ${esc(short('D'))} leads. Hollow dots were paid for by one side.</p>` : ''}<ul class="el-polls">${rows.slice(0, 8).map(line).join('')}</ul></section>`;
}

function chaseBlock(d) {
  const c = d.chase;
  if (!c) return '';
  const can = c.need != null && c.need <= 1;
  return `<section class="el-part el-chase"><h3>What's left</h3><p class="el-big">${can ? `${Math.round(c.need * 100)}%` : 'Out of reach'}</p><p>${can ? `of the votes still out is what ${esc(c.trail)} needs to catch ${esc(c.lead)}.` : `${esc(c.trail)} can't catch ${esc(c.lead)} on this estimate.`} ${esc(c.lead)} leads by ${esc(c.gap.toLocaleString('en-US'))}, with about ${esc(c.left.toLocaleString('en-US'))} votes still out. That's an estimate from the share counted, and late votes often lean one way.</p></section>`;
}

function placeLine(d) {
  const p = d.place;
  if (!p) return '';
  if (p.off === 0) return `<p class="el-place">This is the tipping point: the seat that gets Democrats to a majority if every likelier result holds.</p>`;
  return Math.abs(p.off) > 6 ? '' : `<p class="el-place">${plural(Math.abs(p.off), 'seat')} ${p.off < 0 ? 'safer for Democrats than' : 'harder for Democrats than'} the tipping point, <a href="/elections/race/${esc(p.tipkey)}">${esc(p.tip)}</a>.</p>`;
}

const asked = (title) => `<section class="el-part"><h3>${esc(title)}</h3><div id="el-answer"></div></section>`;

// What moves with the count.
function counted(d) {
  const total = d.runners.reduce((a, c) => a + c.votes, 0);
  const tally = total ? `<section class="el-part"><h3>The count</h3><p class="small">${Math.round(d.rep)}% counted.</p><ul class="plain el-count">${d.runners.map((c) => `<li><b>${esc(c.n)}${c.won ? ' wins' : ''}</b><span>${esc(c.votes.toLocaleString('en-US'))}, ${esc(c.pct)}%</span><i class="${c.p === 'D' ? 's-l' : c.p === 'R' ? 's-r' : 's-c'}" style="width:${c.pct}%"></i></li>`).join('')}</ul></section>` : '';
  return `<div class="el-now">${liveLine(d)}</div><p class="el-verdict">${esc(d.reading.join(' '))}</p>${placeLine(d)}${chaseBlock(d)}${tally}`;
}

export function raceView(d) {
  const facts = [['Held by', d.holder ? `${d.holder.n}${d.inc ? ` (${d.inc})` : ''}` : PARTY[d.inc]], ['Since', d.holder?.since?.slice(0, 4)], ['Seat', d.open ? 'Open' : d.holder ? 'Incumbent running' : ''], ['Rating', d.rating.replace('Tossup', 'Toss-up')]].filter(([, v]) => v);
  return {
    head: seatText(d), deck: nameLine(d), meta: d.won ? `${d.won.n} wins` : '',
    body: `${followBox('race', d.key, d.seat, d.followed)}<div id="el-live">${counted(d)}</div>${signalScale(d)}${d.ai ? asked('What this race is about') : ''}${pollTrail(d)}${stories(d.stories)}${d.news.length ? `<section class="el-part"><h3>More reporting</h3><ul class="wire-list">${d.news.map(storyRow).join('')}</ul></section>` : ''}`,
    side: `<dl class="facts">${facts.map(([k, v]) => `<div><dt>${esc(k)}</dt><dd>${esc(v)}</dd></div>`).join('')}</dl>`,
  };
}

export function fillRace(d) {
  const box = $('#el-answer'), root = $('#el-live');
  if (box) answerInto(box, d.q);
  let shown = d;
  keepUp(d, root, `/api/detail/count/${encodeURIComponent(d.key)}`, (fresh) => {
    const moved = stampOf(fresh.runners) !== stampOf(shown.runners) || stampOf(fresh.reading) !== stampOf(shown.reading);
    shown = fresh;
    if (!moved) { $('.el-now', root).innerHTML = liveLine(fresh); return; }
    root.classList.add('el-tick');  // on its children, which are new each time, so it plays each time
    root.innerHTML = counted(fresh);
    $('.page-sub .byline')?.remove();
    if (fresh.won) $('.page-sub').insertAdjacentHTML('beforeend', `<p class="byline">${esc(fresh.won.n)} wins</p>`);
  });
}

export function ballotView(d) {
  const won = d.won, rows = won?.rows?.length ? `<section class="el-part"><h3>${won.decided ? 'Results' : 'Early results'}</h3>${won.line ? `<p>${esc(won.line)}</p>` : ''}<ul class="plain el-count">${won.rows.map((r) => `<li><b>${esc(r.party)}${r.person ? `, ${esc(r.person)}` : ''}</b><span>${[r.seats != null && plural(r.seats, 'seat'), r.pct != null && `${r.pct}%`].filter(Boolean).map(esc).join(', ')}</span><i class="s-c" style="width:${r.pct || 0}%"></i></li>`).join('')}</ul>${won.url ? `<p class="source"><a href="${esc(won.url)}" target="_blank" rel="noopener noreferrer">Results from Wikipedia</a></p>` : ''}</section>` : '';
  const date = (iso) => new Date(`${iso}T12:00:00Z`).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  const facts = [['Voting', d.start === d.end ? date(d.start) : `${date(d.start)} to ${date(d.end)}`], ['Stage', d.phase === 'results' ? 'Results' : stage(d)], ['Called early', d.snap ? 'Yes' : ''], ['Turnout', won?.turnout]].filter(([, v]) => v);
  return {
    head: d.country, deck: d.offices.join(', '), meta: stage(d), scene: d.lat != null ? { pin: [d.lat, d.lon], span: 8 } : null,
    body: `${followBox('ballot', d.id, `${d.country} election`, d.followed)}${rows}${d.ai ? asked('What this vote is about') : ''}${stories(d.stories)}${d.news.length ? `<section class="el-part"><h3>More reporting</h3><ul class="wire-list">${d.news.map(storyRow).join('')}</ul></section>` : ''}`,
    side: `<dl class="facts">${facts.map(([k, v]) => `<div><dt>${esc(k)}</dt><dd>${esc(v)}</dd></div>`).join('')}</dl>`,
  };
}
