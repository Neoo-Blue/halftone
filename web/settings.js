// One block per connection. Secrets only ever travel from here to the server: the page is told whether one is set, never what it is.
import { $, $$, esc, ICON } from '/lib.js';

const CROSS = '<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M3.5 3.5l9 9M12.5 3.5l-9 9"/></svg>';
let data = null;

const send = (method, path, body) => fetch(path, { method, credentials: 'same-origin', headers: { 'content-type': 'application/json', 'x-paper': '1' }, body: body ? JSON.stringify(body) : undefined }).then((r) => {
  if (r.status === 401) location.assign('/login');
  return r;
});
const section = (id) => data.sections.find((s) => s.id === id);
const ALWAYS = ['paper', 'news', 'access'];
const optional = () => data.sections.filter((s) => !ALWAYS.includes(s.id));
const hint = (f) => (f.hint ? `<small id="h-${f.key}">${esc(f.hint)}</small>` : '');
const described = (f) => (f.hint ? ` aria-describedby="h-${f.key}"` : '');

// ---------------------------------------------------------------- fields

function cell(c, value = '') {
  const label = `aria-label="${esc(c.label)}"`;
  if (c.kind === 'select') return `<select data-col="${c.key}" ${label}>${c.options.map((o) => `<option${o === value ? ' selected' : ''}>${esc(o)}</option>`).join('')}</select>`;
  return `<input data-col="${c.key}" ${label} type="${c.kind === 'date' ? 'date' : 'text'}" value="${esc(value)}" placeholder="${esc(c.placeholder)}" spellcheck="false" autocomplete="off">`;
}

function rowHtml(f, row = {}) {
  return `<li class="set-row" style="--cols:${f.columns.length}">${f.columns.map((c) => cell(c, row[c.key])).join('')}<button type="button" class="ghost" data-drop aria-label="Remove this row">${CROSS}</button></li>`;
}

function rows(f) {
  const body = `<ul class="set-rows" id="rows-${f.key}">${(f.value || []).map((r) => rowHtml(f, r)).join('')}</ul>`;
  return `<div class="field" role="group" aria-labelledby="l-${f.key}"><span id="l-${f.key}">${esc(f.label)}</span>
    ${f.locked ? '<p class="set-lock">Set by the environment.</p>' : `${body}<button type="button" class="ghost text" data-add="${f.key}">Add a row</button>`}${hint(f)}</div>`;
}

function secret(f) {
  if (f.locked) return `<div class="field"><span>${esc(f.label)}</span><p class="set-lock">Set by the environment.</p>${hint(f)}</div>`;
  const entry = `<input id="f-${f.key}" data-key="${f.key}" type="password" autocomplete="new-password" spellcheck="false" placeholder="Paste it here"${described(f)}>`;
  if (!f.set) return `<label class="field"><span>${esc(f.label)}</span>${entry}${hint(f)}</label>`;
  return `<div class="field"><span>${esc(f.label)}</span>
    <p class="set-saved" data-secret="${f.key}">${ICON.good}Saved. It can't be shown again.
      <button type="button" class="ghost text" data-replace="${f.key}">Replace</button><button type="button" class="ghost text" data-clear="${f.key}">Remove</button></p>
    ${hint(f)}</div>`;
}

// Each choice is shown as the paper's own name in that face.
function fonts(f) {
  const name = esc(section('paper').fields.find((x) => x.key === 'PAPER_NAME').value);
  const off = f.locked ? ' disabled' : '';
  return `<fieldset class="set-fonts"><legend>${esc(f.label)}</legend><div class="set-font-grid">${f.options.map(([value, label]) => `<label class="set-font mast-${value}"><input type="radio" name="${f.key}" value="${value}"${value === f.value ? ' checked' : ''}${off}><span data-name>${name}</span><small>${esc(label)}</small></label>`).join('')}</div></fieldset>`;
}

function field(f) {
  if (f.kind === 'rows') return rows(f);
  if (f.kind === 'choice') return fonts(f);
  if (f.kind === 'select') return `<label class="field"><span>${esc(f.label)}</span><select id="f-${f.key}" data-key="${f.key}"${f.locked ? ' disabled' : ''}>${f.options.map(([value, label]) => `<option value="${esc(value)}"${value === f.value ? ' selected' : ''}>${esc(label)}</option>`).join('')}</select>${hint(f)}</label>`;
  if (f.kind === 'secret') return secret(f);
  const off = f.locked ? ' disabled' : '';
  if (f.kind === 'bool') return `<label class="set-check"><input type="checkbox" data-key="${f.key}"${f.value ? ' checked' : ''}${off}${described(f)}><span>${esc(f.label)}</span>${hint(f)}</label>`;
  return `<label class="field"><span>${esc(f.label)}</span><input id="f-${f.key}" data-key="${f.key}" type="${f.kind === 'date' ? 'date' : 'text'}" value="${esc(f.value)}" placeholder="${esc(f.placeholder)}" spellcheck="false" autocomplete="off"${off}${described(f)}>${f.locked ? '<small>Set by the environment.</small>' : ''}${hint(f)}</label>`;
}

