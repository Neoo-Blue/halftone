// The Ask button. It grows out of its own corner into the panel, so the page stays where it is and you can read beside it.
import { $, askPaper } from '/lib.js';

const dock = $('#dock'), button = $('#dock-btn'), panel = $('#dock-panel'), form = $('#dock-form'), box = $('#dock-q'), go = $('#dock-go'), log = $('#dock-log'), tries = $('#dock-try');
let asked = false, story = null, front = [];
const touch = matchMedia('(pointer: coarse)');

function open(on) {
  dock.style.setProperty('--pill-w', `${button.offsetWidth}px`);
  panel.inert = !on;
  dock.classList.toggle('open', on);
  button.setAttribute('aria-expanded', String(on));
  (on ? (touch.matches ? panel : box) : button).focus({ preventScroll: true });  // on a phone the keyboard would cover the suggestions
}

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
