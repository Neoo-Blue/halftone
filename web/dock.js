// The Ask button. It grows out of its own corner into the panel, so the page stays where it is and you can read beside it.
import { $, askPaper } from '/lib.js';

const dock = $('#dock'), button = $('#dock-btn'), panel = $('#dock-panel'), form = $('#dock-form'), box = $('#dock-q'), go = $('#dock-go'), log = $('#dock-log'), tries = $('#dock-try'), pin = $('#dock-side');
let asked = false, story = null, front = [];
const touch = matchMedia('(pointer: coarse)'), roomy = matchMedia('(min-width: 1100px) and (pointer: fine)');
let beside = false;  // a choice for this screen, kept in this browser
try {
  beside = localStorage.getItem('ask-beside') === '1';
} catch { /* private windows can't keep it, and the panel just floats */ }

// Beside the page, the panel takes the right of the window and the page narrows to sit next to it, rather than under it.
function place() {
  const on = beside && roomy.matches && dock.classList.contains('open');
  if (on === dock.classList.contains('side')) return;
  dock.classList.toggle('side', on);
  document.body.classList.toggle('ask-beside', on);
  requestAnimationFrame(() => dispatchEvent(new Event('resize')));  // maps and charts redraw at the page's new width
}

function open(on) {
  dock.style.setProperty('--pill-w', `${button.offsetWidth}px`);
  panel.inert = !on;
  dock.classList.toggle('open', on);
  button.setAttribute('aria-expanded', String(on));
  place();
  (on ? (touch.matches ? panel : box) : button).focus({ preventScroll: true });  // on a phone the keyboard would cover the suggestions
}

const label = () => {
  pin.setAttribute('aria-pressed', String(beside));
  pin.title = beside ? 'Float it over the page' : 'Keep it beside the page';
  pin.setAttribute('aria-label', pin.title);
};
label();
pin.addEventListener('click', () => {
  beside = !beside;
  label();
  try {
    localStorage.setItem('ask-beside', beside ? '1' : '0');
  } catch { /* kept for this visit only */ }
  place();
  box.focus({ preventScroll: true });
});
roomy.addEventListener('change', place);

async function ask(question) {
  tries.hidden = true;
  go.disabled = true;
  const entry = await askPaper(question, log, { last: true, url: story || undefined });
  log.scrollTop = entry.offsetTop - log.offsetTop;  // the start of the answer, not the end of it
  go.disabled = false;
}

button.addEventListener('click', () => open(true));
$('#dock-close').addEventListener('click', () => open(false));
dock.addEventListener('keydown', (e) => { if (e.key === 'Escape') open(false); });
form.addEventListener('submit', (e) => {
  e.preventDefault();
  const question = box.value.trim();
  if (!question || go.disabled) return;  // one question at a time: each one counts against the day's limit
  box.value = '';
  ask(question);
});
box.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    form.requestSubmit();
  }
});
tries.addEventListener('click', (e) => {
  const b = e.target.closest('button');
  if (b) ask(b.textContent);
});
visualViewport?.addEventListener('resize', () => dock.style.setProperty('--kb', `${Math.max(0, innerHeight - visualViewport.height - visualViewport.offsetTop)}px`));  // keeps the box above a phone's keyboard

export const openDock = () => open(true);
export const askDock = (question) => {
  open(true);
  if (!go.disabled) ask(question);
};

function offer(list) {
  tries.replaceChildren(...list.map((text) => {
    const b = document.createElement('button');
    b.type = 'button';
    b.className = 'ghost text';
    b.textContent = text;
    return b;
  }));
  tries.hidden = false;
}

// On a story, the button asks about that story.
export function dockStory(url) {
  story = url;
  dock.classList.toggle('story', !!url);
  offer(url ? ['Explain this simply', 'What led to this?', 'Who disagrees?'] : front);
}

export function showDock(p) {
  dock.hidden = !p.on.ai;
  document.body.classList.toggle('no-ask', !p.on.ai);
  if (asked || !p.on.ai) return;
  asked = true;
  front = [['What needs me today?', true], ['Which races should I watch?', p.elections?.us], ['What changed in the world overnight?', p.on.world], ['Am I making money?', p.on.money], ['Is anything broken?', p.on.systems]].filter(([, on]) => on).map(([text]) => text);
  if (!story) offer(front);
}
