/* Source-owned curriculum board; semester selections never become passed facts. */
(() => {
  'use strict';
  const root = document.getElementById('course-status-board');
  const copy = (vi, en) => window.workspaceI18n.language === 'en' ? en : vi;
  let source = null, board = null, loading = false, failed = false, budget = 20, savingBinding = false;
  let sequence = 0, controller, search = '', track = '', path = '', planError = '';
  let chosen = new Set();
  let savedPlans = [], activePlan = null, planBusy = false, plansLoading = false;
  let planOwnerEpoch = 0, plansSequence = 0, planMessage = '', planTitle = '', planYear = new Date().getFullYear(), planSemester = 1;
  let planDirty = false;
  let sourceKey = '', sourceOwner = null, restoringDraft = false;
  const draftKey = 'study-workspace-semester-draft-v1';
  const sessionIdentity = () => {
    const account = window.systemAuth?.account;
    return account?.account_id && account?.session_id ? `${account.account_id}:${account.session_id}` : null;
  };
  function clearDraft() { try { sessionStorage.removeItem(draftKey); } catch { /* Optional storage. */ } }
  function saveDraft() {
    const owner = sessionIdentity();
    if (!source || !owner || sourceOwner !== owner) return;
    try {
      sessionStorage.setItem(draftKey, JSON.stringify({schema: 1, owner,
        title: planTitle, year: Number(planYear), semester: Number(planSemester), budget,
        track, path, search, codes: [...chosen], dirty: planDirty,
        planId: activePlan?.id || null, version: activePlan?.version || null,
        basis: board?.plan_basis || null}));
    } catch { /* In-memory editing remains available when storage is blocked. */ }
  }
  function restoreDraft() {
    try {
      const raw = sessionStorage.getItem(draftKey);
      if (!raw) return;
      if (raw.length > 20000) { clearDraft(); return; }
      const value = JSON.parse(raw);
      if (value.schema !== 1 || value.owner !== sessionIdentity()) { clearDraft(); return; }
      if (!Array.isArray(value.codes) || value.codes.length > 100
          || !value.codes.every(code => typeof code === 'string' && code.length <= 100)
          || !Number.isInteger(value.budget) || value.budget < 1 || value.budget > 30
          || !Number.isInteger(value.year) || value.year < 2000 || value.year > 2100
          || ![1, 2, 3].includes(value.semester)
          || !['title', 'track', 'path', 'search'].every(key => typeof value[key] === 'string' && value[key].length <= 500)) {
        clearDraft(); return;
      }
      planTitle = value.title; planYear = value.year; planSemester = value.semester;
      budget = value.budget; track = value.track; path = value.path; search = value.search;
      chosen = new Set(value.codes); planDirty = Boolean(value.dirty); restoringDraft = true;
      if (typeof value.planId === 'string' && Number.isInteger(value.version) && value.version > 0) {
        activePlan = {id: value.planId, version: value.version, courses: [], program_id: '',
          title: planTitle, academic_year_start: planYear, semester: planSemester,
          max_credits: budget, total_credits: 0, course_codes: value.codes};
      }
      planMessage = copy('Đã khôi phục bản nháp của phiên này. Dữ liệu học vụ vẫn được kiểm tra lại khi lưu.', 'Draft restored for this session. Academic data is rechecked when you save.');
    } catch { clearDraft(); }
  }
  window.addEventListener('pagehide', saveDraft);
  document.addEventListener('workspace:account-change', () => {
    try {
      const draft = JSON.parse(sessionStorage.getItem(draftKey) || 'null');
      if (draft && draft.owner !== sessionIdentity()) clearDraft();
    } catch { clearDraft(); }
  });
  document.addEventListener('workspace:session-expired', clearDraft);
  const planErrors = code => ({
    context_changed: copy('Bảng điểm hoặc CTĐT đã đổi. Hãy tải lại trước khi lưu.', 'Source data changed. Refresh before saving.'),
    semester_plan_conflict: copy('Phương án đã được sửa ở tab khác. Hãy mở lại phương án.', 'This plan changed in another tab. Reopen it before editing.'),
    semester_plan_course_unavailable: copy('Có môn không còn đủ điều kiện. Bỏ môn đó trước khi lưu.', 'Some courses are no longer eligible. Remove them before saving.'),
    semester_plan_group_full: copy('Lựa chọn vượt yêu cầu nhóm tự chọn.', 'Selected courses exceed the elective group requirement.'),
    semester_plan_budget_exceeded: copy('Tổng tín chỉ vượt ngân sách.', 'Selected credits exceed the budget.'),
    semester_plan_limit: copy('Đã đạt giới hạn 100 phương án. Xóa phương án không cần thiết.', 'You have reached 100 plans. Delete unused alternatives.')
  })[code] || copy('Chưa lưu được kế hoạch. Kiểm tra dữ liệu và thử lại.', 'Could not save the plan. Check the data and try again.');

  async function plansRequest(url, method = 'GET', body) {
    const response = await fetch(url, {method, credentials: 'same-origin', cache: 'no-store',
      headers: {'Content-Type': 'application/json', 'X-CSRF-Token': window.systemAuth?.csrf || ''},
      body: body ? JSON.stringify(body) : undefined});
    if (response.status === 401) document.dispatchEvent(new Event('workspace:session-expired'));
    const result = await response.json();
    if (!response.ok) throw new Error(typeof result.detail === 'string' ? result.detail : 'invalid_semester_plan');
    return result;
  }

  async function fetchPlans() {
    if (!source) return;
    const current = ++plansSequence;
    plansLoading = true; render();
    try {
      const result = await plansRequest('/me/semester-plans');
      if (current !== plansSequence) return;
      savedPlans = result.plans;
      if (activePlan) {
        const saved = savedPlans.find(plan => plan.id === activePlan.id);
        if (saved) activePlan = {...saved, version: activePlan.version};
        else {
          activePlan = null; planDirty = true;
          planMessage = copy('Bản lưu không còn tồn tại; bản nháp được giữ để lưu thành phương án mới.', 'The saved plan no longer exists; your draft is retained as a new alternative.');
        }
      }
    } catch (error) { if (current === plansSequence) planMessage = planErrors(error.message); }
    finally { if (current === plansSequence) { plansLoading = false; render(); } }
  }

  async function persistPlan(remove = false) {
    if (planBusy || !source) return;
    const current = planOwnerEpoch;
    planBusy = true; planMessage = ''; render();
    try {
      const url = '/me/semester-plans' + (activePlan ? `/${encodeURIComponent(activePlan.id)}` : '');
      if (remove) {
        if (!activePlan) return;
        await plansRequest(`${url}?expected_version=${activePlan.version}`, 'DELETE');
        if (current !== planOwnerEpoch) return;
        activePlan = null; planDirty = false; planTitle = '';
      } else {
        const result = await plansRequest(url, activePlan ? 'PUT' : 'POST', {
          title: planTitle.trim(), academic_year_start: Number(planYear), semester: Number(planSemester),
          max_credits: budget, selected_track_id: track || null,
          selected_graduation_path_id: path || null, course_codes: [...chosen],
          expected_basis: board.plan_basis, ...(activePlan ? {expected_version: activePlan.version} : {})
        });
        if (current !== planOwnerEpoch) return;
        activePlan = result; planDirty = false;
      }
      planMessage = remove ? copy('Đã xóa phương án.', 'Plan deleted.') : copy('Đã lưu kế hoạch.', 'Plan saved.');
      await fetchPlans();
    } catch (error) { if (current === planOwnerEpoch) planMessage = planErrors(error.message); }
    finally { if (current === planOwnerEpoch) { planBusy = false; render(); } }
  }

  function renderSavedPlans(ready) {
    const section = el('section', undefined, 'semester-plans workspace-surface');
    section.id = 'semester-plans';
    section.append(el('h3', copy('Kế hoạch học kỳ đã lưu', 'Saved semester plans')),
      el('p', copy('Lưu nhiều phương án; đây là kế hoạch cá nhân, không phải đăng ký học VNU.', 'Save alternatives; these are personal plans, not VNU course registrations.')));
    const pickerLabel = el('label', copy('Phương án', 'Alternative'));
    const picker = el('select'); picker.id = 'semester-plan-picker';
    picker.append(new Option(copy('Phương án mới', 'New alternative'), ''));
    savedPlans.forEach(plan => picker.append(new Option(`${plan.title} · HK${plan.semester} ${plan.academic_year_start}–${plan.academic_year_start + 1}${plan.needs_review ? ' ⚠' : ''}`, plan.id)));
    picker.value = activePlan?.id || ''; picker.disabled = planBusy || plansLoading;
    picker.onchange = () => {
      if (planDirty && !window.confirm(copy('Bỏ thay đổi chưa lưu?', 'Discard unsaved changes?'))) { picker.value = activePlan?.id || ''; return; }
      activePlan = savedPlans.find(plan => plan.id === picker.value) || null;
      planMessage = ''; planDirty = false;
      if (activePlan) {
        planTitle = activePlan.title; planYear = activePlan.academic_year_start; planSemester = activePlan.semester;
        budget = activePlan.max_credits; track = activePlan.selected_track_id || ''; path = activePlan.selected_graduation_path_id || '';
        chosen = new Set(activePlan.course_codes);
      } else { planTitle = ''; chosen = new Set(board?.plan?.course_codes || []); }
      load();
    };
    pickerLabel.append(picker); section.append(pickerLabel);
    if (plansLoading) section.append(el('p', copy('Đang tải phương án…', 'Loading plans…')));
    if (activePlan) {
      const current = savedPlans.find(plan => plan.id === activePlan.id) || activePlan;
      const changed = current.needs_review;
      if (changed) {
        const warning = el('p', copy('Bảng điểm, chương trình hoặc quy chế đã thay đổi. Kiểm tra lại môn trước khi lưu; bản cũ được giữ nguyên.', 'Source data, curriculum or policy changed. Review courses before saving; your saved version is retained.'), 'course-status-notice');
        warning.setAttribute('role', 'status'); section.append(warning);
      }
      section.append(el('p', `${activePlan.program_id} · ${copy('Đã lưu', 'Saved')}: ${activePlan.total_credits}/${activePlan.max_credits} ${copy('TC', 'credits')}`, 'source-profile-value'));
      if (activePlan.selected_track_id || activePlan.selected_graduation_path_id) section.append(el('p',
        `${copy('Hướng/nhánh đã lưu', 'Saved track/path')}: ${activePlan.selected_track_id || '—'} / ${activePlan.selected_graduation_path_id || '—'}`, 'source-profile-value'));
    }
    const form = el('form'); form.id = 'semester-plan-form';
    const fields = el('div', undefined, 'semester-plan-fields');
    for (const [id, labelText, type, value, update] of [
      ['title', copy('Tên phương án', 'Plan name'), 'text', planTitle, value => { planTitle = value; }],
      ['year', copy('Năm bắt đầu (2026 → 2026–2027)', 'Starting year (2026 → 2026–2027)'), 'number', planYear, value => { planYear = value; }]
    ]) {
      const label = el('label', labelText), input = el('input'); input.id = `semester-plan-${id}`;
      input.type = type; input.value = value; input.required = true; input.disabled = planBusy;
      if (type === 'number') { input.min = '2000'; input.max = '2100'; input.step = '1'; } else input.maxLength = 100;
      input.oninput = () => { update(input.value); planDirty = true; saveDraft(); }; label.append(input); fields.append(label);
    }
    const termLabel = el('label', copy('Học kỳ', 'Semester')), term = el('select'); term.id = 'semester-plan-term';
    [1, 2, 3].forEach(number => term.append(new Option(`${copy('Học kỳ', 'Semester')} ${number}`, String(number))));
    term.value = String(planSemester); term.disabled = planBusy;
    term.onchange = () => { planSemester = Number(term.value); planDirty = true; saveDraft(); }; termLabel.append(term); fields.append(termLabel); form.append(fields);
    const selected = el('ul', undefined, 'semester-plan-courses');
    const known = new Map([...(activePlan?.courses || []), ...(board?.courses?.eligible || [])].map(course => [course.code, course]));
    chosen.forEach(code => {
      const course = known.get(code), row = el('li');
      row.dataset.planCourse = code;
      const valid = board?.courses?.eligible?.some(item => item.code === code
        && item.planning_eligible !== false
        && item.eligibility_basis !== 'available_prerequisites');
      row.append(el('span', `${code} · ${course?.name || ''} · ${credits(course?.credits || 0)}${valid ? '' : copy(' — Cần kiểm tra', ' — Needs review')}`));
      const remove = el('button', copy('Bỏ môn', 'Remove'), 'text-action'); remove.type = 'button'; remove.disabled = planBusy;
      remove.setAttribute('aria-label', `${copy('Bỏ', 'Remove')} ${code}`);
      remove.onclick = () => {
        const finishMotion = window.workspaceMotion?.capturePlan(root);
        chosen.delete(code); planDirty = true; render(); finishMotion?.();
      }; row.append(remove); selected.append(row);
    });
    if (!chosen.size) selected.append(el('li', copy('Chưa có môn trong phương án. Các môn được gợi ý theo mức tín chỉ và điều kiện đã hoàn thành.', 'No courses in this alternative. Suggestions use the credit budget and completed prerequisites.')));
    form.append(selected);
    const actions = el('div', undefined, 'portal-actions');
    const save = el('button', planBusy ? copy('Đang lưu…', 'Saving…') : copy('Kiểm tra và lưu phương án', 'Validate and save'), 'portal-button');
    save.type = 'submit'; save.disabled = planBusy || loading || !ready || !board?.plan_basis || planCredits() > budget;
    actions.append(save);
    if (activePlan) {
      const remove = el('button', copy('Xóa phương án', 'Delete alternative'), 'portal-button'); remove.type = 'button'; remove.disabled = planBusy;
      remove.onclick = () => { if (window.confirm(copy('Xóa phương án này?', 'Delete this alternative?'))) persistPlan(true); }; actions.append(remove);
    }
    form.append(actions); form.onsubmit = event => { event.preventDefault(); if (form.reportValidity() && !save.disabled) persistPlan(); };
    section.append(form);
    const message = el('p', planMessage); message.setAttribute('role', 'status'); section.append(message);
    return section;
  }
  const states = ['completed', 'eligible', 'blocked'];
  const titles = () => [copy('Đã hoàn thành', 'Completed'), copy('Có thể học', 'Available to study'), copy('Chưa thể học', 'Blocked')];
  const subtitles = () => [copy('Đã đạt / được công nhận tín chỉ', 'Passed / credits recognized'), copy('Môn có thể học và các môn nối tiếp theo tiên quyết', 'Available courses and their prerequisite sequences'), copy('Xem điều kiện cần hoàn thành', 'See the requirements still unmet')];
  const el = (tag, text, cls) => {
    const node = document.createElement(tag);
    if (text !== undefined) node.textContent = text;
    if (cls) node.className = cls;
    return node;
  };
  const credits = value => `${value} ${copy('TC', 'credits')}`;
  const reasonText = reason => ({
    source_missing: copy('Chưa có bảng điểm VNU đã lưu.', 'No saved VNU transcript is available.'),
    source_incomplete: copy('Chưa xác minh bảng điểm đã được lấy đầy đủ.', 'Transcript completeness has not been verified.'),
    program_binding_unverified: copy('Chưa xác minh chương trình áp dụng cho hồ sơ VNU.', 'The applicable program has not been verified for this VNU profile.'),
    policy_not_applicable: copy('Chưa xác minh quy chế học vụ áp dụng.', 'The applicable academic policy has not been verified.'),
    course_outcomes_unresolved: copy('Có môn học lại, điểm hoặc mã môn cần đối chiếu trước khi xác định môn đã đạt.', 'Retakes, grades or course codes need review before completed courses can be determined.'),
    track_selection_required: copy('Chọn hướng chuyên ngành để xét đúng yêu cầu.', 'Select a study track to apply its requirements.'),
    graduation_selection_required: copy('Chọn nhánh tốt nghiệp để xét đúng yêu cầu.', 'Select a graduation path to apply its requirements.')
    ,source_enrollment_unresolved: copy('Chưa đối chiếu được ngành/khóa đọc từ VNU với các khung đang hỗ trợ.', 'Source enrollment could not be matched to a supported curriculum.'),
    academic_program_source_mismatch: copy('Lựa chọn không khớp ngành/khóa đọc từ VNU.', 'Your selection does not match source enrollment.'),
    context_changed: copy('Dữ liệu đã thay đổi. Hãy tải lại rồi xác nhận.', 'The data changed. Reload it before confirming.')
    ,program_rules_review_required: copy('Quy tắc chọn hướng trong khung này cần đối chiếu thêm. Vẫn hiển thị các môn đã đối chiếu điểm đạt; kế hoạch tạm dừng.', 'This curriculum’s study-track rules need review. Resolved passed courses remain visible; planning is paused.')
    ,catalog_unverified: copy('Khung chương trình chưa được xác minh. Bản đồ đang ở chế độ xem trước; kế hoạch tạm dừng.', 'The curriculum is unverified. The course map is a preview; planning is paused.'),
    course_source_unverified: copy('Một số thông tin môn học chưa được xác minh. Kết quả chỉ là xem trước.', 'Some course details are unverified. Results are shown as a preview.'),
    prerequisite_unverified: copy('Một số điều kiện tiên quyết chưa được xác minh. Kế hoạch tạm dừng.', 'Some prerequisites are unverified. Planning is paused.')
  })[reason] || copy('Dữ liệu bảng điểm cần được kiểm tra thêm.', 'Transcript data needs further review.');

  function blockedReason(reason) {
    return ({
      choice_group_full: copy('Nhóm tự chọn đã đủ tín chỉ yêu cầu.', 'The elective group credit requirement is already fulfilled.'),
      prerequisite_unknown: copy('Chưa xác minh được điều kiện tiên quyết.', 'Prerequisites have not been verified.'),
      course_source_unverified: copy('Thông tin mã môn, tên, tín chỉ hoặc khối chưa được xác minh.', 'Course code, name, credits or block have not been verified.'),
      source_conflict: copy('Tài liệu nguồn có điều kiện tiên quyết mâu thuẫn.', 'Source documents contain conflicting prerequisites.'),
      track_mismatch: copy('Môn thuộc hướng chuyên ngành khác.', 'This course belongs to another study track.'),
      graduation_path_mismatch: copy('Môn thuộc nhánh tốt nghiệp khác.', 'This course belongs to another graduation path.'),
      credits_exceeded: copy('Tín chỉ môn vượt giới hạn xét điều kiện.', 'Course credits exceed the eligibility limit.')
      ,academic_review_required: copy('Kết quả hoặc lựa chọn chương trình cần đối chiếu trước khi lập kế hoạch.', 'Results or curriculum selections need review before planning this course.')
    })[reason.kind] || copy('Cần kiểm tra điều kiện môn học.', 'Course requirements need review.');
  }

  function prerequisiteLabels(clauses, courseLookup) {
    const fragment = document.createDocumentFragment();
    clauses.forEach((group, clauseIndex) => {
      if (clauseIndex) fragment.append(copy(' và ', ' and '));
      fragment.append('(');
      group.forEach((code, index) => {
        if (index) fragment.append(copy(' hoặc ', ' or '));
        const course = courseLookup.get(code);
        const name = window.workspaceI18n.language === 'en' && course?.name_en
          ? course.name_en : course?.name;
        if (name) fragment.append(`${code}: `, el('strong', name));
        else fragment.append(code);
      });
      fragment.append(')');
    });
    return fragment;
  }

  function planCredits() {
    return (board?.courses?.eligible || []).filter(course => chosen.has(course.code)).reduce((sum, course) => sum + course.credits, 0);
  }

  function card(course, state, courseLookup) {
    const node = el('article', undefined, 'course-status-card');
    node.dataset.courseCode = course.code;
    const courseName = window.workspaceI18n.language === 'en' && course.name_en ? course.name_en : course.name;
    node.append(el('span', course.code, 'course-code-name'), el('h4', courseName, 'course-code-name source-course-name'));
    const meta = el('div', undefined, 'course-status-meta');
    const labels = {required: copy('Bắt buộc', 'Required'), elective: copy('Tự chọn', 'Elective'), required_excluded: copy('Bắt buộc', 'Required'), graduation: copy('Tốt nghiệp', 'Graduation')};
    meta.append(el('span', credits(course.credits), 'course-status-badge'), el('span', labels[course.requirement_type] || '', 'course-status-badge'));
    node.append(meta);
    const reasons = el('ul', undefined, 'course-status-reasons');
    if (state === 'blocked') course.reasons.forEach(reason => {
      const item = el('li');
      if (reason.kind === 'missing_prerequisites') {
        item.append(copy('Chưa đạt môn tiên quyết: ', 'Missing prerequisite: '),
          prerequisiteLabels(reason.missing_prerequisites, courseLookup));
      } else item.textContent = blockedReason(reason);
      reasons.append(item);
    });
    if (state === 'eligible') {
      const basis = course.eligibility_basis;
      const availability = el('li');
      if (basis === 'available_prerequisites') {
        availability.append(copy('Tiên quyết nằm trong nhóm Có thể học: ', 'Prerequisites are in Available to study: '),
          prerequisiteLabels(course.prerequisite_clauses || [], courseLookup),
          copy('. Cần hoàn thành các môn tiên quyết trước khi học môn này.', '. Complete those prerequisites before taking this course.'));
      } else availability.textContent = basis === 'no_prerequisites'
          ? copy('Có thể học theo mặc định: môn không có điều kiện tiên quyết.', 'Available by default: this course has no prerequisites.')
          : basis === 'requested_default'
            ? copy('Có thể học theo mặc định đã chọn; điều kiện tiên quyết đã thỏa.', 'Available under the selected default; prerequisites are satisfied.')
          : copy('Đã thỏa điều kiện tiên quyết trong chương trình.', 'Catalog prerequisites are satisfied.');
      reasons.append(availability);
      if (course.result_pending) reasons.append(el('li', copy('Kết quả môn này còn chờ đối chiếu; chưa tính là đã hoàn thành.', 'This result still needs review; the course is not counted as completed.')));
      course.groups.filter(group => group.remaining_credits > 0).forEach(group => {
        const item = el('li');
        item.append(el('span', group.name, 'source-profile-value'), document.createTextNode(`: ${copy('còn thiếu', 'remaining')} ${credits(group.remaining_credits)}`));
        reasons.append(item);
      });
      node.append(reasons);
    } else if (reasons.childElementCount) node.append(reasons);
    return node;
  }

  function matchesSearch(course) {
    return `${course.code} ${course.name} ${course.name_en || ''}`
      .toLocaleLowerCase().includes(search.toLocaleLowerCase());
  }

  function visibleCourses(state) {
    return board?.courses?.[state]?.filter(course => course.counted_in_total !== false);
  }

  function searchResultCount() {
    return states.reduce((total, state) => total + (visibleCourses(state) || []).filter(matchesSearch).length, 0);
  }

  function renderColumns() {
    const columns = el('div', undefined, 'course-status-columns');
    const courseLookup = new Map(Object.entries(board?.prerequisite_courses || {}));
    states.forEach(state => (board?.courses?.[state] || []).forEach(course => {
      if (!courseLookup.has(course.code)) courseLookup.set(course.code, course);
    }));
    states.forEach((state, index) => {
      const section = el('section', undefined, `course-status-column course-state-${state}`);
      const header = el('header');
      const heading = el('h3', titles()[index]);
      const courses = visibleCourses(state);
      heading.append(el('span', courses ? String(courses.length) : '—'));
      header.append(heading, el('p', subtitles()[index]));
      const list = el('div', undefined, 'course-status-list');
      const matching = (courses || []).filter(matchesSearch);
      matching.forEach(course => list.append(card(course, state, courseLookup)));
      if (!matching.length) {
        const pending = board?.blocking_reasons?.includes('source_incomplete')
          ? copy('Chưa phân loại: lần lấy bảng điểm chưa được xác minh đầy đủ.', 'Not classified: transcript collection is not verified complete.')
          : board?.blocking_reasons?.includes('catalog_unverified')
            ? copy('Chưa phân loại: khung chương trình chưa được xác minh.', 'Not classified: curriculum is not verified.')
          : board?.blocking_reasons?.includes('program_binding_unverified')
            ? copy('Chưa phân loại: cần xác nhận chương trình áp dụng ở phía trên.', 'Not classified: confirm your curriculum above.')
            : copy('Chờ dữ liệu học tập được xác minh', 'Awaiting verified academic data');
        list.append(el('p', !courses ? pending : copy('Không có môn phù hợp', 'No matching courses'), 'course-status-empty'));
      }
      section.append(header, list); columns.append(section);
    });
    return columns;
  }

  function renderProgressBreakdown(progress) {
    const sections = [
      {title: copy('Theo khối', 'By block'), items: progress?.blocks || []},
      {title: copy('Nhóm tín chỉ tự chọn', 'Elective credit groups'), items: progress?.choice_groups || []},
    ].filter(section => section.items.length);
    if (!sections.length) return null;

    const section = el('section', undefined, 'course-status-progress-breakdown');
    const heading = el('h3', copy('Tiến độ theo khối và nhóm tín chỉ', 'Progress by blocks and credit groups'));
    heading.id = 'course-status-progress-heading';
    section.setAttribute('aria-labelledby', heading.id);
    section.append(heading, el('p',
      copy('Các khối/nhóm có thể chồng lấp; không cộng các dòng này.',
        'Blocks and groups can overlap; do not add these rows together.'),
      'course-status-progress-note'));
    const content = el('div', undefined, 'course-status-progress-sections');
    sections.forEach(group => {
      const groupSection = el('div');
      groupSection.append(el('h4', group.title));
      const list = el('ul');
      group.items.forEach(item => {
        const row = el('li');
        const earned = item.earned_credits || 0;
        const value = item.required_credits == null
          ? copy(`Đã đạt ${credits(earned)} · chưa xác định yêu cầu`, `${credits(earned)} earned · requirement unknown`)
          : copy(`${earned} / ${item.required_credits} TC · còn thiếu ${item.remaining_credits ?? Math.max(0, item.required_credits - earned)} TC`,
            `${earned} / ${item.required_credits} credits · ${item.remaining_credits ?? Math.max(0, item.required_credits - earned)} remaining`);
        row.append(el('span', item.name), el('span', value));
        list.append(row);
      });
      groupSection.append(list); content.append(groupSection);
    });
    section.append(content);
    return section;
  }

  function select(labelText, items, value, update, focusKey) {
    const label = el('label', labelText), input = el('select'); input.disabled = planBusy || loading || failed;
    input.dataset.courseStatusFocus = focusKey;
    input.setAttribute('aria-label', labelText);
    input.append(new Option(copy('Chưa chọn', 'Not selected'), ''));
    items.forEach(item => input.append(new Option(item.name, item.id)));
    input.value = value;
    input.addEventListener('change', () => { update(input.value); load(focusKey); });
    label.append(input); return label;
  }

  function renderProgramConfirmation(options) {
    const form = el('form', undefined, 'course-program-confirmation');
    form.append(el('h3', copy('Xác nhận chương trình áp dụng', 'Confirm your curriculum')),
      el('p', copy('Xác nhận một lần cho tài khoản này. Ngành và khóa phải khớp thông tin nguồn VNU; các tài khoản khác có xác nhận riêng.', 'Confirm once for this account. Program and cohort must match VNU enrollment; other accounts keep their own confirmation.')));
    const facts = el('p'); facts.append(el('span', options.source_program || '—', 'source-profile-value'),
      document.createTextNode(' · '), el('span', options.source_cohort || '—', 'source-profile-value'));
    form.append(facts);
    const controls = el('div', undefined, 'course-program-controls');
    const programLabel = el('label', copy('Chương trình', 'Curriculum')), programInput = el('select'); programInput.id = 'academic-program-choice';
    programInput.append(new Option(copy('Chọn chương trình', 'Choose a curriculum'), ''));
    options.programs.forEach(item => programInput.append(new Option(item.name, item.program_id)));
    programInput.value = options.suggested_program_id || ''; programInput.required = true;
    programLabel.append(programInput);
    const cohortLabel = el('label', copy('Khóa tuyển sinh', 'Admission cohort')), cohortInput = el('select'); cohortInput.id = 'academic-cohort-choice';
    cohortInput.append(new Option(copy('Chọn khóa', 'Choose a cohort'), ''));
    options.cohorts.forEach(number => cohortInput.append(new Option(`K${number} · ${2022 + number - 67}`, String(number))));
    cohortInput.value = options.suggested_cohort ? String(options.suggested_cohort) : ''; cohortInput.required = true;
    cohortLabel.append(cohortInput); controls.append(programLabel, cohortLabel); form.append(controls);
    const consentLabel = el('label', undefined, 'course-program-consent'), consent = el('input');
    consent.type = 'checkbox'; consent.id = 'academic-program-consent'; consent.required = true;
    consentLabel.append(consent, el('span', copy('Tôi xác nhận khung này áp dụng cho ngành và khóa của tôi.', 'I confirm that this curriculum applies to my program and cohort.'))); form.append(consentLabel);
    const policy = el('a', copy('Xem quy chế đánh giá kết quả học tập 3626/2022', 'View the 3626/2022 assessment policy'));
    policy.href = options.policy_source; policy.target = '_blank'; policy.rel = 'noopener'; form.append(policy);
    const submit = el('button', copy('Xác nhận và đối chiếu bảng điểm', 'Confirm and check my transcript'), 'portal-button'); submit.type = 'submit';
    const candidates = options.program_candidates || (options.suggested_program_id ? [options.suggested_program_id] : []);
    submit.disabled = savingBinding || !candidates.length || !options.suggested_cohort || !options.snapshot_digest;
    if (!candidates.length || !options.suggested_cohort) form.append(el('p', reasonText('source_enrollment_unresolved')));
    else if (candidates.length > 1) form.append(el('p', copy('Ngành nguồn có nhiều chương trình. Chỉ xác nhận nếu bạn thuộc chương trình chuẩn đang được hỗ trợ.', 'The source major has multiple curricula. Confirm only if you attend the supported standard program.')));
    form.append(submit);
    form.addEventListener('submit', async event => {
      event.preventDefault(); if (savingBinding || !form.reportValidity()) return;
      const chosenProgram = options.programs.find(item => item.program_id === programInput.value);
      if (!chosenProgram) return;
      const current = sequence;
      savingBinding = true; planError = ''; submit.disabled = true;
      try {
        const response = await fetch('/me/academic-program', {method: 'POST', credentials: 'same-origin', cache: 'no-store',
          headers: {'Content-Type': 'application/json', 'X-CSRF-Token': window.systemAuth?.csrf || ''}, body: JSON.stringify({program_id: programInput.value,
            cohort: Number(cohortInput.value), expected_catalog_revision: chosenProgram.catalog_revision,
            expected_snapshot_digest: options.snapshot_digest, expected_source_scope: options.source_scope, confirm: consent.checked})});
        const result = await response.json(); if (current !== sequence) return;
        if (response.status === 401) { document.dispatchEvent(new Event('workspace:session-expired')); return; }
        if (!response.ok) throw new Error(typeof result.detail === 'string' ? result.detail : 'context_changed');
        savingBinding = false; await load();
      } catch (error) { if (current === sequence) { planError = reasonText(error.message); savingBinding = false; render(); } }
    });
    return form;
  }

  function render() {
    saveDraft();
    root.replaceChildren(); root.setAttribute('aria-busy', String(loading));
    const heading = el('div', undefined, 'course-status-heading');
    const intro = el('div'); intro.append(el('h2', copy('Bản đồ học phần', 'Your course map')), el('p', copy('Biết mình đã hoàn thành gì, nên học gì tiếp và còn vướng điều kiện nào.', 'See what you have completed, what you can take next and what still needs to be fulfilled.')));
    const refresh = el('button', copy('Cập nhật', 'Refresh'), 'portal-button'); refresh.type = 'button'; refresh.disabled = !source || loading || planBusy;
    refresh.dataset.courseStatusFocus = 'refresh';
    refresh.addEventListener('click', () => load('refresh')); heading.append(intro, refresh); root.append(heading);
    const legend = el('div', undefined, 'course-status-legend');
    states.forEach((state, index) => { const item = el('span', undefined, `course-state-${state}`); item.append(el('i', undefined, 'course-status-dot'), document.createTextNode(titles()[index])); legend.append(item); });
    root.append(legend);
    const displayable = Boolean(board?.courses);
    const ready = !failed && (board?.status === 'ready' || (board?.status === 'partial' && board.can_plan));
    if (!ready || loading || failed || board?.status === 'partial') {
      const notice = el('div', undefined, 'course-status-notice'); notice.setAttribute('role', 'status');
      notice.append(el('p', !source ? copy('Đăng nhập VNU để kiểm tra dữ liệu học tập của bạn.', 'Sign in with VNU to check your academic data.') : loading ? copy('Đang đối chiếu điều kiện học…', 'Checking your course requirements…') : failed ? copy('Chưa tải được kết quả. Vui lòng thử cập nhật lại.', 'Results could not be loaded. Please try refreshing.') : board?.preview_only ? copy('Đây là bản xem trước theo bảng điểm và khung hiện có. Thông tin khung hoặc môn học chưa xác minh nên chưa thể lập kế hoạch. Môn nối tiếp vẫn cần hoàn thành tiên quyết trước khi học.', 'This preview uses the current transcript and curriculum data. Unverified curriculum or course details prevent planning. Complete prerequisites before taking follow-up courses.') : board?.status === 'partial' ? copy('Đã phân loại phần dữ liệu đối chiếu được. Chỉ hiển thị môn tính tín chỉ tích lũy. Các môn nối tiếp trong nhóm Có thể học vẫn cần hoàn thành tiên quyết trước; kết quả chưa rõ không được tính là đã hoàn thành.', 'Reviewed results are shown. Only courses counting toward earned credits are shown. Available prerequisite sequences still require completing prerequisites first; unresolved results do not count as completed.') : copy('Chưa đủ dữ liệu để phân loại chính xác các môn của bạn.', 'More verified data is needed to classify your courses.')));
      if (source && !loading) {
        const reasons = board?.blocking_reasons || ['program_binding_unverified', ...(source.snapshot?.completeness !== 'complete' ? ['source_incomplete'] : [])];
        const list = el('ul'); [...new Set(reasons.map(reasonText))].forEach(text => list.append(el('li', text))); notice.append(list);
        if (board?.collection_status?.completeness !== 'complete' && reasons.includes('source_incomplete')) {
          const collection = board?.latest_collection || source.latest_collection || board?.collection_status, proof = collection?.evidence;
          if (!proof) notice.append(el('p', copy('Vào Hồ sơ của tôi → Cập nhật hồ sơ và bảng điểm để bộ đọc mới kiểm tra toàn bộ bảng điểm.', 'Open My profile → Update profile and transcript so the updated connector can check the full transcript.')));
          else {
            window.workspaceI18n.collectionReviewMessages(collection).forEach(message => notice.append(el('p', message)));
          }
        }
      }
      if (source && (board?.blocking_reasons || []).includes('source_incomplete')) {
        const sync = el('button', copy('Cập nhật bảng điểm VNU', 'Update VNU transcript'), 'portal-button'); sync.type = 'button';
        sync.addEventListener('click', () => {
          window.workspaceNavigate('portal-dialog');
          document.dispatchEvent(new Event('workspace:portal-begin-sync'));
        });
        notice.append(sync);
      }
      const profile = el('button', copy('Xem bảng điểm VNU', 'View VNU transcript'), 'portal-button'); profile.type = 'button'; profile.addEventListener('click', () => window.workspaceNavigate('portal-dialog'));
      notice.append(profile); root.append(notice);
    }
    if (board?.program_selection && source && !loading && !failed) root.append(renderProgramConfirmation(board.program_selection));
    if (board?.review_items?.length) {
      const review = el('details', undefined, 'course-review-items');
      review.append(el('summary', `${board.review_items.length} ${copy('mã môn cần đối chiếu thêm', 'course codes need further review')}`));
      const list = el('ul');
      const descriptions = {
        source_catalog_credit_conflict: copy('Tín chỉ nguồn khác khung chương trình.', 'Source credits differ from the curriculum.'),
        unsupported_or_missing_grade: copy('Điểm đang thiếu/chờ hoặc ký hiệu chưa được hỗ trợ.', 'A grade is missing/pending or its label is unsupported.'),
        source_grade_conflict: copy('Các cột điểm chưa nhất quán với quy chế.', 'The source grade columns do not agree with the policy.'),
        retake_policy_unresolved: copy('Lần học lại cần được đối chiếu thêm theo quy chế.', 'The repeated attempt needs further policy review.'),
        retake_term_unresolved: copy('Chưa xác định được thứ tự học kỳ của các lần học.', 'The terms of repeated attempts cannot be ordered unambiguously.'),
        exact_mapping_unresolved: copy('Mã nguồn chưa có trong khung; không tự gộp mã hoặc bỏ hậu tố.', 'The code is outside this curriculum; codes are not automatically merged or stripped.')
      };
      board.review_items.forEach(item => list.append(el('li', `${item.code}: ${descriptions[item.reason] || copy('Kết quả cần đối chiếu thêm.', 'This result needs further review.')}`)));
      review.append(list); root.append(review);
    }
    const selections = board?.selections;
    const toolbar = el('form', undefined, 'course-status-toolbar');
    if (selections?.track_required) toolbar.append(select(copy('Hướng chuyên ngành', 'Study track'), selections.tracks, track, value => { track = value; path = ''; planDirty = true; }, 'track'));
    if (selections?.path_required) toolbar.append(select(copy('Nhánh tốt nghiệp', 'Graduation path'), selections.paths.filter(item => !track || !item.allowed_track_ids.length || item.allowed_track_ids.includes(track)), path, value => { path = value; planDirty = true; }, 'path'));
    const budgetLabel = el('label', copy('Tín chỉ kỳ tới', 'Next-term credit budget'));
    const budgetInput = el('input'); budgetInput.type = 'number'; budgetInput.disabled = planBusy; budgetInput.min = '1'; budgetInput.max = '30'; budgetInput.step = '1'; budgetInput.value = budget; budgetInput.id = 'course-credit-budget'; budgetInput.disabled = !ready || loading || planBusy;
    budgetLabel.append(budgetInput);
    const apply = el('button', copy('Áp dụng', 'Apply'), 'portal-button'); apply.type = 'submit'; apply.disabled = !ready || loading || planBusy;
    apply.dataset.courseStatusFocus = 'budget';
    toolbar.addEventListener('submit', event => { event.preventDefault(); if (!toolbar.reportValidity()) return; budget = Number(budgetInput.value); planDirty = true; load('budget'); });
    const searchLabel = el('label', copy('Tìm môn học', 'Find a course'), 'course-status-search');
    const searchInput = el('input'); searchInput.type = 'search'; searchInput.value = search; searchInput.placeholder = copy('Mã hoặc tên môn học', 'Course code or name'); searchInput.disabled = !displayable;
    const searchResults = el('p', '', 'course-status-search-results');
    searchResults.setAttribute('role', 'status'); searchResults.setAttribute('aria-live', 'polite');
    searchResults.setAttribute('aria-atomic', 'true');
    searchInput.addEventListener('input', () => {
      search = searchInput.value; saveDraft();
      const count = searchResultCount();
      searchResults.textContent = search
        ? count ? copy(`Có ${count} môn phù hợp.`, `${count} matching courses.`)
          : copy('Không có môn phù hợp.', 'No courses match this search.')
        : copy(`Đã xóa tìm kiếm. Hiện ${count} môn.`, `Search cleared. Showing ${count} courses.`);
      root.querySelector('.course-status-columns').replaceWith(renderColumns());
    });
    searchLabel.append(searchInput); toolbar.append(budgetLabel, apply, searchLabel); root.append(toolbar, searchResults);
    if (displayable && !loading) {
      const summary = el('div', undefined, 'course-status-summary');
      const progress = board.progress.total;
      const done = el('div'); done.append(el('p', board.preview_only ? copy('Tín chỉ tạm tính theo dữ liệu chưa xác minh', 'Estimated credits from unverified data') : board.progress_is_lower_bound ? copy('Tín chỉ đạt đã đối chiếu (tối thiểu)', 'Reviewed earned credits (minimum)') : copy('Tín chỉ tích lũy trong chương trình', 'Earned program credits')), el('strong', `${progress.earned_credits} / ${progress.required_credits} ${copy('TC', 'credits')}`));
      const bar = el('progress'); bar.max = progress.required_credits; bar.value = Math.min(progress.earned_credits, bar.max); bar.setAttribute('aria-label', copy('Tiến độ tín chỉ', 'Credit progress')); done.append(bar, el('p', `${copy('Còn thiếu', 'Remaining')}: ${credits(progress.remaining_credits)}`));
      const plan = el('div'); plan.append(el('p', board.preview_only ? copy('Kế hoạch kỳ tới đang tạm dừng', 'Next-term planning is paused') : copy('Kế hoạch kỳ tới của bạn', 'Your next-term plan')), el('strong', `${planCredits()} / ${credits(budget)}`), el('p', board.preview_only ? copy('Mở lại kế hoạch sau khi khung và thông tin môn học được xác minh.', 'Planning will resume after the curriculum and course details are verified.') : copy('Ưu tiên môn bắt buộc và nhóm tín chỉ còn thiếu; chỉ gợi ý môn có tiên quyết đã hoàn thành. Có thể bỏ bớt môn trong phương án bên dưới.', 'Required courses and unfulfilled credit groups come first; suggestions require completed prerequisites. Remove courses from the alternative below.')));
      summary.append(done, plan); root.append(summary);
      const breakdown = renderProgressBreakdown(board.progress);
      if (breakdown) root.append(breakdown);
    }
    if (source) root.append(renderSavedPlans(ready));
    const error = el('p', planError, 'course-plan-error'); error.setAttribute('role', 'status'); root.append(error, renderColumns());
    root.append(el('p', board?.preview_only ? copy('Màu trong bản xem trước phản ánh dữ liệu hiện có, chưa xác nhận điều kiện học chính thức. Không dùng kết quả này để đăng ký môn; hãy xác nhận khung và quy định với nhà trường.', 'Preview colors reflect the available data and do not confirm official eligibility. Do not use this result to register; confirm the curriculum and rules with the university.') : copy('Màu vàng gồm môn có thể học và các môn nối tiếp khi tiên quyết nằm trong cùng nhóm. Vẫn cần hoàn thành tiên quyết trước khi học môn nối tiếp; chưa xác nhận lịch mở lớp.', 'Yellow includes available courses and sequences whose prerequisites are in this group. Complete prerequisites before taking follow-up courses; course offerings are not confirmed.'), 'course-status-note'));
  }

  async function load(focusKey = null) {
    if (!source) return;
    const current = ++sequence; controller?.abort(); controller = new AbortController();
    loading = true; failed = false; planError = ''; render();
    const params = new URLSearchParams({max_credits: String(budget)});
    if (track) params.set('selected_track_id', track);
    if (path) params.set('selected_graduation_path_id', path);
    try {
      const response = await fetch(`/me/course-status?${params}`, {credentials: 'same-origin', cache: 'no-store', signal: controller.signal});
      if (current !== sequence) return;
      if (response.status === 401) { document.dispatchEvent(new Event('workspace:session-expired')); return; }
      if (response.status === 422 && activePlan && (track || path)) {
        track = ''; path = ''; planDirty = true;
        planMessage = copy('Hướng/nhánh cũ không còn phù hợp. Chọn lại theo chương trình hiện tại.', 'The old track/path is unavailable. Select from your current curriculum.');
        return load(focusKey);
      }
      if (!response.ok) throw new Error('course_status_unavailable');
      const result = await response.json();
      if (current !== sequence) return;
      if ((result.blocking_reasons || []).includes('program_binding_unverified')
          && !result.program_selection) {
        try {
          const selectionResponse = await fetch('/me/academic-program', {
            credentials: 'same-origin', cache: 'no-store', signal: controller.signal,
          });
          if (current !== sequence) return;
          if (selectionResponse.ok) result.program_selection = await selectionResponse.json();
        } catch (selectionError) {
          if (current !== sequence || selectionError.name === 'AbortError') return;
        }
      }
      board = result;
      if (!activePlan && !planDirty && !restoringDraft) chosen = new Set(result.plan?.course_codes || []);
      restoringDraft = false;
      if (planCredits() > budget) planError = copy('Các môn đang chọn vượt ngân sách mới. Bỏ bớt môn hoặc tăng tín chỉ trước khi lưu.', 'Your selected courses exceed the new budget. Remove courses or increase the budget before saving.');
    } catch (error) { if (current !== sequence || error.name === 'AbortError') return; failed = true; }
    if (current !== sequence) return;
    loading = false; render();
    if (focusKey) {
      const focusTarget = [...root.querySelectorAll('[data-course-status-focus]')]
        .find(element => element.dataset.courseStatusFocus === focusKey);
      focusTarget?.focus();
    }
  }
  document.addEventListener('workspace:portal-data', event => {
    const next = event.detail;
    // A profile read/visibility event is not a new academic source.
    const nextKey = next ? JSON.stringify([sessionIdentity(), next.snapshot, next.profile]) : '';
    if (next && source && nextKey === sourceKey) { source = next; return; }
    const sameSession = Boolean(next && source && sourceOwner === sessionIdentity());
    if (source) saveDraft();
    if (!next && (source || !sessionIdentity())) clearDraft();
    ++sequence; ++planOwnerEpoch; ++plansSequence;
    controller?.abort(); source = next; sourceKey = nextKey; sourceOwner = next ? sessionIdentity() : null; board = null;
    savedPlans = []; planBusy = false; plansLoading = false; planError = '';
    loading = false; failed = false; savingBinding = false;
    if (!sameSession) {
      activePlan = null; chosen.clear(); track = ''; path = ''; search = ''; budget = 20;
      planTitle = ''; planMessage = ''; planDirty = false; restoringDraft = false;
      planYear = new Date().getFullYear(); planSemester = 1;
      if (source) restoreDraft();
    } else {
      planMessage = copy('Dữ liệu VNU đã đổi. Bản nháp được giữ; kiểm tra lại các môn trước khi lưu.', 'VNU data changed. Your draft is retained; review the courses before saving.');
      restoringDraft = true;
    }
    render();
    if (source) fetchPlans();
    if (source && !root.hidden && document.documentElement.dataset.view === 'tab-rules') load();
  });
  document.addEventListener('workspace:navigate', event => { if (event.detail === 'tab-rules' && !root.hidden && source && !board && !loading) load(); });
  document.addEventListener('workspace:course-mode', event => { if (event.detail === 'personal' && source && !board && !loading) load(); });
  document.addEventListener('workspace:language-change', render);
  render();
})();
