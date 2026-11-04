// The election map. The whole country in printed dots, and you can go into it: a state opens on its districts and counties,
// a district or a county on what's in it. Everything shares one projection, so the camera moves through a single picture and
// the paper prints each level at its own scale. Names come through the server's checks or from public Census files, and go
// into the page through esc or onto the canvas as text.
import { $, esc } from '/lib.js';

const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
const WIDE = 960, CELL = 8, ROW = .92, GAP = 7, DEEPEST = 90;
let grid = null, swept = false;  // the map prints in once, not at every new count
const gridded = () => (grid ||= fetch('/us-dots.json').then((r) => r.json()).catch((e) => { grid = null; throw e; }));
const held = new Map(), tallied = new Map();
// A statewide race county by county, where WARROOM has read it: the county shapes are keyed by name, as the server keys the count.
const COUNTY_RACE = { senate: ['S', 'Senate'], governor: ['G', "governor's"], president: ['P', 'presidential'] };
const coName = (n) => String(n || '').toLowerCase().replace(/\b(county|parish|borough|census area|city and borough|municipality)\b/g, ' ').replace('saint', 'st').replace(/[^a-z]/g, '');
const coLean = (row) => {
  const share = (p) => row?.c.find((x) => String(x.party).startsWith(p))?.pct ?? null, d = share('Democ'), r = share('Repub');
  return d == null && r == null ? null : Math.max(-1, Math.min(1, (((d ?? 0) - (r ?? 0)) / 100) * 2.5));
};
const coLine = (row) => row.c.map((x) => `${String(x.name).split(' ').slice(-1)[0]} ${Math.round(x.pct ?? 0)}%`).join(', ');
const shapeOf = (st) => {
  if (!held.has(st)) held.set(st, fetch(`/us/${st}.json`).then((r) => { if (!r.ok) throw new Error(st); return r.json(); }).catch((e) => { held.delete(st); throw e; }));
  return held.get(st);
};
const ease = (t) => (t < .5 ? 4 * t ** 3 : 1 - (2 - 2 * t) ** 3 / 2);
const blend = (a, b, t) => a + (b - a) * t;
const clip = (t) => Math.max(0, Math.min(1, t));
const leaning = (v) => (v == null ? 'nothing on the ballot here' : Math.abs(v) < .1 ? 'too close to call' : `leans ${v > 0 ? 'Democratic' : 'Republican'}`);

function colours(el) {
  const css = getComputedStyle(el), get = (k) => css.getPropertyValue(k).trim();
  return { l: get('--left'), r: get('--right'), m: get('--mid'), h: get('--hair'), ink: get('--ink'), bg: get('--bg'), font: get('--ui') };
}

// Which shape is under a point: each is filled in its own colour, and the blended pixels along an edge fail the check, so a dot on a border is left out and the districts part with a hairline of paper.
function shapeMap(w, h, paths) {
  const c = document.createElement('canvas');
  c.width = w;
  c.height = h;
  const x = c.getContext('2d', { willReadFrequently: true });
  paths.forEach((p, i) => {
    const v = (i + 1) * 7;
    x.fillStyle = `rgb(${v >> 8},${v & 255},255)`;
    x.fill(p);
  });
  const d = x.getImageData(0, 0, w, h).data;
  return (px, py) => {
    const o = (Math.floor(py) * w + Math.floor(px)) * 4;
    if (px < 0 || py < 0 || px >= w || py >= h || d[o + 2] !== 255 || d[o + 3] !== 255) return -1;
    const v = (d[o] << 8) | d[o + 1];
    return v % 7 ? -1 : v / 7 - 1;
  };
}

