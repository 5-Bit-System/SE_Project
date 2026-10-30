/* A local-only visual experiment. No account data, storage or network calls. */
(() => {
  if (new URLSearchParams(window.location.search).get('preview') !== 'study-login') return;
  const scene = document.querySelector('.login-study-scene');
  if (!scene) return;
  document.documentElement.dataset.loginScenePreview = 'true';
  scene.hidden = false;
  const compact = window.matchMedia('(max-width: 850px)');
  const placeScene = () => {
    const target = document.querySelector(compact.matches ? '#system-auth' : '.auth-intro');
    target.append(scene);
  };
  placeScene();
  compact.addEventListener('change', placeScene);
  const observer = new IntersectionObserver(entries => {
    scene.dataset.visible = String(entries[0].isIntersecting);
  });
  observer.observe(scene);
})();
