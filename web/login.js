// The door: sign in, or on a new install turn the setup code from the log into a password.
globalThis.caches?.delete('paper-v1');  // every ended session lands here, and the saved edition goes with it
import { $ } from '/lib.js';

const field = (id, label, type, auto, note = '') => `<label class="field"><span>${label}</span><input id="${id}" name="${id}" type="${type}" autocomplete="${auto}" required>${note ? `<small>${note}</small>` : ''}</label>`;
const MODES = {
  login: { head: 'Sign in', note: '', go: 'Open the paper', path: '/api/login', fields: field('password', 'Password', 'password', 'current-password') },
  setup: {
    head: 'Set a password',
    note: 'This paper is new. The setup code is in its log: run <code>docker compose logs paper</code>.',
    go: 'Set password and open the paper',
    path: '/api/setup',
    fields: field('code', 'Setup code', 'text', 'off') + field('password', 'New password', 'password', 'new-password', 'At least 10 characters.'),
  },
};

const r = await fetch('/api/auth', { credentials: 'same-origin' }).then((x) => x.json());
if (r.signed_in) location.replace('/');
const mode = MODES[r.state] || MODES.login, form = $('#door'), error = $('#door-error'), go = $('#door-go');
$('#door-head').textContent = mode.head;
$('#door-note').innerHTML = mode.note;
$('#door-note').hidden = !mode.note;
$('#door-fields').innerHTML = mode.fields;
go.textContent = mode.go;
form.hidden = false;
$('input', form).focus();

form.addEventListener('submit', async (e) => {
  e.preventDefault();
  error.hidden = true;
  go.disabled = true;
  try {
    const sent = await fetch(mode.path, { method: 'POST', headers: { 'content-type': 'application/json', 'x-paper': '1' }, credentials: 'same-origin', body: JSON.stringify(Object.fromEntries(new FormData(form))) });
    if (sent.ok) { location.replace('/'); return; }
    error.textContent = (await sent.json()).error;
  } catch {
    error.textContent = 'The paper did not answer. Check your connection and try again.';
  }
  error.hidden = false;
  go.disabled = false;
  $('#password', form).select();
});