class Lens {
  constructor(host, g) {
    Object.assign(this, { host, g, where: { st: null, seat: null, county: null }, canvas: $('canvas', host), tip: $('.el-tip', host), crumbs: $('.el-crumbs', host), panel: $('.el-panel', host), mix: 0, hot: null, turn: 0, sweep: 1 });
    this.ctx = this.canvas.getContext('2d');
    this.canvas.onpointermove = (e) => this.hover(e);
    this.canvas.onpointerleave = () => { this.hot = this.hotSt = null; this.tip.hidden = true; this.paint(); };
    this.canvas.onclick = (e) => this.press(e);
    this.host.onkeydown = (e) => { if (e.key === 'Escape' && this.where.st) { e.preventDefault(); this.up(); } };
    this.crumbs.onclick = (e) => {
      const b = e.target.closest('[data-to]');
      if (b) this.go({ ...JSON.parse(b.dataset.to) });
    };
    this.panel.onclick = (e) => {
      const b = e.target.closest('[data-seat],[data-county]');
      if (!b) return;
      if (b.dataset.seat) this.go({ st: this.where.st, seat: +b.dataset.seat, county: null });
      else this.go({ st: this.where.st, seat: this.where.seat, county: +b.dataset.county });
    };
    this.panel.onpointerover = (e) => {
      const b = e.target.closest('[data-seat],[data-county]');
      const hot = b ? { seat: b.dataset.seat ? +b.dataset.seat : null, county: b.dataset.county ? +b.dataset.county : null } : null;
      if (JSON.stringify(hot) !== JSON.stringify(this.hot)) { this.hot = hot; this.paint(); }
    };
    this.panel.onpointerleave = () => { this.hot = null; this.paint(); };
    this.grown = new ResizeObserver(() => {
      if (!this.canvas.isConnected) { this.grown.disconnect(); return; }
      const w = Math.round(this.canvas.clientWidth);
      if (w && w !== this.W) this.fitAll();  // 0 is the page being hidden: everything it knows still holds for when it's back
    });
    this.grown.observe(this.canvas);
  }

  // ------------------------------------------------------------ the country
  update(map, view, opts) {
    Object.assign(this, { map, view, opts, ink: colours(this.host), stale: true });
    const races = map[view] || {}, g = this.g;
    this.cells = [];
    this.byCell = new Map();
    for (const [st, flat] of Object.entries(g.states)) {
      const seats = races[st];
      for (let i = 0; i < flat.length; i += 2) {
        const c = flat[i], r = flat[i + 1], v = seats?.length ? seats[Math.floor(((Math.imul(i / 2 + 1, 2654435761) >>> 0) / 4294967296) * seats.length)] : null;  // a state's House seats scatter across it
        const cell = { st, x: (c + .5 + (r % 2) / 2) * CELL, y: (r + .5) * ROW * CELL, v };
        this.cells.push(cell);
        this.byCell.set(`${c},${r}`, cell);
      }
    }
    this.borders = [];  // where two states' dots meet, a short stroke between them: the country's state lines, in the print's own grain
    for (const [k, a] of this.byCell) {
      const [c, r] = k.split(',').map(Number), down = r % 2 ? [c, c + 1] : [c - 1, c];
      for (const b of [this.byCell.get(`${c + 1},${r}`), ...down.map((d) => this.byCell.get(`${d},${r + 1}`))]) {
        if (!b || b.st === a.st) continue;
        const mx = (a.x + b.x) / 2, my = (a.y + b.y) / 2, dx = b.x - a.x, dy = b.y - a.y, n = Math.hypot(dx, dy) || 1, half = CELL * .32;
        this.borders.push([mx - (dy / n) * half, my + (dx / n) * half, mx + (dy / n) * half, my - (dx / n) * half]);
      }
    }
    this.size();
    if (!this.W) return;  // the observer draws it once it can be seen
    if (this.pending) { this.paint(); return; }  // a move already on its way will draw this count
    if (this.where.st) { this.go(this.where, true); return; }
    this.mix = 0;
    this.cam = this.home;
    if (reduce || swept) { this.paint(); return; }
    swept = true;
    const from = performance.now(), step = (now) => {
      const t = Math.min(1, (now - from) / 1100);
      this.sweep = t;
      this.paint();
      if (t < 1 && this.canvas.isConnected) requestAnimationFrame(step);
    };
    requestAnimationFrame(step);
  }