// ---------------------------------------------------------------- blocks

function mark(s) {
  if (s.result) return s.result.ok ? ['good', 'Connected'] : ['bad', 'Not answering'];
  return s.on ? ['good', 'Saved'] : ['off', 'Off'];
}

function block(s) {
  const [cls, text] = mark(s);
  const always = ALWAYS.includes(s.id);
  return `<section class="set" id="set-${s.id}" aria-labelledby="t-${s.id}">
    <div class="set-head"><h2 id="t-${s.id}">${esc(s.title)}</h2>${always ? '' : `<p class="set-state ${cls}">${text}</p>`}</div>
    <p class="set-about">${esc(s.about)}</p>
    <div class="set-fields">${s.fields.map(field).join('')}</div>
    ${s.id === 'access' ? connect() : ''}
    <div class="set-foot"><button type="button" class="btn" data-save="${s.id}" disabled>Save</button>
      ${s.can_test ? `<button type="button" class="ghost text" data-test="${s.id}">Test</button>` : ''}
      <span class="set-say" id="say-${s.id}" role="status"></span></div>
  </section>`;
}

function signIn() {
  const a = data.auth;
  if (a.state === 'open') return '<section class="set" id="set-door"><div class="set-head"><h2>Sign-in</h2></div><p class="set-about">Sign-in is off, because PAPER_AUTH is none. Anyone who reaches this address can read the paper and change these settings, so keep it behind a gate of your own.</p></section>';
  const change = a.locked ? '<p class="set-lock">The password is set by the environment.</p>' : `
    <div class="set-fields"><label class="field"><span>Current password</span><input id="pw-current" type="password" autocomplete="current-password"></label>
    <label class="field"><span>New password</span><input id="pw-new" type="password" autocomplete="new-password"><small>At least 10 characters. Every other device is signed out.</small></label></div>`;
  return `<section class="set" id="set-door" aria-labelledby="t-door">
    <div class="set-head"><h2 id="t-door">Sign-in</h2></div>${change}
    <div class="set-foot">${a.locked ? '' : '<button type="button" class="btn" id="pw-save">Change password</button>'}<button type="button" class="ghost text" id="sign-out">Sign out</button><span class="set-say" id="say-door" role="status"></span></div>
  </section>`;
}

function rail() {
  const on = optional().filter((s) => s.on).length;
  $('#set-deck').textContent = `${on} of ${optional().length} connections are on. Anything you leave blank stays off the page.`;
  $('#set-rail').innerHTML = `<ul>${data.sections.map((s) => {
    const [cls] = mark(s);
    const always = ALWAYS.includes(s.id);
    return `<li><a href="#set-${s.id}">${esc(s.title)}${always ? '' : `<i class="dot ${cls}"></i><span class="vh">${cls === 'off' ? 'Off' : cls === 'bad' ? 'Not answering' : 'On'}</span>`}</a></li>`;
  }).join('')}<li><a href="#set-door">Sign-in</a></li></ul>`;
}

// Where an AI connects. The token is shown once, when it's made, and only its hash is kept.
function connect() {
  const a = data.ai, shared = a.tools.join(', ') || 'nothing yet';
  const token = a.token_locked ? '<p class="set-lock">The token is set by the environment.</p>' : a.token
    ? '<p>A token is active. <button type="button" class="ghost text" id="token-new">Replace it</button> <button type="button" class="ghost text" id="token-revoke">Turn it off</button></p>'
    : '<p><button type="button" class="ghost text" id="token-new">Make a token</button></p>';
  return `<div class="set-connect"><dl><dt>MCP</dt><dd>${esc(location.origin)}/mcp</dd><dt>REST</dt><dd>${esc(location.origin)}/api/ai/news</dd><dt>Shared</dt><dd>${esc(shared)}</dd></dl>
    <div id="token-spot"></div>${token}<p class="set-about">Send it as <code>Authorization: Bearer</code>. See docs/ai.md for Claude, ChatGPT and Cursor.</p></div>`;
}

