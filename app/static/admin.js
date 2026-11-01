/* HUS Admin Console UI Module: Overview Dashboard and Sourced Metrics. */
(() => {
  'use strict';

  const $ = id => document.getElementById(id);
  const t = key => (window.workspaceI18n ? window.workspaceI18n.t(key) : null) || key;

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

  // Expose module API
  window.adminOverview = {
    load: loadOverview,
    render: renderOverview,
    renderError,
    get data() { return overviewData; }
  };
})();
