// Questions about the paper. The answer goes in as text, never as markup: the model has read strangers' words, so nothing it says may become a link or a tag.
import { $ } from '/lib.js';

const form = $('#ask-form'), box = $('#question'), go = $('#ask-go'), log = $('#ask-log');

async function ask(question) {
  const entry = document.createElement('article'), head = document.createElement('h2'), reply = document.createElement('p');
  head.textContent = question;
  reply.textContent = 'Reading the paper.';
  reply.className = 'wait';
  entry.append(head, reply);
  log.prepend(entry);
  go.disabled = true;
  try {
    const r = await fetch('/api/ask', { method: 'POST', credentials: 'same-origin', headers: { 'content-type': 'application/json', 'x-paper': '1' }, body: JSON.stringify({ question }) });
    if (r.status === 401) { location.assign('/login'); return; }
    const body = await r.json();
    reply.textContent = r.ok ? body.answer : body.error;
  } catch {
    reply.textContent = 'The paper did not answer. Check your connection and try again.';
  }
  reply.className = '';
  go.disabled = false;
}

form.addEventListener('submit', (e) => {
  e.preventDefault();
  const question = box.value.trim();
  if (!question) return;
  box.value = '';
  ask(question);
});
box.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && !e.shiftKey) form.requestSubmit();
});
$('#ask-try').addEventListener('click', (e) => {
  const b = e.target.closest('button');
  if (b) ask(b.textContent);
});
box.focus();
