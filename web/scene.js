// One stage for every story with a place. Halftone land at any zoom, the story's own layers, and a clock you can drag.
// A spec holds any of: track (a thing moving), areas (ground covered), dots (things happening), pin (the place itself), ripple (spreading from a point).
import { $, esc } from '/lib.js';

const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
const STEP = 6, PLAY_MS = 7000, HIT = 18;
const css = (name) => getComputedStyle(document.documentElement).getPropertyValue(name).trim();
const when = (t) => new Date(t * 1000).toLocaleString('en-US', { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' });
const ICONS = {
  play: '<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M4.5 2.5v11l9-5.5z"/></svg>',
  pause: '<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M4 2.5h3v11H4zM9 2.5h3v11H9z"/></svg>',
  plus: '<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M8 3v10M3 8h10"/></svg>',
  minus: '<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M3 8h10"/></svg>',
};

let land = null;
const landReady = new Promise((done) => {
  const img = new Image();
  img.onload = () => {
    const c = document.createElement('canvas');
    c.width = img.width; c.height = img.height;
    const x = c.getContext('2d', { willReadFrequently: true });
    x.drawImage(img, 0, 0);
    land = { w: img.width, h: img.height, px: x.getImageData(0, 0, img.width, img.height).data };
    done();
  };
  img.onerror = done;
  img.src = '/land-sharp.png';  // far finer than the globe's, because a scene can be zoomed right in on a coast
});
function isLand(lat, lon) {
  if (!land || lat > 90 || lat < -90) return false;
  const x = Math.floor((((lon + 180) % 360 + 360) % 360) / 360 * land.w), y = Math.min(land.h - 1, Math.floor(((90 - lat) / 180) * land.h));
  return land.px[(y * land.w + x) * 4] > 127;
}

let atlas = null;
const atlasReady = fetch('/places.json', { credentials: 'same-origin' }).then((r) => r.json()).then((a) => { atlas = a; }).catch(() => {});

function places(spec) {
  const out = [];
  for (const p of spec.track || []) out.push([p.la, p.lo]);
  for (const d of spec.dots || []) out.push([d.la, d.lo]);
  for (const a of spec.areas || []) for (const r of a.rings) for (const [lo, la] of r) out.push([la, lo]);
  if (spec.pin) out.push(spec.pin);
  return out.filter(([la, lo]) => Number.isFinite(la) && Number.isFinite(lo));
}

export function mountScene(host, spec, { open = () => {} } = {}) {
  const times = [...(spec.track || []).map((p) => p.t), ...(spec.dots || []).map((d) => d.t)].filter(Boolean);
  const timed = spec.ripple || new Set(times).size > 1;
  const t0 = spec.ripple ? 0 : Math.min(...times), t1 = spec.ripple ? 1 : Math.max(...times);
  host.innerHTML = `<figure class="scene">
    <div class="scene-map"><canvas tabindex="0" role="img" aria-label="${esc(spec.alt || 'Map of this story')}. Drag to move, use the buttons to zoom."></canvas>
      <div class="scene-tip" hidden></div>
      <div class="scene-zoom"><button type="button" data-zoom="1.5" aria-label="Zoom in">${ICONS.plus}</button><button type="button" data-zoom="0.66" aria-label="Zoom out">${ICONS.minus}</button></div>
      ${spec.key ? `<ul class="scene-key">${spec.key.map(([cls, text]) => `<li><i class="${esc(cls)}"></i>${esc(text)}</li>`).join('')}</ul>` : ''}
    </div>
    ${timed ? `<figcaption class="scene-clock"><button type="button" class="scene-play" aria-label="Play">${ICONS.play}</button>
      <div class="scene-time"><canvas class="scene-curve" aria-hidden="true"></canvas><input type="range" min="0" max="1000" value="0" aria-label="Move through time"></div>
      <output class="scene-now"></output></figcaption>` : ''}
  </figure>`;
  const canvas = $('canvas', host), ctx = canvas.getContext('2d'), tip = $('.scene-tip', host), range = $('input', host), output = $('.scene-now', host), play = $('.scene-play', host), curve = $('.scene-curve', host);
  const base = document.createElement('canvas'), names = document.createElement('canvas');
  let w = 0, h = 0, dpr = 1, view = null, now = timed ? t0 : t1, playing = false, last = 0, frame = 0, seen = true, dirty = true, inks = {}, screens = {}, drag = null;

  function fit() {
    const all = places(spec);
    if (!all.length) return { lat: 20, lon: 0, k: Math.max(w / 360, h / 170) };
    const las = all.map((p) => p[0]), los = all.map((p) => p[1]);
    const lat = (Math.min(...las) + Math.max(...las)) / 2, lon = (Math.min(...los) + Math.max(...los)) / 2;
    const c = Math.max(0.2, Math.cos((lat * Math.PI) / 180));
    const spanLat = Math.max(spec.span || 5, (Math.max(...las) - Math.min(...las)) * 1.5), spanLon = Math.max(spec.span || 5, (Math.max(...los) - Math.min(...los)) * 1.35);
    return { lat, lon, k: Math.min(h / spanLat, w / (spanLon * c)) };
  }
  const scale = () => Math.max(0.2, Math.cos((view.lat * Math.PI) / 180));
  const at = (la, lo) => [w / 2 + (lo - view.lon) * view.k * scale(), h / 2 - (la - view.lat) * view.k];

  function dotted(color, r) {
    const p = document.createElement('canvas');
    p.width = p.height = Math.round(STEP * dpr);
    const x = p.getContext('2d');
    x.fillStyle = color;
    x.beginPath(); x.arc(p.width / 2, p.height / 2, r * dpr, 0, 7); x.fill();
    const pattern = ctx.createPattern(p, 'repeat');
    pattern.setTransform(new DOMMatrix().scale(1 / dpr));
    return pattern;
  }

  function paintBase() {
    inks = { ink: css('--globe-ink'), line: css('--ink'), bg: css('--bg'), k: css('--spot-k'), e: css('--spot-e'), h: css('--spot-h'), hair: css('--hair'), ui: css('--ui') };
    screens = { 0: dotted(inks.line, 0.8), 1: dotted(inks.h, 1.5), 2: dotted(inks.h, 2.3), 3: dotted(inks.k, 2.7) };
    base.width = w * dpr; base.height = h * dpr;
    const b = base.getContext('2d');
    b.scale(dpr, dpr);
    const c = scale(), sea = new Path2D(), ground = new Path2D();
    for (let y = STEP / 2; y < h; y += STEP) {
      for (let x = STEP / 2; x < w; x += STEP) {
        const lat = view.lat - (y - h / 2) / view.k, lon = view.lon + (x - w / 2) / (view.k * c);
        if (isLand(lat, lon)) { ground.moveTo(x + 1.7, y); ground.arc(x, y, 1.7, 0, 7); } else { sea.moveTo(x + 0.5, y); sea.arc(x, y, 0.5, 0, 7); }
      }
    }
    b.fillStyle = inks.ink;
    b.globalAlpha = 0.22; b.fill(sea);
    b.globalAlpha = 0.42; b.fill(ground);  // the map is the page the story is printed on, so it stays quiet
    b.globalAlpha = 1;
    names.width = w * dpr;
    names.height = h * dpr;
    const n = names.getContext('2d');
    n.scale(dpr, dpr);
    printNames(n);
    printInset(n);
    dirty = false;
  }

  // The names on the map, biggest first. Each takes its own room, so a crowded coast keeps only what fits at this zoom.
  function printNames(b) {
    if (!atlas) return;
    const taken = [], k = view.k, body = css('--body'), soft = css('--ink2'), max = Math.round((w * h) / 42000) + 8;
    const fits = (x, y, tw, th) => {
      const box = [x - 5, y - th / 2 - 3, x + tw + 5, y + th / 2 + 3];
      if (box[0] < 6 || box[2] > w - 6 || box[1] < 6 || box[3] > h - 6) return false;
      if (taken.some((t) => box[0] < t[2] && box[2] > t[0] && box[1] < t[3] && box[3] > t[1])) return false;
      taken.push(box);
      return true;
    };
    const words = (text, x, y, font, color) => {
      b.font = font;
      b.textBaseline = 'middle';
      b.lineJoin = 'round';
      b.lineWidth = 3.5;
      b.strokeStyle = inks.bg;
      b.strokeText(text, x, y);
      b.fillStyle = color;
      b.fillText(text, x, y);
    };
    const caps = `600 11px ${inks.ui}`, town = `500 12px ${inks.ui}`, water = `italic 400 13px ${body}`;
    let count = 0;
    b.font = caps;
    for (const [name, la, lo, rank] of atlas.countries) {
      if (k < 6 && rank > Math.max(2, k * 1.1 + 1)) continue;
      const text = name.toUpperCase(), [x, y] = at(la, lo), tw = b.measureText(text).width;
      if (x < 0 || y < 0 || x > w || y > h || count >= max || !fits(x - tw / 2, y, tw, 12)) continue;
      words(text, x - tw / 2, y, caps, soft);
      count += 1;
    }
    if (k >= 5) {
      const cap = Math.max(4, Math.min(max, Math.round(k * 1.2)));
      let cities = 0;
      b.font = town;
      for (const [name, la, lo] of atlas.cities) {
        const [x, y] = at(la, lo);
        if (x < 0 || y < 0 || x > w || y > h) continue;
        const tw = b.measureText(name).width;
        if (cities >= cap || !fits(x, y, tw + 9, 14)) continue;
        b.fillStyle = inks.line;
        b.beginPath();
        b.arc(x, y, 2.4, 0, 7);
        b.fill();
        words(name, x + 6, y, town, inks.line);
        cities += 1;
      }
    }
    b.font = water;
    for (const [name, la, lo] of atlas.seas) {
      const [x, y] = at(la, lo), tw = b.measureText(name).width;
      if (x < 0 || y < 0 || x > w || y > h || isLand(la, lo) || !fits(x - tw / 2, y, tw, 14)) continue;
      words(name, x - tw / 2, y, water, soft);
    }
  }

  // A small world in the corner, marking the part of it this map shows.
  function printInset(b) {
    if (w < 560 || !land) return;
    const iw = 132, ih = 66, ix = w - iw - 12, iy = h - ih - 12, c = scale();
    b.globalAlpha = 0.92; b.fillStyle = inks.bg; b.fillRect(ix - 4, iy - 4, iw + 8, ih + 8);
    b.globalAlpha = 1; b.fillStyle = inks.ink;
    for (let y = 1; y < ih; y += 2.2) for (let x = 1; x < iw; x += 2.2) if (isLand(90 - (y / ih) * 180, (x / iw) * 360 - 180)) b.fillRect(ix + x, iy + y, 1.2, 1.2);
    const halfLat = (h / 2) / view.k, halfLon = (w / 2) / (view.k * c), bx = ix + ((view.lon - halfLon + 180) / 360) * iw, by = iy + ((90 - view.lat - halfLat) / 180) * ih;
    const bw = Math.max(5, (halfLon * 2 / 360) * iw), bh = Math.max(5, (halfLat * 2 / 180) * ih);
    b.strokeStyle = inks.k; b.lineWidth = 1.6; b.strokeRect(bx, by, bw, bh);
  }

  function paintCurve() {
    if (!curve) return;
    const r = curve.getBoundingClientRect(), cw = Math.round(r.width), ch = Math.round(r.height);
    if (!cw) return;
    curve.width = cw * dpr; curve.height = ch * dpr;
    const c = curve.getContext('2d');
    c.scale(dpr, dpr);
    const bins = new Array(Math.max(10, Math.round(cw / 6))).fill(0);
    const put = (t, v) => { const i = Math.min(bins.length - 1, Math.floor(((t - t0) / ((t1 - t0) || 1)) * bins.length)); bins[i] = spec.track?.length ? Math.max(bins[i], v) : bins[i] + v; };
    if (spec.track?.length) spec.track.forEach((p) => put(p.t, p.v || 1)); else (spec.dots || []).forEach((d) => put(d.t, 1));
    const top = Math.max(...bins, 1), share = (now - t0) / ((t1 - t0) || 1);
    bins.forEach((v, i) => {
      if (!v) return;
      const dots = Math.max(1, Math.round((v / top) * Math.floor(ch / 5)));
      c.fillStyle = i / bins.length <= share ? css('--accent') : css('--ink3');
      for (let d = 0; d < dots; d += 1) { c.beginPath(); c.arc(i * 6 + 3, ch - 3 - d * 5, 1.6, 0, 7); c.fill(); }
    });
  }

  function label(x, y, text) {
    ctx.font = `600 11.5px ${inks.ui}`;
    const tw = ctx.measureText(text).width, lx = Math.min(w - tw - 12, Math.max(4, x + 9)), ly = Math.max(16, y - 8);
    ctx.globalAlpha = 0.9; ctx.fillStyle = inks.bg; ctx.fillRect(lx - 4, ly - 12, tw + 8, 17);
    ctx.globalAlpha = 1; ctx.fillStyle = inks.line; ctx.fillText(text, lx, ly);
  }

  function paintAreas(time) {
    const areas = spec.areas || [];
    if (!areas.length) return;
    ctx.save();
    if (spec.ripple) {
      const [x, y] = at(spec.pin[0], spec.pin[1]), far = Math.hypot(w, h);
      ctx.beginPath(); ctx.arc(x, y, far * (1 - (1 - time) ** 3) * 0.75, 0, 7); ctx.clip();
    }
    for (const a of areas) {
      ctx.fillStyle = screens[a.level] || screens[1];
      ctx.beginPath();
      for (const ring of a.rings) ring.forEach(([lo, la], i) => { const [x, y] = at(la, lo); if (i) ctx.lineTo(x, y); else ctx.moveTo(x, y); });
      ctx.fill();
    }
    ctx.restore();
  }

  function paintTrack(beat) {
    const t = spec.track || [];
    if (!t.length) return null;
    let head = null;
    ctx.lineWidth = 2.2; ctx.lineCap = 'round'; ctx.strokeStyle = inks.line;
    for (let i = 0; i < t.length - 1; i += 1) {
      const a = t[i], b = t[i + 1];
      if (a.t > now) break;
      const share = b.t > now ? (now - a.t) / ((b.t - a.t) || 1) : 1, [x1, y1] = at(a.la, a.lo), [x2, y2] = at(b.la, b.lo), x = x1 + (x2 - x1) * share, y = y1 + (y2 - y1) * share;
      ctx.setLineDash(b.fc ? [2, 6] : []);
      ctx.beginPath(); ctx.moveTo(x1, y1); ctx.lineTo(x, y); ctx.stroke();
      if (share < 1) head = { x, y, p: share < 0.5 ? a : b };
    }
    ctx.setLineDash([]);
    const top = Math.max(...t.map((p) => p.v || 0), 1);
    t.forEach((p) => {
      if (p.t > now) return;
      const [x, y] = at(p.la, p.lo), power = (p.v || 0) / top;
      ctx.fillStyle = p.fc ? inks.bg : power > 0.66 ? inks.k : inks.h;
      ctx.strokeStyle = inks.line; ctx.lineWidth = 1.2;
      ctx.beginPath(); ctx.arc(x, y, 3 + power * 4, 0, 7); ctx.fill(); ctx.stroke();
    });
    if (!head) { const p = [...t].reverse().find((q) => q.t <= now) || t[0], [x, y] = at(p.la, p.lo); head = { x, y, p }; }
    if (head.p.r) {
      const radius = (head.p.r / 111) * view.k;
      ctx.globalAlpha = 0.14; ctx.fillStyle = inks.k; ctx.beginPath(); ctx.arc(head.x, head.y, radius, 0, 7); ctx.fill();
      ctx.globalAlpha = 1; ctx.strokeStyle = inks.k; ctx.lineWidth = 1; ctx.beginPath(); ctx.arc(head.x, head.y, radius, 0, 7); ctx.stroke();
    }
    ctx.strokeStyle = inks.line; ctx.lineWidth = 1.5; ctx.globalAlpha = 1 - beat;
    ctx.beginPath(); ctx.arc(head.x, head.y, 8 + beat * 14, 0, 7); ctx.stroke();
    ctx.globalAlpha = 1;
    const [sx, sy] = at(t[0].la, t[0].lo);
    label(sx, sy, spec.startLabel || 'Started here');
    const fc = t.find((p) => p.fc);
    if (fc && fc.t <= now) { const [x, y] = at(fc.la, fc.lo); label(x, y, 'Forecast from here'); }
    return head;
  }

  function paintDots() {
    const span = (t1 - t0) || 1;
    for (const d of spec.dots || []) {
      if (timed && d.t > now) continue;
      const [x, y] = at(d.la, d.lo);
      if (x < -20 || y < -20 || x > w + 20 || y > h + 20) continue;
      const age = timed ? (now - d.t) / span : 1, fresh = timed && playing && age < 0.04;
      ctx.globalAlpha = Math.max(0.45, 1 - age * 0.6);
      ctx.fillStyle = inks[d.k] || inks.k;
      ctx.beginPath(); ctx.arc(x, y, 2.5 + (d.s || 0.4) * 4.5, 0, 7); ctx.fill();
      if (fresh) { ctx.globalAlpha = 1 - age * 25; ctx.strokeStyle = ctx.fillStyle; ctx.lineWidth = 1.5; ctx.beginPath(); ctx.arc(x, y, 6 + age * 400, 0, 7); ctx.stroke(); }
    }
    ctx.globalAlpha = 1;
  }

  function draw(stamp = performance.now()) {
    if (!w) return;
    if (dirty) paintBase();
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, w, h);
    ctx.drawImage(base, 0, 0, w, h);
    const time = spec.ripple ? (now - t0) / ((t1 - t0) || 1) : 1, beat = reduce ? 0 : (stamp % 2200) / 2200;
    paintAreas(time);
    paintDots();
    ctx.drawImage(names, 0, 0, w, h);  // above the dots: where it happened is the thing a reader looks for
    paintTrack(beat);
    if (spec.pin) {
      const [x, y] = at(spec.pin[0], spec.pin[1]);
      ctx.fillStyle = inks.k; ctx.beginPath(); ctx.arc(x, y, 5, 0, 7); ctx.fill();
      ctx.strokeStyle = inks.k; ctx.lineWidth = 1.5;
      for (const shift of [0, 0.5]) { const q = (beat + shift) % 1; ctx.globalAlpha = 1 - q; ctx.beginPath(); ctx.arc(x, y, 6 + q * 34, 0, 7); ctx.stroke(); }
      ctx.globalAlpha = 1;
    }
  }

  function readout() {
    if (!output) return;
    if (spec.ripple) { output.textContent = spec.rippleText || ''; return; }
    if (spec.track?.length) {
      const p = [...spec.track].reverse().find((q) => q.t <= now) || spec.track[0];
      output.textContent = [when(now), p.v ? `${Math.round(p.v)} ${spec.unit || 'km/h'}` : '', p.label, p.fc ? 'forecast' : ''].filter(Boolean).join(', ');
    } else {
      const n = spec.dots.filter((d) => d.t <= now).length;
      output.textContent = `${when(now)}, ${n} of ${spec.dots.length} reports`;
    }
  }

  function setTime(t, fromInput) {
    now = Math.min(t1, Math.max(t0, t));
    if (range && !fromInput) range.value = Math.round(((now - t0) / ((t1 - t0) || 1)) * 1000);
    readout();
    paintCurve();
  }

  function loop(stamp) {
    frame = requestAnimationFrame(loop);
    if (!seen) return;
    if (playing) {
      const dt = stamp - (last || stamp);
      setTime(now + ((t1 - t0) * dt) / PLAY_MS);
      if (now >= t1) setPlaying(false);
    }
    last = stamp;
    if (playing || spec.pin || spec.track?.length) draw(stamp);
  }

  function setPlaying(on) {
    playing = on;
    last = 0;
    if (on && now >= t1) setTime(t0);
    if (play) { play.innerHTML = on ? ICONS.pause : ICONS.play; play.setAttribute('aria-label', on ? 'Pause' : 'Play'); }
  }

  function resize() {
    const r = canvas.parentNode.getBoundingClientRect();
    w = Math.round(r.width); h = Math.round(r.height); dpr = Math.min(2, devicePixelRatio || 1);
    if (!w || !h) return;
    canvas.width = w * dpr; canvas.height = h * dpr;
    const zoomed = view?.moved ? view : null;
    view = zoomed || fit();
    dirty = true;
    paintCurve();
    draw();
  }

  function pick(ev) {
    const r = canvas.getBoundingClientRect(), mx = ev.clientX - r.left, my = ev.clientY - r.top;
    let best = null, gap = HIT;
    const look = (p, text) => {
      const [x, y] = at(p.la, p.lo), d = Math.hypot(x - mx, y - my);
      if (d < gap) { gap = d; best = { x, y, text, href: p.href }; }
    };
    for (const p of spec.track || []) if (p.t <= now) look(p, [when(p.t), p.v ? `${Math.round(p.v)} ${spec.unit || 'km/h'}` : '', p.label, p.fc ? 'forecast' : ''].filter(Boolean).join(', '));
    for (const d of spec.dots || []) if (!timed || d.t <= now) look(d, d.label);
    return best;
  }

  const showTip = (hit) => {
    tip.hidden = !hit;
    canvas.style.cursor = hit?.href ? 'pointer' : drag ? 'grabbing' : 'grab';
    if (!hit) return;
    tip.textContent = hit.text;
    tip.style.transform = `translate(${Math.max(6, Math.min(hit.x + 12, w - tip.offsetWidth - 6))}px, ${Math.max(6, hit.y - tip.offsetHeight - 10)}px)`;
  };
  const zoom = (by) => { view = { ...view, k: Math.min(view.k * by, 320), moved: true }; view.k = Math.max(w / 720, view.k); dirty = true; draw(); };
  const pan = (dx, dy) => { view = { ...view, lat: Math.max(-85, Math.min(85, view.lat + dy / view.k)), lon: view.lon - dx / (view.k * scale()), moved: true }; dirty = true; draw(); };

  canvas.addEventListener('pointerdown', (e) => { drag = { x: e.clientX, y: e.clientY, moved: 0 }; canvas.setPointerCapture(e.pointerId); showTip(pick(e)); });
  canvas.addEventListener('pointermove', (e) => {
    if (drag) { pan(e.clientX - drag.x, e.clientY - drag.y); drag.moved += Math.abs(e.clientX - drag.x) + Math.abs(e.clientY - drag.y); drag.x = e.clientX; drag.y = e.clientY; }
    if (!drag || drag.moved < 6) showTip(pick(e));
  });
  canvas.addEventListener('pointerup', (e) => { const tap = drag && drag.moved < 6, hit = tap && pick(e); drag = null; if (hit?.href) open(hit.href); });
  canvas.addEventListener('pointerleave', () => { if (!drag) tip.hidden = true; });
  canvas.addEventListener('dblclick', () => zoom(1.5));
  canvas.addEventListener('keydown', (e) => {
    const move = { ArrowLeft: [40, 0], ArrowRight: [-40, 0], ArrowUp: [0, 40], ArrowDown: [0, -40] }[e.key];
    if (move) { e.preventDefault(); pan(...move); } else if (e.key === '+' || e.key === '=') zoom(1.5); else if (e.key === '-') zoom(0.66);
  });
  host.addEventListener('click', (e) => {
    const z = e.target.closest('[data-zoom]');
    if (z) zoom(Number(z.dataset.zoom));
    if (e.target.closest('.scene-play')) setPlaying(!playing);
  });
  range?.addEventListener('input', () => { setPlaying(false); setTime(t0 + (Number(range.value) / 1000) * (t1 - t0), true); draw(); });

  const sized = new ResizeObserver(resize);
  sized.observe(canvas.parentNode);
  const watched = new IntersectionObserver((en) => { seen = en[0].isIntersecting; });
  watched.observe(canvas);
  const themed = new MutationObserver(() => { dirty = true; paintCurve(); draw(); });
  themed.observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });

  resize();
  Promise.all([landReady, atlasReady]).then(() => {
    dirty = true;
    if (timed && !reduce) { setTime(t0); setPlaying(true); } else setTime(t1);
    if (!timed) draw();
    if (!reduce || playing) frame = requestAnimationFrame(loop);
    if (reduce) draw();
  });
  return { destroy() { cancelAnimationFrame(frame); sized.disconnect(); watched.disconnect(); themed.disconnect(); } };
}
