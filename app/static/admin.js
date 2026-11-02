/* HUS Admin Console UI Module: Overview Dashboard and Sourced Metrics. */
(() => {
  'use strict';

  const $ = id => document.getElementById(id);

  let overviewData = null;
  let isFetching = false;

  const copy = {
    vi: {
      adminAccounts: 'Tài khoản người dùng',
      adminPrograms: 'Chương trình đào tạo',
      adminCourses: 'Học phần trong danh mục',
      adminCatalogStatus: 'Trạng thái danh mục',
      adminReadiness: 'Vận hành hệ thống',
      adminDraftUnverified: 'Bản thảo chưa kiểm định',
      adminVerified: 'Đã kiểm định',
      adminOperational: 'Sẵn sàng vận hành',
      adminDegraded: 'Cần kiểm tra',
      adminUnavailable: 'Không khả dụng',
      adminSourcePrefix: 'Nguồn: ',
      adminJustNow: 'Vừa cập nhật',
      adminDraftNotice: 'Bản thảo tham khảo nội bộ, chưa qua kiểm định chính thức.',
      adminRetry: 'Thử lại',
      adminRefresh: 'Làm mới',
      adminLoadError: 'Không thể tải chỉ số tổng quan. Vui lòng thử lại.'
    },
    en: {
      adminAccounts: 'User Accounts',
      adminPrograms: 'Academic Programs',
      adminCourses: 'Courses in Catalog',
      adminCatalogStatus: 'Catalog Status',
      adminReadiness: 'System Health',
      adminDraftUnverified: 'Draft (Unverified)',
      adminVerified: 'Verified',
      adminOperational: 'Operational',
      adminDegraded: 'Degraded',
      adminUnavailable: 'Unavailable',
      adminSourcePrefix: 'Source: ',
      adminJustNow: 'Just now',
      adminDraftNotice: 'Internal reference draft, not officially approved.',
      adminRetry: 'Retry',
      adminRefresh: 'Refresh',
      adminLoadError: 'Unable to load overview metrics. Please try again.'
    }
  };

  function getCopy(key) {
    const lang = window.workspaceI18n?.language === 'en' ? 'en' : 'vi';
    return copy[lang][key] || copy.vi[key] || key;
  }

  function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  function sanitizeUrl(rawUrl) {
    if (!rawUrl || typeof rawUrl !== 'string') return '';
    const trimmed = rawUrl.trim();
    try {
      const parsed = new URL(trimmed, window.location.origin);
      if (parsed.protocol === 'http:' || parsed.protocol === 'https:') {
        return trimmed;
      }
    } catch (e) {
      if (trimmed.startsWith('/') && !trimmed.startsWith('//')) {
        return trimmed;
      }
    }
    return '';
  }

  function renderSkeletons() {
    const grid = $('admin-overview-grid');
    if (!grid) return;
    grid.innerHTML = `
      <div class="admin-card-skeleton admin-kpi-card" aria-hidden="true">
        <div class="admin-skeleton-line short"></div>
        <div class="admin-skeleton-num"></div>
        <div class="admin-skeleton-line"></div>
      </div>
      <div class="admin-card-skeleton admin-kpi-card" aria-hidden="true">
        <div class="admin-skeleton-line short"></div>
        <div class="admin-skeleton-num"></div>
        <div class="admin-skeleton-line"></div>
      </div>
      <div class="admin-card-skeleton admin-kpi-card" aria-hidden="true">
        <div class="admin-skeleton-line short"></div>
        <div class="admin-skeleton-num"></div>
        <div class="admin-skeleton-line"></div>
      </div>
      <div class="admin-card-skeleton admin-kpi-card" aria-hidden="true">
        <div class="admin-skeleton-line short"></div>
        <div class="admin-skeleton-num"></div>
        <div class="admin-skeleton-line"></div>
      </div>
      <div class="admin-card-skeleton admin-kpi-card" aria-hidden="true">
        <div class="admin-skeleton-line short"></div>
        <div class="admin-skeleton-num"></div>
        <div class="admin-skeleton-line"></div>
      </div>
    `;
  }

  function createCard(title, iconSvg, valueHtml, noteHtml, sourceText, isWarning = false) {
    const card = document.createElement('article');
    card.className = 'admin-kpi-card' + (isWarning ? ' is-warning' : '');

    card.innerHTML = `
      <div class="admin-kpi-head">
        <div class="admin-kpi-icon-wrap" aria-hidden="true">${iconSvg}</div>
        <h4 class="admin-kpi-title">${title}</h4>
      </div>
      <div class="admin-kpi-body">
        <div class="admin-kpi-value-row">${valueHtml}</div>
        ${noteHtml ? `<p class="admin-kpi-note">${noteHtml}</p>` : ''}
      </div>
      <div class="admin-kpi-foot">
        <span class="admin-source-tag">${getCopy('adminSourcePrefix')}${sourceText}</span>
        <span class="admin-time-tag">${getCopy('adminJustNow')}</span>
      </div>
    `;
    return card;
  }

  function renderOverview(data) {
    const grid = $('admin-overview-grid');
    if (!grid) return;
    grid.replaceChildren();

    // 1. Accounts card
    const acc = data.accounts_total;
    const accVal = (acc?.status === 'available' && acc.value !== null)
      ? `<span class="admin-metric-number" data-metric="accounts">${Number(acc.value).toLocaleString()}</span>`
      : `<span class="admin-metric-unavailable" data-unavailable="true">${getCopy('adminUnavailable')}</span>`;
    const accCard = createCard(
      getCopy('adminAccounts'),
      `<svg viewBox="0 0 20 20" fill="none"><circle cx="10" cy="6" r="3.2" stroke="currentColor" stroke-width="1.5"/><path d="M4 16.5c0-3.3 2.7-5.5 6-5.5s6 2.2 6 5.5" stroke="currentColor" stroke-width="1.5"/></svg>`,
      accVal,
      null,
      acc?.source || 'postgres:accounts'
    );
    grid.append(accCard);

    // 2. Programs card
    const prog = data.programs_count;
    const progVal = (prog?.status === 'available' && prog.value !== null)
      ? `<span class="admin-metric-number" data-metric="programs">${Number(prog.value).toLocaleString()}</span>`
      : `<span class="admin-metric-unavailable" data-unavailable="true">${getCopy('adminUnavailable')}</span>`;
    const progCard = createCard(
      getCopy('adminPrograms'),
      `<svg viewBox="0 0 20 20" fill="none"><path d="M3 5.5 10 2l7 3.5-7 3.5-7-3.5Z" stroke="currentColor" stroke-width="1.5"/><path d="M6 7.5v5.5c0 1.5 1.8 3 4 3s4-1.5 4-3V7.5" stroke="currentColor" stroke-width="1.5"/></svg>`,
      progVal,
      null,
      prog?.source || 'catalog:active'
    );
    grid.append(progCard);

    // 3. Courses card
    const crs = data.courses_count;
    const crsVal = (crs?.status === 'available' && crs.value !== null)
      ? `<span class="admin-metric-number" data-metric="courses">${Number(crs.value).toLocaleString()}</span>`
      : `<span class="admin-metric-unavailable" data-unavailable="true">${getCopy('adminUnavailable')}</span>`;
    const crsCard = createCard(
      getCopy('adminCourses'),
      `<svg viewBox="0 0 20 20" fill="none"><rect x="3.5" y="3.5" width="13" height="13" rx="2" stroke="currentColor" stroke-width="1.5"/><path d="M7 7h6M7 10h6M7 13h4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>`,
      crsVal,
      null,
      crs?.source || 'catalog:active'
    );
    grid.append(crsCard);

    // 4. Catalog Verification Status card (Truthful indicator: draft_unverified)
    const cat = data.catalog_status;
    let catVal = '';
    let isWarning = false;
    if (cat?.status === 'available' && cat.value) {
      if (cat.value === 'draft_unverified') {
        isWarning = true;
        catVal = `
          <span class="admin-status-badge badge-warning" data-catalog-status="draft_unverified">
            <svg viewBox="0 0 16 16" fill="none" class="badge-icon"><path d="M8 2.5 14 13H2L8 2.5Z" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/><path d="M8 6.5v3M8 11.5v.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>
            ${getCopy('adminDraftUnverified')}
          </span>
        `;
      } else {
        catVal = `
          <span class="admin-status-badge badge-success" data-catalog-status="verified">
            <svg viewBox="0 0 16 16" fill="none" class="badge-icon"><path d="m3.5 8 3 3 6-6" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg>
            ${getCopy('adminVerified')}
          </span>
        `;
      }
    } else {
      catVal = `<span class="admin-metric-unavailable" data-unavailable="true">${getCopy('adminUnavailable')}</span>`;
    }
    const catCard = createCard(
      getCopy('adminCatalogStatus'),
      `<svg viewBox="0 0 20 20" fill="none"><path d="M10 2.5 16 5v4.5c0 3.8-2.6 6.8-6 8-3.4-1.2-6-4.2-6-8V5l6-2.5Z" stroke="currentColor" stroke-width="1.5"/><path d="m7.5 9.5 1.8 1.8 3.5-3.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>`,
      catVal,
      isWarning ? getCopy('adminDraftNotice') : null,
      cat?.source || 'catalog:verification_state',
      isWarning
    );
    grid.append(catCard);

    // 5. System Readiness card
    const rdy = data.system_readiness;
    let rdyVal = '';
    if (rdy?.status === 'available' && rdy.value) {
      if (rdy.value === 'operational') {
        rdyVal = `
          <span class="admin-status-badge badge-success" data-readiness="operational">
            <span class="admin-pulse-dot" aria-hidden="true"></span>
            ${getCopy('adminOperational')}
          </span>
        `;
      } else {
        rdyVal = `
          <span class="admin-status-badge badge-warning" data-readiness="degraded">
            ${getCopy('adminDegraded')}
          </span>
        `;
      }
    } else {
      rdyVal = `<span class="admin-metric-unavailable" data-unavailable="true">${getCopy('adminUnavailable')}</span>`;
    }
    const rdyCard = createCard(
      getCopy('adminReadiness'),
      `<svg viewBox="0 0 20 20" fill="none"><circle cx="10" cy="10" r="7" stroke="currentColor" stroke-width="1.5"/><path d="M10 6v4l2.5 2.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>`,
      rdyVal,
      rdy?.details?.storage_backend ? `Backend: ${rdy.details.storage_backend}` : null,
      rdy?.source || 'system:readiness_checks'
    );
    grid.append(rdyCard);
  }

  function renderError(message) {
    const grid = $('admin-overview-grid');
    if (!grid) return;
    grid.innerHTML = `
      <div class="admin-error-banner" role="alert">
        <svg viewBox="0 0 20 20" fill="none" class="admin-error-icon" aria-hidden="true">
          <circle cx="10" cy="10" r="8" stroke="currentColor" stroke-width="1.6"/>
          <path d="M10 6.5v4M10 13.5v.5" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>
        </svg>
        <div class="admin-error-text">
          <p><strong>${getCopy('adminLoadError')}</strong></p>
          <p class="admin-error-sub">${message || ''}</p>
        </div>
        <button type="button" id="admin-overview-retry" class="portal-button primary-action">
          ${getCopy('adminRetry')}
        </button>
      </div>
    `;
    const retryBtn = $('admin-overview-retry');
    if (retryBtn) retryBtn.onclick = () => loadOverview(true);
  }

  async function loadOverview(force = false) {
    if (isFetching) return;
    if (overviewData && !force) {
      renderOverview(overviewData);
      return;
    }
    isFetching = true;
    renderSkeletons();
    const refreshBtn = $('admin-overview-refresh');
    if (refreshBtn) refreshBtn.disabled = true;

    try {
      if (!window.systemAuth?.request) throw new Error('systemAuth not available');
      const data = await window.systemAuth.request('/admin/overview');
      overviewData = data;
      renderOverview(data);
      loadOperationalHealth();
    } catch (err) {
      renderError(err.message || 'Error loading overview');
    } finally {
      isFetching = false;
      if (refreshBtn) refreshBtn.disabled = false;
    }
  }

  // Bind refresh button
  document.addEventListener('DOMContentLoaded', () => {
    const refreshBtn = $('admin-overview-refresh');
    if (refreshBtn) refreshBtn.onclick = () => loadOverview(true);
  });
  const refreshBtn = $('admin-overview-refresh');
  if (refreshBtn) refreshBtn.onclick = () => loadOverview(true);

  // ==========================================================================
  // Curriculum Catalog Views
  // ==========================================================================
  let curriculumPrograms = [];
  let currentProgramCourses = [];
  let activeProgram = null;

  async function loadCurriculum() {
    try {
      if (!window.systemAuth?.request) return;
      const data = await window.systemAuth.request('/admin/programs');
      curriculumPrograms = data || [];
      renderPrograms();
    } catch (err) {
      console.error('Failed to load curriculum programs:', err);
    }
  }

  function renderPrograms() {
    const tbody = $('admin-programs-tbody');
    if (!tbody) return;
    tbody.replaceChildren();

    const searchQuery = ($('admin-curriculum-search')?.value || '').trim().toLowerCase();
    const statusFilter = $('admin-curriculum-status-filter')?.value || 'all';

    const filtered = curriculumPrograms.filter(prog => {
      const matchSearch = !searchQuery ||
        prog.name.toLowerCase().includes(searchQuery) ||
        prog.program_id.toLowerCase().includes(searchQuery) ||
        (prog.cohort && prog.cohort.toLowerCase().includes(searchQuery));
      const matchStatus = statusFilter === 'all' || prog.catalog_status === statusFilter;
      return matchSearch && matchStatus;
    });

    if (filtered.length === 0) {
      const tr = tbody.insertRow();
      const td = tr.insertCell();
      td.colSpan = 8;
      td.className = 'admin-empty-state';
      td.textContent = 'Không tìm thấy chương trình đào tạo phù hợp.';
      return;
    }

    filtered.forEach(p => {
      const tr = tbody.insertRow();
      tr.dataset.programId = p.program_id;

      // 1. Program ID
      const tdId = tr.insertCell();
      const codeId = document.createElement('code');
      codeId.className = 'admin-course-code';
      codeId.textContent = p.program_id;
      tdId.appendChild(codeId);

      // 2. Name
      const tdName = tr.insertCell();
      const strongName = document.createElement('strong');
      strongName.textContent = p.name;
      tdName.appendChild(strongName);

      // 3. Cohort / Year
      const tdCohort = tr.insertCell();
      tdCohort.textContent = p.cohort || '—';

      // 4. Credits
      const tdCredits = tr.insertCell();
      tdCredits.className = 'tabular-nums';
      tdCredits.textContent = p.total_credits;

      // 5. Courses count
      const tdCourses = tr.insertCell();
      tdCourses.className = 'tabular-nums';
      tdCourses.textContent = p.course_count;

      // 6. Status
      const tdStatus = tr.insertCell();
      if (p.catalog_status === 'draft_unverified') {
        tdStatus.innerHTML = `<span class="admin-status-badge badge-warning">${getCopy('adminDraftUnverified')}</span>`;
      } else {
        tdStatus.innerHTML = `<span class="admin-status-badge badge-success">${getCopy('adminVerified')}</span>`;
      }

      // 7. Source
      const tdSource = tr.insertCell();
      tdSource.className = 'admin-sub-text';
      tdSource.title = p.source_file;
      tdSource.textContent = p.source_file ? (p.source_file.split('/').pop() || p.source_file) : '—';

      // 8. Actions
      const tdAction = tr.insertCell();
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'portal-button admin-view-courses-btn';
      btn.textContent = 'Xem học phần';
      btn.setAttribute('aria-label', `Xem học phần chương trình ${p.name}`);
      btn.onclick = () => openProgramCourses(p);
      tdAction.append(btn);
    });
  }

  async function openProgramCourses(prog) {
    activeProgram = prog;
    $('admin-curriculum-list-view').hidden = true;
    $('admin-curriculum-detail-view').hidden = false;

    // Header info
    $('admin-detail-program-name').textContent = prog.name;
    $('admin-detail-program-id').textContent = `Mã: ${prog.program_id}`;
    $('admin-detail-program-credits').textContent = `Tổng tín chỉ: ${prog.total_credits}`;
    $('admin-detail-program-courses').textContent = `${prog.course_count} học phần`;
    $('admin-detail-source-file').textContent = prog.source_file || '—';
    $('admin-detail-source-pages').textContent = prog.source_pages || '—';

    const badge = $('admin-detail-status-badge');
    if (badge) {
      if (prog.catalog_status === 'draft_unverified') {
        badge.className = 'admin-status-badge badge-warning';
        badge.textContent = getCopy('adminDraftUnverified');
      } else {
        badge.className = 'admin-status-badge badge-success';
        badge.textContent = getCopy('adminVerified');
      }
    }

    const tbody = $('admin-courses-tbody');
    if (tbody) {
      tbody.innerHTML = `<tr><td colspan="8" class="admin-empty-state">Đang tải danh sách học phần…</td></tr>`;
    }

    try {
      const data = await window.systemAuth.request('/admin/courses?program_id=' + encodeURIComponent(prog.program_id));
      currentProgramCourses = data || [];
      populateBlockFilter();
      renderCourses();
    } catch (err) {
      if (tbody) {
        tbody.innerHTML = `<tr><td colspan="8" class="admin-empty-state">Lỗi tải học phần: ${err.message}</td></tr>`;
      }
    }
  }

  function populateBlockFilter() {
    const select = $('admin-courses-block-filter');
    if (!select) return;
    select.replaceChildren();
    select.add(new Option('Tất cả khối kiến thức', 'all'));

    const blocks = Array.from(new Set(currentProgramCourses.map(c => c.block).filter(Boolean)));
    blocks.forEach(b => {
      select.add(new Option(b, b));
    });
  }

  function renderCourses() {
    const tbody = $('admin-courses-tbody');
    if (!tbody) return;
    tbody.replaceChildren();

    const searchQuery = ($('admin-courses-search')?.value || '').trim().toLowerCase();
    const blockFilter = $('admin-courses-block-filter')?.value || 'all';

    const filtered = currentProgramCourses.filter(c => {
      const matchSearch = !searchQuery ||
        c.code.toLowerCase().includes(searchQuery) ||
        c.name.toLowerCase().includes(searchQuery) ||
        (c.name_en && c.name_en.toLowerCase().includes(searchQuery));
      const matchBlock = blockFilter === 'all' || c.block === blockFilter;
      return matchSearch && matchBlock;
    });

    if (filtered.length === 0) {
      const tr = tbody.insertRow();
      const td = tr.insertCell();
      td.colSpan = 8;
      td.className = 'admin-empty-state';
      td.textContent = 'Không có học phần nào phù hợp bộ lọc.';
      return;
    }

    filtered.forEach(c => {
      const tr = tbody.insertRow();

      // 1. Code
      const tdCode = tr.insertCell();
      const codeEl = document.createElement('code');
      codeEl.className = 'admin-course-code';
      codeEl.textContent = c.code;
      tdCode.appendChild(codeEl);

      // 2. Name
      const tdName = tr.insertCell();
      const strongName = document.createElement('strong');
      strongName.textContent = c.name;
      tdName.appendChild(strongName);
      if (c.name_en) {
        const divEn = document.createElement('div');
        divEn.className = 'admin-sub-text';
        divEn.textContent = c.name_en;
        tdName.appendChild(divEn);
      }

      // 3. Credits
      const tdCredits = tr.insertCell();
      tdCredits.className = 'tabular-nums';
      tdCredits.textContent = c.credits;

      // 4. Block
      const tdBlock = tr.insertCell();
      const spanBlock = document.createElement('span');
      spanBlock.className = 'admin-meta-tag';
      spanBlock.textContent = c.block || 'Chưa phân khối';
      tdBlock.appendChild(spanBlock);

      // 5. Requirement Type
      const tdReq = tr.insertCell();
      tdReq.textContent = c.requirement_type === 'required' ? 'Bắt buộc' : 'Tự chọn';

      // 6. Term / Year
      const tdTerm = tr.insertCell();
      if (c.suggested_term) {
        tdTerm.textContent = `Kỳ ${c.suggested_term}`;
      } else if (c.year) {
        tdTerm.textContent = `Năm ${c.year}`;
      } else {
        tdTerm.textContent = '—';
      }

      // 7. Prerequisites
      const tdPrereq = tr.insertCell();
      if (c.prerequisites && c.prerequisites.length > 0) {
        const parts = c.prerequisites.map(andGroup => {
          if (andGroup.length === 1) return `<span class="prereq-pill">${andGroup[0]}</span>`;
          return `<span class="prereq-pill">(${andGroup.join(' | ')})</span>`;
        });
        tdPrereq.innerHTML = parts.join(' & ');
      } else {
        tdPrereq.textContent = 'Không';
      }

      // 8. Status
      const tdStatus = tr.insertCell();
      if (c.prerequisite_status === 'draft_unverified') {
        tdStatus.innerHTML = `<span class="admin-status-badge badge-warning">Bản thảo</span>`;
      } else {
        tdStatus.innerHTML = `<span class="admin-status-badge badge-success">Kiểm định</span>`;
      }

      // 9. Actions
      const tdAction = tr.insertCell();
      const editBtn = document.createElement('button');
      editBtn.type = 'button';
      editBtn.className = 'admin-action-btn-sm btn-edit-rules';
      editBtn.textContent = 'Sửa quy tắc';
      editBtn.setAttribute('aria-label', `Sửa điều kiện tiên quyết môn ${c.code}`);
      editBtn.onclick = () => openPrereqEditor(c);
      tdAction.append(editBtn);
    });
  }

  // Bind Curriculum filter events
  document.addEventListener('DOMContentLoaded', () => {
    $('admin-curriculum-search')?.addEventListener('input', renderPrograms);
    $('admin-curriculum-status-filter')?.addEventListener('change', renderPrograms);
    $('admin-curriculum-detail-back')?.addEventListener('click', () => {
      $('admin-curriculum-detail-view').hidden = true;
      $('admin-curriculum-list-view').hidden = false;
    });
    $('admin-courses-search')?.addEventListener('input', renderCourses);
    $('admin-courses-block-filter')?.addEventListener('change', renderCourses);
    bindImportModal();
  });
  $('admin-curriculum-search')?.addEventListener('input', renderPrograms);
  $('admin-curriculum-status-filter')?.addEventListener('change', renderPrograms);
  $('admin-curriculum-detail-back')?.addEventListener('click', () => {
    $('admin-curriculum-detail-view').hidden = true;
    $('admin-curriculum-list-view').hidden = false;
  });
  $('admin-courses-search')?.addEventListener('input', renderCourses);
  $('admin-courses-block-filter')?.addEventListener('change', renderCourses);

  function bindImportModal() {
    const importBtn = $('admin-curriculum-import-btn');
    const modal = $('admin-import-modal');
    const closeBtn = $('admin-import-close-btn');
    const cancelBtn = $('admin-import-cancel-btn');
    const form = $('admin-import-form');
    const fileInput = $('admin-import-file-input');
    const csvTextArea = $('admin-import-csv-text');
    const progSelect = $('admin-import-program-select');
    const previewDiv = $('admin-import-preview');

    if (!modal || modal.dataset.bound === 'true') return;
    modal.dataset.bound = 'true';

    importBtn?.addEventListener('click', async () => {
      // Ensure programs are loaded
      if (curriculumPrograms.length === 0 && window.systemAuth?.request) {
        try {
          const data = await window.systemAuth.request('/admin/programs');
          curriculumPrograms = data || [];
        } catch (_) {}
      }

      // Populate program select options
      if (progSelect && curriculumPrograms.length > 0) {
        progSelect.innerHTML = '<option value="">-- Chọn chương trình đào tạo --</option>';
        curriculumPrograms.forEach(p => {
          const opt = document.createElement('option');
          opt.value = p.program_id;
          opt.textContent = `${p.name} (${p.program_id})`;
          progSelect.appendChild(opt);
        });
      }
      form?.reset();
      if (previewDiv) {
        previewDiv.hidden = true;
        previewDiv.innerHTML = '';
      }
      modal.showModal();
    });

    closeBtn?.addEventListener('click', () => modal.close());
    cancelBtn?.addEventListener('click', () => modal.close());

    fileInput?.addEventListener('change', (e) => {
      const file = e.target.files?.[0];
      if (!file) return;
      const titleInput = $('admin-import-version-title');
      if (titleInput && !titleInput.value) {
        titleInput.value = file.name.replace(/\.csv$/i, '');
      }
      const reader = new FileReader();
      reader.onload = (evt) => {
        if (csvTextArea) csvTextArea.value = evt.target.result;
      };
      reader.readAsText(file, 'utf-8');
    });

    form?.addEventListener('submit', async (e) => {
      e.preventDefault();
      const submitBtn = $('admin-import-submit-btn');
      if (submitBtn) submitBtn.disabled = true;

      const payload = {
        program_id: progSelect.value,
        version_title: $('admin-import-version-title').value,
        cohort: $('admin-import-cohort').value || null,
        csv_content: csvTextArea.value,
        filename: fileInput?.files?.[0]?.name || 'manual_entry.csv'
      };

      try {
        const csrf = window.systemAuth?.csrf || '';
        const res = await fetch('/admin/catalog-revisions/import', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            ...(csrf ? { 'X-CSRF-Token': csrf } : {})
          },
          body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (!res.ok) {
          throw new Error(data.detail || 'Lỗi nhập dữ liệu bản thảo');
        }

        renderImportPreview(data);
      } catch (err) {
        if (previewDiv) {
          previewDiv.replaceChildren();
          previewDiv.hidden = false;
          const header = document.createElement('div');
          header.className = 'preview-header';
          const pill = document.createElement('span');
          pill.className = 'preview-status-pill danger';
          pill.textContent = 'Lỗi hệ thống';
          header.appendChild(pill);
          const p = document.createElement('p');
          p.className = 'err-msg';
          p.textContent = err.message || 'Đã có lỗi xảy ra';
          previewDiv.appendChild(header);
          previewDiv.appendChild(p);
        }
      } finally {
        if (submitBtn) submitBtn.disabled = false;
      }
    });
  }

  function renderImportPreview(data) {
    const previewDiv = $('admin-import-preview');
    if (!previewDiv) return;
    previewDiv.replaceChildren();
    previewDiv.hidden = false;

    const summary = data.validation_summary || {};
    const isValid = summary.valid === true;
    const stats = summary.stats || {};
    const errors = summary.errors || [];
    const warnings = summary.warnings || [];

    // Header
    const header = document.createElement('div');
    header.className = 'preview-header';
    const headerTitle = document.createElement('strong');
    headerTitle.textContent = 'Kết quả kiểm tra dữ liệu: ';
    const statusPill = document.createElement('span');
    statusPill.className = `preview-status-pill ${isValid ? 'success' : 'danger'}`;
    statusPill.textContent = isValid ? '✓ Hợp lệ (Đã tạo bản thảo)' : '⚠ Có lỗi cần chỉnh sửa';
    header.appendChild(headerTitle);
    header.appendChild(statusPill);
    previewDiv.appendChild(header);

    // Meta stats info
    const metaDiv = document.createElement('div');
    metaDiv.style.cssText = "margin: 6px 0; color: var(--text-muted); font-size: 0.82rem;";

    metaDiv.appendChild(document.createTextNode('Mã bản thảo: '));
    const revCode = document.createElement('code');
    revCode.style.fontFamily = "'JetBrains Mono', monospace";
    revCode.textContent = String(data.revision_id || 'N/A');
    metaDiv.appendChild(revCode);

    metaDiv.appendChild(document.createTextNode(' | Số học phần: '));
    const countStrong = document.createElement('strong');
    countStrong.textContent = String(stats.course_count ?? 0);
    metaDiv.appendChild(countStrong);

    metaDiv.appendChild(document.createTextNode(' | Tổng tín chỉ: '));
    const credStrong = document.createElement('strong');
    credStrong.textContent = String(stats.total_credits ?? 0);
    metaDiv.appendChild(credStrong);
    previewDiv.appendChild(metaDiv);

    // Errors list (inert text)
    if (errors.length > 0) {
      const errBox = document.createElement('div');
      errBox.style.marginTop = '8px';
      const errTitle = document.createElement('strong');
      errTitle.className = 'err-msg';
      errTitle.textContent = `Danh sách lỗi (${errors.length}):`;
      errBox.appendChild(errTitle);

      const ul = document.createElement('ul');
      errors.forEach(err => {
        const li = document.createElement('li');
        li.className = 'err-msg';
        const rowPrefix = err.row != null ? `Dòng ${err.row}: ` : '';
        li.textContent = `${rowPrefix}${err.message || 'Lỗi không xác định'}`;
        ul.appendChild(li);
      });
      errBox.appendChild(ul);
      previewDiv.appendChild(errBox);
    }

    // Warnings list (inert text)
    if (warnings.length > 0) {
      const warnBox = document.createElement('div');
      warnBox.style.marginTop = '8px';
      const warnTitle = document.createElement('strong');
      warnTitle.className = 'warn-msg';
      warnTitle.textContent = `Cảnh báo (${warnings.length}):`;
      warnBox.appendChild(warnTitle);

      const ul = document.createElement('ul');
      warnings.forEach(w => {
        const li = document.createElement('li');
        li.className = 'warn-msg';
        li.textContent = w.message || '';
        ul.appendChild(li);
      });
      warnBox.appendChild(ul);
      previewDiv.appendChild(warnBox);
    }

    // Success notice
    if (isValid) {
      const successDiv = document.createElement('div');
      successDiv.style.cssText = 'margin-top: 10px; padding: 8px; border-radius: 4px; background: rgba(16, 185, 129, 0.1); color: #10b981;';
      successDiv.textContent = '✓ Bản thảo đã được lưu trữ an toàn trong hàng đợi kiểm duyệt. Không ảnh hưởng đến dữ liệu đang vận hành.';
      previewDiv.appendChild(successDiv);
    }
  }
  bindImportModal();

  // ==========================================================================
  // Revisions & Review Workflow (Diff, Approve, Publish, Rollback)
  // ==========================================================================
  let curriculumRevisions = [];

  const subtabPrograms = $('admin-curriculum-subtab-programs');
  const subtabRevisions = $('admin-curriculum-subtab-revisions');
  const subtabPreview = $('admin-curriculum-subtab-preview');
  const programsView = $('admin-curriculum-container');
  const programsToolbar = document.querySelector('.admin-curriculum-toolbar');
  const revisionsView = $('admin-curriculum-revisions-view');
  const previewView = $('admin-curriculum-preview-view');
  const diffModal = $('admin-diff-modal');
  const diffCloseBtn = $('admin-diff-close-btn');
  const diffDismissBtn = $('admin-diff-dismiss-btn');

  function switchCurriculumSubtab(tab) {
    [subtabPrograms, subtabRevisions, subtabPreview].forEach(btn => {
      btn?.classList.remove('active');
      btn?.setAttribute('aria-selected', 'false');
    });
    if (programsView) programsView.hidden = true;
    if (programsToolbar) programsToolbar.hidden = true;
    if (revisionsView) revisionsView.hidden = true;
    if (previewView) previewView.hidden = true;

    if (tab === 'programs') {
      subtabPrograms?.classList.add('active');
      subtabPrograms?.setAttribute('aria-selected', 'true');
      if (programsView) programsView.hidden = false;
      if (programsToolbar) programsToolbar.hidden = false;
    } else if (tab === 'revisions') {
      subtabRevisions?.classList.add('active');
      subtabRevisions?.setAttribute('aria-selected', 'true');
      if (revisionsView) revisionsView.hidden = false;
      loadRevisions();
    } else if (tab === 'preview') {
      subtabPreview?.classList.add('active');
      subtabPreview?.setAttribute('aria-selected', 'true');
      if (previewView) previewView.hidden = false;
      initSyntheticPreview();
    }
  }

  subtabPrograms?.addEventListener('click', () => switchCurriculumSubtab('programs'));
  subtabRevisions?.addEventListener('click', () => switchCurriculumSubtab('revisions'));
  subtabPreview?.addEventListener('click', () => switchCurriculumSubtab('preview'));
  $('admin-revisions-refresh-btn')?.addEventListener('click', () => loadRevisions());
  $('admin-revisions-search')?.addEventListener('input', renderRevisions);
  $('admin-revisions-status-filter')?.addEventListener('change', renderRevisions);

  diffCloseBtn?.addEventListener('click', () => diffModal?.close());
  diffDismissBtn?.addEventListener('click', () => diffModal?.close());

  const provModal = $('admin-provenance-modal');
  $('admin-prov-close-btn')?.addEventListener('click', () => provModal?.close());
  $('admin-prov-dismiss-btn')?.addEventListener('click', () => provModal?.close());

  async function loadRevisions() {
    try {
      if (!window.systemAuth?.request) return;
      const data = await window.systemAuth.request('/admin/catalog-revisions');
      curriculumRevisions = data || [];
      renderRevisions();
    } catch (err) {
      console.error('Failed to load curriculum revisions:', err);
    }
  }

  function renderRevisions() {
    const tbody = $('admin-revisions-tbody');
    if (!tbody) return;
    tbody.replaceChildren();

    const query = ($('admin-revisions-search')?.value || '').trim().toLowerCase();
    const statusFilter = $('admin-revisions-status-filter')?.value || 'all';

    const filtered = curriculumRevisions.filter(r => {
      const matchQuery = !query ||
        r.revision_id.toLowerCase().includes(query) ||
        r.program_id.toLowerCase().includes(query) ||
        r.version_title.toLowerCase().includes(query) ||
        (r.cohort && r.cohort.toLowerCase().includes(query));
      const matchStatus = statusFilter === 'all' || r.status === statusFilter;
      return matchQuery && matchStatus;
    });

    if (filtered.length === 0) {
      const tr = tbody.insertRow();
      const td = tr.insertCell();
      td.colSpan = 8;
      td.className = 'admin-empty-state';
      td.textContent = 'Không có bản thảo hoặc phiên bản nào phù hợp.';
      return;
    }

    filtered.forEach(rev => {
      const tr = tbody.insertRow();
      tr.dataset.revisionId = rev.revision_id;

      // 1. Revision ID
      const tdId = tr.insertCell();
      const codeId = document.createElement('code');
      codeId.className = 'admin-course-code';
      codeId.textContent = rev.revision_id;
      tdId.appendChild(codeId);

      // 2. Program ID
      const tdProg = tr.insertCell();
      const codeProg = document.createElement('code');
      codeProg.textContent = rev.program_id;
      tdProg.appendChild(codeProg);

      // 3. Title
      const tdTitle = tr.insertCell();
      const strongTitle = document.createElement('strong');
      strongTitle.textContent = rev.version_title;
      tdTitle.appendChild(strongTitle);

      // 4. Cohort
      const tdCohort = tr.insertCell();
      tdCohort.textContent = rev.cohort || '—';

      // 5. Status
      const tdStatus = tr.insertCell();
      let statusBadge = '';
      if (rev.status === 'published') {
        statusBadge = '<span class="admin-status-badge badge-success">Đã phát hành</span>';
      } else if (rev.status === 'approved') {
        statusBadge = '<span class="admin-status-badge badge-success" style="background: rgba(59, 130, 246, 0.15); color: #3b82f6;">Đã duyệt</span>';
      } else if (rev.status === 'validated') {
        statusBadge = '<span class="admin-status-badge badge-warning" style="background: rgba(16, 185, 129, 0.15); color: #10b981;">Đã kiểm tra</span>';
      } else if (rev.status === 'rejected') {
        statusBadge = '<span class="admin-status-badge badge-danger">Từ chối</span>';
      } else {
        statusBadge = '<span class="admin-status-badge badge-warning">Bản thảo</span>';
      }
      tdStatus.innerHTML = statusBadge;

      // 6. Active Pointer
      const tdActive = tr.insertCell();
      if (rev.is_active) {
        tdActive.innerHTML = '<span class="admin-status-badge badge-success"><span class="admin-pulse-dot"></span> Đang chạy</span>';
      } else {
        tdActive.innerHTML = '<span style="color: var(--text-muted); font-size: 0.8rem;">Lưu trữ</span>';
      }

      // 7. Created At
      const tdDate = tr.insertCell();
      tdDate.className = 'admin-sub-text tabular-nums';
      tdDate.textContent = rev.created_at ? new Date(rev.created_at).toLocaleString('vi-VN') : '—';

      // 8. Actions
      const tdAction = tr.insertCell();
      tdAction.style.whiteSpace = 'nowrap';

      // Diff button
      const diffBtn = document.createElement('button');
      diffBtn.type = 'button';
      diffBtn.className = 'admin-action-btn-sm';
      diffBtn.textContent = 'So sánh';
      diffBtn.onclick = () => openDiffModal(rev.revision_id);
      tdAction.appendChild(diffBtn);

      // Rules button
      const rulesBtn = document.createElement('button');
      rulesBtn.type = 'button';
      rulesBtn.className = 'admin-action-btn-sm btn-rev-rules';
      rulesBtn.textContent = 'Sửa quy tắc';
      rulesBtn.onclick = () => openRevisionRulesPicker(rev);
      tdAction.appendChild(rulesBtn);

      // Approve button (if draft or validated)
      if (['draft', 'validated'].includes(rev.status)) {
        const appBtn = document.createElement('button');
        appBtn.type = 'button';
        appBtn.className = 'admin-action-btn-sm btn-approve';
        appBtn.textContent = 'Duyệt';
        appBtn.onclick = () => handleApproveRevision(rev.revision_id);
        tdAction.appendChild(appBtn);
      }

      // Publish button (if approved and not active)
      if (rev.status === 'approved' && !rev.is_active) {
        const pubBtn = document.createElement('button');
        pubBtn.type = 'button';
        pubBtn.className = 'admin-action-btn-sm btn-publish';
        pubBtn.textContent = 'Phát hành';
        pubBtn.onclick = () => handlePublishRevision(rev.revision_id);
        tdAction.appendChild(pubBtn);
      }

      // Rollback button (if published but not currently active)
      if (rev.status === 'published' && !rev.is_active) {
        const rbBtn = document.createElement('button');
        rbBtn.type = 'button';
        rbBtn.className = 'admin-action-btn-sm btn-rollback';
        rbBtn.textContent = 'Khôi phục';
        rbBtn.onclick = () => handleRollbackRevision(rev.revision_id);
        tdAction.appendChild(rbBtn);
      }

      // Provenance button (if published or active)
      if (rev.status === 'published' || rev.is_active) {
        const provBtn = document.createElement('button');
        provBtn.type = 'button';
        provBtn.className = 'admin-action-btn-sm btn-diff';
        provBtn.style.color = 'var(--primary)';
        provBtn.textContent = 'Chứng thực';
        provBtn.title = 'Xem chứng thực và hồ sơ nguồn gốc của phiên bản đã ban hành';
        provBtn.onclick = () => openProvenanceModal(rev.revision_id);
        tdAction.appendChild(provBtn);
      }
    });
  }

  async function openProvenanceModal(revisionId) {
    const modal = $('admin-provenance-modal');
    if (!modal) return;
    modal.showModal();

    const loading = $('admin-prov-loading');
    const content = $('admin-prov-content');
    if (loading) loading.style.display = 'block';
    if (content) content.style.display = 'none';

    try {
      const data = await window.systemAuth.request(`/admin/catalog-revisions/${revisionId}/provenance`);
      const manifest = data.provenance_manifest;
      if (!manifest) throw new Error('Không tìm thấy dữ liệu chứng thực');

      const subTitle = $('admin-prov-subtitle');
      if (subTitle) subTitle.textContent = `Mã phiên bản: ${manifest.revision_id} | Ngành: ${manifest.program_id}`;
      const chk = $('admin-prov-checksum');
      if (chk) chk.textContent = manifest.manifest_checksum || 'N/A';
      const pubAt = $('admin-prov-published-at');
      if (pubAt) pubAt.textContent = manifest.published_at ? new Date(manifest.published_at).toLocaleString('vi-VN') : 'N/A';
      const pHash = $('admin-prov-payload-hash');
      if (pHash) {
        pHash.textContent = manifest.payload_hash || 'N/A';
        pHash.title = manifest.payload_hash || '';
      }
      const pubBy = $('admin-prov-publisher');
      if (pubBy) pubBy.textContent = manifest.publisher_id ? `UUID: ${manifest.publisher_id.slice(0, 8)}…` : 'Hệ thống';
      const reasonEl = $('admin-prov-reason');
      if (reasonEl) reasonEl.textContent = manifest.publication_reason || 'Ban hành áp dụng đào tạo';
      const countEl = $('admin-prov-docs-count');
      if (countEl) countEl.textContent = `${manifest.documents_count || 0} tài liệu`;

      const tbody = $('admin-prov-docs-tbody');
      if (tbody) {
        tbody.innerHTML = '';
        if (!manifest.source_documents || manifest.source_documents.length === 0) {
          tbody.innerHTML = '<tr><td colspan="4" style="text-align: center; color: var(--text-muted); padding: 12px;">Không có tài liệu căn cứ thu thập đính kèm trực tiếp.</td></tr>';
        } else {
          manifest.source_documents.forEach(doc => {
            const tr = document.createElement('tr');
            const td1 = document.createElement('td');
            const c1 = document.createElement('code');
            c1.textContent = doc.document_id;
            td1.appendChild(c1);

            const td2 = document.createElement('td');
            const s2 = document.createElement('strong');
            s2.textContent = doc.title || doc.document_id;
            td2.appendChild(s2);
            if (doc.url) {
              td2.appendChild(document.createElement('br'));
              const safeUrl = sanitizeUrl(doc.url);
              if (safeUrl) {
                const a2 = document.createElement('a');
                a2.href = safeUrl;
                a2.target = '_blank';
                a2.rel = 'noopener noreferrer';
                a2.style.cssText = 'font-size: 0.78rem; color: var(--primary);';
                a2.textContent = 'Mở URL gốc ↗';
                td2.appendChild(a2);
              } else {
                const spWarn = document.createElement('span');
                spWarn.style.cssText = 'font-size: 0.78rem; color: var(--text-muted);';
                spWarn.textContent = `${doc.url} (không an toàn)`;
                td2.appendChild(spWarn);
              }
            }

            const td3 = document.createElement('td');
            const c3 = document.createElement('code');
            c3.style.fontSize = '0.78rem';
            c3.textContent = doc.content_hash ? doc.content_hash.slice(0, 16) + '…' : 'N/A';
            td3.appendChild(c3);

            const td4 = document.createElement('td');
            const sp4 = document.createElement('span');
            sp4.className = 'admin-status-badge badge-active';
            sp4.textContent = doc.review_status || 'approved';
            td4.appendChild(sp4);

            tr.appendChild(td1);
            tr.appendChild(td2);
            tr.appendChild(td3);
            tr.appendChild(td4);
            tbody.appendChild(tr);
          });
        }
      }

      if (loading) loading.style.display = 'none';
      if (content) content.style.display = 'flex';
    } catch (err) {
      if (loading) loading.style.display = 'none';
      alert(`Không tải được chứng thực xuất bản: ${err.message}`);
      modal.close();
    }
  }

  async function openDiffModal(revisionId) {
    if (!diffModal) return;
    const statsGrid = $('admin-diff-stats');
    const detailsContainer = $('admin-diff-details');
    const targetPill = $('admin-diff-target-pill');
    const basePill = $('admin-diff-base-pill');

    if (statsGrid) statsGrid.innerHTML = 'Đang tính toán sai khác…';
    if (detailsContainer) detailsContainer.innerHTML = '';
    diffModal.showModal();

    try {
      const data = await window.systemAuth.request(`/admin/catalog-revisions/${revisionId}/diff`);
      if (targetPill) targetPill.textContent = `Bản thảo: ${data.revision_id}`;
      if (basePill) basePill.textContent = `So với: ${data.base_revision_id || 'Chưa có bản phát hành'}`;

      const sum = data.summary || {};
      if (statsGrid) {
        statsGrid.innerHTML = `
          <div class="diff-stat-card added">
            <span class="diff-stat-num">+${sum.added_count || 0}</span>
            <span class="diff-stat-label">Học phần thêm mới</span>
          </div>
          <div class="diff-stat-card removed">
            <span class="diff-stat-num">-${sum.removed_count || 0}</span>
            <span class="diff-stat-label">Học phần lược bỏ</span>
          </div>
          <div class="diff-stat-card modified">
            <span class="diff-stat-num">${sum.modified_count || 0}</span>
            <span class="diff-stat-label">Học phần sửa đổi</span>
          </div>
          <div class="diff-stat-card unchanged">
            <span class="diff-stat-num">${sum.unchanged_count || 0}</span>
            <span class="diff-stat-label">Không thay đổi</span>
          </div>
        `;
      }

      const ch = data.changes || {};
      let detailsHtml = '';

      if (ch.added?.length > 0) {
        detailsHtml += `
          <div>
            <div class="diff-section-title" style="color: #10b981;">Học phần mới thêm (${ch.added.length}):</div>
            <div>
              ${ch.added.map(c => `<span class="diff-item-added">+ [${c.code}] ${c.name} (${c.credits} tín chỉ)</span>`).join(' ')}
            </div>
          </div>
        `;
      }

      if (ch.removed?.length > 0) {
        detailsHtml += `
          <div>
            <div class="diff-section-title" style="color: #ef4444;">Học phần lược bỏ (${ch.removed.length}):</div>
            <div>
              ${ch.removed.map(c => `<span class="diff-item-removed">- [${c.code}] ${c.name} (${c.credits} tín chỉ)</span>`).join(' ')}
            </div>
          </div>
        `;
      }

      if (ch.modified?.length > 0) {
        detailsHtml += `
          <div>
            <div class="diff-section-title" style="color: #f59e0b;">Học phần có thay đổi chi tiết (${ch.modified.length}):</div>
            <table class="diff-mod-table">
              <thead>
                <tr>
                  <th>Mã môn</th>
                  <th>Thuộc tính</th>
                  <th>Trước (Base)</th>
                  <th>Sau (Mới)</th>
                </tr>
              </thead>
              <tbody>
                ${ch.modified.map(m => `
                  ${m.field_changes.map(fc => `
                    <tr>
                      <td><code>${m.code}</code></td>
                      <td>${fc.label}</td>
                      <td class="diff-val-before">${JSON.stringify(fc.before)}</td>
                      <td class="diff-val-after">${JSON.stringify(fc.after)}</td>
                    </tr>
                  `).join('')}
                `).join('')}
              </tbody>
            </table>
          </div>
        `;
      }

      if (!detailsHtml) {
        detailsHtml = '<p style="color: var(--text-muted); font-size: 0.88rem;">Hai phiên bản có cấu trúc và môn học hoàn toàn trùng khớp.</p>';
      }

      if (detailsContainer) detailsContainer.innerHTML = detailsHtml;
    } catch (err) {
      if (statsGrid) statsGrid.innerHTML = `<span class="err-msg">Lỗi so sánh: ${err.message}</span>`;
    }
  }

  async function handleApproveRevision(revisionId) {
    const reason = window.prompt('Nhập lý do phê duyệt bản thảo (Bắt buộc):', 'Đã đối chiếu theo quyết định đào tạo của Trường ĐHKHTN');
    if (!reason || reason.trim().length < 3) return;

    try {
      await window.systemAuth.request(`/admin/catalog-revisions/${revisionId}/approve`, 'POST', { reason: reason.trim() });
      await loadRevisions();
    } catch (err) {
      alert(`Lỗi phê duyệt: ${err.message}`);
    }
  }

  async function handlePublishRevision(revisionId) {
    const confirmed = window.confirm(`XÁC NHẬN PHÁT HÀNH:\n\nBạn có chắc chắn muốn phát hành phiên bản [${revisionId}] thành chương trình đào tạo chính thức đang hoạt động?\nPhiên bản đang chạy trước đó sẽ được chuyển vào kho lưu trữ an toàn.`);
    if (!confirmed) return;

    const reason = window.prompt('Nhập quyết định / lý do phát hành (Bắt buộc):', 'Ban hành áp dụng từ năm học 2026-2027');
    if (!reason || reason.trim().length < 3) return;

    try {
      await window.systemAuth.request(`/admin/catalog-revisions/${revisionId}/publish`, 'POST', { reason: reason.trim() });
      await loadRevisions();
      if (window.adminCurriculum?.load) window.adminCurriculum.load();
    } catch (err) {
      alert(`Lỗi phát hành: ${err.message}`);
    }
  }

  async function handleRollbackRevision(revisionId) {
    const confirmed = window.confirm(`CẢNH BÁO KHÔI PHỤC:\n\nBạn có chắc chắn muốn khôi phục phiên bản [${revisionId}] thành bản chạy chính thức thay thế phiên bản hiện tại?`);
    if (!confirmed) return;

    const reason = window.prompt('Nhập lý do khôi phục phiên bản (Bắt buộc):', 'Khôi phục bản ổn định trước đó');
    if (!reason || reason.trim().length < 3) return;

    try {
      await window.systemAuth.request(`/admin/catalog-revisions/${revisionId}/rollback`, 'POST', { reason: reason.trim() });
      await loadRevisions();
      if (window.adminCurriculum?.load) window.adminCurriculum.load();
    } catch (err) {
      alert(`Lỗi khôi phục: ${err.message}`);
    }
  }

  // ==========================================================================
  // Prerequisite Rule Editor
  // ==========================================================================
  let currentEditingCourse = null;
  let currentEditingRevisionId = null;
  let editingRuleGroups = [];

  async function openRevisionRulesPicker(rev) {
    try {
      const data = await window.systemAuth.request(`/admin/catalog-revisions/${rev.revision_id}`);
      const courses = (data.payload || {}).courses || [];
      if (courses.length === 0) {
        alert('Bản thảo này không có danh sách học phần.');
        return;
      }
      const code = window.prompt(
        `Chọn mã môn học cần sửa quy tắc trong bản [${rev.revision_id}]:\n(Các môn: ${courses.slice(0, 8).map(c => c.code).join(', ')}${courses.length > 8 ? '...' : ''})`,
        courses[0].code
      );
      if (!code) return;
      const targetCourse = courses.find(c => c.code.toUpperCase() === code.trim().toUpperCase());
      if (!targetCourse) {
        alert(`Không tìm thấy mã môn ${code} trong bản thảo này.`);
        return;
      }
      openPrereqEditor(targetCourse, rev.revision_id);
    } catch (err) {
      alert(`Lỗi: ${err.message}`);
    }
  }

  async function openPrereqEditor(course, revisionId) {
    const modal = $('admin-prereq-modal');
    if (!modal) return;

    if (!revisionId) {
      if (curriculumRevisions.length === 0 && window.systemAuth?.request) {
        try {
          curriculumRevisions = await window.systemAuth.request('/admin/catalog-revisions') || [];
        } catch (_) {}
      }
      const targetRev = curriculumRevisions.find(r => r.program_id === activeProgram?.program_id && r.is_active)
        || curriculumRevisions.find(r => r.program_id === activeProgram?.program_id);

      if (!targetRev) {
        alert('Chương trình đào tạo này chưa có bản ghi phiên bản/bản thảo trong hệ thống. Vui lòng bấm "Nhập bản thảo (CSV)" để khởi tạo trước khi sửa quy tắc.');
        return;
      }
      revisionId = targetRev.revision_id;
    }

    currentEditingCourse = course;
    currentEditingRevisionId = revisionId;

    if ($('admin-prereq-course-code')) $('admin-prereq-course-code').textContent = course.code;
    if ($('admin-prereq-course-name')) $('admin-prereq-course-name').textContent = course.name;

    const rev = curriculumRevisions.find(r => r.revision_id === revisionId);
    const badge = $('admin-prereq-rev-badge');
    if (badge) {
      if (rev && (rev.is_active || rev.status === 'published')) {
        badge.textContent = `Phiên bản: ${revisionId} (Đang chạy - Sẽ tự rẽ nhánh bản thảo)`;
        badge.style.color = '#f59e0b';
      } else {
        badge.textContent = `Bản thảo: ${revisionId}`;
        badge.style.color = '';
      }
    }

    editingRuleGroups = [];
    if (Array.isArray(course.prerequisites)) {
      editingRuleGroups = course.prerequisites.map(g => Array.isArray(g) ? [...g] : [g]);
    }

    const reasonInput = $('admin-prereq-reason');
    if (reasonInput) reasonInput.value = '';

    const errAlert = $('admin-prereq-error-alert');
    if (errAlert) {
      errAlert.hidden = true;
      errAlert.textContent = '';
    }

    renderPrereqGroups();
    modal.showModal();
  }

  function renderPrereqGroups() {
    const builder = $('admin-prereq-builder');
    if (!builder) return;
    builder.replaceChildren();

    if (editingRuleGroups.length === 0) {
      const emptyDiv = document.createElement('div');
      emptyDiv.className = 'admin-empty-state';
      emptyDiv.style.padding = '12px';
      emptyDiv.style.border = '1px dashed var(--border-light)';
      emptyDiv.textContent = 'Học phần hiện không có điều kiện tiên quyết nào (tự do đăng ký).';
      builder.appendChild(emptyDiv);
      return;
    }

    editingRuleGroups.forEach((grp, gIdx) => {
      const card = document.createElement('div');
      card.className = 'prereq-group-card';
      card.dataset.groupIndex = gIdx;

      // Group Header
      const header = document.createElement('div');
      header.className = 'prereq-group-header';
      header.innerHTML = `<span>Nhóm điều kiện ${gIdx + 1} (Học ít nhất 1 môn - OR)</span>`;

      const delGroupBtn = document.createElement('button');
      delGroupBtn.type = 'button';
      delGroupBtn.className = 'admin-action-btn-sm';
      delGroupBtn.style.color = '#ef4444';
      delGroupBtn.style.borderColor = 'rgba(239, 68, 68, 0.3)';
      delGroupBtn.textContent = 'Xóa nhóm';
      delGroupBtn.onclick = () => {
        editingRuleGroups.splice(gIdx, 1);
        renderPrereqGroups();
      };
      header.appendChild(delGroupBtn);
      card.appendChild(header);

      // Pill List
      const pillList = document.createElement('div');
      pillList.className = 'prereq-pill-list';

      grp.forEach((code, cIdx) => {
        const pill = document.createElement('span');
        pill.className = 'prereq-code-pill';
        pill.innerHTML = `<span>${code}</span>`;

        const rmBtn = document.createElement('button');
        rmBtn.type = 'button';
        rmBtn.className = 'prereq-code-remove';
        rmBtn.textContent = '×';
        rmBtn.setAttribute('aria-label', `Xóa mã ${code}`);
        rmBtn.onclick = () => {
          grp.splice(cIdx, 1);
          renderPrereqGroups();
        };
        pill.appendChild(rmBtn);
        pillList.appendChild(pill);
      });

      // Inline Add input + button
      const addContainer = document.createElement('div');
      addContainer.className = 'prereq-inline-add';

      const input = document.createElement('input');
      input.type = 'text';
      input.className = 'modern-input prereq-inline-input';
      input.placeholder = 'Mã môn';
      input.maxLength = 15;

      const addBtn = document.createElement('button');
      addBtn.type = 'button';
      addBtn.className = 'admin-action-btn-sm';
      addBtn.textContent = '+ Thêm';
      const doAdd = () => {
        const val = input.value.trim().toUpperCase();
        if (val) {
          if (!grp.includes(val)) {
            grp.push(val);
          }
          renderPrereqGroups();
        }
      };
      addBtn.onclick = doAdd;
      input.onkeydown = (e) => {
        if (e.key === 'Enter') {
          e.preventDefault();
          doAdd();
        }
      };

      addContainer.appendChild(input);
      addContainer.appendChild(addBtn);
      pillList.appendChild(addContainer);

      card.appendChild(pillList);
      builder.appendChild(card);
    });
  }

  function bindPrereqEditorModal() {
    const modal = $('admin-prereq-modal');
    if (!modal || modal.dataset.bound === 'true') return;
    modal.dataset.bound = 'true';

    $('admin-prereq-close-btn')?.addEventListener('click', () => modal.close());
    $('admin-prereq-cancel-btn')?.addEventListener('click', () => modal.close());

    $('admin-prereq-add-group-btn')?.addEventListener('click', () => {
      editingRuleGroups.push([]);
      renderPrereqGroups();
    });

    $('admin-prereq-form')?.addEventListener('submit', async (e) => {
      e.preventDefault();
      const saveBtn = $('admin-prereq-save-btn');
      const errAlert = $('admin-prereq-error-alert');
      if (saveBtn) saveBtn.disabled = true;
      if (errAlert) {
        errAlert.hidden = true;
        errAlert.textContent = '';
      }

      const reason = $('admin-prereq-reason')?.value?.trim();
      const cleaned = editingRuleGroups
        .map(grp => grp.map(c => String(c).trim().toUpperCase()).filter(Boolean))
        .filter(grp => grp.length > 0);

      try {
        const csrf = window.systemAuth?.csrf || '';
        const res = await fetch(`/admin/catalog-revisions/${currentEditingRevisionId}/courses/${currentEditingCourse.code}/prerequisites`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            ...(csrf ? { 'X-CSRF-Token': csrf } : {})
          },
          body: JSON.stringify({
            prerequisites: cleaned,
            reason: reason
          })
        });

        const data = await res.json();
        if (!res.ok) {
          throw new Error(data.detail || 'Lỗi khi lưu quy tắc tiên quyết');
        }

        currentEditingCourse.prerequisites = data.prerequisites;
        modal.close();

        await loadRevisions();
        renderCourses();

        const msg = data.branched
          ? `Đã tạo bản thảo rẽ nhánh [${data.revision_id}] do phiên bản trước đã phát hành!`
          : `Đã cập nhật quy tắc tiên quyết cho môn ${data.course_code}!`;
        alert(msg);
      } catch (err) {
        if (errAlert) {
          errAlert.hidden = false;
          errAlert.textContent = err.message;
        }
      } finally {
        if (saveBtn) saveBtn.disabled = false;
      }
    });
  }
  bindPrereqEditorModal();

  // ==========================================================================
  // Document Review Workspace
  // ==========================================================================
  $('admin-crawler-refresh-btn')?.addEventListener('click', () => loadDocuments());
  $('admin-docs-search')?.addEventListener('input', renderCrawlerDocuments);
  $('admin-docs-major-filter')?.addEventListener('change', renderCrawlerDocuments);
  $('admin-docs-status-filter')?.addEventListener('change', renderCrawlerDocuments);
  $('admin-docs-refresh-btn')?.addEventListener('click', () => loadDocuments());

  // ==========================================================================
  // Document Review Workspace (Task 12 & 13)
  // ==========================================================================
  let crawledDocuments = [];
  let currentReviewDoc = null;

  async function loadDocuments() {
    try {
      if (!window.systemAuth?.request) return;
      const major = $('admin-docs-major-filter')?.value || 'all';
      const status = $('admin-docs-status-filter')?.value || 'all';
      const search = ($('admin-docs-search')?.value || '').trim();

      let url = '/admin/crawler/documents?limit=100';
      if (major !== 'all') url += `&major=${encodeURIComponent(major)}`;
      if (status !== 'all') url += `&status=${encodeURIComponent(status)}`;
      if (search) url += `&search=${encodeURIComponent(search)}`;

      const data = await window.systemAuth.request(url);
      crawledDocuments = data.documents || [];
      renderCrawlerDocuments();
    } catch (err) {
      console.error('Failed to load crawled documents:', err);
    }
  }

  function renderCrawlerDocuments() {
    const tbody = $('admin-crawler-docs-tbody');
    if (!tbody) return;
    tbody.replaceChildren();

    const query = ($('admin-docs-search')?.value || '').trim().toLowerCase();
    const majorFilter = $('admin-docs-major-filter')?.value || 'all';
    const statusFilter = $('admin-docs-status-filter')?.value || 'all';

    const filtered = crawledDocuments.filter(d => {
      const matchQuery = !query || d.title.toLowerCase().includes(query) || d.url.toLowerCase().includes(query) || d.id.toLowerCase().includes(query);
      const matchMajor = majorFilter === 'all' || d.major === majorFilter;
      const matchStatus = statusFilter === 'all' || d.review_status === statusFilter;
      return matchQuery && matchMajor && matchStatus;
    });

    if (filtered.length === 0) {
      const tr = tbody.insertRow();
      const td = tr.insertCell();
      td.colSpan = 6;
      td.className = 'admin-empty-state';
      td.textContent = 'Không có tài liệu nào trong hàng đợi kiểm duyệt.';
      return;
    }

    filtered.forEach(doc => {
      const tr = tbody.insertRow();
      tr.dataset.docId = doc.id;

      // 1. Doc ID
      const tdId = tr.insertCell();
      const codeId = document.createElement('code');
      codeId.className = 'admin-course-code';
      codeId.textContent = doc.id;
      tdId.appendChild(codeId);

      // 2. Title & URL
      const tdTitle = tr.insertCell();
      const strongTitle = document.createElement('strong');
      strongTitle.textContent = doc.title;
      const divUrl = document.createElement('div');
      divUrl.className = 'admin-sub-text';
      divUrl.style.cssText = 'max-width: 320px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;';
      divUrl.textContent = doc.url;
      tdTitle.appendChild(strongTitle);
      tdTitle.appendChild(divUrl);

      // 3. Major / Type
      const tdMajor = tr.insertCell();
      const spanMajor = document.createElement('span');
      spanMajor.className = 'admin-meta-tag';
      spanMajor.textContent = doc.major;
      const divType = document.createElement('div');
      divType.className = 'admin-sub-text';
      divType.textContent = doc.doc_type;
      tdMajor.appendChild(spanMajor);
      tdMajor.appendChild(divType);

      // 4. Size
      const tdSize = tr.insertCell();
      tdSize.className = 'tabular-nums';
      tdSize.textContent = doc.content_length ? `${doc.content_length.toLocaleString()} B` : '—';

      // 5. Review Status Badge
      const tdStatus = tr.insertCell();
      let badge = '';
      if (doc.review_status === 'approved') {
        badge = '<span class="admin-status-badge badge-success">Đã duyệt</span>';
      } else if (doc.review_status === 'rejected') {
        badge = '<span class="admin-status-badge badge-danger">Từ chối</span>';
      } else {
        badge = '<span class="admin-status-badge badge-warning">Chờ duyệt</span>';
      }
      tdStatus.innerHTML = badge;

      // 6. Action
      const tdAction = tr.insertCell();
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'admin-action-btn-sm btn-review-doc';
      btn.textContent = 'Kiểm duyệt';
      btn.setAttribute('aria-label', `Kiểm duyệt tài liệu ${doc.title}`);
      btn.onclick = () => openDocumentReviewModal(doc.id);
      tdAction.appendChild(btn);
    });
  }

  async function openDocumentReviewModal(docId) {
    const modal = $('admin-doc-review-modal');
    if (!modal) return;

    try {
      const doc = await window.systemAuth.request(`/admin/crawler/documents/${docId}`);
      currentReviewDoc = doc;

      if ($('admin-doc-modal-title')) $('admin-doc-modal-title').textContent = doc.title;
      if ($('admin-doc-modal-id')) $('admin-doc-modal-id').textContent = `Mã: ${doc.id} · Băm: ${doc.content_hash.slice(0, 12)}…`;

      const sourceLink = $('admin-doc-source-link');
      if (sourceLink) {
        const safeUrl = sanitizeUrl(doc.url);
        if (safeUrl) {
          sourceLink.href = safeUrl;
          sourceLink.textContent = doc.url;
        } else {
          sourceLink.removeAttribute('href');
          sourceLink.textContent = `${doc.url} (URL không an toàn)`;
        }
      }

      // Duplicate warning
      const dupAlert = $('admin-doc-duplicate-alert');
      if (dupAlert) {
        if (doc.duplicate_count > 0) {
          dupAlert.style.display = 'flex';
          const countEl = $('admin-doc-dup-count');
          if (countEl) countEl.textContent = `${doc.duplicate_count}`;
        } else {
          dupAlert.style.display = 'none';
        }
      }

      // Safe Preview Pane (Formatted paragraphs)
      const previewPane = $('admin-doc-preview-pane');
      if (previewPane) {
        previewPane.innerHTML = formatMarkdownToSafeHtml(doc.safe_markdown || doc.markdown_content || '');
      }

      // Status Badge
      const statusBadge = $('admin-doc-status-badge');
      if (statusBadge) {
        if (doc.review_status === 'approved') {
          statusBadge.innerHTML = '<span class="admin-status-badge badge-success">✓ Đã phê duyệt</span>';
        } else if (doc.review_status === 'rejected') {
          statusBadge.innerHTML = '<span class="admin-status-badge badge-danger">✕ Bị từ chối</span>';
        } else {
          statusBadge.innerHTML = '<span class="admin-status-badge badge-warning">⏳ Chờ kiểm duyệt</span>';
        }
      }

      const decMeta = $('admin-doc-decision-meta');
      if (decMeta) {
        if (doc.reviewed_at) {
          decMeta.textContent = `Duyệt lúc: ${new Date(doc.reviewed_at).toLocaleString('vi-VN')} · Lý do: ${doc.review_reason || '—'}`;
        } else {
          decMeta.textContent = 'Chưa có quyết định kiểm duyệt.';
        }
      }

      // Form values
      if ($('admin-doc-edit-title')) $('admin-doc-edit-title').value = doc.title || '';
      if ($('admin-doc-edit-major')) $('admin-doc-edit-major').value = doc.major || '';
      if ($('admin-doc-edit-type')) $('admin-doc-edit-type').value = doc.doc_type || '';
      if ($('admin-doc-decision-reason')) $('admin-doc-decision-reason').value = '';

      modal.showModal();
    } catch (err) {
      alert(`Lỗi tải chi tiết tài liệu: ${err.message}`);
    }
  }

  function formatMarkdownToSafeHtml(md) {
    if (!md) return '<p style="color: var(--text-muted);">Tài liệu không có nội dung văn bản.</p>';
    const lines = md.split('\n');
    let html = '';
    for (const rawLine of lines) {
      const line = rawLine.trim();
      if (!line) continue;
      if (line.startsWith('# ')) {
        html += `<h3 style="font-size: 1.1rem; margin: 12px 0 6px 0; color: var(--text-main); font-weight: 700;">${escapeHtml(line.slice(2))}</h3>`;
      } else if (line.startsWith('## ')) {
        html += `<h4 style="font-size: 0.95rem; margin: 10px 0 4px 0; color: var(--text-main); font-weight: 700;">${escapeHtml(line.slice(3))}</h4>`;
      } else if (line.startsWith('- ')) {
        html += `<li style="margin-left: 18px; margin-bottom: 3px;">${escapeHtml(line.slice(2))}</li>`;
      } else {
        html += `<p style="margin-bottom: 8px;">${escapeHtml(line)}</p>`;
      }
    }
    return html;
  }

  function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  function bindDocReviewModal() {
    const modal = $('admin-doc-review-modal');
    $('admin-doc-review-close-btn')?.addEventListener('click', () => modal?.close());

    // Save metadata
    $('admin-doc-meta-form')?.addEventListener('submit', async (e) => {
      e.preventDefault();
      if (!currentReviewDoc) return;
      const btn = $('admin-doc-meta-save-btn');
      if (btn) btn.disabled = true;

      const payload = {
        title: $('admin-doc-edit-title')?.value?.trim(),
        major: $('admin-doc-edit-major')?.value?.trim(),
        doc_type: $('admin-doc-edit-type')?.value?.trim(),
      };

      try {
        await window.systemAuth.request(`/admin/crawler/documents/${currentReviewDoc.id}/metadata`, 'PUT', payload);
        alert('Đã cập nhật metadata thành công!');
        await loadDocuments();
      } catch (err) {
        alert(`Lỗi cập nhật metadata: ${err.message}`);
      } finally {
        if (btn) btn.disabled = false;
      }
    });

    // Approve button
    $('admin-doc-approve-btn')?.addEventListener('click', async () => {
      if (!currentReviewDoc) return;
      const reason = $('admin-doc-decision-reason')?.value?.trim();
      if (!reason || reason.length < 3) {
        alert('Vui lòng nhập lý do phê duyệt (tối thiểu 3 ký tự).');
        $('admin-doc-decision-reason')?.focus();
        return;
      }

      try {
        await window.systemAuth.request(`/admin/crawler/documents/${currentReviewDoc.id}/approve`, 'POST', { reason });
        modal?.close();
        await loadDocuments();
        alert(`Đã phê duyệt tài liệu [${currentReviewDoc.id}]!`);
      } catch (err) {
        alert(`Lỗi phê duyệt: ${err.message}`);
      }
    });

    // Reject button
    $('admin-doc-reject-btn')?.addEventListener('click', async () => {
      if (!currentReviewDoc) return;
      const reason = $('admin-doc-decision-reason')?.value?.trim();
      if (!reason || reason.length < 3) {
        alert('Vui lòng nhập lý do từ chối (tối thiểu 3 ký tự).');
        $('admin-doc-decision-reason')?.focus();
        return;
      }

      try {
        await window.systemAuth.request(`/admin/crawler/documents/${currentReviewDoc.id}/reject`, 'POST', { reason });
        modal?.close();
        await loadDocuments();
        alert(`Đã từ chối tài liệu [${currentReviewDoc.id}].`);
      } catch (err) {
        alert(`Lỗi từ chối: ${err.message}`);
      }
    });
  }
  bindDocReviewModal();

  // ==========================================================================
  // Privileged Admin Action Audit Trail Module (Task 15)
  // ==========================================================================
  let auditLogs = [];
  let auditTotal = 0;
  let auditOffset = 0;
  const auditLimit = 20;
  let auditSearchTimer = null;

  async function loadAuditMetrics() {
    try {
      if (!window.systemAuth?.request) return;
      const metrics = await window.systemAuth.request('/admin/audit-logs/metrics');
      if (metrics) {
        const kpiTot = $('admin-audit-kpi-total');
        if (kpiTot) kpiTot.textContent = metrics.total_events ?? 0;
        const kpi24 = $('admin-audit-kpi-24h');
        if (kpi24) kpi24.textContent = metrics.events_last_24h ?? 0;
        const kpiWarn = $('admin-audit-kpi-warn');
        if (kpiWarn) kpiWarn.textContent = metrics.failed_or_warn_count ?? 0;
      }
    } catch (err) {
      console.warn('Could not load audit metrics:', err);
    }
  }

  async function loadAuditLogs(resetOffset = false) {
    if (resetOffset) auditOffset = 0;
    const actionFilter = $('admin-audit-action-filter')?.value || 'all';
    const targetFilter = $('admin-audit-target-filter')?.value || 'all';
    const searchQuery = $('admin-audit-search')?.value?.trim() || '';

    const params = new URLSearchParams();
    if (actionFilter !== 'all') params.set('action', actionFilter);
    if (targetFilter !== 'all') params.set('target_type', targetFilter);
    if (searchQuery) params.set('q', searchQuery);
    params.set('limit', String(auditLimit));
    params.set('offset', String(auditOffset));

    const tbody = $('admin-audit-tbody');
    if (tbody) tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; color: var(--text-muted); padding: 18px;">Đang tải nhật ký kiểm toán…</td></tr>';

    try {
      if (!window.systemAuth?.request) return;
      const data = await window.systemAuth.request(`/admin/audit-logs?${params.toString()}`);
      auditLogs = data.items || [];
      auditTotal = data.total || 0;
      renderAuditTable();
      renderAuditPagination();
    } catch (err) {
      if (tbody) tbody.innerHTML = `<tr><td colspan="7" style="text-align: center; color: #ef4444; padding: 18px;">Lỗi tải nhật ký: ${escapeHtml(err.message)}</td></tr>`;
    }
  }

  function getActionBadge(action) {
    let colorClass = 'badge-active';
    if (action.startsWith('catalog.')) colorClass = 'badge-purple';
    else if (action.startsWith('crawler.')) colorClass = 'badge-blue';
    else if (action.startsWith('document.')) colorClass = 'badge-success';
    else if (action.startsWith('account.')) colorClass = 'badge-warning';

    return `<span class="admin-status-badge ${colorClass}">${escapeHtml(action)}</span>`;
  }

  function renderAuditTable() {
    const tbody = $('admin-audit-tbody');
    if (!tbody) return;
    tbody.innerHTML = '';

    if (auditLogs.length === 0) {
      tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; color: var(--text-muted); padding: 24px;">Không tìm thấy bản ghi kiểm toán nào phù hợp với bộ lọc.</td></tr>';
      return;
    }

    auditLogs.forEach(item => {
      const tr = document.createElement('tr');
      const timeStr = item.created_at ? new Date(item.created_at).toLocaleString('vi-VN') : 'N/A';
      const isOk = item.result === 'ok';

      tr.innerHTML = `
        <td style="font-size: 0.82rem; font-variant-numeric: tabular-nums;">${escapeHtml(timeStr)}</td>
        <td>
          <strong>${escapeHtml(item.actor_email || (item.actor_id ? item.actor_id.slice(0, 8) + '…' : 'Hệ thống'))}</strong>
        </td>
        <td>${getActionBadge(item.action)}</td>
        <td>
          <code style="font-size: 0.78rem;">${escapeHtml(item.target_type)}</code>
          <br><span style="font-size: 0.78rem; color: var(--text-muted); font-family: monospace;">${escapeHtml(item.target_id)}</span>
        </td>
        <td style="max-width: 320px; line-height: 1.4; font-size: 0.85rem;">
          ${escapeHtml(item.summary)}
        </td>
        <td>
          <span class="admin-status-badge ${isOk ? 'badge-success' : 'badge-danger'}">${escapeHtml(item.result)}</span>
        </td>
        <td>
          <button type="button" class="admin-action-btn-sm btn-diff" style="color: var(--primary);" data-audit-id="${item.id}">Chi tiết</button>
        </td>
      `;

      tr.querySelector('button[data-audit-id]')?.addEventListener('click', () => openAuditDetailModal(item));
      tbody.appendChild(tr);
    });
  }

  function renderAuditPagination() {
    const pageInfo = $('admin-audit-page-info');
    const prevBtn = $('admin-audit-prev-btn');
    const nextBtn = $('admin-audit-next-btn');

    if (pageInfo) {
      const start = auditTotal === 0 ? 0 : auditOffset + 1;
      const end = Math.min(auditOffset + auditLimit, auditTotal);
      pageInfo.textContent = `Hiển thị ${start} - ${end} trên tổng số ${auditTotal} sự kiện`;
    }

    if (prevBtn) {
      prevBtn.disabled = auditOffset === 0;
      prevBtn.onclick = () => {
        if (auditOffset > 0) {
          auditOffset = Math.max(0, auditOffset - auditLimit);
          loadAuditLogs();
        }
      };
    }

    if (nextBtn) {
      nextBtn.disabled = auditOffset + auditLimit >= auditTotal;
      nextBtn.onclick = () => {
        if (auditOffset + auditLimit < auditTotal) {
          auditOffset += auditLimit;
          loadAuditLogs();
        }
      };
    }
  }

  function openAuditDetailModal(item) {
    const modal = $('admin-audit-detail-modal');
    if (!modal) return;

    if ($('admin-audit-detail-id')) $('admin-audit-detail-id').textContent = `Mã sự kiện: #${item.id}`;
    if ($('admin-audit-detail-actor')) $('admin-audit-detail-actor').textContent = item.actor_email || item.actor_id || 'System';
    if ($('admin-audit-detail-time')) $('admin-audit-detail-time').textContent = item.created_at ? new Date(item.created_at).toLocaleString('vi-VN') : 'N/A';
    if ($('admin-audit-detail-action')) $('admin-audit-detail-action').innerHTML = `${getActionBadge(item.action)} <span class="admin-status-badge ${item.result === 'ok' ? 'badge-success' : 'badge-danger'}">${escapeHtml(item.result)}</span>`;
    if ($('admin-audit-detail-target')) $('admin-audit-detail-target').textContent = `${item.target_type}: ${item.target_id}`;
    if ($('admin-audit-detail-summary')) $('admin-audit-detail-summary').textContent = item.summary || 'Không có mô tả chi tiết.';

    const jsonPre = $('admin-audit-detail-json');
    if (jsonPre) {
      jsonPre.textContent = JSON.stringify(item.details || {}, null, 2);
    }

    modal.showModal();
  }

  function bindAuditEvents() {
    $('admin-audit-refresh-btn')?.addEventListener('click', () => {
      loadAuditMetrics();
      loadAuditLogs(true);
    });
    $('admin-audit-action-filter')?.addEventListener('change', () => loadAuditLogs(true));
    $('admin-audit-target-filter')?.addEventListener('change', () => loadAuditLogs(true));
    $('admin-audit-search')?.addEventListener('input', () => {
      clearTimeout(auditSearchTimer);
      auditSearchTimer = setTimeout(() => loadAuditLogs(true), 300);
    });

    $('admin-audit-detail-close-btn')?.addEventListener('click', () => $('admin-audit-detail-modal')?.close());
    $('admin-audit-detail-dismiss-btn')?.addEventListener('click', () => $('admin-audit-detail-modal')?.close());
  }
  bindAuditEvents();

  // Expose module APIs
  window.adminOverview = {
    load: loadOverview,
    render: renderOverview,
    renderError,
    get data() { return overviewData; }
  };


  // ==========================================================================
  // Synthetic Recommendation Preview Logic
  // ==========================================================================
  let previewProgramsLoaded = false;
  let currentPreviewCourses = [];

  async function initSyntheticPreview() {
    const progSelect = $('admin-preview-prog-select');
    if (!progSelect) return;

    if (!previewProgramsLoaded) {
      try {
        const progs = await window.systemAuth.request('/admin/programs');
        progSelect.innerHTML = progs.map(p => `
          <option value="${p.program_id}">${p.name} (${p.program_id})</option>
        `).join('');
        previewProgramsLoaded = true;
        if (progs.length > 0) {
          loadPreviewCourses(progs[0].program_id);
        }
      } catch (err) {
        console.warn('Failed to load programs for preview:', err);
      }
    }
  }

  async function loadPreviewCourses(programId) {
    const picker = $('admin-preview-courses-picker');
    if (!picker) return;
    picker.innerHTML = '<div style="color: var(--text-muted); font-size: 12px; padding: 8px;">Đang tải danh sách học phần...</div>';

    try {
      const data = await window.systemAuth.request(`/admin/courses?program_id=${encodeURIComponent(programId)}`);
      currentPreviewCourses = Array.isArray(data) ? data : (data.courses || []);
      renderPreviewCheckboxes(currentPreviewCourses);
    } catch (err) {
      picker.innerHTML = '<div style="color: #ef4444; font-size: 12px; padding: 8px;">Không thể tải danh sách học phần.</div>';
    }
  }

  function renderPreviewCheckboxes(courses) {
    const picker = $('admin-preview-courses-picker');
    if (!picker) return;

    if (!courses.length) {
      picker.innerHTML = '<div style="color: var(--text-muted); font-size: 12px; padding: 8px;">Không có học phần nào.</div>';
      return;
    }

    picker.innerHTML = courses.map(c => `
      <label style="display: flex; align-items: center; gap: 8px; font-size: 12px; padding: 6px 8px; border-radius: 6px; cursor: pointer; background: var(--bg-card); border: 1px solid var(--border-subtle);">
        <input type="checkbox" value="${c.code}" class="admin-preview-chk" style="cursor: pointer;">
        <span style="overflow: hidden; text-overflow: ellipsis; white-space: nowrap;"><strong>${c.code}</strong>: ${c.name}</span>
      </label>
    `).join('');

    picker.querySelectorAll('.admin-preview-chk').forEach(chk => {
      chk.addEventListener('change', updateSelectedPreviewCount);
    });
    updateSelectedPreviewCount();
  }

  function updateSelectedPreviewCount() {
    const countEl = $('admin-preview-selected-num');
    const checked = document.querySelectorAll('.admin-preview-chk:checked');
    if (countEl) countEl.textContent = checked.length;
  }

  // Hook program selector change
  $('admin-preview-prog-select')?.addEventListener('change', (e) => {
    loadPreviewCourses(e.target.value);
  });

  // Hook Presets
  document.querySelectorAll('.admin-preset-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
      const preset = e.currentTarget.dataset.preset;
      const chks = document.querySelectorAll('.admin-preview-chk');
      chks.forEach(c => c.checked = false);

      if (preset === 'year1') {
        Array.from(chks).slice(0, 6).forEach(c => c.checked = true);
      } else if (preset === 'core') {
        Array.from(chks).slice(0, 12).forEach(c => c.checked = true);
      }
      updateSelectedPreviewCount();
    });
  });

  // Hook Run Simulation Button
  $('admin-preview-run-btn')?.addEventListener('click', async () => {
    const progId = $('admin-preview-prog-select')?.value;
    if (!progId) return;

    const runBtn = $('admin-preview-run-btn');
    if (runBtn) {
      runBtn.disabled = true;
      runBtn.innerHTML = '<span>Đang chạy mô phỏng...</span>';
    }

    const checkedCodes = Array.from(document.querySelectorAll('.admin-preview-chk:checked')).map(c => c.value);
    const maxCredits = parseInt($('admin-preview-credits-input')?.value || '18', 10);
    const goal = $('admin-preview-goal-input')?.value || '';

    try {
      const res = await window.systemAuth.request('/admin/recommendations/preview', 'POST', {
        program_id: progId,
        passed_course_codes: checkedCodes,
        max_credits: maxCredits,
        goal: goal,
      });
      renderPreviewResults(res);
    } catch (err) {
      alert('Lỗi mô phỏng: ' + (err.message || 'Không thể thực hiện mô phỏng'));
    } finally {
      if (runBtn) {
        runBtn.disabled = false;
        runBtn.innerHTML = `
          <svg viewBox="0 0 20 20" fill="none" class="admin-btn-icon" aria-hidden="true" style="width: 16px; height: 16px; margin-right: 6px;">
            <path d="M7 2h6M10 2v5l-5 8.5A2 2 0 0 0 6.7 18h6.6a2 2 0 0 0 1.7-2.5L10 7V2" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          <span>Chạy Mô phỏng Cố vấn</span>
        `;
      }
    }
  });

  function renderPreviewResults(data) {
    const area = $('admin-preview-results-area');
    if (!area) return;
    area.hidden = false;

    // 1. Banner
    let bannerHtml = `
      <div style="background: rgba(67, 97, 238, 0.08); border: 1px solid rgba(67, 97, 238, 0.3); border-radius: 8px; padding: 12px 16px; display: flex; align-items: center; gap: 12px; margin-bottom: 8px;">
        <span class="admin-status-badge badge-success" style="font-size: 11px;">MÔ PHỎNG GIẢ ĐỊNH</span>
        <span style="font-size: 13px; color: var(--text-main);">${data.simulation_disclaimer}</span>
      </div>
    `;
    if (data.catalog?.is_unverified) {
      bannerHtml += `
        <div style="background: rgba(245, 158, 11, 0.1); border: 1px solid rgba(245, 158, 11, 0.4); border-radius: 8px; padding: 10px 14px; font-size: 12px; color: #b45309; display: flex; align-items: center; gap: 8px;">
          <svg viewBox="0 0 16 16" fill="none" class="badge-icon" style="width: 16px; height: 16px; flex-shrink: 0;"><path d="M8 2.5 14 13H2L8 2.5Z" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/><path d="M8 6.5v3M8 11.5v.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>
          <span>${data.catalog.warning}</span>
        </div>
      `;
    }
    $('admin-preview-banner').innerHTML = bannerHtml;

    // 2. Counts
    $('admin-res-count-rec').textContent = data.recommendations?.length || 0;
    $('admin-res-count-eli').textContent = data.eligible_courses?.length || 0;
    $('admin-res-count-blk').textContent = data.blocked_courses?.length || 0;

    // 3. Recommended Table
    const tbodyRec = $('admin-tbody-rec');
    if (tbodyRec) {
      const recs = data.recommendations || [];
      if (!recs.length) {
        tbodyRec.innerHTML = '<tr><td colspan="6" style="text-align: center; color: var(--text-muted); padding: 16px;">Không có học phần nào được đề xuất cho hồ sơ này.</td></tr>';
      } else {
        tbodyRec.innerHTML = recs.map(r => `
          <tr>
            <td style="text-align: center;"><span class="admin-source-tag" style="font-weight: 700;">#${r.rank}</span></td>
            <td><strong>${r.code}</strong></td>
            <td>${r.name}</td>
            <td style="text-align: right; font-variant-numeric: tabular-nums;">${r.credits}</td>
            <td>
              <span class="admin-status-badge badge-success" style="font-size: 11px;">Điểm: ${Math.round(r.score * 100)}%</span>
            </td>
            <td style="font-size: 12px;">${r.reason || r.fit_reason || '-'}</td>
          </tr>
        `).join('');
      }
    }

    // 4. Eligible Table
    const tbodyEli = $('admin-tbody-eli');
    if (tbodyEli) {
      const elis = data.eligible_courses || [];
      if (!elis.length) {
        tbodyEli.innerHTML = '<tr><td colspan="5" style="text-align: center; color: var(--text-muted); padding: 16px;">Không có học phần nào đủ điều kiện.</td></tr>';
      } else {
        tbodyEli.innerHTML = elis.map(c => `
          <tr>
            <td><strong>${c.code}</strong></td>
            <td>${c.name}</td>
            <td style="text-align: right; font-variant-numeric: tabular-nums;">${c.credits}</td>
            <td><span class="admin-meta-tag">${c.block || '-'}</span></td>
            <td>${c.term || '-'}</td>
          </tr>
        `).join('');
      }
    }

    // 5. Blocked Table
    const tbodyBlk = $('admin-tbody-blk');
    if (tbodyBlk) {
      const blks = data.blocked_courses || [];
      if (!blks.length) {
        tbodyBlk.innerHTML = '<tr><td colspan="5" style="text-align: center; color: var(--text-muted); padding: 16px;">Không có học phần nào bị chặn.</td></tr>';
      } else {
        tbodyBlk.innerHTML = blks.map(b => {
          const reasonsText = (b.reasons || []).map(rs => {
            const prereqs = (rs.missing_prerequisites || []).flat().join(', ');
            return `<div>• ${rs.message}${prereqs ? ` (Thiếu: <span class="admin-reason-tag">${prereqs}</span>)` : ''}</div>`;
          }).join('');
          return `
            <tr>
              <td><strong>${b.code}</strong></td>
              <td>${b.name}</td>
              <td style="text-align: right; font-variant-numeric: tabular-nums;">${b.credits}</td>
              <td><span class="admin-meta-tag">${b.block || '-'}</span></td>
              <td style="font-size: 12px; color: #dc2626;">${reasonsText || 'Bị chặn'}</td>
            </tr>
          `;
        }).join('');
      }
    }

    // Switch to Recommended panel by default
    switchPreviewResultsTab('recommended');
  }

  function switchPreviewResultsTab(tab) {
    const tabs = {
      recommended: { btn: $('admin-res-tab-recommended'), panel: $('admin-res-panel-recommended') },
      eligible: { btn: $('admin-res-tab-eligible'), panel: $('admin-res-panel-eligible') },
      blocked: { btn: $('admin-res-tab-blocked'), panel: $('admin-res-panel-blocked') },
    };

    Object.entries(tabs).forEach(([k, item]) => {
      if (k === tab) {
        item.btn?.classList.add('active');
        if (item.panel) item.panel.hidden = false;
      } else {
        item.btn?.classList.remove('active');
        if (item.panel) item.panel.hidden = true;
      }
    });
  }

  $('admin-res-tab-recommended')?.addEventListener('click', () => switchPreviewResultsTab('recommended'));
  $('admin-res-tab-eligible')?.addEventListener('click', () => switchPreviewResultsTab('eligible'));
  $('admin-res-tab-blocked')?.addEventListener('click', () => switchPreviewResultsTab('blocked'));

    window.adminCurriculum = {
    load: loadCurriculum,
    renderPrograms,
    openProgramCourses,
    renderCourses,
    openPrereqEditor
  };

  window.adminCrawler = {
    load: loadDocuments,
    renderDocuments: renderCrawlerDocuments
  };


  // ==========================================================================
  // Academic Announcements Management
  // ==========================================================================
  let announcementsList = [];
  let announcementsTotal = 0;

  async function loadAnnouncements() {
    loadAnnouncementsSummary();
    fetchAnnouncements();
  }

  async function loadAnnouncementsSummary() {
    try {
      const summary = await window.systemAuth.request('/admin/announcements/summary');
      if ($('admin-ann-kpi-total')) $('admin-ann-kpi-total').textContent = summary.total || 0;
      if ($('admin-ann-kpi-published')) $('admin-ann-kpi-published').textContent = summary.published || 0;
      if ($('admin-ann-kpi-other')) $('admin-ann-kpi-other').textContent = (summary.draft || 0) + (summary.expired || 0);
    } catch (err) {
      console.warn('Failed to load announcements summary:', err);
    }
  }

  async function fetchAnnouncements() {
    const status = $('admin-ann-status-filter')?.value || 'all';
    const audience = $('admin-ann-audience-filter')?.value || 'all';
    const q = $('admin-ann-search')?.value || '';

    const params = new URLSearchParams();
    if (status !== 'all') params.set('status', status);
    if (audience !== 'all') params.set('audience', audience);
    if (q.trim()) params.set('q', q.trim());

    try {
      const data = await window.systemAuth.request(`/admin/announcements?${params.toString()}`);
      announcementsList = data.items || [];
      announcementsTotal = data.total || 0;
      renderAnnouncementsTable();
    } catch (err) {
      console.warn('Failed to fetch announcements:', err);
    }
  }

  function renderAnnouncementsTable() {
    const tbody = $('admin-ann-tbody');
    if (!tbody) return;

    if (!announcementsList.length) {
      tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; color: var(--text-muted); padding: 24px;">Chưa có thông báo học thuật nào phù hợp với bộ lọc.</td></tr>';
      return;
    }

    tbody.innerHTML = announcementsList.map(a => {
      let statusBadge = '<span class="admin-status-badge badge-warning">Bản thảo</span>';
      if (a.status === 'published') {
        statusBadge = '<span class="admin-status-badge badge-success">Đang phát hành</span>';
      } else if (a.status === 'expired') {
        statusBadge = '<span class="admin-status-badge" style="background: var(--soft-surface); color: var(--text-muted);">Đã hết hạn</span>';
      }

      const audLabels = { all: 'Tất cả', students: 'Sinh viên', faculty: 'Giảng viên' };
      const audText = audLabels[a.audience] || a.audience;

      const effDate = a.effective_date ? new Date(a.effective_date).toLocaleDateString('vi-VN') : '-';
      const expDate = a.expiry_date ? new Date(a.expiry_date).toLocaleDateString('vi-VN') : 'Không thời hạn';

      let actionBtns = '';
      if (a.status === 'draft') {
        actionBtns += `<button type="button" class="portal-button admin-ann-btn-publish" data-id="${a.id}" style="font-size: 11px; padding: 4px 8px; margin-right: 4px; color: #10b981;">Phát hành</button>`;
      } else if (a.status === 'published') {
        actionBtns += `<button type="button" class="portal-button admin-ann-btn-expire" data-id="${a.id}" style="font-size: 11px; padding: 4px 8px; margin-right: 4px; color: #f59e0b;">Đóng / Hết hạn</button>`;
      }
      actionBtns += `<button type="button" class="portal-button admin-ann-btn-delete" data-id="${a.id}" style="font-size: 11px; padding: 4px 8px; color: #ef4444;">Xóa</button>`;

      return `
        <tr>
          <td>
            <strong>${a.title}</strong>
            <div style="font-size: 12px; color: var(--text-muted); margin-top: 2px; max-width: 320px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${a.content}</div>
          </td>
          <td>
            <a href="${a.source_url}" target="_blank" rel="noopener noreferrer" style="color: var(--accent-primary, #4361ee); text-decoration: underline; font-size: 12px; display: inline-flex; align-items: center; gap: 4px;">
              <span>Văn bản nguồn</span>
              <svg viewBox="0 0 16 16" fill="none" style="width: 12px; height: 12px;"><path d="M6 3h7v7M13 3 6.5 9.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>
            </a>
          </td>
          <td><span class="admin-meta-tag">${audText}</span></td>
          <td style="font-size: 12px; font-variant-numeric: tabular-nums;">${effDate}</td>
          <td style="font-size: 12px; font-variant-numeric: tabular-nums;">${expDate}</td>
          <td>${statusBadge}</td>
          <td style="text-align: right; white-space: nowrap;">${actionBtns}</td>
        </tr>
      `;
    }).join('');

    // Bind action buttons
    tbody.querySelectorAll('.admin-ann-btn-publish').forEach(btn => {
      btn.addEventListener('click', async (e) => {
        const id = e.currentTarget.dataset.id;
        try {
          await window.systemAuth.request(`/admin/announcements/${id}/publish`, 'POST');
          loadAnnouncements();
        } catch (err) {
          alert('Không thể phát hành thông báo: ' + err.message);
        }
      });
    });

    tbody.querySelectorAll('.admin-ann-btn-expire').forEach(btn => {
      btn.addEventListener('click', async (e) => {
        const id = e.currentTarget.dataset.id;
        try {
          await window.systemAuth.request(`/admin/announcements/${id}/expire`, 'POST');
          loadAnnouncements();
        } catch (err) {
          alert('Không thể chuyển trạng thái hết hạn: ' + err.message);
        }
      });
    });

    tbody.querySelectorAll('.admin-ann-btn-delete').forEach(btn => {
      btn.addEventListener('click', async (e) => {
        const id = e.currentTarget.dataset.id;
        if (!confirm('Bạn có chắc chắn muốn xóa thông báo này?')) return;
        try {
          await window.systemAuth.request(`/admin/announcements/${id}`, 'DELETE');
          loadAnnouncements();
        } catch (err) {
          alert('Không thể xóa thông báo: ' + err.message);
        }
      });
    });
  }

  // Hook filters
  $('admin-ann-status-filter')?.addEventListener('change', fetchAnnouncements);
  $('admin-ann-audience-filter')?.addEventListener('change', fetchAnnouncements);
  $('admin-ann-search')?.addEventListener('input', fetchAnnouncements);

  // Hook modal dialog
  const annModal = $('admin-ann-modal');
  $('admin-ann-create-btn')?.addEventListener('click', () => {
    $('admin-ann-form')?.reset();
    annModal?.showModal();
  });
  $('admin-ann-modal-close')?.addEventListener('click', () => annModal?.close());
  $('admin-ann-cancel-btn')?.addEventListener('click', () => annModal?.close());

  // Form submit
  $('admin-ann-form')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const title = $('admin-ann-input-title')?.value || '';
    const sourceUrl = $('admin-ann-input-source')?.value || '';
    const audience = $('admin-ann-input-audience')?.value || 'all';
    const effective = $('admin-ann-input-effective')?.value || null;
    const expiry = $('admin-ann-input-expiry')?.value || null;
    const content = $('admin-ann-input-content')?.value || '';

    try {
      await window.systemAuth.request('/admin/announcements', 'POST', {
        title,
        source_url: sourceUrl,
        audience,
        effective_date: effective ? new Date(effective).toISOString() : null,
        expiry_date: expiry ? new Date(expiry).toISOString() : null,
        content,
      });
      annModal?.close();
      loadAnnouncements();
    } catch (err) {
      alert('Không thể tạo thông báo: ' + err.message);
    }
  });

  window.adminAnnouncements = {
    load: loadAnnouncements,
  };

    window.adminAudit = {
    load() {
      loadAuditMetrics();
      loadAuditLogs();
    },
  };

  // ==========================================================================
  // Operational & Consultation Health Monitoring
  // ==========================================================================
  let currentHealthWindow = '24h';
  let healthMetricsData = null;

  const ROUTE_LABELS = {
    academic: 'Học thuật & CTĐT',
    portal: 'Cổng đào tạo VNU',
    auth: 'Xác thực & Phiên',
    consultation: 'Cố vấn & Khuyến nghị',
    admin: 'Quản trị hệ thống',
    other: 'Khác'
  };

  async function loadOperationalHealth(win = currentHealthWindow) {
    currentHealthWindow = win;
    try {
      if (!window.systemAuth?.request) return;
      const data = await window.systemAuth.request(`/admin/metrics/health?window=${encodeURIComponent(win)}`);
      healthMetricsData = data;
      renderOperationalHealth(data);
    } catch (err) {
      console.warn('Failed to load operational health:', err);
    }
  }

  
  function createHealthCard(title, iconSvg, valueHtml, noteHtml, sourceText, isWarning = false) {
    const card = document.createElement('article');
    card.className = 'admin-health-kpi-card admin-kpi-card-base' + (isWarning ? ' is-warning' : '');

    card.innerHTML = `
      <div class="admin-kpi-head">
        <div class="admin-kpi-icon-wrap" aria-hidden="true">${iconSvg}</div>
        <h4 class="admin-kpi-title">${title}</h4>
      </div>
      <div class="admin-kpi-body">
        <div class="admin-health-value-row">${valueHtml}</div>
        ${noteHtml ? `<p class="admin-kpi-note">${noteHtml}</p>` : ''}
      </div>
      <div class="admin-kpi-foot">
        <span class="admin-source-tag">${getCopy('adminSourcePrefix')}${sourceText}</span>
        <span class="admin-time-tag">${getCopy('adminJustNow')}</span>
      </div>
    `;
    return card;
  }

  function renderOperationalHealth(data) {
    if (!data) return;

    // 1. Health KPI cards
    const kpiGrid = $('admin-health-kpi-grid');
    if (kpiGrid) {
      kpiGrid.replaceChildren();
      const oh = data.overall_health || {};
      const ch = data.consultation_health || {};
      const fb = data.feedback_signals || {};

      // Card 1: Traffic & Success Rate
      let successValHtml = '';
      if (oh.status === 'available' && oh.total_requests !== null) {
        successValHtml = `
          <div style="display: flex; align-items: baseline; gap: 8px;">
            <span class="admin-metric-number" data-metric="overall-success">${oh.success_rate_pct}%</span>
            <span style="font-size: 13px; color: var(--text-muted); font-variant-numeric: tabular-nums;">(${Number(oh.total_requests).toLocaleString()} reqs)</span>
          </div>
        `;
      } else {
        successValHtml = `<span class="admin-metric-unavailable" data-health-unavailable="true">${getCopy('adminUnavailable')}</span>`;
      }
      const trafficCard = createHealthCard(
        'Lưu lượng & Tỉ lệ Thành công',
        `<svg viewBox="0 0 20 20" fill="none"><path d="M3 13.5l4-4 3.5 3.5L17 6.5M13.5 6.5H17V10" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>`,
        successValHtml,
        oh.status === 'available' ? `Lỗi hệ thống (5xx): ${oh.server_error_rate_pct || 0}%` : 'Chưa có yêu cầu ghi nhận',
        `telemetry:${data.window}`
      );
      kpiGrid.append(trafficCard);

      // Card 2: Latency p50 / p95
      let latencyValHtml = '';
      if (oh.status === 'available' && oh.p50_latency_ms !== null) {
        latencyValHtml = `
          <div style="display: flex; align-items: baseline; gap: 10px;">
            <span class="admin-metric-number" data-metric="p50-latency">${oh.p50_latency_ms}<small style="font-size: 14px; font-weight: normal; margin-left: 2px;">ms</small></span>
            <span style="font-size: 12px; color: var(--text-muted); font-variant-numeric: tabular-nums;">p95: ${oh.p95_latency_ms}ms</span>
          </div>
        `;
      } else {
        latencyValHtml = `<span class="admin-metric-unavailable" data-health-unavailable="true">${getCopy('adminUnavailable')}</span>`;
      }
      const latencyCard = createHealthCard(
        'Độ trễ Phản hồi (p50 / p95)',
        `<svg viewBox="0 0 20 20" fill="none"><circle cx="10" cy="10" r="7" stroke="currentColor" stroke-width="1.5"/><path d="M10 6.5v4l2.5 1.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>`,
        latencyValHtml,
        oh.status === 'available' ? 'Độ trễ trung vị qua các API endpoints' : 'Chưa có mẫu thời gian',
        'runtime:timings'
      );
      kpiGrid.append(latencyCard);

      // Card 3: Consultation Health
      let consultValHtml = '';
      let isConsultWarn = false;
      if (ch.status === 'available' && ch.total_consultations !== null) {
        const failRate = ch.failure_rate_pct || 0;
        if (failRate > 10) isConsultWarn = true;
        consultValHtml = `
          <div style="display: flex; align-items: baseline; gap: 8px;">
            <span class="admin-metric-number" data-metric="consultation-failures" style="${failRate > 0 ? 'color: #f59e0b;' : ''}">${failRate}%</span>
            <span style="font-size: 13px; color: var(--text-muted); font-variant-numeric: tabular-nums;">lỗi (${ch.total_consultations} lượt)</span>
          </div>
        `;
      } else {
        consultValHtml = `<span class="admin-metric-unavailable" data-health-unavailable="true">${getCopy('adminUnavailable')}</span>`;
      }
      const consultCard = createHealthCard(
        'Sức khỏe Cố vấn & Khuyến nghị',
        `<svg viewBox="0 0 20 20" fill="none"><path d="M4 4h12v9a3 3 0 0 1-3 3H7a3 3 0 0 1-3-3V4Z" stroke="currentColor" stroke-width="1.5"/><path d="M7 8h6M7 11h4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>`,
        consultValHtml,
        ch.status === 'available' ? `Thời gian xử lý TB: ${ch.avg_duration_ms || 0}ms` : 'Không có phiên tư vấn',
        'domain:consultation',
        isConsultWarn
      );
      kpiGrid.append(consultCard);

      // Card 4: Quality & Feedback Signals
      let fbValHtml = '';
      if (fb.status === 'available' && fb.total_feedbacks !== null) {
        fbValHtml = `
          <div style="display: flex; align-items: baseline; gap: 8px;">
            <span class="admin-metric-number" data-metric="feedback-positive">${fb.positive_rate_pct}%</span>
            <span style="font-size: 13px; color: var(--text-muted); font-variant-numeric: tabular-nums;">hài lòng (${fb.total_feedbacks} mẫu)</span>
          </div>
        `;
      } else {
        fbValHtml = `<span class="admin-metric-unavailable" data-health-unavailable="true">Chưa ghi nhận</span>`;
      }
      const fbCard = createHealthCard(
        'Tín hiệu Chất lượng Người dùng',
        `<svg viewBox="0 0 20 20" fill="none"><path d="M10 2.5l2.3 4.7 5.2.8-3.7 3.6.9 5.2-4.7-2.5-4.7 2.5.9-5.2-3.7-3.6 5.2-.8L10 2.5Z" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/></svg>`,
        fbValHtml,
        fb.status === 'available' ? 'Đánh giá hữu ích từ sinh viên' : 'Chưa có khảo sát phản hồi',
        'user:feedback'
      );
      kpiGrid.append(fbCard);
    }

    // 2. Route Groups Table
    const tbody = $('admin-route-groups-tbody');
    if (tbody && data.route_groups) {
      tbody.replaceChildren();
      const groups = ['academic', 'portal', 'auth', 'consultation', 'admin', 'other'];
      groups.forEach(grp => {
        const row = document.createElement('tr');
        const gdata = data.route_groups[grp];
        const label = ROUTE_LABELS[grp] || grp;

        if (!gdata || gdata.status === 'unavailable' || gdata.total_requests === null) {
          row.innerHTML = `
            <td><strong>${label}</strong></td>
            <td class="num" style="color: var(--text-muted);">-</td>
            <td class="num" style="color: var(--text-muted);">-</td>
            <td class="num" style="color: var(--text-muted);">-</td>
            <td class="num" style="color: var(--text-muted);">-</td>
            <td class="num" style="color: var(--text-muted);">-</td>
            <td style="text-align: center;"><span class="admin-status-badge" style="background: var(--soft-surface); color: var(--text-muted); font-size: 11px;">Chưa có request</span></td>
          `;
        } else {
          const successPct = gdata.success_rate_pct ?? 0;
          const errorPct = gdata.error_rate_pct ?? 0;
          let badgeStatus = '<span class="admin-status-badge badge-success" style="font-size: 11px;">Ổn định</span>';
          if (errorPct > 20) {
            badgeStatus = '<span class="admin-status-badge badge-danger" style="font-size: 11px;">Báo động</span>';
          } else if (errorPct > 5) {
            badgeStatus = '<span class="admin-status-badge badge-warning" style="font-size: 11px;">Cảnh báo</span>';
          }

          row.innerHTML = `
            <td><strong>${label}</strong></td>
            <td class="num">${Number(gdata.total_requests).toLocaleString()}</td>
            <td class="num">
              <span>${successPct}%</span>
              <span class="admin-rate-bar-wrap" aria-hidden="true"><span class="admin-rate-bar-fill" style="width: ${Math.min(100, successPct)}%;"></span></span>
            </td>
            <td class="num" style="${errorPct > 0 ? 'color: #ef4444; font-weight: 600;' : ''}">${errorPct}%</td>
            <td class="num">${gdata.p50_latency_ms}</td>
            <td class="num">${gdata.p95_latency_ms}</td>
            <td style="text-align: center;">${badgeStatus}</td>
          `;
        }
        tbody.append(row);
      });
    }

    // 3. Consultation Breakdown details
    const consultBox = $('admin-consultation-health-details');
    if (consultBox) {
      consultBox.replaceChildren();
      const ch = data.consultation_health || {};
      const fb = data.feedback_signals || {};

      let reasonsHtml = '';
      if (ch.top_failure_reasons && ch.top_failure_reasons.length > 0) {
        reasonsHtml = ch.top_failure_reasons.map(r => `
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
            <span class="admin-reason-tag">${r.reason}</span>
            <span style="font-size: 12px; font-weight: 600; font-variant-numeric: tabular-nums;">${r.count} sự cố</span>
          </div>
        `).join('');
      } else {
        reasonsHtml = `<div style="font-size: 12px; color: var(--text-muted); font-style: italic;">Không có sự cố nào được ghi nhận.</div>`;
      }

      consultBox.innerHTML = `
        <div class="admin-consult-stat-row">
          <span class="admin-consult-stat-label">Tổng lượt phân tích & cố vấn</span>
          <span class="admin-consult-stat-val">${ch.total_consultations !== null ? Number(ch.total_consultations).toLocaleString() : 'Chưa có'}</span>
        </div>
        <div class="admin-consult-stat-row">
          <span class="admin-consult-stat-label">Lượt thực hiện thành công</span>
          <span class="admin-consult-stat-val" style="color: #10b981;">${ch.successful_consultations !== null ? Number(ch.successful_consultations).toLocaleString() : '-'}</span>
        </div>
        <div class="admin-consult-stat-row">
          <span class="admin-consult-stat-label">Lượt gặp sự cố / chặn điều kiện</span>
          <span class="admin-consult-stat-val" style="${(ch.failed_consultations || 0) > 0 ? 'color: #f59e0b;' : ''}">${ch.failed_consultations !== null ? Number(ch.failed_consultations).toLocaleString() : '-'}</span>
        </div>
        <div style="margin-top: 14px;">
          <h6 style="font-size: 12px; font-weight: 600; color: var(--text-muted); margin: 0 0 8px 0; text-transform: uppercase; letter-spacing: 0.04em;">Nguyên nhân sự cố phổ biến</h6>
          ${reasonsHtml}
        </div>
        <div style="margin-top: 16px; padding-top: 12px; border-top: 1px dashed var(--border-medium);">
          <div style="display: flex; justify-content: space-between; align-items: center; font-size: 12px;">
            <span style="color: var(--text-muted);">Khung mẫu phân tích:</span>
            <span style="font-weight: 600;">${data.sample_count || 0} telemetry points</span>
          </div>
        </div>
      `;
    }
  }

  // Hook window selector pills
  document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.admin-window-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        document.querySelectorAll('.admin-window-btn').forEach(b => b.classList.remove('active'));
        e.currentTarget.classList.add('active');
        const win = e.currentTarget.dataset.window || '24h';
        loadOperationalHealth(win);
      });
    });
  });

})();
