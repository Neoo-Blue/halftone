// Runs before first paint. Your pick wins. Until you make one it follows the device, so a phone set to dark gets a real dark page rather than a browser's guess at one, and otherwise it's Morning by day and Night after dark.
(() => {
  const root = document.documentElement, BG = { morning: '#f6d3bd', night: '#0b0b0d', cobalt: '#1a2ae0', glass: '#e8ecf6' };
  let pick = null, text = null;
  try {
    pick = localStorage.getItem('paper-theme');
    text = localStorage.getItem('paper-text');
  } catch { /* private window */ }
  const hour = new Date().getHours(), dark = matchMedia('(prefers-color-scheme: dark)').matches;
  const theme = BG[pick] ? pick : dark || hour < 6 || hour >= 18 ? 'night' : 'morning';
  root.dataset.theme = theme;
  if (text) root.style.setProperty('--text', text);
  document.querySelector('meta[name=theme-color]')?.setAttribute('content', BG[theme]);
})();