  size() {
    const { canvas, g } = this, w = Math.round(canvas.clientWidth), whole = w * (g.rows * ROW + 1) / g.cols, dpr = Math.min(3, devicePixelRatio || 1);
    if (!w) return;
    const h = Math.round(Math.min(whole, Math.max(300, innerHeight - 170)));  // never taller than the window, so a state or a district is seen whole
    Object.assign(this, { W: w, H: h, dpr, base: w / WIDE });
    canvas.width = w * dpr;
    canvas.height = h * dpr;
    canvas.style.height = `${h}px`;
    this.ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    this.home = { x: WIDE / 2, y: whole / this.base / 2, z: h / whole };  // the whole country, however short the window
  }

  cellAt(px, py) {
    const { cam, base } = this, wx = cam.x + (px - this.W / 2) / (base * cam.z), wy = cam.y + (py - this.H / 2) / (base * cam.z);
    const r = Math.round(wy / CELL / ROW - .5);
    return this.byCell.get(`${Math.round(wx / CELL - .5 - (r % 2) / 2)},${r}`);
  }

  fitAll() {
    this.size();
    if (this.where.st) this.go(this.where, true);
    else { this.cam = this.home; this.paint(); }
  }

  x(cam, wx) { return this.W / 2 + (wx - cam.x) * this.base * cam.z; }

  y(cam, wy) { return this.H / 2 + (wy - cam.y) * this.base * cam.z; }

  dots(cam) {
    const { ctx, cells, ink, W, H, mix, sweep, base } = this, focus = this.where.st, size = CELL * base * cam.z;
    for (const c of cells) {
      const sx = this.x(cam, c.x), sy = this.y(cam, c.y);
      if (sx < -20 || sy < -20 || sx > W + 20 || sy > H + 20) continue;
      const sure = c.v == null ? 0 : Math.abs(c.v), rise = Math.min(1, Math.max(0, sweep * 2.2 - (1 - c.x / WIDE)));  // the east reports first
      let big = (c.v == null ? .2 : .26 + .62 * sure) * rise * (this.hotSt === c.st ? 1.25 : 1);
      if (big <= 0) continue;
      const mine = focus === c.st;
      ctx.globalAlpha = (c.v == null ? .45 : this.hotSt && this.hotSt !== c.st ? .55 : 1) * (mine ? 1 - mix : 1 - mix * .88);
      if (ctx.globalAlpha <= .01) continue;
      big = Math.min(big * size * .5, Math.max(big * size * .5 * (1 - mix), W < 600 ? 2 : 4));  // the country stays small behind a state
      ctx.fillStyle = c.v == null ? ink.h : c.v > .02 ? ink.l : c.v < -.02 ? ink.r : ink.m;
      ctx.beginPath();
      ctx.arc(sx, sy, big, 0, 7);
      ctx.fill();
    }
    ctx.globalAlpha = .55 * (1 - mix) * Math.min(1, sweep * 1.5);
    if (ctx.globalAlpha > .01) {
      const k = base * cam.z, ox = W / 2 - cam.x * k, oy = H / 2 - cam.y * k;
      ctx.beginPath();
      for (const [ax, ay, bx, by] of this.borders) { ctx.moveTo(ox + ax * k, oy + ay * k); ctx.lineTo(ox + bx * k, oy + by * k); }
      ctx.strokeStyle = ink.ink;
      ctx.lineWidth = W < 600 ? .8 : 1.1;
      ctx.lineCap = 'round';
      ctx.stroke();
    }
    ctx.globalAlpha = 1;
  }

  paint() {
    const { ctx, W, H, cam, det } = this;
    if (!cam) return;
    ctx.clearRect(0, 0, W, H);
    this.dots(cam);
    if (this.was && this.wasOn > 0) this.blit(this.was, this.wasOn);
    if (det && this.on > 0) this.blit(det, this.on);
    if (det && this.on >= 1) this.lit();
  }

