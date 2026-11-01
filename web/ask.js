// The full page for Ask. The button on the front page uses the same askPaper.
import { $, askPaper } from '/lib.js';

const form = $('#ask-form'), box = $('#question'), go = $('#ask-go'), log = $('#ask-log');

async function ask(question) {
  go.disabled = true;
  await askPaper(question, log);
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