function helper() {
  if (!data.ai.ready) return '';
  return `<section class="set set-helper" id="set-helper" aria-labelledby="t-helper">
    <div class="set-head"><h2 id="t-helper">Set it up by asking</h2></div>
    <p class="set-about">Say what you have, in your own words. Nothing changes until you approve it. Type keys into their own fields, never here: this goes to your AI provider.</p>
    <label class="field"><span>What do you want to change?</span><textarea id="help-text" placeholder="My Plex is at 192.168.1.10, and check my router at 192.168.1.1 every minute"></textarea></label>
    <div class="set-foot"><button type="button" class="btn" id="help-go">Suggest changes</button><span class="set-say" id="say-helper" role="status"></span></div>
    <div class="help-result" id="help-result"></div>
  </section>`;
}

const shown = (v) => (Array.isArray(v) ? `${v.length} ${v.length === 1 ? 'row' : 'rows'}: ${v.map((r) => Object.values(r).filter(Boolean).join(', ')).join('; ')}` : String(v));
let proposal = null;

async function suggest() {
  const say = $('#say-helper'), out = $('#help-result'), request = $('#help-text').value;
  say.textContent = 'Thinking.';
  out.innerHTML = '';
  proposal = null;
  try {
    const r = await send('POST', '/api/configure', { request });
    const body = await r.json();
    if (!r.ok) throw new Error(body.error);
    say.textContent = '';
    proposal = body.changes;
    const list = body.changes.map((c) => `<li><b>${esc(c.label)}</b><span>${c.was && shown(c.was) !== shown(c.value) && (!Array.isArray(c.was) || c.was.length) ? `<code>${esc(shown(c.was))}</code> becomes ` : ''}<code>${esc(shown(c.value))}</code></span></li>`).join('');
    out.innerHTML = `<p>${esc(body.say)}</p>${list ? `<ul>${list}</ul><div class="set-foot"><button type="button" class="btn" id="help-apply">Apply these changes</button></div>` : ''}
      ${body.needs.length ? `<p>Then enter yourself: ${esc(body.needs.join(', '))}.</p>` : ''}${body.refused.length ? `<p>Left out: ${esc(body.refused.join(', '))}. An address with a saved key has to be changed by hand, and Settings has to accept every value.</p>` : ''}`;
  } catch (e) {
    say.textContent = e.message && !e.message.includes('fetch') ? e.message : 'The paper did not answer.';
  }
}

async function applyProposal() {
  const say = $('#say-helper');
  say.textContent = 'Saving.';
  const r = await send('PUT', '/api/settings', { values: Object.fromEntries(proposal.map((c) => [c.key, c.value])) });
  const body = await r.json();
  if (!r.ok) { say.textContent = body.error; return; }
  data = body;
  const dropped = body.dropped.length;
  draw();
  $('#say-helper').textContent = dropped ? 'Saved. An address changed, so its saved key was removed. Enter it again.' : 'Saved.';
}

async function token(path) {
  const r = await send('POST', path);
  const body = await r.json();
  if (!r.ok) return;
  data = await (await send('GET', '/api/settings')).json();
  draw();
  if (body.token) $('#token-spot').innerHTML = `<p>Copy this now. It won't be shown again.</p><code class="set-token">${esc(body.token)}</code>`;
}

function draw() {
  $('#set-main').innerHTML = helper() + data.sections.map(block).join('') + signIn();
  rail();
}

function redraw(id) {
  $(`#set-${id}`).outerHTML = block(section(id));
  rail();
}

// ---------------------------------------------------------------- saving

function collect(s) {
  const values = {}, el = $(`#set-${s.id}`);
  for (const f of s.fields) {
    if (f.locked) continue;
    if (f.kind === 'rows') {
      values[f.key] = $$(`#rows-${f.key} .set-row`, el).map((row) => Object.fromEntries($$('[data-col]', row).map((i) => [i.dataset.col, i.value])));
    } else if (f.kind === 'choice') {
      values[f.key] = $(`[name="${f.key}"]:checked`, el).value;
    } else if (f.kind === 'secret') {
      const input = $(`[data-key="${f.key}"]`, el), held = $(`[data-secret="${f.key}"]`, el);
      if (held?.dataset.cleared) values[f.key] = null;
      else if (input?.value) values[f.key] = input.value;
    } else {
      const input = $(`[data-key="${f.key}"]`, el);
      values[f.key] = f.kind === 'bool' ? input.checked : input.value;
    }
  }
  return values;
}