  blit(print, alpha) {
    const { ctx, cam, W, H, base } = this, k = cam.z / print.cam.z;
    const wx = print.cam.x - W / 2 / (base * print.cam.z), wy = print.cam.y - H / 2 / (base * print.cam.z);
    ctx.globalAlpha = alpha;
    ctx.drawImage(print.canvas, this.x(cam, wx), this.y(cam, wy), W * k, H * k);
    ctx.globalAlpha = 1;
  }

  // What the pointer is on, drawn over the print.
  lit() {
    const { ctx, det, hot, ink } = this;
    if (!hot) return;
    ctx.save();
    ctx.strokeStyle = ink.ink;
    ctx.fillStyle = ink.ink;
    ctx.lineJoin = 'round';
    ctx.lineWidth = 2;
    for (const p of [det.seatPaths[hot.seat], det.coPaths[hot.county]]) {
      if (!p) continue;
      ctx.globalAlpha = .08;
      ctx.fill(p);
      ctx.globalAlpha = 1;
      ctx.stroke(p);
    }
    ctx.restore();
  }

  // ------------------------------------------------------------ a print at one place and one scale
  print(cam, s, at) {
    const { W, H, dpr, base, ink } = this, k = base * cam.z;
    const canvas = document.createElement('canvas');
    canvas.width = W * dpr;
    canvas.height = H * dpr;
    const x = canvas.getContext('2d');
    x.setTransform(dpr, 0, 0, dpr, 0, 0);
    const sx = (v) => W / 2 + (v - cam.x) * k, sy = (v) => H / 2 + (v - cam.y) * k;
    const trace = (rings) => {
      const p = new Path2D();
      for (const r of rings) {
        p.moveTo(sx(r[0]), sy(r[1]));
        for (let i = 2; i < r.length; i += 2) p.lineTo(sx(r[i]), sy(r[i + 1]));
        p.closePath();
      }
      return p;
    };
    const seatPaths = s.seats.map((q) => trace(q.r)), coPaths = s.cos.map((q) => trace(q.r));
    const seatAt = shapeMap(W, H, seatPaths), countyAt = shapeMap(W, H, coPaths);
    const inks = s.seats.map((q) => this.rowOf(q.k)?.ink ?? null), focus = at.seat, gap = W < 600 ? 4.5 : GAP;
    const byCo = this.coRows ? s.cos.map((c) => coLean(this.coRows[coName(c.n)])) : null;  // a Senate or governor race prints by county
    const plates = new Map();
    for (let r = 0, py = gap / 2; py < H; r += 1, py += gap * ROW) {
      for (let px = gap / 2 + (r % 2) * gap / 2; px < W; px += gap) {
        const i = byCo ? countyAt(px, py) : seatAt(px, py);
        if (i < 0) continue;
        const v = byCo ? byCo[i] : inks[i], dim = byCo ? at.county != null && i !== at.county : focus != null && i !== focus, sure = v == null ? 0 : Math.abs(v);
        const key = `${v == null ? ink.h : v > .02 ? ink.l : v < -.02 ? ink.r : ink.m}|${dim ? .22 : 1}`;
        if (!plates.has(key)) plates.set(key, new Path2D());
        const p = plates.get(key), big = gap * .5 * (v == null ? .3 : .34 + .62 * sure);
        p.moveTo(px + big, py);
        p.arc(px, py, big, 0, 7);
      }
    }
    for (const [key, p] of plates) {
      const [fill, alpha] = key.split('|');
      x.fillStyle = fill;
      x.globalAlpha = +alpha;
      x.fill(p);
    }
    x.globalAlpha = 1;
    x.lineJoin = 'round';
    x.strokeStyle = ink.h;
    x.lineWidth = .7;
    if (s.cos.reduce((a, c) => a + c.box[2] - c.box[0], 0) / s.cos.length * k > 16) coPaths.forEach((p) => x.stroke(p));  // counties too small to draw would only be a smudge
    x.strokeStyle = ink.ink;
    x.lineWidth = 1;
    x.globalAlpha = .6;
    seatPaths.forEach((p) => x.stroke(p));
    x.globalAlpha = 1;
    x.lineWidth = 1.4;
    x.stroke(trace(s.line));
    if (focus != null) {
      x.lineWidth = 2.4;
      x.stroke(seatPaths[focus]);
    }
    if (at.county != null) {
      x.lineWidth = 2.4;
      x.stroke(coPaths[at.county]);
    }
    this.labels(x, s, at, cam, sx, sy, seatAt, countyAt);
    return { canvas, cam, seatAt, countyAt, seatPaths, coPaths };
  }

