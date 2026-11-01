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
      tdId.innerHTML = `<code class="admin-course-code">${p.program_id}</code>`;

      // 2. Name
      const tdName = tr.insertCell();
      tdName.innerHTML = `<strong>${p.name}</strong>`;

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
      tdCode.innerHTML = `<code class="admin-course-code">${c.code}</code>`;

      // 2. Name
      const tdName = tr.insertCell();
      tdName.innerHTML = `<strong>${c.name}</strong>${c.name_en ? `<div class="admin-sub-text">${c.name_en}</div>` : ''}`;

      // 3. Credits
      const tdCredits = tr.insertCell();
      tdCredits.className = 'tabular-nums';
      tdCredits.textContent = c.credits;

      // 4. Block
      const tdBlock = tr.insertCell();
      tdBlock.innerHTML = `<span class="admin-meta-tag">${c.block || 'Chưa phân khối'}</span>`;

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
          previewDiv.hidden = false;
          previewDiv.innerHTML = `
            <div class="preview-header">
              <span class="preview-status-pill danger">Lỗi hệ thống</span>
            </div>
            <p class="err-msg">${err.message}</p>
          `;
        }
      } finally {
        if (submitBtn) submitBtn.disabled = false;
      }
    });
  }

  function renderImportPreview(data) {
    const previewDiv = $('admin-import-preview');
    if (!previewDiv) return;
    const summary = data.validation_summary || {};
    const isValid = summary.valid;
    const stats = summary.stats || {};
    const errors = summary.errors || [];
    const warnings = summary.warnings || [];

    previewDiv.hidden = false;
    let html = `
      <div class="preview-header">
        <strong>Kết quả kiểm tra dữ liệu:</strong>
        <span class="preview-status-pill ${isValid ? 'success' : 'danger'}">
          ${isValid ? '✓ Hợp lệ (Đã tạo bản thảo)' : '⚠ Có lỗi cần chỉnh sửa'}
        </span>
      </div>
      <div style="margin: 6px 0; color: var(--text-muted); font-size: 0.82rem;">
        Mã bản thảo: <code style="font-family: 'JetBrains Mono', monospace;">${data.revision_id}</code> | 
        Số học phần: <strong>${stats.course_count || 0}</strong> | 
        Tổng tín chỉ: <strong>${stats.total_credits || 0}</strong>
      </div>
    `;

    if (errors.length > 0) {
      html += `
        <div style="margin-top: 8px;">
          <strong class="err-msg">Danh sách lỗi (${errors.length}):</strong>
          <ul>
            ${errors.map(err => `<li class="err-msg">Dòng ${err.row || '-'}: ${err.message}</li>`).join('')}
          </ul>
        </div>
      `;
    }

    if (warnings.length > 0) {
      html += `
        <div style="margin-top: 8px;">
          <strong class="warn-msg">Cảnh báo (${warnings.length}):</strong>
          <ul>
            ${warnings.map(w => `<li class="warn-msg">${w.message}</li>`).join('')}
          </ul>
        </div>
      `;
    }

    if (isValid) {
      html += `
        <div style="margin-top: 10px; padding: 8px; border-radius: 4px; background: rgba(16, 185, 129, 0.1); color: #10b981;">
          ✓ Bản thảo đã được lưu trữ an toàn trong hàng đợi kiểm duyệt. Không ảnh hưởng đến dữ liệu đang vận hành.
        </div>
      `;
    }

    previewDiv.innerHTML = html;
  }
  bindImportModal();

  // Expose module APIs
  window.adminOverview = {
    load: loadOverview,
    render: renderOverview,
    renderError,
    get data() { return overviewData; }
  };

  window.adminCurriculum = {
    load: loadCurriculum,
    renderPrograms,
    openProgramCourses,
    renderCourses
  };
})();
