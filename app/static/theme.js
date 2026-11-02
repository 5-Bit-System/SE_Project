/* Only the appearance preference is persisted. Transcript/chat stay in memory. */
(() => {
  const storageKey = "study-workspace-theme";
  const valid = value => value === "light" || value === "dark";
  let saved;
  try { saved = localStorage.getItem(storageKey); } catch { /* Storage is optional. */ }
  const preferred = window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";

  function applyTheme(theme) {
    document.documentElement.dataset.theme = theme;
    document.querySelectorAll("[data-theme-choice]").forEach(button => {
      button.setAttribute("aria-pressed", String(button.dataset.themeChoice === theme));
    });
    const color = document.querySelector('meta[name="theme-color"]');
    if (color) color.content = theme === "dark" ? "#151522" : "#f7f5ff";
  }

  applyTheme(valid(saved) ? saved : preferred);
  document.addEventListener("DOMContentLoaded", () => {
    applyTheme(document.documentElement.dataset.theme);
    document.querySelectorAll("[data-theme-choice]").forEach(button => {
      button.addEventListener("click", () => {
        const theme = button.dataset.themeChoice;
        if (!valid(theme)) return;
        applyTheme(theme);
        try { localStorage.setItem(storageKey, theme); } catch { /* Keep session choice. */ }
      });
    });
  });
  window.addEventListener("storage", event => {
    if (event.key === storageKey) applyTheme(valid(event.newValue) ? event.newValue : preferred);
  });
})();