  labels(x, s, at, cam, sx, sy, seatAt, countyAt) {
    const { ink, W, H, base } = this, k = base * cam.z, taken = [];
    const put = (text, px, py, font, strong) => {
      x.font = font;
      const w = x.measureText(text).width + 6, h = parseInt(font, 10) + 3, box = [px - w / 2, py - h / 2, px + w / 2, py + h / 2];
      if (box[0] < 2 || box[1] < 2 || box[2] > W - 2 || box[3] > H - 2 || taken.some((t) => box[0] < t[2] && box[2] > t[0] && box[1] < t[3] && box[3] > t[1])) return false;
      taken.push(box);
      x.textAlign = 'center';
      x.textBaseline = 'middle';
      x.lineWidth = strong ? 4 : 3;
      x.strokeStyle = ink.bg;
      x.fillStyle = ink.ink;
      x.strokeText(text, px, py);
      x.fillText(text, px, py);
      return true;
    };
    const deep = at.seat != null || at.county != null;
    if (!deep) {
      s.seats.forEach((q) => {
        const wide = (q.box[2] - q.box[0]) * k, tall = (q.box[3] - q.box[1]) * k;
        if (s.seats.length > 1 && wide > 20 && tall > 16) put(String(q.n), sx(q.at[0]), sy(q.at[1]), `700 13px ${ink.font}`, true);
      });
      return;
    }
    const inView = (px, py) => (at.county != null ? countyAt(px, py) === at.county : seatAt(px, py) === at.seat);
    s.cos.forEach((c) => {
      if ((c.box[2] - c.box[0]) * k > 46) put(c.n.toUpperCase(), sx(c.at[0]), sy(c.at[1]), `700 11px ${ink.font}`, true);
    });
    for (const [wx, wy, name] of s.towns) {
      const px = sx(wx), py = sy(wy);
      if (px < 0 || py < 0 || px >= W || py >= H || !inView(px, py)) continue;
      if (put(name, px, py - 9, `500 12px ${ink.font}`, false)) {
        x.fillStyle = ink.ink;
        x.beginPath();
        x.arc(px, py, 2, 0, 7);
        x.fill();
      }
    }
  }

  // ------------------------------------------------------------ moving
  fit(box) {
    const { W, H, base } = this, side = W > 700 ? Math.min(340, W * .36) : 0, room = W - side - 32, top = 44, high = H - top - 16;
    const z = Math.min(room / Math.max(1, (box[2] - box[0]) * base), high / Math.max(1, (box[3] - box[1]) * base), DEEPEST);
    const cx = (box[0] + box[2]) / 2, cy = (box[1] + box[3]) / 2;
    return { x: cx - (16 + room / 2 - W / 2) / (base * z), y: cy - (top + high / 2 - H / 2) / (base * z), z };
  }