async function test(id, lead = '') {
  const say = $(`#say-${id}`);
  say.textContent = `${lead} Testing.`.trim();
  try {
    const r = await (await send('POST', `/api/settings/test/${id}`)).json();
    section(id).result = r;
    redraw(id);
    $(`#say-${id}`).textContent = `${lead} ${r.text}`.trim();
  } catch {
    say.textContent = 'The paper did not answer.';
  }
}

async function save(id) {
  const s = section(id), say = $(`#say-${id}`), button = $(`[data-save="${id}"]`);
  say.textContent = 'Saving.';
  button.disabled = true;
  try {
    const r = await send('PUT', '/api/settings', { values: collect(s) });
    const body = await r.json();
    if (!r.ok) throw new Error(body.error);
    data = body;
    redraw(id);
    const lead = body.dropped.length ? 'Saved. That change removed the saved key, so enter it again.' : 'Saved.';
    if (section(id).can_test && section(id).on) await test(id, lead);
    else $(`#say-${id}`).textContent = lead;
  } catch (e) {
    say.textContent = e.message && !e.message.includes('fetch') ? e.message : 'Could not save. Check your connection and try again.';
    button.disabled = false;
  }
}

async function changePassword() {
  const say = $('#say-door');
  const r = await send('PUT', '/api/password', { current: $('#pw-current').value, new: $('#pw-new').value });
  const body = await r.json();
  say.textContent = r.ok ? 'Password changed. Other devices are signed out.' : body.error;
  if (r.ok) { $('#pw-current').value = ''; $('#pw-new').value = ''; }
}

// ---------------------------------------------------------------- behaviour

const dirty = (el) => { const b = $('[data-save]', el.closest('.set')); if (b) { b.disabled = false; $('.set-say', el.closest('.set')).textContent = 'Not saved yet.'; } };
document.addEventListener('input', (e) => {
  if (e.target.closest('.set') && !e.target.closest('#set-helper') && !e.target.id.startsWith('pw-')) dirty(e.target);
  if (e.target.name === 'PAPER_FONT') document.documentElement.dataset.masthead = e.target.value;  // try it on the masthead above, before saving
  if (e.target.id === 'f-PAPER_NAME') $$('.nameplate a, [data-name]').forEach((n) => { n.textContent = e.target.value; });
});
addEventListener('beforeunload', (e) => { if ($$('[data-save]').some((b) => !b.disabled)) e.preventDefault(); });

document.addEventListener('click', async (e) => {
  const t = e.target.closest('button');
  if (!t) return;
  if (t.dataset.save) save(t.dataset.save);
  else if (t.dataset.test) test(t.dataset.test);
  else if (t.dataset.add) {
    const f = data.sections.flatMap((s) => s.fields).find((x) => x.key === t.dataset.add);
    $(`#rows-${f.key}`).insertAdjacentHTML('beforeend', rowHtml(f));
    $(`#rows-${f.key} .set-row:last-child input`).focus();
    dirty(t);
  } else if (t.hasAttribute('data-drop')) {
    const host = t.closest('.set');
    t.closest('.set-row').remove();
    dirty($('.set-about', host));
  } else if (t.dataset.replace) {
    const f = data.sections.flatMap((s) => s.fields).find((x) => x.key === t.dataset.replace), hold = t.closest('.set-saved');
    hold.outerHTML = `<input id="f-${f.key}" data-key="${f.key}" type="password" autocomplete="new-password" spellcheck="false" placeholder="Paste the new one here">`;
    $(`#f-${f.key}`).focus();
  } else if (t.dataset.clear) {
    const hold = t.closest('.set-saved');
    hold.dataset.cleared = '1';
    hold.innerHTML = `${ICON.warn}Will be removed when you save.`;
    dirty(hold);
  } else if (t.id === 'help-go') suggest();
  else if (t.id === 'help-apply') applyProposal();
  else if (t.id === 'token-new') token('/api/ai-token');
  else if (t.id === 'token-revoke') token('/api/ai-token/revoke');
  else if (t.id === 'pw-save') changePassword();
  else if (t.id === 'sign-out') {
    await send('POST', '/api/logout');
    location.assign('/login');
  }
});

try {
  const r = await send('GET', '/api/settings');
  data = await r.json();
  draw();
  if (location.hash) $(location.hash)?.scrollIntoView();
  data.sections.filter((s) => s.on && s.can_test && s.id !== 'ai').forEach((s) => test(s.id));  // a test of the AI costs money, so that one waits for the button
} catch {
  $('#set-deck').textContent = 'Settings did not load. Reload the page to try again.';
}
