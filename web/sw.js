// The last edition, for when the homelab or the connection is down. The network always comes first, so a new build is never held back, and a saved copy is marked so the page can say it's old.
// It's a private copy held in this browser: it goes when the session does, and it stops being offered after three days.
const CACHE = 'paper-v1', MAX_AGE = 3 * 864e5;
const SHELL = ['/', '/style.css', '/app.js', '/lib.js', '/detail.js', '/dock.js', '/phone.js', '/find.js', '/globe.js', '/scene.js', '/theme.js', '/icon-512.png'];

self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', (e) => e.waitUntil(self.clients.claim()));
self.addEventListener('fetch', (e) => {
  const url = new URL(e.request.url), keep = SHELL.includes(url.pathname) || url.pathname === '/api/paper';
  if (e.request.method !== 'GET' || url.origin !== location.origin || !keep) return;
  const key = url.pathname;
  e.respondWith(fetch(e.request).then((r) => {
    if (r.status >= 500) throw r;  // a tunnel answers for a dead homelab, so this counts as down
    if (r.status === 401) caches.delete(CACHE);
    if (r.ok && !r.redirected) {
      const copy = r.clone();
      caches.open(CACHE).then((c) => c.put(key, copy));
    }
    return r;
  }).catch(async () => {
    const saved = await caches.match(key);
    if (!saved) return Response.error();
    if (key !== '/api/paper') return saved;
    if (Date.now() - new Date(saved.headers.get('date')) > MAX_AGE) return Response.error();
    return new Response(saved.body, { headers: { 'content-type': 'application/json', 'x-paper-offline': '1' } });
  }));
});