  async go(next, still = false, stay = false) {
    const turn = (this.turn += 1), target = { st: next.st || null, seat: next.seat ?? null, county: next.county ?? null };
    this.hot = null;
    this.tip.hidden = true;
    $('[data-el-state]', this.host).value = target.st || '';
    if (!target.st) {
      this.pending = false;
      this.where = target;
      this.crumbs.hidden = this.panel.hidden = true;
      this.opts.pick?.(null);
      const was = this.det;
      this.det = null;
      this.was = was;
      this.fly(this.home, still, (e) => { this.wasOn = 1 - clip(e / .6); this.mix = 1 - e; this.on = 0; });
      return;
    }
    this.pending = true;
    let s, rows, coRows;
    try {
      [s, rows, coRows] = await Promise.all([shapeOf(target.st), this.loadRows(), this.countyRows(target.st)]);
      this.here = rows.filter((r) => r.state === target.st);
    } catch {
      if (turn !== this.turn) return;
      this.pending = false;
      if (!this.det) this.where = { st: null, seat: null, county: null };  // nothing to stand on, so back to the country rather than an empty frame
      this.cam ||= this.home;
      $('[data-el-state]', this.host).value = this.where.st || '';
      this.paint();
      this.say('That state could not be opened just now.');
      return;
    }
    if (turn !== this.turn || !this.canvas.isConnected) return;
    this.pending = false;
    this.coRows = coRows;
    if (target.seat >= s.seats.length) target.seat = null;
    if (target.county >= s.cos.length) target.county = null;
    this.s = s;
    this.opts.pick?.(target.st);
    const box = target.county != null ? s.cos[target.county].box : target.seat != null ? s.seats[target.seat].box : s.box;
    const cam = this.fit(box), fresh = this.print(cam, s, target), from = this.mix;
    this.cam ||= this.home;
    this.was = this.det;
    this.det = fresh;
    this.where = target;
    this.card(still, stay);
    this.fly(cam, still, (e) => { this.mix = Math.max(from, e); this.on = clip((e - .3) / .7); this.wasOn = this.was ? 1 - clip(e / .55) : 0; });
  }

  fly(cam, still, tick) {
    cancelAnimationFrame(this.frame);
    this.flying = !still && !reduce;
    const from = { ...(this.cam || this.home) }, start = performance.now(), ms = still || reduce ? 0 : 1500;
    const step = (now) => {
      const t = ms ? Math.min(1, (now - start) / ms) : 1, e = ease(t);
      this.cam = { x: blend(from.x, cam.x, e), y: blend(from.y, cam.y, e), z: from.z * (cam.z / from.z) ** e };
      tick(e);
      this.paint();
      if (t < 1 && this.canvas.isConnected) this.frame = requestAnimationFrame(step);
      else { this.was = null; this.wasOn = 0; this.flying = false; }
    };
    if (ms) this.frame = requestAnimationFrame(step);
    else step(start);
  }

  up() {
    const { st, seat, county } = this.where;
    this.go(county != null ? { st, seat } : seat != null ? { st } : {});
  }

  say(text) {
    this.tip.textContent = text;
    this.tip.hidden = false;
    this.tip.style.transform = 'translate(12px, 12px)';
  }

  async loadRows() {
    if (this.stale) {
      this.stale = false;  // cleared first, so a count arriving during this read marks it old
      const read = this.reading = this.opts.races().then((rows) => {
        if (read === this.reading || !this.rows) this.rows = rows;  // an older read never replaces a newer one, but it beats nothing
      }, (e) => {
        this.stale = true;
        if (!this.rows) throw e;  // the last count stands until a new one can be read
      });
    }
    await this.reading;  // a move made during a read waits for it, so it can't draw the count before
    return this.rows;
  }

  rowOf(key) { return this.rows?.find((r) => r.key === key); }

  async countyRows(st) {
    const kind = COUNTY_RACE[this.view];
    if (!kind || !st) return null;
    const key = `${kind[0]}-${st}`, had = tallied.get(key);
    if (had && Date.now() - had.at < 60e3) return had.rows;
    const got = await fetch(`/api/detail/counties/${key}`, { credentials: 'same-origin' }).then((r) => (r.ok ? r.json() : null)).catch(() => null);
    const rows = got?.rows && Object.keys(got.rows).length ? got.rows : null;  // none yet: the state keeps its usual print
    tallied.set(key, { at: Date.now(), rows });
    return rows;
  }

