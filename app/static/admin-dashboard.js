/* Presentation for the authenticated admin dashboard. Data arrives through the
   existing guarded admin requests; this module never fetches or mutates data. */
(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  const state = { overview: null, insights: null, health: null, programs: null };
  const palette = ['#3676d9', '#6c9be8', '#9abdf0', '#bdd4f5', '#5b89c6', '#d3e1f4'];
  let identity = '', sidebarOpen = false;
  const mobile = matchMedia('(max-width: 760px)');
  const en = () => window.workspaceI18n?.language === 'en';
  const text = (vi, english) => en() ? english : vi;
  const html = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const numeric = value => typeof value === 'number' && Number.isFinite(value);
  const fmt = value => numeric(value) ? value.toLocaleString(en() ? 'en-US' : 'vi-VN') : text('Chưa có dữ liệu', 'Unavailable');
  const copy = {
    navigation: ['KHÔNG GIAN QUẢN TRỊ', 'ADMIN WORKSPACE'], administrator: ['Quản trị viên', 'Administrator'],
    adminOnly: ['Không gian quản trị hệ thống', 'System administration'], operations: ['VẬN HÀNH', 'OPERATIONS'],
    activity: ['Hoạt động hệ thống', 'System activity'], trafficScope: ['Lưu lượng API theo nhóm dịch vụ trong phiên chạy hiện tại.', 'API traffic by service group in the current process.'],
    catalogStatus: ['Trạng thái catalog', 'Catalog verification'], catalogSource: ['Theo chương trình đang hoạt động.', 'Active academic programs.'],
    activeSource: ['Nguồn hiện hành', 'Active source'], serviceHealth: ['Trạng thái hệ thống', 'System status'],
    serviceSource: ['Kiểm tra sẵn sàng và trạng thái dữ liệu.', 'Readiness checks and catalog status.'],
    documentReview: ['TÀI LIỆU', 'DOCUMENTS'], documentStatus: ['Kiểm duyệt tài liệu', 'Document review'],
    documentSource: ['Thống kê theo trạng thái tài liệu đã thu thập.', 'Breakdown of collected documents by review status.'],
    documentPill: ['Nguồn tài liệu', 'Document source']
  };
  function empty(message) { return `<p class="ad-empty">${html(message || text('Chưa có dữ liệu để hiển thị.', 'No data to display.'))}</p>`; }
  function readiness() {
    const metric = state.overview?.system_readiness;
    const available = metric?.status === 'available';
    const ready = available && metric.value === 'operational';
    $('ad-readiness-label').textContent = !available ? text('Chưa xác định trạng thái', 'Status unavailable') : ready ? text('Hệ thống sẵn sàng', 'System ready') : text('Hệ thống cần kiểm tra', 'System needs attention');
    const pill = $('ad-readiness-label').closest('.admin-status-pill');
    pill.dataset.readiness = !available ? 'unavailable' : ready ? 'operational' : 'degraded';
  }
  function memberships() {
    const grid = $('admin-overview-grid');
    if (!grid || grid.querySelector('.admin-error-banner') || !grid.querySelector('[data-metric], [data-unavailable]')) return;
    let card = $('ad-membership-card');
    if (!card) { card = document.createElement('article'); card.id = 'ad-membership-card'; card.className = 'admin-kpi-card'; grid.append(card); }
    const result = state.insights?.courses;
    const value = result?.status === 'available' ? result.data?.course_memberships : null;
    card.innerHTML = `<div class="admin-kpi-head"><div class="admin-kpi-icon-wrap" aria-hidden="true"><svg viewBox="0 0 20 20" fill="none"><path d="m10 2 8 4-8 4-8-4zm-8 8 8 4 8-4M2 14l8 4 8-4" stroke="currentColor" stroke-width="1.4"/></svg></div><h4 class="admin-kpi-title">${text('Lượt học phần', 'Program course memberships')}</h4></div><div class="admin-kpi-body"><div class="admin-kpi-value-row"><span class="${numeric(value)?'admin-metric-number':'admin-metric-unavailable'}" data-metric="memberships">${fmt(value)}</span></div><p class="admin-kpi-note">${text('Đếm riêng từng chương trình đào tạo', 'Counted separately in each program')}</p></div><div class="admin-kpi-foot"><span class="admin-source-tag">${text('Nguồn: catalog hiện hành', 'Source: active catalogs')}</span></div>`;
  }
  function renderTraffic() {
    const data = state.health, overall = data?.overall_health;
    const target = $('ad-traffic-chart');
    if (overall?.status !== 'available' || !numeric(overall.total_requests)) {
      target.innerHTML = empty(data ? text('Chưa ghi nhận yêu cầu trong khoảng thời gian này.', 'No requests recorded in this window.') : text('Chưa tải được số liệu hoạt động.', 'Activity data is unavailable.'));
      return;
    }
    const labels = [text('Học vụ','Academic'), text('VNU','VNU'), text('Xác thực','Auth'), text('Tư vấn','Advisor'), text('Quản trị','Admin'), text('Khác','Other')];
    const keys = ['academic','portal','auth','consultation','admin','other'];
    const groups = keys.map((key,i) => ({label:labels[i], value:data.route_groups?.[key]?.status === 'available' && numeric(data.route_groups[key].total_requests) ? data.route_groups[key].total_requests : null}));
    const maximum = Math.max(1, ...groups.map(g => g.value || 0));
    const chart = groups.some(g => g.value !== null) ? `<div class="ad-column-chart" role="list" aria-label="${text('Số yêu cầu theo nhóm dịch vụ','Requests by service group')}">${groups.map((group,i) => `<div class="ad-column" role="listitem"><div class="ad-column-track"><div class="ad-column-fill" style="--ad-bar-height:${group.value === null ? 0 : group.value / maximum * 100}%;--ad-bar-color:${palette[i]}"><span>${group.value === null ? '—' : fmt(group.value)}</span></div></div><span class="ad-column-label">${html(group.label)}</span><span class="sr-only">: ${group.value === null ? text('chưa ghi nhận', 'not recorded') : fmt(group.value)}</span></div>`).join('')}</div>` : empty(text('Chưa có phân bố theo nhóm dịch vụ.', 'Service group distribution is unavailable.'));
    target.innerHTML = `<div class="ad-traffic-total"><strong>${fmt(overall.total_requests)}</strong><span>${text('yêu cầu API được ghi nhận','recorded API requests')}</span><span class="ad-source-pill">${html(data.window || '')}</span></div>${chart}<div class="ad-chart-footer"><span><i></i>${text('Yêu cầu API theo nhóm dịch vụ','API requests by service group')}</span><span>${text('Phiên chạy hiện tại','Current process')}</span></div>`;
  }
  function renderCatalog() {
    const metric = state.overview?.document_review_status;
    let total = 0, approved = 0, pending = 0, rejected = 0;
    if (metric?.status === 'available' && metric.details) {
      total = Number(metric.details.total) || 0;
      approved = Number(metric.details.approved) || 0;
      pending = Number(metric.details.pending) || 0;
      rejected = Number(metric.details.rejected) || 0;
    } else if (metric?.status === 'available' && numeric(metric.value)) {
      total = metric.value;
    } else {
      $('ad-catalog-chart').innerHTML = empty(text('Chưa có số liệu kiểm duyệt tài liệu.', 'Document review metrics unavailable.'));
      return;
    }

    if (!total && !approved && !pending && !rejected) {
      $('ad-catalog-chart').innerHTML = empty(text('Chưa có tài liệu nào trong hệ thống.', 'No documents in the system.'));
      return;
    }

    const circumference = 389.56;
    const sum = total || (approved + pending + rejected) || 1;
    const segApproved = (approved / sum) * circumference;
    const segPending = (pending / sum) * circumference;
    const segRejected = (rejected / sum) * circumference;

    const offsetApproved = 0;
    const offsetPending = -segApproved;
    const offsetRejected = -(segApproved + segPending);

    $('ad-catalog-chart').innerHTML = `<div class="ad-donut-wrap"><svg viewBox="0 0 160 160" role="img" aria-label="${text('Thống kê kiểm duyệt tài liệu: ', 'Document review statistics: ')}${approved} ${text('đã duyệt', 'approved')}, ${pending} ${text('chờ duyệt', 'pending')}, ${rejected} ${text('từ chối', 'rejected')}"><circle cx="80" cy="80" r="62" fill="none" stroke="var(--ad-chart-track)" stroke-width="16"/>${approved ? `<circle cx="80" cy="80" r="62" fill="none" stroke="#10b981" stroke-width="16" stroke-dasharray="${segApproved} ${circumference - segApproved}" stroke-dashoffset="${offsetApproved}" transform="rotate(-90 80 80)"/>` : ''}${pending ? `<circle cx="80" cy="80" r="62" fill="none" stroke="#f59e0b" stroke-width="16" stroke-dasharray="${segPending} ${circumference - segPending}" stroke-dashoffset="${offsetPending}" transform="rotate(-90 80 80)"/>` : ''}${rejected ? `<circle cx="80" cy="80" r="62" fill="none" stroke="#ef4444" stroke-width="16" stroke-dasharray="${segRejected} ${circumference - segRejected}" stroke-dashoffset="${offsetRejected}" transform="rotate(-90 80 80)"/>` : ''}</svg><div><strong>${fmt(total)}</strong><span>${text('tài liệu đã thu thập', 'collected documents')}</span></div></div><div class="ad-verification-legend"><span><i style="background:#10b981"></i>${text('Đã duyệt', 'Approved')}<strong>${fmt(approved)}</strong></span><span><i style="background:#f59e0b"></i>${text('Chờ duyệt', 'Pending')}<strong>${fmt(pending)}</strong></span><span><i style="background:#ef4444"></i>${text('Từ chối', 'Rejected')}<strong>${fmt(rejected)}</strong></span></div><p class="ad-chart-note">${text('Thống kê kiểm duyệt tài liệu từ hệ thống thu thập.', 'Document review statistics from crawler subsystem.')}</p>`;
  }
  function renderStudentChart() {
    const target = $('admin-student-insights');
    target?.querySelector('.ad-student-visual')?.remove();
    const result = state.insights?.students;
    if (!target || result?.status !== 'available') return;
    const groups = (result.data?.by_program || []).filter(g => numeric(g.count) && g.count >= 0);
    const total = groups.reduce((sum,g) => sum + g.count, 0);
    if (!total) return;
    const visual = document.createElement('div'); visual.className = 'ad-student-visual';
    visual.innerHTML = `<div class="ad-stacked-bar" role="img" aria-label="${html(groups.map(g=>`${g.label}: ${g.count}`).join('; '))}">${groups.map((g,i)=>`<span style="width:${g.count/total*100}%;background:${palette[i%palette.length]}"></span>`).join('')}</div><div class="ad-student-legend">${groups.map((g,i)=>`<span><i style="background:${palette[i%palette.length]}"></i>${html(g.label)}<strong>${fmt(g.count)}</strong></span>`).join('')}</div>`;
    target.prepend(visual);
  }
  function render() {
    if (window.systemAuth?.account?.role !== 'admin') return;
    readiness(); memberships(); renderTraffic(); renderCatalog();
    document.querySelectorAll('[data-ad-copy]').forEach(node => { const pair = copy[node.dataset.adCopy]; if (pair) node.textContent = pair[en()?1:0]; });
  }
  function update(kind, data) {
    if (!(kind in state) || window.systemAuth?.account?.role !== 'admin') return;
    state[kind] = data;
    render();
    // Insights are rendered by admin.js after this hook; decorate the resulting DOM.
    if (kind === 'insights') queueMicrotask(renderStudentChart);
  }
  function setSidebar(open, restoreFocus = false) {
    sidebarOpen = open;
    $('admin-sidebar').classList.toggle('ad-open', open);
    $('admin-sidebar').inert = mobile.matches && !open;
    $('admin-sidebar-shade').hidden = !open || !mobile.matches;
    $('admin-sidebar-toggle').setAttribute('aria-expanded', String(open));
    if (restoreFocus && mobile.matches) $('admin-sidebar-toggle').focus();
  }
  $('admin-sidebar-toggle')?.addEventListener('click', () => { setSidebar(!sidebarOpen); if (sidebarOpen) document.querySelector('.admin-tab-btn[aria-selected="true"]')?.focus(); });
  $('admin-sidebar-shade')?.addEventListener('click', () => setSidebar(false,true));
  mobile.addEventListener('change', () => setSidebar(false));
  document.addEventListener('keydown', event => { if (event.key === 'Escape' && sidebarOpen) setSidebar(false,true); });
  $('admin-sidebar').addEventListener('keydown', event => {
    if (event.key !== 'Tab' || !mobile.matches || !sidebarOpen) return;
    const focusable = [...$('admin-sidebar').querySelectorAll('a,button:not([tabindex="-1"])')];
    const first=focusable[0], last=focusable.at(-1);
    if (event.shiftKey && document.activeElement===first) { event.preventDefault();last?.focus(); }
    else if (!event.shiftKey && document.activeElement===last) { event.preventDefault();first?.focus(); }
  });
  document.addEventListener('click', event => {
    const button = event.target.closest('[data-ad-tab],[data-ad-program],.admin-tab-btn,.ad-brand');
    if (!button) return;
    if (button.dataset.adTab) window.systemAuth?.switchAdminTab(button.dataset.adTab);
    if (button.dataset.adProgram) {
      const program=state.programs?.find(p=>p.program_id===button.dataset.adProgram);
      if(program){window.systemAuth?.switchAdminTab('curriculum');window.adminCurriculum?.openProgramCourses(program);}
    }
    if(button.classList.contains('ad-brand')){event.preventDefault();window.systemAuth?.switchAdminTab('overview');window.scrollTo(0,0);}
    setSidebar(false);
    if(mobile.matches) $('admin-heading')?.focus({preventScroll:true});
  });
  document.addEventListener('workspace:account-change',event=>{
    const account=event.detail;
    const next=account?JSON.stringify([account.account_id,account.session_id,account.role,account.auth_version]):'';
    if(next===identity)return;
    identity=next;
    Object.keys(state).forEach(key=>{state[key]=null;});
    ['ad-traffic-chart','ad-catalog-chart','ad-status-cards'].forEach(id=>$(id)?.replaceChildren());
    setSidebar(false);
    readiness();
  });
  document.addEventListener('workspace:language-change',()=>{render();queueMicrotask(renderStudentChart);});
  setSidebar(false);
  window.adminDashboard = { update };
})();
