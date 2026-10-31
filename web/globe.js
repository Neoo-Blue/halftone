// The front page's globe, printed the way a newspaper prints a photograph: each data layer is its own
// halftone plate at its own screen angle. Land is the ink plate, conflict, economy and hazards are spot plates,
// and dot size carries the tone. A fragment shader, so it stays smooth at retina size on a phone.
const VERT = `#version 300 es
void main(){vec2 p=vec2((gl_VertexID<<1)&2,gl_VertexID&2);gl_Position=vec4(p*2.-1.,0.,1.);}`;

const FRAG = `#version 300 es
precision highp float;
out vec4 o;
uniform vec2 uCtr,uRot;
uniform float uR,uCell,uIn,uT;
uniform vec3 cInk,cK,cE,cH,uOn;
uniform sampler2D tLand,tHeat;
const float PI=3.14159265359;

vec2 toUv(vec2 p,out float nz){
  vec2 q=p/uR;float r2=dot(q,q);
  if(r2>=1.){nz=-1.;return vec2(0.);}
  vec3 n=vec3(q,sqrt(1.-r2));nz=n.z;
  float c=cos(uRot.y),s=sin(uRot.y);
  vec3 v=vec3(n.x,c*n.y+s*n.z,-s*n.y+c*n.z);
  return vec2(fract((atan(v.x,v.z)+uRot.x)/(2.*PI)+.5),.5-asin(clamp(v.y,-1.,1.))/PI);
}
// One plate: the dot under this pixel on a grid turned by a. Returns the distance to the dot's centre;
// the tone is always read at the centre, or the dots would melt into blobs.
float plate(vec2 p,float a,out vec2 uv,out float nz){
  float c=cos(a),s=sin(a);
  mat2 R=mat2(c,-s,s,c);
  vec2 g=R*p/uCell;
  vec2 ctr=transpose(R)*((floor(g)+.5)*uCell);
  uv=toUv(ctr,nz);
  return length(p-ctr);
}
float disc(float d,float tone,float gain){
  float r=uCell*.5*sqrt(clamp(tone,0.,1.))*gain;
  return 1.-smoothstep(r-.8,r+.8,d);
}
void main(){
  vec2 p=gl_FragCoord.xy-uCtr,uv;float nz,d;
  vec4 c=vec4(0.);
  d=plate(p,.785,uv,nz);
  if(nz>0.){
    float land=texture(tLand,uv).r;
    float tone=mix(.018,.12+.5*pow(nz,.7),smoothstep(.25,.6,land));
    float a=disc(d,tone*uIn,1.3);
    c=vec4(cInk*a,a);
  }
  d=plate(p,1.31,uv,nz);
  if(nz>0.){
    float h=texture(tHeat,uv).r*uOn.x;
    float a=disc(d,h*(.8+.2*sin(uT*2.2+uv.x*60.))*uIn,1.42);
    c=c*(1.-a)+vec4(cK*a,a);
  }
  d=plate(p,.262,uv,nz);
  if(nz>0.){
    float h=texture(tHeat,uv).g*uOn.y;
    float a=disc(d,h*uIn,1.3);
    c=c*(1.-a)+vec4(cE*a,a);
  }
  d=plate(p,2.36,uv,nz);
  if(nz>0.){
    float h=texture(tHeat,uv).b*uOn.z;
    float a=disc(d,h*(.82+.18*sin(uT*3.1))*uIn,1.42);
    c=c*(1.-a)+vec4(cH*a,a);
  }
  float rim=(1.-smoothstep(.0,1.4,abs(length(p)-uR)))*.32*uIn;
  o=c*(1.-rim)+vec4(cInk*rim,rim);
}`;

const rgb = (hex) => [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16) / 255);
const wrap = (a) => ((a + Math.PI * 3) % (Math.PI * 2)) - Math.PI;
const rad = Math.PI / 180;