  // ------------------------------------------------------------ the pointer
  hover(e) {
    if (this.flying) return;
    const box = this.canvas.getBoundingClientRect(), px = e.clientX - box.left, py = e.clientY - box.top, tip = this.tip;
    const put = (text) => {
      if (text === null) { tip.hidden = true; return; }
      tip.hidden = false;
      tip.textContent = text;
      tip.style.transform = `translate(${Math.min(box.width - 200, Math.max(0, px - 60))}px, ${py + 14}px)`;
    };
    if (!this.where.st) {
      const c = this.cellAt(px, py), st = c?.st || null;
      if (st === this.hotSt) return;
      this.hotSt = st;
      put(c ? `${this.opts.states[st] || st}: ${leaning(c.v)}` : null);
      this.paint();
      return;
    }
    if (!this.det || this.on < 1) return;
    const seat = this.det.seatAt(px, py), county = this.det.countyAt(px, py), hot = this.where.seat != null ? { seat: null, county: county < 0 ? null : county } : { seat: seat < 0 ? null : seat, county: null };
    if (JSON.stringify(hot) === JSON.stringify(this.hot)) { if (!tip.hidden) put(tip.textContent); return; }
    this.hot = hot;
    const q = this.s.seats[seat], row = q && this.rowOf(q.k), co = this.s.cos[county];
    const tally = co && this.coRows?.[coName(co.n)];
    if (tally) put(`${co.n}: ${coLine(tally)}, ${Math.round(tally.reporting ?? 0)}% counted`);
    else put(q ? `${row ? this.opts.seat(row) : `District ${q.n}`}: ${leaning(row?.ink)}${co ? `. ${co.n}` : ''}` : co ? co.n : null);
    this.paint();
  }

  press(e) {
    if (this.flying) return;  // what's under a click in flight isn't what the click would land on
    const box = this.canvas.getBoundingClientRect(), px = e.clientX - box.left, py = e.clientY - box.top;
    if (!this.where.st) {
      const c = this.cellAt(px, py);
      if (c) { this.hotSt = null; this.go({ st: c.st }); }
      return;
    }
    if (!this.det) return;
    const seat = this.det.seatAt(px, py), county = this.det.countyAt(px, py), { st } = this.where;
    if (seat < 0 && county < 0) { this.up(); return; }
    if (this.where.seat == null && this.where.county == null) { if (seat >= 0) this.go({ st, seat }); return; }
    if (this.where.seat != null && seat >= 0 && seat !== this.where.seat) { this.go({ st, seat }); return; }
    if (county >= 0 && county !== this.where.county) this.go({ st, seat: this.where.seat, county });
  }

