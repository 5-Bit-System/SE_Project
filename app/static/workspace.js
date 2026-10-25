/* VNU-only workspace. Legacy manual-input clients are no longer loaded. */
(() => {
  'use strict';
  const buttons = [...document.querySelectorAll('.tab-btn')];
  const languageButtons = [...document.querySelectorAll('[data-language-choice]')];
  const copy = (vi, en) => window.workspaceI18n.language === 'en' ? en : vi;
  let authenticated = false, reasons = [], status = 'signed-out';
  let sourceProgram = null, sourceCohort = null;

  function renderProfile() {
    document.getElementById('workspace-program-label').textContent = copy('Ngành học', 'Program');
    document.getElementById('workspace-cohort-label').textContent = copy('Khóa học', 'Cohort');
    const empty = authenticated ? copy('Chưa có thông tin', 'Unavailable') : copy('Chưa kết nối VNU', 'Not connected to VNU');
    document.getElementById('workspace-program').textContent = sourceProgram || empty;
    document.getElementById('workspace-cohort').textContent = sourceCohort || empty;
    // Source labels are display information, not a reviewed catalog binding.
    document.getElementById('catalog-name-text').textContent = sourceProgram || copy('Hồ sơ học tập VNU', 'VNU academic profile');
  }

  function renderStatus() {
    const messages = {
      source_incomplete: copy('Chưa xác minh bảng điểm đã được lấy đầy đủ.', 'Transcript completeness has not been verified.'),
      program_binding_unverified: copy('Chưa xác minh chương trình áp dụng cho hồ sơ VNU.', 'The applicable program has not been verified for this VNU profile.'),
      policy_not_applicable: copy('Chưa xác minh quy chế học vụ áp dụng.', 'The applicable academic policy has not been verified.')
    };
    document.querySelectorAll('[data-academic-status]').forEach(node => {
      node.replaceChildren();
      const text = document.createElement('p');
      text.textContent = status === 'signed-out'
        ? copy('Đăng nhập VNU để kiểm tra dữ liệu học tập của bạn.', 'Sign in with VNU to check your academic data.')
        : copy('Tính năng này đang chờ hoàn tất chuyển đổi sang bảng điểm VNU.', 'This feature is awaiting completion of the VNU transcript integration.');
      node.append(text);
      if (status === 'blocked') {
        const list = document.createElement('ul');
        [...new Set(reasons.map(reason => messages[reason] || copy('Một phần dữ liệu nguồn cần được kiểm tra thêm.', 'Some source data requires further review.')))].forEach(message => {
          const item = document.createElement('li'); item.textContent = message; list.append(item);
        });
        node.append(list);
      }
    });
  }

  window.workspaceNavigate = target => {
    if (target === 'tab-transcript') target = 'portal-dialog';
    const selected = buttons.find(button => button.dataset.tab === target) || buttons[0];
    buttons.forEach(button => {
      const active = button === selected;
      button.classList.toggle('active', active); button.setAttribute('aria-selected', String(active));
      button.tabIndex = active ? 0 : -1;
    });
    document.querySelectorAll('.tab-panel').forEach(panel => panel.classList.toggle('active', panel.id === selected.dataset.tab));
    document.documentElement.dataset.view = selected.dataset.tab;
    const route = selected.dataset.tab === 'portal-dialog' ? 'profile' : selected.dataset.tab.replace('tab-', '');
    if (location.hash !== `#${route}`) history.pushState(null, '', `#${route}`);
    document.getElementById('workspace-heading').textContent = selected.querySelector('.tab-label').firstChild.textContent;
    document.dispatchEvent(new CustomEvent('workspace:navigate', {detail: selected.dataset.tab}));
  };
  buttons.forEach((button, index) => {
    button.addEventListener('click', () => window.workspaceNavigate(button.dataset.tab));
    button.addEventListener('keydown', event => {
      const offset = {ArrowDown: 1, ArrowRight: 1, ArrowUp: -1, ArrowLeft: -1}[event.key];
      const next = event.key === 'Home' ? 0 : event.key === 'End' ? buttons.length - 1
        : offset ? (index + offset + buttons.length) % buttons.length : null;
      if (next === null) return;
      event.preventDefault(); buttons[next].focus(); buttons[next].click();
    });
  });
  document.querySelectorAll('[data-navigate]').forEach(button => button.addEventListener('click', () => window.workspaceNavigate(button.dataset.navigate)));
  function restoreRoute() {
    const route = location.hash.slice(1);
    if (route === 'transcript') history.replaceState(null, '', '#profile');
    window.workspaceNavigate(['profile', 'transcript'].includes(route) ? 'portal-dialog' : `tab-${route || 'dashboard'}`);
  }
  window.addEventListener('popstate', restoreRoute);
  window.addEventListener('hashchange', restoreRoute);
  function renderLanguage() {
    languageButtons.forEach(button => button.setAttribute('aria-pressed', String(button.dataset.languageChoice === window.workspaceI18n.language)));
  }
  languageButtons.forEach(button => button.addEventListener('click', () => {
    window.workspaceI18n.setLanguage(button.dataset.languageChoice);
    renderLanguage(); renderProfile(); renderStatus();
    document.dispatchEvent(new CustomEvent('workspace:language-change'));
  }));
  renderLanguage();
  document.addEventListener('workspace:portal-data', event => {
    const source = event.detail;
    authenticated = Boolean(source);
    const value = text => typeof text === 'string' && text.trim() ? text : null;
    sourceProgram = value(source?.profile?.program);
    sourceCohort = value(source?.profile?.cohort);
    // No default program selection or name-to-catalog guess. Academic output
    // stays gated until a server-reviewed binding is available.
    reasons = authenticated ? ['program_binding_unverified'] : [];
    if (authenticated && source.snapshot?.completeness !== 'complete') reasons.unshift('source_incomplete');
    status = authenticated ? 'blocked' : 'signed-out';
    renderProfile(); renderStatus();
  });
  restoreRoute(); renderProfile(); renderStatus();
})();
