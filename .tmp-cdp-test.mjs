import { spawn } from 'node:child_process';

const CHROME = '/home/shuvam/.cache/ms-playwright/chromium-1254/chrome-linux64/chrome';
const PORT = 9223;
const chrome = spawn(CHROME, [
  '--headless=new', '--no-sandbox', '--disable-gpu', '--disable-dev-shm-usage',
  `--remote-debugging-port=${PORT}`, '--user-data-dir=/tmp/opencode/chrome-cdp-test',
  'about:blank'
], { stdio: 'ignore' });

const sleep = (ms) => new Promise(r => setTimeout(r, ms));
let targets;
for (let i = 0; i < 40; i++) {
  try {
    targets = await (await fetch(`http://127.0.0.1:${PORT}/json`)).json();
    if (targets.some(t => t.type === 'page')) break;
  } catch (e) { /* not up yet */ }
  await sleep(150);
}
const target = targets.find(t => t.type === 'page');
const ws = new WebSocket(target.webSocketDebuggerUrl);
await new Promise(r => ws.addEventListener('open', r, { once: true }));

let nextId = 0;
const pending = new Map();
const events = [];
ws.addEventListener('message', (e) => {
  const m = JSON.parse(e.data);
  if (m.id && pending.has(m.id)) {
    const p = pending.get(m.id); pending.delete(m.id);
    if (m.error) p.rej(new Error(JSON.stringify(m.error))); else p.res(m.result);
  } else if (m.method) events.push(m);
});
function send(method, params = {}) {
  return new Promise((res, rej) => {
    const id = ++nextId;
    pending.set(id, { res, rej });
    ws.send(JSON.stringify({ id, method, params }));
  });
}
async function js(expr) {
  const r = await send('Runtime.evaluate', { expression: expr, returnByValue: true, awaitPromise: true });
  if (r.exceptionDetails) throw new Error('JS exception: ' + r.exceptionDetails.text + ' ' + (r.exceptionDetails.exception?.description || ''));
  return r.result.value;
}
async function go(url) {
  await send('Page.navigate', { url });
  await sleep(1400);
}
function errors() {
  return events.filter(e =>
    e.method === 'Runtime.exceptionThrown' ||
    (e.method === 'Log.entryAdded' && e.params.entry.level === 'error') ||
    (e.method === 'Runtime.consoleAPICalled' && e.params.type === 'error')
  ).map(e => e.method + ': ' + JSON.stringify(e.params).slice(0, 300));
}

await send('Runtime.enable');
await send('Log.enable');
await send('Page.enable');

const results = [];
const base = 'http://127.0.0.1:8788/';

await go(base + 'index.html');
results.push(['landing', await js(`JSON.stringify({
  stats:[...document.querySelectorAll('.stat .num')].map(n=>n.textContent),
  arcs:document.querySelectorAll('.arc-item').length,
  chapters:document.querySelectorAll('.arc-chapters li').length,
  epub:document.getElementById('epub-btn').getAttribute('href').slice(0,8),
  continueDisabled:document.getElementById('continue-btn').getAttribute('aria-disabled'),
  teasers:[...document.querySelectorAll('.teaser h3')].map(h=>h.textContent)
})`)]);

await go(base + 'read.html');
results.push(['reader', await js(`JSON.stringify({
  crumb:document.getElementById('crumb').textContent,
  fragment:!!document.querySelector('.chapter-fragment .chronicle'),
  plate:!!document.querySelector('.plate-figure img'),
  days:document.querySelectorAll('.daymark').length,
  hash:location.hash,
  pdf:!document.getElementById('chapter-pdf').hidden,
  next:document.getElementById('next-ch').dataset.n
})`)]);

await js(`document.getElementById('toc-toggle').click()`);
results.push(['toc-open', await js(`JSON.stringify({open:document.getElementById('toc-drawer').classList.contains('open'),aria:document.getElementById('toc-drawer').getAttribute('aria-hidden'),focus:document.activeElement.id})`)]);
await js(`document.querySelector('.toc-arc summary').click()`);
results.push(['toc-arc', await js(`JSON.stringify({arcs:document.querySelectorAll('.toc-arc').length,chapters:document.querySelectorAll('.toc-chapter').length,days:document.querySelectorAll('.toc-days a').length})`)]);
await js(`const i=document.getElementById('toc-search'); i.value='day 8'; i.dispatchEvent(new Event('input',{bubbles:true}))`);
results.push(['toc-search', await js(`JSON.stringify({results:document.querySelectorAll('.toc-result').length,label:document.querySelector('.toc-result')?.textContent.slice(0,60)})`)]);
await js(`document.getElementById('toc-search').value=''; document.getElementById('toc-search').dispatchEvent(new Event('input',{bubbles:true})); document.getElementById('toc-toggle').click()`);

