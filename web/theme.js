// Runs before first paint. Your pick wins; until you make one, it is Morning by day and Night after dark.
(() => {
  let pick = null;
  try { pick = localStorage.getItem('paper-theme'); } catch { /* private window */ }
  const hour = new Date().getHours();
  const theme = ['morning', 'night', 'cobalt', 'glass'].includes(pick) ? pick : hour >= 6 && hour < 18 ? 'morning' : 'night';
  document.documentElement.dataset.theme = theme;
})();
