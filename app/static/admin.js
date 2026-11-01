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

  // ==========================================================================
  // Revisions & Review Workflow (Diff, Approve, Publish, Rollback)
  // ==========================================================================
  let curriculumRevisions = [];

  const subtabPrograms = $('admin-curriculum-subtab-programs');
  const subtabRevisions = $('admin-curriculum-subtab-revisions');
  const programsView = $('admin-curriculum-container');
  const programsToolbar = document.querySelector('.admin-curriculum-toolbar');
  const revisionsView = $('admin-curriculum-revisions-view');
  const diffModal = $('admin-diff-modal');
  const diffCloseBtn = $('admin-diff-close-btn');
  const diffDismissBtn = $('admin-diff-dismiss-btn');

  function switchCurriculumSubtab(tab) {
    if (tab === 'programs') {
      subtabPrograms?.classList.add('active');
      subtabPrograms?.setAttribute('aria-selected', 'true');
      subtabRevisions?.classList.remove('active');
      subtabRevisions?.setAttribute('aria-selected', 'false');
      if (programsView) programsView.hidden = false;
      if (programsToolbar) programsToolbar.hidden = false;
      if (revisionsView) revisionsView.hidden = true;
    } else {
      subtabPrograms?.classList.remove('active');
      subtabPrograms?.setAttribute('aria-selected', 'false');
      subtabRevisions?.classList.add('active');
      subtabRevisions?.setAttribute('aria-selected', 'true');
      if (programsView) programsView.hidden = true;
      if (programsToolbar) programsToolbar.hidden = true;
      if (revisionsView) revisionsView.hidden = false;
      loadRevisions();
    }
  }

  subtabPrograms?.addEventListener('click', () => switchCurriculumSubtab('programs'));
  subtabRevisions?.addEventListener('click', () => switchCurriculumSubtab('revisions'));
  $('admin-revisions-refresh-btn')?.addEventListener('click', () => loadRevisions());
  $('admin-revisions-search')?.addEventListener('input', renderRevisions);
  $('admin-revisions-status-filter')?.addEventListener('change', renderRevisions);

  diffCloseBtn?.addEventListener('click', () => diffModal?.close());
  diffDismissBtn?.addEventListener('click', () => diffModal?.close());

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
      tdId.innerHTML = `<code class="admin-course-code">${rev.revision_id}</code>`;

      // 2. Program ID
      const tdProg = tr.insertCell();
      tdProg.innerHTML = `<code>${rev.program_id}</code>`;

      // 3. Title
      const tdTitle = tr.insertCell();
      tdTitle.innerHTML = `<strong>${rev.version_title}</strong>`;

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
    });
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
    renderCourses,
    openPrereqEditor
  };
})();
