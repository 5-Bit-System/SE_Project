/* Shared study background and default enlarged login layout. */
(() => {
  const scene = document.querySelector('.login-study-scene');
  if (!scene) return;
  document.documentElement.dataset.studyScene = 'true';
  document.documentElement.dataset.loginScene = 'true';
  document.body.append(scene);
  scene.hidden = false;
  const observer = new IntersectionObserver(entries => {
    scene.dataset.visible = String(entries[0].isIntersecting);
  });
  observer.observe(scene);
})();