await go(base + 'read.html#ch=5&day=day-8-1');
results.push(['deep-link', await js(`JSON.stringify({crumb:document.getElementById('crumb').textContent,hash:location.hash,day:document.getElementById('day-8-1')?.id||null})`)]);

await js(`document.getElementById('settings-toggle').click()`);
await js(`(()=>{const i=document.getElementById('set-size');i.value=24;i.dispatchEvent(new Event('input',{bubbles:true}));const b=document.querySelector('[data-theme-choice="night"]');b.click();})()`);
results.push(['settings', await js(`JSON.stringify({theme:document.documentElement.getAttribute('data-theme'),size:getComputedStyle(document.documentElement).getPropertyValue('--read-size').trim(),stored:localStorage.getItem('sarn.reader.settings')?.slice(0,80)})`)]);
await js(`document.getElementById('settings-toggle').click()`);

await js(`(()=>{document.dispatchEvent(new KeyboardEvent('keydown',{key:'ArrowRight',bubbles:true}));})()`);
await sleep(500);
results.push(['keyboard-next', await js(`JSON.stringify({crumb:document.getElementById('crumb').textContent,hash:location.hash})`)]);

await go(base + 'cast.html');
results.push(['cast', await js(`JSON.stringify({cards:document.querySelectorAll('.cast-card').length,hidden:document.querySelectorAll('.cast-card[hidden]').length,toggleHidden:document.getElementById('spoiler-label').hidden})`)]);
await js(`document.querySelector('.cast-card:not([hidden])').click()`);
await sleep(500);
results.push(['cast-sheet', await js(`JSON.stringify({open:document.getElementById('sheet-dialog').open,title:document.getElementById('sheet-title').textContent,heads:document.querySelectorAll('#sheet-body h3').length})`)]);
await js(`document.getElementById('sheet-close').click()`);
await js(`(()=>{const c=document.getElementById('spoilers');c.checked=true;c.dispatchEvent(new Event('change',{bubbles:true}));})()`);
results.push(['cast-spoilers', await js(`JSON.stringify({hidden:document.querySelectorAll('.cast-card[hidden]').length})`)]);

await go(base + 'atlas.html');
results.push(['atlas', await js(`JSON.stringify({maps:document.querySelectorAll('.map-card').length})`)]);
await js(`document.querySelector('.map-card').click()`);
await js(`document.getElementById('zoom-in').click();document.getElementById('zoom-in').click()`);
results.push(['atlas-zoom', await js(`JSON.stringify({open:document.getElementById('map-dialog').open,transform:document.getElementById('map-image').style.transform})`)]);
await js(`document.getElementById('map-close').click()`);

await go(base + 'codex.html');
results.push(['codex', await js(`JSON.stringify({nav:document.querySelectorAll('#doc-nav a').length,title:document.querySelector('.document-head h1')?.textContent.slice(0,40),prose:!!document.querySelector('#doc-panel .prose'),hash:location.hash})`)]);
await js(`(()=>{const a=document.querySelector('#doc-nav a[data-lore="2"]');a.click();})()`);
await sleep(400);
results.push(['codex-lore', await js(`JSON.stringify({title:document.querySelector('.document-head h1')?.textContent,hash:location.hash})`)]);

await go(base + 'days.html');
results.push(['days', await js(`JSON.stringify({rows:document.querySelectorAll('.ledger-row').length,note:document.getElementById('days-note').textContent,firstLink:document.querySelector('.ledger-day a')?.getAttribute('href')})`)]);
await js(`(()=>{const i=document.getElementById('day-jump');i.value=8;i.dispatchEvent(new Event('change',{bubbles:true}));})()`);
results.push(['days-jump', await js(`JSON.stringify({rows:document.querySelectorAll('.ledger-row').length,note:document.getElementById('days-note').textContent})`)]);

console.log('=== RESULTS ===');
for (const [name, value] of results) console.log(name.padEnd(16), value);
console.log('=== ERRORS ===');
const errs = errors();
console.log(errs.length ? errs.join('\n') : 'none');

ws.close();
chrome.kill('SIGKILL');
