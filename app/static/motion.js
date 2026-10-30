/* Presentation only: no requests, source data writes, or persistent state. */
(() => {
  'use strict';
  const reduced = window.matchMedia('(prefers-reduced-motion: reduce)');
  const activeAnimations = new Set(), chartRevisions = new Map();
  const transients = new Set();
  const easing = 'cubic-bezier(.2,.7,.2,1)';
  const feedbackDuration = parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--feedback-duration')) || 380;
  function animate(node, frames, options) {
    if (!node || reduced.matches || !node.animate) return null;
    const animation = node.animate(frames, {easing, ...options});
    activeAnimations.add(animation);
    const forget = () => activeAnimations.delete(animation);
    animation.finished.then(forget, forget);
    return animation;
  }

  const navigation = document.querySelector('.nav-tabs');
  const indicator = document.createElement('span');
  indicator.className = 'navigation-indicator'; indicator.setAttribute('aria-hidden', 'true');
  navigation.prepend(indicator);
  let indicatorFrame;
  function moveIndicator() {
    cancelAnimationFrame(indicatorFrame);
    indicatorFrame = requestAnimationFrame(() => {
      const selected = navigation.querySelector('.tab-btn.active');
      if (!selected) return;
      indicator.style.width = `${selected.offsetWidth}px`;
      indicator.style.height = `${selected.offsetHeight}px`;
      indicator.style.transform = `translate(${selected.offsetLeft}px, ${selected.offsetTop}px)`;
      navigation.dataset.motionReady = 'true';
    });
  }
  const resize = new ResizeObserver(moveIndicator);
  resize.observe(navigation);
  navigation.querySelectorAll('.tab-btn').forEach(button => resize.observe(button));
  document.addEventListener('workspace:language-change', moveIndicator);
  moveIndicator();

  // This scene scrolls with the heading. Layout reads happen on changes, never per scroll frame.
  const book = document.querySelector('.study-book');
  let bookFrame, bookInView = false;
  const inView = new IntersectionObserver(entries => entries.forEach(entry => {
    entry.target.dataset.paused = String(!entry.isIntersecting || (entry.target === book && book.dataset.visible !== 'true'));
    if (entry.target === book) bookInView = entry.isIntersecting;
  }));
  if (book) inView.observe(book);
  const intersects = (a, b, gap = 6) => a.left < b.right + gap && a.right > b.left - gap && a.top < b.bottom + gap && a.bottom > b.top - gap;
  function fitBook() {
    if (!book) return;
    const panel = document.querySelector('.tab-panel.active');
    const area = document.querySelector('.workspace-body').getBoundingClientRect();
    const heading = panel?.querySelector('.dashboard-heading, .portal-top, .course-status-heading, h2');
    const notice = {bottom: heading?.getBoundingClientRect().top ?? area.top};
    book.dataset.visible = 'false'; book.dataset.paused = 'true';
    if (innerWidth <= 800 || !panel || bookSettling) return;
    const protectedRects = [];
    const surfaces = 'button,input,select,textarea,table,progress,.workspace-surface,.profile-login-layout,.profile-identity-strip,.profile-facts,.portal-table-scroll,.academic-readiness,.course-status-summary,.course-status-columns,.course-status-toolbar,.semester-plans,.course-status-notice,.course-program-confirmation,.course-review-items,.reference-program-grid,.reference-selectors,.reference-facts,.reference-plan,.reference-source-issues,.reference-scope,.reference-error';
    panel.querySelectorAll(surfaces).forEach(node => {
      if (node.getClientRects().length) protectedRects.push(node.getBoundingClientRect());
    });
    panel.querySelectorAll('h2,p,summary,li,label').forEach(node => {
      if (!node.getClientRects().length) return;
      const box = node.getBoundingClientRect();
      if (box.top > notice.bottom + 170 || box.bottom < notice.bottom) return;
      const range = document.createRange(); range.selectNodeContents(node);
      protectedRects.push(...range.getClientRects());
    });
    for (const scale of [1, .88, .76, .66, .56, .5]) {
      const width = 200 * scale, height = 150 * scale;
      for (const offset of [0, 184, 340]) {
        const left = area.right - width - offset, top = notice.bottom + 8;
        const box = {left, top, right: left + width, bottom: top + height};
        if (left < area.left + area.width * .43 || protectedRects.some(rect => intersects(box, rect))) continue;
        book.style.left = `${left + scrollX}px`; book.style.top = `${top + scrollY}px`;
        book.style.width = `${width}px`; book.style.height = `${height}px`;
        book.style.setProperty('--book-scale', scale);
        book.hidden = false; book.dataset.visible = 'true';
        book.dataset.paused = String(!bookInView);
        return;
      }
    }
  }
  function positionBook() { cancelAnimationFrame(bookFrame); bookFrame = requestAnimationFrame(fitBook); }
  new ResizeObserver(positionBook).observe(document.querySelector('.workspace-body'));
  new MutationObserver(positionBook).observe(document.querySelector('.workspace-body'), {childList: true, subtree: true});
  window.addEventListener('resize', () => { if (book) book.dataset.visible = 'false'; positionBook(); });
  document.fonts.ready.then(positionBook);
  positionBook();

  function clearTransientFeedback() {
    [...transients].forEach(entry => { entry.animation?.cancel(); entry.remove(); });
  }
  function keepTransient(node, animation, layer = null, control = null) {
    const entry = {animation, control, remove() {
      node.remove(); if (layer && !layer.childElementCount) layer.remove(); transients.delete(entry);
    }};
    while (transients.size >= 4) { const old = transients.values().next().value; old.animation?.cancel(); old.remove(); }
    transients.add(entry);
    if (animation) animation.finished.then(() => entry.remove(), () => entry.remove()); else entry.remove();
  }
  document.addEventListener('click', event => {
    const control = event.target.closest?.('button');
    if (!control || !control.isConnected || control.closest('[inert]') || control.disabled || control.getAttribute('aria-disabled') === 'true' || reduced.matches || document.getSelection()?.toString()) return;
    [...transients].filter(entry => entry.control === control).forEach(entry => { entry.animation?.cancel(); entry.remove(); });
    const box = control.getBoundingClientRect(), keyboard = event.detail === 0;
    if (!box.width || !box.height) return;
    const x = keyboard ? control.clientWidth / 2 : (event.clientX - box.left) * control.offsetWidth / box.width - control.clientLeft;
    const y = keyboard ? control.clientHeight / 2 : (event.clientY - box.top) * control.offsetHeight / box.height - control.clientTop;
    const layer = document.createElement('span'), ripple = document.createElement('span');
    layer.className = 'control-feedback-layer'; layer.setAttribute('aria-hidden', 'true');
    ripple.className = 'control-ripple'; ripple.style.left = `${x}px`; ripple.style.top = `${y}px`;
    layer.append(ripple); control.append(layer);
    const radius = Math.hypot(Math.max(x, control.clientWidth - x), Math.max(y, control.clientHeight - y));
    keepTransient(ripple, animate(ripple, [
      {opacity: .2, transform: 'translate(-50%,-50%) scale(.3)'},
      {opacity: 0, transform: `translate(-50%,-50%) scale(${radius / 8})`}
    ], {duration: feedbackDuration}), layer, control);
  });

  function capturePlan(root) {
    if (reduced.matches) return () => {};
    const selector = '.semester-plan-courses [data-plan-course]';
    const before = new Map([...root.querySelectorAll(selector)].map(node => {
      const clone = node.cloneNode(true), style = getComputedStyle(node);
      Object.assign(clone.style, {font: style.font, padding: style.padding, backgroundColor: style.backgroundColor,
        borderRadius: style.borderRadius, color: style.color, whiteSpace: style.whiteSpace});
      return [node.dataset.planCourse, {box: node.getBoundingClientRect(), clone}];
    }));
    const totalSelector = '.course-status-summary > div:nth-child(2) strong';
    const totalBefore = root.querySelector(totalSelector)?.textContent;
    return () => {
      const after = new Map([...root.querySelectorAll(selector)].map(node => [node.dataset.planCourse, node]));
      let additions = 0;
      after.forEach((node, code) => {
        const old = before.get(code);
        if (!old && additions++ < 6) animate(node, [{opacity: 0, transform: 'translateY(5px)'}, {opacity: 1, transform: 'none'}], {duration: 220});
        else if (old) {
          const box = node.getBoundingClientRect(), x = old.box.x - box.x, y = old.box.y - box.y;
          if (x || y) animate(node, [{transform: `translate(${x}px,${y}px)`}, {transform: 'none'}], {duration: 220});
        }
      });
      before.forEach(({box, clone}, code) => {
        if (after.has(code) || box.bottom < 0 || box.top > innerHeight) return;
        clone.removeAttribute('id'); clone.setAttribute('aria-hidden', 'true'); clone.inert = true;
        clone.querySelectorAll('.control-feedback-layer').forEach(node => node.remove());
        clone.classList.add('plan-exit-ghost');
        Object.assign(clone.style, {left: `${box.x}px`, top: `${box.y}px`, width: `${box.width}px`, height: `${box.height}px`});
        document.body.append(clone);
        keepTransient(clone, animate(clone, [{opacity: .6, transform: 'none'}, {opacity: 0, transform: 'translateY(-4px)'}], {duration: 160}));
      });
      const total = root.querySelector(totalSelector);
      if (total && total.textContent !== totalBefore) animate(total, [{opacity: .55}, {opacity: 1}], {duration: 180});
    };
  }
  const statusIcons = new WeakMap();
  function statusFeedback(node, state) {
    const previous = statusIcons.get(node);
    if (previous) { inView.unobserve(previous); previous.remove(); statusIcons.delete(node); }
    node.dataset.feedback = state;
    if (!['loading', 'success'].includes(state)) return;
    const icon = document.createElement('span');
    icon.className = `status-motion-icon ${state === 'loading' ? 'book-loader' : 'status-success'}`;
    icon.setAttribute('aria-hidden', 'true');
    icon.innerHTML = state === 'loading'
      ? '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"><path d="M3 5q4-2 9 0 5-2 9 0v15q-5-2-9 0-5-2-9 0zM12 5v15"/><path class="loader-turn" d="M12 5q4-2 8 0v13q-4-2-8 0z"/></svg>'
      : '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10" opacity=".35"/><path class="success-check-path" d="m7 12 3 3 7-7"/></svg>';
    node.prepend(icon); statusIcons.set(node, icon);
    if (state === 'loading') inView.observe(icon);
    else animate(node, [{opacity: .55, transform: 'translateY(4px)'}, {opacity: 1, transform: 'none'}], {duration: 180});
  }

  function animateCharts() {
    if (document.documentElement.dataset.view !== 'tab-dashboard' || reduced.matches) return;
    for (const id of ['analytics-trend', 'analytics-trend4', 'analytics-credits', 'analytics-distribution']) {
      const chart = document.getElementById(id);
      if (!chart) continue;
      // WAAPI does not mutate markup, so hover and duplicate notifications do not replay.
      const revision = chart.innerHTML;
      if (chartRevisions.get(id) === revision) continue;
      chartRevisions.set(id, revision);
      if (id === 'analytics-trend' || id === 'analytics-trend4') {
        chart.querySelectorAll('.chart-trend-line').forEach(line => {
          const length = line.getTotalLength();
          if (length > 0) animate(line, [
            {strokeDasharray: `${length} ${length}`, strokeDashoffset: length},
            {strokeDasharray: `${length} ${length}`, strokeDashoffset: 0}
          ], {duration: 700});
        });
        chart.querySelectorAll('.chart-point, .chart-point-label').forEach(point => {
          animate(point, [{opacity: 0}, {opacity: 1}], {duration: 450, delay: 140, fill: 'backwards'});
        });
      } else if (id === 'analytics-credits') {
        chart.querySelectorAll('.credit-chart-bar').forEach((bar, index) => {
          animate(bar, [{transform: 'scaleX(0)'}, {transform: 'scaleX(1)'}],
            {duration: 650, delay: Math.min(index * 45, 180), fill: 'backwards'});
        });
      } else {
        animate(chart.querySelector('svg'), [{opacity: 0, transform: 'scale(.96)'}, {opacity: 1, transform: 'none'}], {duration: 650});
      }
    }
  }
  document.addEventListener('workspace:charts-rendered', animateCharts);
  document.addEventListener('workspace:portal-data', event => {
    if (!event.detail) {
      clearTransientFeedback();
      chartRevisions.clear();
      [...activeAnimations].forEach(animation => {
        const target = animation.effect?.target;
        if (!target?.isConnected || target.matches('.chart-trend-line, .chart-point, .chart-point-label, .credit-chart-bar, .distribution-layout > svg')) animation.cancel();
      });
    }
  });
  let lastPanel, bookSettling = false, transitionRevision = 0;
  function navigate(id, initial = false) {
    moveIndicator();
    if (id === lastPanel && !initial) return;
    clearTransientFeedback(); positionBook();
    lastPanel = id;
    const panel = document.getElementById(id);
    if (!panel) return;
    bookSettling = true;
    const revision = ++transitionRevision, transitions = [];
    if (initial) {
      const targets = panel.querySelectorAll('.dashboard-heading, .analytics-toolbar, .analytics-grid > section, .portal-top, .profile-login-layout, .course-mode-controls, .course-status-heading, .reference-heading, .academic-readiness');
      [...targets].filter(node => node.getClientRects().length && node.offsetHeight).slice(0, 5).forEach((node, index) => {
        const entrance = animate(node, [{opacity: 0, transform: 'translateY(10px)'}, {opacity: 1, transform: 'none'}],
          {duration: 420, delay: index * 60, fill: 'backwards'});
        if (entrance) transitions.push(entrance.finished);
      });
    } else {
      const entrance = animate(panel, [{opacity: 0, transform: 'translateY(8px)'}, {opacity: 1, transform: 'none'}], {duration: 220});
      if (entrance) transitions.push(entrance.finished);
    }
    Promise.allSettled(transitions).then(() => {
      if (revision === transitionRevision) { bookSettling = false; positionBook(); }
    });
    animateCharts();
  }
  document.addEventListener('workspace:navigate', event => navigate(event.detail));
  const initialize = () => {
    if (document.body.dataset.authState !== 'workspace') return;
    navigate(document.documentElement.dataset.view || 'tab-dashboard', true);
  };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', initialize, {once: true});
  else initialize();
  let motionAccount;
  document.addEventListener('workspace:account-change', event => {
    const account = event.detail;
    const identity = account ? `${account.account_id}:${account.session_id}` : null;
    if (identity === motionAccount) return;
    motionAccount = identity;
    if (identity) initialize();
    else {
      lastPanel = null; clearTransientFeedback();
      if (book) { book.dataset.visible = 'false'; book.dataset.paused = 'true'; }
    }
  });

  // Native dialog keeps its focus/escape behavior. A close animation never traps it.
  const closing = new WeakSet();
  function closeDialog(dialog) {
    if (!dialog.open || closing.has(dialog)) return;
    closing.add(dialog);
    const animation = animate(dialog, [{opacity: 1, transform: 'none'}, {opacity: 0, transform: 'translateY(6px)'}], {duration: 160});
    const finish = () => { if (dialog.open) dialog.close(); closing.delete(dialog); };
    if (animation) animation.finished.then(finish, finish); else finish();
  }
  window.workspaceMotion = {closeDialog, capturePlan, statusFeedback};
  reduced.addEventListener('change', () => {
    if (reduced.matches) { [...activeAnimations].forEach(animation => animation.cancel()); clearTransientFeedback(); }
  });
  const background = document.querySelector('.ambient-background');
  const updateVisibility = () => {
    background.dataset.paused = String(document.hidden);
    document.documentElement.dataset.motionPaused = String(document.hidden);
    if (document.hidden) clearTransientFeedback();
  };
  document.addEventListener('visibilitychange', updateVisibility); updateVisibility();
  window.addEventListener('pagehide', clearTransientFeedback);
})();