  // ------------------------------------------------------------ what's beside the map
  card(still, stay) {
    const { s, here, opts, crumbs, panel } = this, { st, seat, county } = this.where, name = opts.states[st] || st;
    if (still && (panel.contains(document.activeElement) || crumbs.contains(document.activeElement))) return;  // a new count doesn't take the reader's place
    const step = (label, to) => `<button type="button" data-to='${esc(JSON.stringify(to))}'>${esc(label)}</button>`;
    const seatRow = (q) => { const r = this.rowOf(q.k); return r ? `${opts.seat(r)}` : `${name} ${q.n}`; };
    const trail = [step('United States', {}), step(name, { st })];
    if (seat != null) trail.push(step(seatRow(s.seats[seat]), { st, seat }));
    if (county != null) trail.push(`<span>${esc(s.cos[county].n)}</span>`);
    crumbs.innerHTML = trail.join('<i aria-hidden="true">/</i>');
    crumbs.hidden = false;
    const list = (seats) => `<ul class="el-seats">${seats.map((q) => {
      const r = this.rowOf(q.k), v = r?.ink;
      return `<li><button type="button" data-seat="${s.seats.indexOf(q)}"><b>${esc(s.seats.length > 1 ? q.n : 'At large')}</b><span>${esc(r ? opts.names(r) : '')}</span><i class="${v == null ? '' : v > .02 ? 's-l' : v < -.02 ? 's-r' : 's-c'}" style="opacity:${v == null ? .2 : .35 + .65 * Math.abs(v)}"></i></button></li>`;
    }).join('')}</ul>`;
    let body;
    if (county != null) {
      const c = s.cos[county], seats = s.seats.filter((q) => c.k.includes(q.k)), towns = s.towns.filter((t) => this.det && this.det.countyAt(this.x(this.det.cam, t[0]), this.y(this.det.cam, t[1])) === county);
      const tally = this.coRows?.[coName(c.n)], race = COUNTY_RACE[this.view];
      body = `<h3 tabindex="-1">${esc(c.n)}</h3>${tally ? `<p class="el-who">${esc(coLine(tally))}</p><p class="small">${Math.round(tally.reporting ?? 0)}% counted in the ${esc(race[1])} race.</p>` : ''}<p class="small">${seats.length > 1 ? `Split between ${seats.length} House seats.` : seats.length ? 'All in one House seat.' : 'Not matched to a House seat.'}</p>${list(seats)}
        ${towns.length ? `<h4>Towns and cities</h4><p class="el-chips">${towns.slice(0, 40).map((t) => `<a href="/topic/${encodeURIComponent(t[2])}">${esc(t[2])}</a>`).join('')}</p>` : ''}`;
    } else if (seat != null) {
      const q = s.seats[seat], r = this.rowOf(q.k), cos = s.cos.filter((c) => c.k.includes(q.k));
      body = `<h3 tabindex="-1">${esc(seatRow(q))}</h3>${r ? `<p class="el-who">${esc(opts.names(r))}</p>${opts.bar(r.pd)}<p class="small">${opts.state(r)}</p>${r.note ? `<p class="el-said">${esc(r.note)}</p>` : ''}<p><a class="btn" href="/elections/race/${esc(r.key)}">Open the race</a></p>` : ''}
        ${cos.length ? `<h4>Counties here</h4><p class="el-chips">${cos.map((c) => `<button type="button" data-county="${s.cos.indexOf(c)}">${esc(c.n)}</button>`).join('')}</p>` : ''}`;
    } else {
      const big = here.filter((r) => r.kind !== 'house'), tally = { D: 0, R: 0, T: 0 };
      s.seats.forEach((q) => { const v = this.rowOf(q.k)?.ink ?? 0; tally[Math.abs(v) < .1 ? 'T' : v > 0 ? 'D' : 'R'] += 1; });
      body = `<h3 tabindex="-1">${esc(name)}</h3>${this.coRows ? `<p class="small">Counties shaded by who leads the ${esc(COUNTY_RACE[this.view][1])} count. Tap one for its numbers.</p>` : ''}${s.seats.length ? `<p class="small">${s.seats.length === 1 ? 'One House seat' : `${s.seats.length} House seats`}: ${tally.D} leaning Democratic, ${tally.R} Republican${tally.T ? `, ${tally.T} too close` : ''}.</p>` : '<p class="small">No voting seat in the House.</p>'}
        ${big.length ? `<ul class="wire-list el-races">${big.map(opts.row).join('')}</ul>` : ''}${s.seats.length ? `<h4>House seats</h4>${list(s.seats)}` : ''}`;
    }
    panel.innerHTML = body;
    panel.hidden = false;
    if (still) return;
    panel.scrollTop = 0;
    if (!stay) $('h3', panel).focus({ preventScroll: true });
  }
}

export async function openMap(host, map, view, opts) {
  const g = await gridded();
  if (!host.isConnected) return null;
  host.lens ||= new Lens(host, g);
  host.lens.update(map, view, opts);
  return host.lens;
}

export const shut = (host) => { if (host.lens?.where.st) host.lens.go({}, true); };
export const going = (host, st) => host.lens?.go({ st }, false, true);
