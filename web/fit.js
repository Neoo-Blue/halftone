// Nothing prints over its neighbour. A layout is drawn for the words it expects, and the words change every day: a
// sentence arrives where a number was meant to go ("Democrats win the House. Democrats win the Senate" in a row built
// for "55° Clear"), a name runs long, a source sends a string with no spaces. So the page checks itself as drawn,
// every time it changes or resizes: text whose box runs past the side of a container that doesn't clip it is
// spilling over the next thing, and that container is let wrap its words inside itself. Text still past it is
// clipped at its edge. It's measured, not assumed, so it holds for tomorrow's words too. Only sideways: a tall
// line's inline box overhangs a tight headline by design, and that isn't a spill.
const SKIP = 'svg, canvas, img, video, picture, iframe, pre, code, .tape, .scene, .globe, .maplibregl-map, .explain, [data-fit="off"]';
const SLACK = 4;  // px: a glyph's overhang and subpixel rounding aren't a spill

const text = (el) => [...el.childNodes].some((n) => n.nodeType === 3 && n.nodeValue.trim());

export function guard(root) {
  const boxes = new Map(), looks = new Map();
  const box = (e) => (boxes.has(e) ? boxes.get(e) : boxes.set(e, e.getBoundingClientRect()).get(e));
  const look = (e) => (looks.has(e) ? looks.get(e) : looks.set(e, getComputedStyle(e)).get(e));
  const wide = new Set();
  for (const el of root.querySelectorAll('*')) {
    if (!text(el) || el.closest(SKIP) || !el.getClientRects().length) continue;
    const shut = el.closest('details:not([open])');
    if (shut && !el.closest('summary')) continue;  // a closed section's words are measured where they'd be, not drawn
    const own = look(el);
    if (own.display !== 'inline' && own.overflowX === 'visible' && el.scrollWidth > el.clientWidth + SLACK) {
      wide.add(el);  // its words run past its own box: one line forced into a box held to its column
      continue;
    }
    const r = box(el);
    for (let a = el.parentElement, up = 0; a && a !== root.parentElement && up < 8; a = a.parentElement, up += 1) {
      const s = look(a);
      if (s.display === 'inline' || s.display === 'contents') continue;
      if (s.overflowX !== 'visible') break;  // a container that clips or scrolls keeps its own overflow
      const b = box(a);
      if (r.right > b.right + SLACK || r.left < b.left - SLACK) {
        wide.add(a);
        break;
      }
    }
  }
  for (const a of wide) a.classList.add(a.classList.contains('fit-wrap') ? 'fit-clip' : 'fit-wrap');
  return [...wide];
}

// Watches `root` for good: whatever arrives later (an answer, a count, a reading) is checked the frame after it lands.
export function watchLayout(root, onFix) {
  if (!root) return;  // a page without this region just isn't watched
  let queued = false, rounds = 0;
  const unmark = (el) => el.classList.remove('fit-wrap', 'fit-clip');
  const watcher = new MutationObserver((records) => {
    // changed words are measured afresh: a box wrapped or clipped for yesterday's long string isn't kept that way
    for (const r of records) for (let n = r.target.nodeType === 1 ? r.target : r.target.parentElement; n && n !== root; n = n.parentElement) unmark(n);
    schedule();
  });
  const run = () => {
    queued = false;
    const fixed = guard(root);
    if (!fixed.length) {
      rounds = 0;
      return;
    }
    rounds += 1;
    console.info(`layout: ${fixed.length} spill${fixed.length === 1 ? '' : 's'} kept inside ${fixed.length === 1 ? 'its box' : 'their boxes'}`, fixed);
    window.paperLayout = { fixed: (window.paperLayout?.fixed || 0) + fixed.length };
    if (onFix) {
      onFix();
      watcher.takeRecords();  // the fix's own moves aren't new words: left in, a fix that moves things would chase itself
    }
    if (rounds < 3) schedule();  // a wrap can move other things: look again, a couple of times at most
  };
  const schedule = () => {
    if (!queued) {
      queued = true;
      requestAnimationFrame(() => requestAnimationFrame(run));  // after layout has settled
    }
  };
  watcher.observe(root, { childList: true, subtree: true, characterData: true });
  addEventListener('resize', () => {
    root.querySelectorAll('.fit-wrap, .fit-clip').forEach(unmark);  // a wider window may need none of them
    schedule();
  });
  document.fonts?.ready.then(schedule);
  schedule();
}