export function makeGlobe(canvas, { onPick, onOpen, still = null }) {
  const gl = canvas.getContext('webgl2', { alpha: true, premultipliedAlpha: true, antialias: false });
  if (!gl) return null;
  const shader = (type, src) => {
    const s = gl.createShader(type);
    gl.shaderSource(s, src);
    gl.compileShader(s);
    if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(s));
    return s;
  };
  const prog = gl.createProgram();
  gl.attachShader(prog, shader(gl.VERTEX_SHADER, VERT));
  gl.attachShader(prog, shader(gl.FRAGMENT_SHADER, FRAG));
  gl.linkProgram(prog);
  gl.useProgram(prog);
  const u = Object.fromEntries(['uCtr', 'uRot', 'uR', 'uCell', 'uIn', 'uT', 'cInk', 'cK', 'cE', 'cH', 'uOn', 'tLand', 'tHeat'].map((n) => [n, gl.getUniformLocation(prog, n)]));
  gl.uniform1i(u.tLand, 0);
  gl.uniform1i(u.tHeat, 1);
  gl.bindVertexArray(gl.createVertexArray());

  const texture = (unit) => {
    const t = gl.createTexture();
    gl.activeTexture(gl.TEXTURE0 + unit);
    gl.bindTexture(gl.TEXTURE_2D, t);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.REPEAT);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
    gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, 1, 1, 0, gl.RGBA, gl.UNSIGNED_BYTE, new Uint8Array([0, 0, 0, 255]));
    return t;
  };
  const land = texture(0), heat = texture(1);
  const img = new Image();
  img.onload = () => {
    gl.activeTexture(gl.TEXTURE0);
    gl.bindTexture(gl.TEXTURE_2D, land);
    gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, img);
    ink(0);
  };
  img.src = '/land.png';

  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const view = { lon: -30 * rad, lat: 22 * rad, goal: null, idle: 0, drag: null, vx: 0, on: [1, 1, 1], in: 0, inFrom: 0, inAt: 0, w: 0, h: 0, dpr: 1, seen: true };
  let dots = [], labels = [], hover = null, stopped = false;
  if (still) {  // a detail page's locator: it starts over the place and stays there until dragged
    view.lat = Math.max(-1.1, Math.min(1.1, still[0] * rad * 0.8));
    view.lon = wrap(still[1] * rad);
    view.vx = 0;
  }

  function size() {
    const box = canvas.getBoundingClientRect();
    view.dpr = Math.min(devicePixelRatio || 1, 2);
    view.w = box.width;
    view.h = box.height;
    canvas.width = Math.round(box.width * view.dpr);
    canvas.height = Math.round(box.height * view.dpr);
    gl.viewport(0, 0, canvas.width, canvas.height);
  }
  new ResizeObserver(size).observe(canvas);
  size();

  function colors() {
    const css = getComputedStyle(document.documentElement);
    const take = (n) => rgb(css.getPropertyValue(n).trim());
    gl.uniform3fv(u.cInk, take('--globe-ink'));
    gl.uniform3fv(u.cK, take('--spot-k'));
    gl.uniform3fv(u.cE, take('--spot-e'));
    gl.uniform3fv(u.cH, take('--spot-h'));
  }
  function ink(from) {
    view.inFrom = from;
    view.inAt = performance.now();
  }

  function paintHeat() {
    const c = document.createElement('canvas');
    c.width = 1024;
    c.height = 512;
    const x = c.getContext('2d');
    x.fillStyle = '#000';
    x.fillRect(0, 0, 1024, 512);
    x.globalCompositeOperation = 'lighter';
    const tint = { k: '255,0,0', e: '0,255,0', h: '0,0,255' };
    for (const d of dots) {
      const px = (d.lo + 180) / 360 * 1024, py = (90 - d.la) / 180 * 512, r = 5 + d.s * 13;
      const g = x.createRadialGradient(px, py, 0, px, py, r);
      g.addColorStop(0, `rgba(${tint[d.k]},${0.5 + d.s * 0.5})`);
      g.addColorStop(1, `rgba(${tint[d.k]},0)`);
      x.fillStyle = g;
      x.fillRect(px - r, py - r, r * 2, r * 2);
    }
    gl.activeTexture(gl.TEXTURE1);
    gl.bindTexture(gl.TEXTURE_2D, heat);
    gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, c);
  }

  // screen position of a place, or null when it is round the back
  function project(lat, lon, R) {
    const la = lat * rad, dl = lon * rad - view.lon, c = Math.cos(view.lat), s = Math.sin(view.lat);
    const vx = Math.cos(la) * Math.sin(dl), vy = Math.sin(la), vz = Math.cos(la) * Math.cos(dl);
    const ny = c * vy - s * vz, nz = s * vy + c * vz;
    return nz > 0.08 ? { x: view.w / 2 + vx * R, y: view.h / 2 - ny * R, z: nz } : null;
  }
  const radius = () => Math.min(view.w, view.h) / 2 - 6;

  let last = performance.now();
  function frame(now) {
    if (stopped) return;
    requestAnimationFrame(frame);
    if (!view.seen || document.hidden) {
      last = now;
      return;
    }
    const dt = Math.min(now - last, 60) / 1000;
    last = now;
    if (view.goal) {
      const k = 1 - Math.exp(-dt * 3.6);
      view.lon = wrap(view.lon + wrap(view.goal.lon - view.lon) * k);
      view.lat += (view.goal.lat - view.lat) * k;
      if (Math.abs(wrap(view.goal.lon - view.lon)) < 0.002) view.goal = null;
    } else if (!view.drag) {
      view.lon = wrap(view.lon + view.vx * dt);
      view.vx *= Math.exp(-dt * 2.4);
      if (!reduce && !still && now > view.idle) view.lon = wrap(view.lon + 5.5 * rad * dt);
    }
    view.in = view.inAt ? Math.min(1, view.inFrom + (1 - view.inFrom) * (1 - Math.exp(-(now - view.inAt) / 420))) : 0;
    const R = radius() * view.dpr;
    gl.uniform2f(u.uCtr, canvas.width / 2, canvas.height / 2);
    gl.uniform2f(u.uRot, view.lon, view.lat);
    gl.uniform1f(u.uR, R);
    gl.uniform1f(u.uCell, Math.max(3.2, R / 62));
    gl.uniform1f(u.uIn, view.in);
    gl.uniform1f(u.uT, reduce ? 0 : now / 1000);
    gl.uniform3fv(u.uOn, view.on);
    gl.drawArrays(gl.TRIANGLES, 0, 3);
    const placed = [];
    for (const l of labels) {
      const p = project(l.lat, l.lon, radius());
      // ponytail: first label wins a crowded spot, the higher-ranked theater is the one worth naming
      const clear = p && !placed.some((q) => Math.abs(q.y - p.y) < 22 && Math.abs(q.x - p.x) < 150);
      l.el.style.opacity = clear ? Math.min(1, (p.z - 0.08) * 6) : 0;
      if (!clear) continue;
      placed.push(p);
      l.el.style.transform = `translate(${p.x}px,${p.y}px) translateX(${p.x > view.w * 0.58 ? 'calc(-100% - 16px)' : '0'})`;
    }
  }

  function near(e) {
    const box = canvas.getBoundingClientRect(), x = e.clientX - box.left, y = e.clientY - box.top, R = radius();
    let best = null, dist = 16;
    for (const d of dots) {
      if (!view.on['keh'.indexOf(d.k)]) continue;
      const p = project(d.la, d.lo, R);
      const far = p && Math.hypot(p.x - x, p.y - y);
      if (p && far < dist) {
        dist = far;
        best = { dot: d, x: p.x, y: p.y };
      }
    }
    return best;
  }
  canvas.addEventListener('pointerdown', (e) => {
    canvas.setPointerCapture(e.pointerId);
    view.drag = { x: e.clientX, y: e.clientY, t: performance.now() };
    view.press = { x: e.clientX, y: e.clientY };
    view.goal = null;
    view.vx = 0;
    canvas.classList.add('held');
  });
  canvas.addEventListener('pointermove', (e) => {
    if (view.drag) {
      const k = Math.PI / (radius() * 2), dx = e.clientX - view.drag.x, dy = e.clientY - view.drag.y, t = performance.now();
      view.lon = wrap(view.lon - dx * k);
      view.lat = Math.max(-1.25, Math.min(1.25, view.lat + dy * k));
      view.vx = -dx * k / Math.max(0.008, (t - view.drag.t) / 1000);
      view.drag = { x: e.clientX, y: e.clientY, t };
      view.idle = performance.now() + 5000;
      return;
    }
    if (e.pointerType === 'mouse') {
      hover = near(e);
      view.idle = performance.now() + (hover ? 2500 : 1200);
      onPick(hover);
    }
  });
  const release = (e) => {
    const tap = view.drag && view.press && Math.hypot(e.clientX - view.press.x, e.clientY - view.press.y) < 6;
    if (tap && e.type === 'pointerup') {
      const hit = near(e);
      if (hit?.dot.i) onOpen(hit.dot);
    }
    view.drag = null;
    canvas.classList.remove('held');
  };
  canvas.addEventListener('pointerup', release);
  canvas.addEventListener('pointercancel', release);
  canvas.addEventListener('pointerleave', () => {
    if (hover) onPick((hover = null));
  });
  canvas.addEventListener('keydown', (e) => {
    const step = { ArrowLeft: [-12, 0], ArrowRight: [12, 0], ArrowUp: [0, 10], ArrowDown: [0, -10] }[e.key];
    if (!step) return;
    e.preventDefault();
    api.fly(((view.goal ? view.goal.lat : view.lat) / rad) + step[1], ((view.goal ? view.goal.lon : view.lon) / rad) + step[0]);
  });
  new IntersectionObserver(([en]) => { view.seen = en.isIntersecting; }).observe(canvas);

  const api = {
    setDots(next) {
      dots = next;
      paintHeat();
    },
    setLabels(list, host) {
      host.replaceChildren();
      labels = list.map((l) => {
        const el = document.createElement('span');
        el.className = 'glabel';
        el.textContent = l.name;
        host.append(el);
        return { ...l, el };
      });
    },
    fly(lat, lon) {
      view.goal = { lat: Math.max(-1.1, Math.min(1.1, lat * rad * 0.8)), lon: wrap(lon * rad) };
      view.idle = performance.now() + 9000;
    },
    filter(i, on) {
      view.on[i] = on ? 1 : 0;
    },
    recolor() {
      colors();
      ink(0);
    },
    destroy() {
      stopped = true;
      gl.getExtension('WEBGL_lose_context')?.loseContext();  // browsers allow only so many live contexts
    },
  };
  colors();
  requestAnimationFrame(frame);
  return api;
}
