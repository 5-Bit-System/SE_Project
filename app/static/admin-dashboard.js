/* Presentation for the authenticated admin dashboard. Data arrives through the
   existing guarded admin requests; this module never fetches or mutates data. */
(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  const state = { overview: null, insights: null, health: null, programs: null };
  const palette = ['#3676d9', '#6c9be8', '#9abdf0', '#bdd4f5', '#5b89c6', '#d3e1f4'];
  let identity = '', filter = 'all', sidebarOpen = false;
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
    serviceSource: ['Kiểm tra sẵn sàng và trạng thái dữ liệu.', 'Readiness checks and catalog status.'], training: ['ĐÀO TẠO', 'ACADEMICS'],
    programs: ['Chương trình đào tạo', 'Academic programs'], programDescription: ['Danh mục hiện hành theo ngành và khóa tuyển sinh.', 'Active catalogs by program and admission year.'],
    managePrograms: ['Quản lý chương trình ↗', 'Manage programs ↗'], all: ['Tất cả', 'All'], verified: ['Đã xác minh', 'Verified'],
    draft: ['Bản nháp', 'Draft'], searchPrograms: ['Tìm chương trình', 'Search programs']
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
    const metric = state.overview?.catalog_status;
    const values = metric?.status === 'available' && metric.details?.statuses ? Object.values(metric.details.statuses) : Array.isArray(state.programs) ? state.programs.map(p => p.catalog_status) : null;
    if (!values?.length) { $('ad-catalog-chart').innerHTML = empty(); return; }
    const verified = values.filter(value => value === 'verified').length;
    const draft = values.filter(value => value === 'draft_unverified').length;
    const unknown = values.length - verified - draft;
    const circumference = 389.56, segment = verified / values.length * circumference;
    $('ad-catalog-chart').innerHTML = `<div class="ad-donut-wrap"><svg viewBox="0 0 160 160" role="img" aria-label="${verified} / ${values.length} ${text('chương trình đã xác minh cấp dự án','programs verified at project level')}"><circle cx="80" cy="80" r="62" fill="none" stroke="var(--ad-chart-track)" stroke-width="16"/>${verified ? `<circle cx="80" cy="80" r="62" fill="none" stroke="var(--ad-blue)" stroke-width="16" stroke-dasharray="${segment} ${circumference-segment}" transform="rotate(-90 80 80)"/>` : ''}</svg><div><strong>${verified}<small> / ${values.length}</small></strong><span>${text('chương trình đã xác minh','verified programs')}</span></div></div><div class="ad-verification-legend"><span><i></i>${text('Đã xác minh cấp dự án','Project verification')}<strong>${verified}</strong></span><span><i class="ad-draft-dot"></i>${text('Bản nháp, cần đối chiếu','Draft, pending review')}<strong>${draft}</strong></span>${unknown?`<span>${text('Chưa rõ trạng thái','Unknown status')}<strong>${unknown}</strong></span>`:''}</div><p class="ad-chart-note">${text('Xác nhận trong phạm vi dự án; không thay thế xác nhận học vụ của nhà trường.', 'Project-level review does not replace official institutional verification.')}</p>`;
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
  function renderPrograms() {
    const target = $('ad-program-table');
    if (!Array.isArray(state.programs)) { target.innerHTML = empty(text('Chưa tải được danh mục chương trình. Chọn Làm mới để thử lại.', 'Programs are unavailable. Refresh to retry.')); return; }
    const query = ($('ad-program-search')?.value || '').trim().toLocaleLowerCase();
    const programs = state.programs.filter(p => (filter === 'all' || p.catalog_status === filter) && `${p.name} ${p.program_id} ${p.cohort || ''}`.toLocaleLowerCase().includes(query));
    const headers = [text('Chương trình','Program'),text('Khóa','Cohort'),text('Tín chỉ','Credits'),text('Học phần','Courses'),text('Trạng thái','Status'),text('Chi tiết','Details')];
    target.innerHTML = `<div class="ad-table-scroll"><table class="ad-program-table"><thead><tr>${headers.map(h=>`<th scope="col">${h}</th>`).join('')}</tr></thead><tbody>${programs.length?programs.map(p=>`<tr><td><strong>${html(p.name)}</strong><small>${html(p.program_id)}</small></td><td>${html(p.cohort || '—')}</td><td>${fmt(p.total_credits)}</td><td>${fmt(p.course_count)}</td><td><span class="ad-program-status ${p.catalog_status==='verified'?'ad-verified':'ad-draft'}">${p.catalog_status==='verified'?text('Đã xác minh','Verified'):p.catalog_status==='draft_unverified'?text('Bản nháp','Draft'):text('Chưa xác định','Unknown')}</span></td><td><button type="button" data-ad-program="${html(p.program_id)}" class="ad-text-button" aria-label="${html(text('Xem học phần: ','View courses: ')+p.name)}">${text('Xem học phần ↗','View courses ↗')}</button></td></tr>`).join(''):`<tr><td colspan="6">${text('Không có chương trình phù hợp.','No matching programs.')}</td></tr>`}</tbody></table></div><p class="ad-table-note">${programs.length} / ${state.programs.length} ${text('chương trình · Nguồn catalog hiện hành','programs · Active catalogs')}</p>`;
  }
  function render() {
    if (window.systemAuth?.account?.role !== 'admin') return;
    readiness(); memberships(); renderTraffic(); renderCatalog(); renderPrograms();
    document.querySelectorAll('[data-ad-copy]').forEach(node => { const pair = copy[node.dataset.adCopy]; if (pair) node.textContent = pair[en()?1:0]; });
    $('ad-program-search').placeholder = text('Tìm chương trình, mã ngành, khóa…','Search program, code or cohort…');
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
    const button = event.target.closest('[data-ad-tab],[data-ad-program],[data-ad-filter],.admin-tab-btn,.ad-brand');
    if (!button) return;
    if (button.dataset.adFilter) {
      filter=button.dataset.adFilter;
      document.querySelectorAll('[data-ad-filter]').forEach(node=>{const active=node.dataset.adFilter===filter;node.classList.toggle('active',active);node.setAttribute('aria-pressed',String(active));});
      renderPrograms(); return;
    }
    if (button.dataset.adTab) window.systemAuth?.switchAdminTab(button.dataset.adTab);
    if (button.dataset.adProgram) {
      const program=state.programs?.find(p=>p.program_id===button.dataset.adProgram);
      if(program){window.systemAuth?.switchAdminTab('curriculum');window.adminCurriculum?.openProgramCourses(program);}
    }
    if(button.classList.contains('ad-brand')){event.preventDefault();window.systemAuth?.switchAdminTab('overview');window.scrollTo(0,0);}
    setSidebar(false);
    if(mobile.matches) $('admin-heading')?.focus({preventScroll:true});
  });
  $('ad-program-search')?.addEventListener('input',renderPrograms);
  document.addEventListener('workspace:account-change',event=>{
    const account=event.detail;
    const next=account?JSON.stringify([account.account_id,account.session_id,account.role,account.auth_version]):'';
    if(next===identity)return;
    identity=next;
    Object.keys(state).forEach(key=>{state[key]=null;});
    filter='all';$('ad-program-search').value='';
    document.querySelectorAll('[data-ad-filter]').forEach(node=>{const active=node.dataset.adFilter==='all';node.classList.toggle('active',active);node.setAttribute('aria-pressed',String(active));});
    ['ad-traffic-chart','ad-catalog-chart','ad-program-table','ad-status-cards'].forEach(id=>$(id)?.replaceChildren());
    setSidebar(false);
    readiness();
  });
  document.addEventListener('workspace:language-change',()=>{render();queueMicrotask(renderStudentChart);});
  setSidebar(false);
  window.adminDashboard = { update };
})();
