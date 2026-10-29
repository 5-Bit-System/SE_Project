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
      const valid = board?.courses?.eligible?.some(item => item.code === code);
      row.append(el('span', `${code} · ${course?.name || ''} · ${credits(course?.credits || 0)}${valid ? '' : copy(' — Cần kiểm tra', ' — Needs review')}`));
      const remove = el('button', copy('Bỏ môn', 'Remove'), 'text-action'); remove.type = 'button'; remove.disabled = planBusy;
      remove.setAttribute('aria-label', `${copy('Bỏ', 'Remove')} ${code}`);
      remove.onclick = () => {
        const finishMotion = window.workspaceMotion?.capturePlan(root);
        chosen.delete(code); planDirty = true; render(); finishMotion?.();
      }; row.append(remove); selected.append(row);
    });
    if (!chosen.size) selected.append(el('li', copy('Chưa chọn môn. Chọn môn đủ điều kiện ở phía dưới.', 'No courses selected. Choose eligible courses below.')));
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
  const titles = () => [copy('Đã hoàn thành', 'Completed'), copy('Có thể học kỳ tới', 'Eligible next term'), copy('Chưa thể học', 'Blocked')];
  const subtitles = () => [copy('Đã đạt / được công nhận tín chỉ', 'Passed / credits recognized'), copy('Đủ điều kiện; chọn môn cho kế hoạch', 'Eligible; choose courses for your plan'), copy('Xem điều kiện cần hoàn thành', 'See the requirements still unmet')];
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
    ,catalog_unverified: copy('Khung chương trình chưa được xác minh; tạm dừng phân loại và lập kế hoạch.', 'The curriculum has not been verified; classification and planning are paused.')
  })[reason] || copy('Dữ liệu bảng điểm cần được kiểm tra thêm.', 'Transcript data needs further review.');

  function blockedReason(reason) {
    if (reason.kind === 'missing_prerequisites') {
      const clauses = reason.missing_prerequisites.map(group => group.join(copy(' hoặc ', ' or ')));
      return copy('Chưa đạt môn tiên quyết: ', 'Missing prerequisite: ') + clauses.map(value => `(${value})`).join(copy(' và ', ' and '));
    }
    return ({
      choice_group_full: copy('Nhóm tự chọn đã đủ tín chỉ yêu cầu.', 'The elective group credit requirement is already fulfilled.'),
      prerequisite_unknown: copy('Chưa xác minh được điều kiện tiên quyết.', 'Prerequisites have not been verified.'),
      source_conflict: copy('Tài liệu nguồn có điều kiện tiên quyết mâu thuẫn.', 'Source documents contain conflicting prerequisites.'),
      track_mismatch: copy('Môn thuộc hướng chuyên ngành khác.', 'This course belongs to another study track.'),
      graduation_path_mismatch: copy('Môn thuộc nhánh tốt nghiệp khác.', 'This course belongs to another graduation path.'),
      credits_exceeded: copy('Tín chỉ môn vượt giới hạn xét điều kiện.', 'Course credits exceed the eligibility limit.')
      ,academic_review_required: copy('Kết quả hoặc lựa chọn chương trình cần đối chiếu trước khi lập kế hoạch.', 'Results or curriculum selections need review before planning this course.')
    })[reason.kind] || copy('Cần kiểm tra điều kiện môn học.', 'Course requirements need review.');
  }

  function planCredits() {
    return (board?.courses?.eligible || []).filter(course => chosen.has(course.code)).reduce((sum, course) => sum + course.credits, 0);
  }

  function updatePlan(course, checked) {
    if (board?.can_plan === false || planBusy || loading) return;
    const finishMotion = window.workspaceMotion?.capturePlan(root);
    planError = ''; planDirty = true;
    if (!checked) chosen.delete(course.code);
    else {
      const courses = board.courses.eligible.filter(item => chosen.has(item.code));
      const remaining = course.groups.filter(group => group.required_credits !== null);
      if (planCredits() + course.credits > budget) planError = copy('Lựa chọn này vượt mức tín chỉ kỳ tới. Hãy bỏ bớt môn hoặc tăng mức tín chỉ.', 'This selection exceeds the term budget. Remove a course or increase the credit budget.');
      else if (remaining.length && remaining.every(group => group.earned_credits + courses.filter(item => item.groups.some(value => value.id === group.id)).reduce((sum, item) => sum + item.credits, 0) >= group.required_credits)) {
        planError = copy('Các môn đã chọn đủ yêu cầu của nhóm tự chọn này.', 'Your selected courses already fulfill this elective group requirement.');
      } else chosen.add(course.code);
    }
    render();
    finishMotion?.();
    root.querySelectorAll('input[data-plan-code]').forEach(input => {
      if (input.dataset.planCode === course.code) input.focus();
    });
  }

  function card(course, state) {
    const node = el('article', undefined, 'course-status-card');
    node.dataset.courseCode = course.code;
    node.append(el('span', course.code, 'course-code-name'), el('h4', window.workspaceI18n.language === 'en' && course.name_en ? course.name_en : course.name, 'course-code-name source-course-name'));
    const meta = el('div', undefined, 'course-status-meta');
    const labels = {required: copy('Bắt buộc', 'Required'), elective: copy('Tự chọn', 'Elective'), required_excluded: copy('Bắt buộc', 'Required'), graduation: copy('Tốt nghiệp', 'Graduation')};
    meta.append(el('span', credits(course.credits), 'course-status-badge'), el('span', labels[course.requirement_type] || '', 'course-status-badge'));
    node.append(meta);
    const reasons = el('ul', undefined, 'course-status-reasons');
    if (!course.counted_in_total) reasons.append(el('li', copy('Không tính vào tổng tín chỉ tích lũy của chương trình.', 'Excluded from the program credit total.')));
    if (state === 'blocked') course.reasons.forEach(reason => reasons.append(el('li', blockedReason(reason))));
    if (state === 'eligible') {
      const basis = course.eligibility_basis;
      reasons.append(el('li', basis === 'excluded_from_total'
        ? copy('Có thể học theo mặc định: môn không tính vào tín chỉ tích lũy.', 'Available by default: excluded from earned program credits.')
        : basis === 'no_prerequisites'
          ? copy('Có thể học theo mặc định: môn không có điều kiện tiên quyết.', 'Available by default: this course has no prerequisites.')
          : basis === 'requested_default'
            ? copy('Có thể học theo mặc định đã chọn; điều kiện tiên quyết đã thỏa.', 'Available under the selected default; prerequisites are satisfied.')
          : copy('Đã thỏa điều kiện tiên quyết trong chương trình.', 'Catalog prerequisites are satisfied.')));
      if (course.result_pending) reasons.append(el('li', copy('Kết quả môn này còn chờ đối chiếu; chưa tính là đã hoàn thành.', 'This result still needs review; the course is not counted as completed.')));
      course.groups.filter(group => group.remaining_credits > 0).forEach(group => {
        const item = el('li');
        item.append(el('span', group.name, 'source-profile-value'), document.createTextNode(`: ${copy('còn thiếu', 'remaining')} ${credits(group.remaining_credits)}`));
        reasons.append(item);
      });
      const label = el('label', undefined, 'course-status-check');
      const input = el('input'); input.type = 'checkbox'; input.disabled = planBusy || loading || board?.can_plan === false; input.checked = chosen.has(course.code); input.dataset.planCode = course.code;
      input.addEventListener('change', () => updatePlan(course, input.checked));
      label.append(input, el('span', copy('Chọn cho kế hoạch kỳ tới', 'Select for next term')));
      node.append(reasons, label);
    } else if (reasons.childElementCount) node.append(reasons);
    return node;
  }

  function renderColumns() {
    const columns = el('div', undefined, 'course-status-columns');
    states.forEach((state, index) => {
      const section = el('section', undefined, `course-status-column course-state-${state}`);
      const header = el('header');
      const heading = el('h3', titles()[index]);
      const courses = board?.courses?.[state];
      heading.append(el('span', courses ? String(courses.length) : '—'));
      header.append(heading, el('p', subtitles()[index]));
      const list = el('div', undefined, 'course-status-list');
      const matching = (courses || []).filter(course => `${course.code} ${course.name} ${course.name_en || ''}`.toLocaleLowerCase().includes(search.toLocaleLowerCase()));
      matching.forEach(course => list.append(card(course, state)));
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

  function select(labelText, items, value, update) {
    const label = el('label', labelText), input = el('select'); input.disabled = planBusy;
    input.setAttribute('aria-label', labelText);
    input.append(new Option(copy('Chưa chọn', 'Not selected'), ''));
    items.forEach(item => input.append(new Option(item.name, item.id)));
    input.value = value;
    input.addEventListener('change', () => { update(input.value); load(); });
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
    refresh.addEventListener('click', load); heading.append(intro, refresh); root.append(heading);
    const legend = el('div', undefined, 'course-status-legend');
    states.forEach((state, index) => { const item = el('span', undefined, `course-state-${state}`); item.append(el('i', undefined, 'course-status-dot'), document.createTextNode(titles()[index])); legend.append(item); });
    root.append(legend);
    const displayable = Boolean(board?.courses);
    const ready = board?.status === 'ready' || (board?.status === 'partial' && board.can_plan);
    if (!ready || loading || failed || board?.status === 'partial') {
      const notice = el('div', undefined, 'course-status-notice'); notice.setAttribute('role', 'status');
      notice.append(el('p', !source ? copy('Đăng nhập VNU để kiểm tra dữ liệu học tập của bạn.', 'Sign in with VNU to check your academic data.') : loading ? copy('Đang đối chiếu điều kiện học…', 'Checking your course requirements…') : failed ? copy('Chưa tải được kết quả. Vui lòng thử cập nhật lại.', 'Results could not be loaded. Please try refreshing.') : board?.status === 'partial' ? copy('Đã phân loại phần dữ liệu đối chiếu được. Môn không có tiên quyết hoặc không tính tín chỉ tích lũy được hiển thị có thể học theo mặc định. Kết quả chưa rõ chưa được tính là hoàn thành để mở khóa môn khác.', 'Reviewed results are shown. Courses without prerequisites or excluded from earned credits remain available by default. Unresolved results do not count as completed or unlock other courses.') : copy('Chưa đủ dữ liệu để phân loại chính xác các môn của bạn.', 'More verified data is needed to classify your courses.')));
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
    if (board?.program_selection && source && !loading) root.append(renderProgramConfirmation(board.program_selection));
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
    if (selections?.track_required) toolbar.append(select(copy('Hướng chuyên ngành', 'Study track'), selections.tracks, track, value => { track = value; path = ''; planDirty = true; }));
    if (selections?.path_required) toolbar.append(select(copy('Nhánh tốt nghiệp', 'Graduation path'), selections.paths.filter(item => !track || !item.allowed_track_ids.length || item.allowed_track_ids.includes(track)), path, value => { path = value; planDirty = true; }));
    const budgetLabel = el('label', copy('Tín chỉ kỳ tới', 'Next-term credit budget'));
    const budgetInput = el('input'); budgetInput.type = 'number'; budgetInput.disabled = planBusy; budgetInput.min = '1'; budgetInput.max = '30'; budgetInput.step = '1'; budgetInput.value = budget; budgetInput.id = 'course-credit-budget'; budgetInput.disabled = !ready || loading || planBusy;
    budgetLabel.append(budgetInput);
    const apply = el('button', copy('Áp dụng', 'Apply'), 'portal-button'); apply.type = 'submit'; apply.disabled = !ready || loading || planBusy;
    toolbar.addEventListener('submit', event => { event.preventDefault(); if (!toolbar.reportValidity()) return; budget = Number(budgetInput.value); planDirty = true; load(); });
    const searchLabel = el('label', copy('Tìm môn học', 'Find a course'), 'course-status-search');
    const searchInput = el('input'); searchInput.type = 'search'; searchInput.value = search; searchInput.placeholder = copy('Mã hoặc tên môn học', 'Course code or name'); searchInput.disabled = !displayable;
    searchInput.addEventListener('input', () => { search = searchInput.value; saveDraft(); root.querySelector('.course-status-columns').replaceWith(renderColumns()); });
    searchLabel.append(searchInput); toolbar.append(budgetLabel, apply, searchLabel); root.append(toolbar);
    if (displayable && !loading) {
      const summary = el('div', undefined, 'course-status-summary');
      const progress = board.progress.total;
      const done = el('div'); done.append(el('p', board.progress_is_lower_bound ? copy('Tín chỉ đạt đã đối chiếu (tối thiểu)', 'Reviewed earned credits (minimum)') : copy('Tín chỉ tích lũy trong chương trình', 'Earned program credits')), el('strong', `${progress.earned_credits} / ${progress.required_credits} ${copy('TC', 'credits')}`));
      const bar = el('progress'); bar.max = progress.required_credits; bar.value = Math.min(progress.earned_credits, bar.max); bar.setAttribute('aria-label', copy('Tiến độ tín chỉ', 'Credit progress')); done.append(bar, el('p', `${copy('Còn thiếu', 'Remaining')}: ${credits(progress.remaining_credits)}`));
      const plan = el('div'); plan.append(el('p', copy('Kế hoạch kỳ tới của bạn', 'Your next-term plan')), el('strong', `${planCredits()} / ${credits(budget)}`), el('p', copy('Ưu tiên môn bắt buộc; tự chọn theo nhóm tín chỉ còn thiếu. Bạn có thể thay đổi các môn đã chọn.', 'Required courses come first, then electives in unfulfilled credit groups. You can change the selected courses.')));
      summary.append(done, plan); root.append(summary);
    }
    if (source) root.append(renderSavedPlans(ready));
    const error = el('p', planError, 'course-plan-error'); error.setAttribute('role', 'status'); root.append(error, renderColumns());
    root.append(el('p', copy('Màu vàng cho biết có thể học theo điều kiện chương trình hoặc quy tắc mặc định ghi trên môn; chưa xác nhận môn sẽ mở kỳ tới. Tổng tín chỉ và lựa chọn là kế hoạch tham khảo; cần đối chiếu quy định của nhà trường.', 'Yellow means availability under catalog requirements or the default rule shown on the course; it does not confirm next-term course availability. Credit totals and selections are an advisory plan; confirm official requirements with the university.'), 'course-status-note'));
  }

  async function load() {
    if (!source) return;
    const current = ++sequence; controller?.abort(); controller = new AbortController();
    loading = true; failed = false; board = null; planError = ''; render();
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
        return load();
      }
      if (!response.ok) throw new Error('course_status_unavailable');
      const result = await response.json();
      if (current !== sequence) return;
      board = result;
      if (!activePlan && !planDirty && !restoringDraft) chosen = new Set(result.plan?.course_codes || []);
      restoringDraft = false;
      if (planCredits() > budget) planError = copy('Các môn đang chọn vượt ngân sách mới. Bỏ bớt môn hoặc tăng tín chỉ trước khi lưu.', 'Your selected courses exceed the new budget. Remove courses or increase the budget before saving.');
    } catch (error) { if (current !== sequence || error.name === 'AbortError') return; failed = true; }
    if (current !== sequence) return;
    loading = false; render();
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
