/* Keep the export usable if a device cannot initialize the original renderer. */
(() => {
  let timer;
  function revealFallback() {
    const overlay = document.querySelector('.transition-w');
    if (!overlay || getComputedStyle(overlay).visibility === 'hidden') return;
    document.documentElement.dataset.replicaFallback = 'true';
    overlay.style.display = 'none';
    window.lenisStart?.();
    document.documentElement.classList.remove('lenis-stopped');
    document.querySelectorAll('[data-rive-placeholder]').forEach(el => { el.style.display = 'block'; });
  }
  window.addEventListener('replica-runtime-error', revealFallback);
  window.addEventListener('load', () => { timer = window.setTimeout(revealFallback, 20000); }, {once:true});
})();
