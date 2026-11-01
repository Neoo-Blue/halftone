// The paper on a phone: one desk at a time, swiped between, with what you reach for under your thumb.
import { $, $$ } from '/lib.js';
import { openDock } from '/dock.js';

const small = matchMedia('(max-width: 860px)');
const held = {};
let tab = 'today', opened = () => {}, mirror = null;

export const onPhone = () => small.matches;
const tabs = () => ['today', ...$$('.desks a[href^="/#"]').filter((a) => !a.parentNode.hidden).map((a) => a.getAttribute('href').slice(2))];

function show(id, { y, step = 0 } = {}) {
  if (id !== tab) held[tab] = scrollY;
  const top = id === tab ? y : held[id];
  tab = id;
  document.body.dataset.tab = id;
  document.body.dataset.slide = step > 0 ? 'next' : step < 0 ? 'back' : '';
  $$('.desk').forEach((d) => d.classList.toggle('shown', d.id === id));
  const link = $(id === 'today' ? '.desks [data-today]' : `.desks a[href="/#${id}"]`), nav = $('.desks');
  $$('.desks a').forEach((a) => (a === link ? a.setAttribute('aria-current', 'true') : a.removeAttribute('aria-current')));
  if (link) nav.scrollTo({ left: link.offsetLeft - nav.clientWidth / 2 + link.offsetWidth / 2, behavior: 'smooth' });
  scrollTo({ top: top || 0, behavior: 'instant' });
  opened(id);
}

// Which tab an address belongs to. On a big screen every desk is on the page already, so this leaves it alone.
export function phoneTab(hash, y) {
  if (!small.matches) return false;
  const el = hash ? document.getElementById(hash) : null;
  show(el?.closest('.desk')?.id || 'today', { y });
  if (el && !el.matches('.desk')) el.scrollIntoView();
  return true;
}

// A desk that was just switched off can't stay open.
export function phoneCheck() {
  if (small.matches && !tabs().includes(tab)) show('today');
}

// On a story the bar becomes the reading tools, each one a stand-in for the real button on the page.
export function phonePage(kind) {
  if (kind) document.body.dataset.page = kind;
  else delete document.body.dataset.page;
  mirror?.disconnect();
  const tools = kind === 'read' ? $('#page .story-tools') : null;
  $('.tab-read').hidden = kind !== 'read';
  $('.tab-main').hidden = kind === 'read';
  if (!tools) return;
  const sync = () => {
    for (const [sel, act] of [['[data-listen]', 'listen'], ['[data-save]', 'save']]) {
      const from = $(sel, tools), to = $(`[data-phone=${act}]`);
      to.hidden = !from;
      if (!from) continue;
      $('span', to).textContent = from.textContent.replace('device voice', '').trim();
      to.setAttribute('aria-pressed', from.getAttribute('aria-pressed'));
    }
  };
  mirror = new MutationObserver(sync);
  mirror.observe(tools, { subtree: true, childList: true, attributes: true, characterData: true });
  sync();
}

async function share() {
  const out = $('#page [data-url]')?.dataset.url, title = $('#page .page-head')?.textContent;
  if (!out) return;
  try {
    if (navigator.share) await navigator.share({ title, url: out });
    else {
      await navigator.clipboard.writeText(out);
      const label = $('[data-phone=share] span');
      label.textContent = 'Copied';
      setTimeout(() => { label.textContent = 'Share'; }, 1600);
    }
  } catch { /* they closed the share sheet */ }
}

const sideways = (el) => {
  for (let e = el; e && e !== document.body; e = e.parentElement) {
    if (e.scrollWidth > e.clientWidth + 2 && /auto|scroll/.test(getComputedStyle(e).overflowX)) return true;
  }
  return false;
};

function swipes() {
  const area = $('#paper');
  let x = 0, y = 0, at = 0, from = null;
  area.addEventListener('touchstart', (e) => {
    [x, y, at, from] = [e.touches[0].clientX, e.touches[0].clientY, e.timeStamp, e.target];
  }, { passive: true });
  area.addEventListener('touchend', (e) => {
    if (!small.matches) return;
    const dx = e.changedTouches[0].clientX - x, dy = e.changedTouches[0].clientY - y;
    if (Math.abs(dx) < 70 || Math.abs(dy) > Math.abs(dx) / 2 || e.timeStamp - at > 600 || e.touches.length) return;
    if (x < 24 || x > innerWidth - 24 || from.closest('canvas, input, textarea, select') || sideways(from)) return;  // the screen's edges belong to the browser's own back gesture
    const list = tabs(), step = dx < 0 ? 1 : -1, next = list[list.indexOf(tab) + step];
    if (!next) return;
    history.replaceState(null, '', next === 'today' ? '/' : `/#${next}`);
    show(next, { step });
  }, { passive: true });
}

export function startPhone({ go, onTab, onForm }) {
  opened = onTab;
  const fit = () => {  // a tablet turning between the two layouts, and the page as it first opens
    onForm(small.matches);
    if (small.matches) phoneTab(location.hash.slice(1), scrollY);
    else {
      delete document.body.dataset.tab;
      $$('.desk').forEach((d) => d.classList.remove('shown'));
      $$('.desks a').forEach((a) => a.removeAttribute('aria-current'));
    }
  };
  small.addEventListener('change', fit);
  fit();
  swipes();
  $$('.phone-sheet').forEach((d) => d.addEventListener('click', (e) => { if (e.target === d || e.target.closest('a, [data-close]')) d.close(); }));
  $('#sheet-find-form').addEventListener('submit', (e) => {
    e.preventDefault();
    const q = $('#sheet-q').value.trim();
    if (!q) return;
    $('#sheet-find').close();
    $('#sheet-q').value = '';
    go(`/topic/${encodeURIComponent(q)}`);
  });
  document.addEventListener('click', (e) => {
    if (small.matches) e.target.closest('#editor')?.classList.toggle('open');
    const act = e.target.closest('[data-phone]')?.dataset.phone;
    if (!act) return;
    if (act === 'search') {
      $('#sheet-tags').innerHTML = $('#trend-tags').innerHTML;
      $('#sheet-find').showModal();
      $('#sheet-q').focus();
    } else if (act === 'more') $('#sheet-more').showModal();
    else if (act === 'ask') openDock();
    else if (act === 'back') { if (history.length > 1) history.back(); else go('/'); }
    else if (act === 'share') share();
    else $(`#page [data-${act}]`)?.click();
  });
}
