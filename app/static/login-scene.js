/* A local-only visual experiment. No account data, storage or network calls. */
(() => {
  if (new URLSearchParams(window.location.search).get('preview') !== 'study-login') return;
  const scene = document.querySelector('.login-study-scene');
  if (!scene) return;
  document.documentElement.dataset.loginScenePreview = 'true';
  document.body.append(scene);
  scene.hidden = false;
  const observer = new IntersectionObserver(entries => {
    scene.dataset.visible = String(entries[0].isIntersecting);
  });
  observer.observe(scene);
})();
