/* Public curriculum facts and an explicitly hypothetical plan; no student inputs. */
(() => {
  'use strict';
  const root = document.getElementById('curriculum-reference');
  const personal = document.getElementById('course-status-board');
  const modeButtons = ['reference', 'personal'].map(mode => document.getElementById(`course-mode-${mode}`));
  const copy = (vi, en) => window.workspaceI18n.language === 'en' ? en : vi;
  const el = (tag, text, cls = '') => {
    const node = document.createElement(tag);
    if (text !== undefined) node.textContent = text;
    if (cls) node.className = cls;
    return node;
  };
  const fold = text => String(text).toLocaleLowerCase().normalize('NFD').replace(/\p{M}/gu, '').replaceAll('đ', 'd');
  const credits = value => `${value} ${copy('TC', 'credits')}`;
  let mode = 'reference', index = null, curriculum = null, plan = null;
  let program = '', cohort = 67, budget = 20, query = '', group = '', type = '', prerequisite = '';
  let loading = false, planning = false, error = '', epoch = 0, controller;
  let selected = new Set();

  function setMode(value) {
    mode = value;
    root.hidden = mode !== 'reference'; personal.hidden = mode !== 'personal';
    modeButtons.forEach((button, i) => button.setAttribute('aria-pressed', String(['reference', 'personal'][i] === mode)));
    document.dispatchEvent(new CustomEvent('workspace:course-mode', {detail: mode}));
    if (mode === 'reference' && !index && !loading) initialize();
  }
  modeButtons.forEach((button, i) => button.addEventListener('click', () => setMode(['reference', 'personal'][i])));

  async function api(url, options = {}) {
    const response = await fetch(url, {cache: 'no-store', ...options});
    const value = await response.json();
    if (!response.ok) throw new Error(typeof value.detail === 'string' ? value.detail : 'invalid_plan');
    return value;
  }
  function errorMessage(code) {
    return ({
      planning_budget_exceeded: copy('Các môn đã chọn vượt ngân sách tín chỉ. Hãy tăng ngân sách hoặc bỏ bớt môn.', 'Selected courses exceed your credit budget. Increase it or remove a course.'),
      multiple_languages_in_same_level: copy('Chỉ chọn một ngoại ngữ ở mỗi mức B1/B2 theo khung chương trình.', 'Choose one language at each B1/B2 level, as specified by the curriculum.'),
      cohort_outside_source_scope: copy('Khóa này nằm ngoài phạm vi tra cứu của bộ tài liệu.', 'This cohort is outside the source collection’s scope.')
    })[code] || copy('Chưa tải được kết quả. Vui lòng thử lại.', 'Results could not be loaded. Please try again.');
  }
  async function initialize() {
    const current = ++epoch;
    loading = true; error = ''; render();
    try { const result = await api('/curricula/reference'); if (current === epoch) index = result; }
    catch (err) { if (current === epoch) error = err.message; }
    if (current === epoch) { loading = false; render(); }
  }
  async function load() {
    const current = ++epoch;
    controller?.abort(); controller = new AbortController();
    curriculum = null; plan = null; selected.clear(); query = ''; group = ''; type = ''; prerequisite = '';
    error = ''; loading = Boolean(program); planning = false; render();
    if (!program) return;
    try {
      const result = await api(`/curricula/reference/${encodeURIComponent(program)}?cohort=${cohort}`, {signal: controller.signal});
      if (current === epoch) curriculum = result;
    } catch (err) { if (current === epoch && err.name !== 'AbortError') error = err.message; }
    if (current === epoch) { loading = false; render(); }
  }
  async function updatePlan(codes, suggest = false, nextBudget = budget) {
    if (!curriculum || planning) return;
    const current = epoch;
    planning = true; error = ''; render();
    try {
      const result = await api(`/curricula/reference/${encodeURIComponent(program)}/plan`, {
        method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({cohort, max_credits: nextBudget, course_codes: codes, suggest})
      });
      if (current !== epoch) return;
      plan = result; selected = new Set(result.course_codes); budget = nextBudget;
    } catch (err) { if (current === epoch) error = err.message; }
    if (current === epoch) { planning = false; render(); }
  }
  function select(labelText, id, values, value, change) {
    const label = el('label', labelText), input = el('select'); input.id = id;
    values.forEach(([text, key]) => input.append(new Option(text, key)));
    input.value = value;
    input.addEventListener('change', () => change(input.value)); label.append(input);
    return label;
  }
  function button(text, action, disabled = false) {
    const node = el('button', text, 'portal-button'); node.type = 'button'; node.disabled = disabled;
    node.addEventListener('click', action); return node;
  }
  function sourceLink(page, label) {
    const link = el('a', label || `PDF · ${copy('tr.', 'p.')} ${page}`);
    link.href = curriculum.source_url + (page ? `#page=${page}` : '');
    link.target = '_blank'; link.rel = 'noopener'; return link;
  }
  function prerequisites(course) {
    if (!course.prerequisites.length) return course.prerequisites_raw || copy('Không ghi tiên quyết', 'No prerequisite recorded');
    return course.prerequisites.map(clause => clause.length > 1 ? `(${clause.join(copy(' hoặc ', ' or '))})` : clause[0]).join(copy(' và ', ' and '));
  }
  function unresolved(course) { return ['conflict', 'unknown', 'source_conflict'].includes(course.prerequisite_status); }
  function courseDetail(course) {
    const dialog = el('dialog', undefined, 'reference-detail');
    const top = el('div', undefined, 'reference-detail-heading');
    top.append(el('h3', `${course.code} · ${course.name}`), button(copy('Đóng', 'Close'), () => dialog.close()));
    dialog.append(top, el('p', credits(course.credits)), el('h4', copy('Điều kiện tiên quyết', 'Prerequisites')), el('p', prerequisites(course)));
    if (course.prerequisite_variants.length) {
      dialog.append(el('p', copy('Các cách ghi khác nhau trong nguồn:', 'Different source expressions:')));
      course.prerequisite_variants.forEach(variant => dialog.append(el('p', prerequisites({...course, prerequisites: variant}))));
    }
    const dependencies = [...new Set(course.prerequisites.flat())];
    if (dependencies.length) {
      const list = el('ul');
      dependencies.forEach(code => {
        const target = curriculum.courses.find(item => item.code === code);
        list.append(el('li', `${code} — ${target ? target.name : copy('Chưa có định nghĩa trong khung này', 'Not defined in this curriculum')}`));
      }); dialog.append(list);
    }
    const next = curriculum.courses.filter(item => item.prerequisites.flat().includes(course.code));
    dialog.append(el('h4', copy('Các môn có tham chiếu môn này', 'Courses referencing this course')),
      el('p', next.length ? next.map(item => `${item.code} · ${item.name}`).join('; ') : copy('Không có trong khung này.', 'None in this curriculum.')));
    if (course.hours) dialog.append(el('p', `${copy('Số giờ LT / TH / tự học', 'Hours: lectures / practice / self-study')}: ${['lecture', 'practice', 'self_study'].map(key => course.hours[key] ?? '—').join(' / ')}`));
    dialog.append(el('h4', copy('Vị trí trong tài liệu gốc', 'Original source locations')));
    course.source_occurrences.forEach(row => {
      const line = el('p'); line.append(sourceLink(row.pdf_page), document.createTextNode(` · ${copy('dòng', 'row')} ${row.source_row_number ?? '—'} · ${row.group_key}`)); dialog.append(line);
    });
    dialog.append(el('p', copy('Môn dự kiến học cùng kỳ không được coi là tiên quyết đã hoàn thành.', 'A course planned for this term does not count as a completed prerequisite.')));
    dialog.addEventListener('close', () => dialog.remove()); root.append(dialog); dialog.showModal();
  }
  function filteredCourses() {
    return curriculum.courses.filter(course => {
      const groups = course.group_ids;
      return (!query || fold(`${course.code} ${course.name} ${course.name_en || ''}`).includes(fold(query)))
        && (!group || groups.some(id => id === group || id.startsWith(`${group}.`)))
        && (!type || course.requirement_type === type)
        && (!prerequisite || (prerequisite === 'none' ? !course.prerequisites.length && !unresolved(course) : prerequisite === 'has' ? course.prerequisites.length > 0 : unresolved(course) || course.external_prerequisite_codes.length > 0));
    });
  }
  function renderTable() {
    const section = el('section', undefined, 'reference-courses');
    const courses = filteredCourses();
    section.append(el('p', `${courses.length} / ${curriculum.course_count} ${copy('học phần', 'courses')}`, 'reference-result-count'));
    const scroll = el('div', undefined, 'reference-table-scroll'); scroll.tabIndex = 0;
    scroll.setAttribute('role', 'region'); scroll.setAttribute('aria-label', copy('Danh sách học phần trong khung', 'Curriculum courses'));
    const table = el('table', undefined, 'reference-table'), header = table.createTHead().insertRow();
    [copy('Kế hoạch', 'Plan'), copy('Mã và tên học phần', 'Course'), copy('Tín chỉ', 'Credits'), copy('Nhóm / loại', 'Group / type'), copy('Tiên quyết', 'Prerequisites'), copy('Nguồn', 'Source')].forEach(text => {
      const cell = el('th', text); cell.scope = 'col'; header.append(cell);
    });
    const body = table.createTBody();
    const labels = {required: copy('Bắt buộc', 'Required'), elective: copy('Tự chọn', 'Elective'), required_excluded: copy('Điều kiện, không tính tổng', 'Required, excluded from total'), graduation: copy('Tốt nghiệp', 'Graduation')};
    courses.forEach(course => {
      const row = body.insertRow(); row.dataset.referenceCourse = course.code;
      const input = el('input'); input.type = 'checkbox'; input.checked = selected.has(course.code); input.disabled = planning;
      input.dataset.referencePlan = course.code; input.setAttribute('aria-label', `${copy('Chọn', 'Select')} ${course.code}`);
      input.addEventListener('change', () => {
        const next = new Set(selected); if (input.checked) next.add(course.code); else next.delete(course.code); updatePlan([...next]);
      }); row.insertCell().append(input);
      const name = row.insertCell();
      name.append(button(course.code, () => courseDetail(course)), el('strong', window.workspaceI18n.language === 'en' && course.name_en ? course.name_en : course.name));
      row.insertCell().textContent = course.credits;
      const classification = row.insertCell(); classification.append(el('span', labels[course.requirement_type], 'reference-badge'));
      course.group_ids.forEach(id => classification.append(el('small', curriculum.groups.find(value => value.id === id)?.name || id)));
      const pre = row.insertCell(); pre.append(el('p', prerequisites(course)));
      if (unresolved(course)) pre.append(el('span', copy('Nguồn chưa rõ / mâu thuẫn', 'Unresolved / conflicting source'), 'reference-source-warning'));
      if (course.external_prerequisite_codes.length) pre.append(el('small', `${copy('Mã ngoài khung', 'Codes outside this curriculum')}: ${course.external_prerequisite_codes.join(', ')}`));
      const sources = row.insertCell();
      [...new Set(course.source_occurrences.map(value => value.pdf_page))].forEach(page => sources.append(sourceLink(page)));
    });
    if (!courses.length) { const cell = body.insertRow().insertCell(); cell.colSpan = 6; cell.textContent = copy('Không có môn phù hợp bộ lọc.', 'No courses match the filters.'); }
    scroll.append(table); section.append(scroll); return section;
  }
  function download() {
    const escape = value => {
      let text = String(value ?? ''); if (/^[=+@-]/.test(text)) text = `'${text}`;
      return `"${text.replaceAll('"', '""')}"`;
    };
    const rows = [['Program', 'Cohort', 'Course code', 'Course name', 'Credits', 'Prerequisites', 'Source', 'Status'],
      ...curriculum.courses.filter(course => selected.has(course.code)).map(course => [curriculum.name, `K${cohort}`, course.code, course.name, course.credits, prerequisites(course), curriculum.source_file, 'Hypothetical plan; eligibility not evaluated'])];
    const blob = new Blob(['\uFEFF' + rows.map(row => row.map(escape).join(',')).join('\r\n')], {type: 'text/csv;charset=utf-8'});
    const url = URL.createObjectURL(blob), link = el('a'); link.href = url; link.download = `ke-hoach-${program}-K${cohort}.csv`; link.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
  function renderPlan() {
    const section = el('section', undefined, 'reference-plan');
    section.append(el('h3', copy('Kế hoạch kỳ tới', 'Next-term plan')),
      el('p', copy('Kế hoạch tham khảo, chưa đối chiếu bảng điểm hoặc lịch mở lớp.', 'A hypothetical plan; transcript results and course offerings have not been checked.'), 'reference-muted'));
    const total = curriculum.courses.filter(course => selected.has(course.code)).reduce((sum, course) => sum + course.credits, 0);
    const controls = el('form', undefined, 'reference-budget-form'), label = el('label', copy('Ngân sách tín chỉ mỗi kỳ', 'Credits per term'));
    const input = el('input'); input.type = 'number'; input.min = '1'; input.max = '30'; input.step = '1'; input.value = budget; input.id = 'reference-credit-budget'; input.disabled = planning;
    label.append(input); const apply = el('button', copy('Áp dụng', 'Apply'), 'portal-button'); apply.type = 'submit'; apply.disabled = planning;
    controls.addEventListener('submit', event => { event.preventDefault(); if (controls.reportValidity()) updatePlan([...selected], false, Number(input.value)); });
    controls.append(label, apply, el('strong', `${total} / ${credits(budget)}`)); section.append(controls);
    const progress = el('progress'); progress.max = budget; progress.value = Math.min(total, budget); progress.setAttribute('aria-label', copy('Tín chỉ đã chọn', 'Selected credits')); section.append(progress);
    const actions = el('div', undefined, 'reference-plan-actions');
    actions.append(button(copy('Gợi ý môn không ghi tiên quyết', 'Suggest courses without recorded prerequisites'), () => updatePlan([], true), planning),
      button(copy('Bỏ chọn tất cả', 'Clear selection'), () => updatePlan([]), planning || !selected.size),
      button(copy('Tải kế hoạch CSV', 'Download plan CSV'), download, planning || !selected.size)); section.append(actions);
    const chips = el('div', undefined, 'reference-selected');
    curriculum.courses.filter(course => selected.has(course.code)).forEach(course => chips.append(button(`${course.code} · ${credits(course.credits)} ×`, () => updatePlan([...selected].filter(code => code !== course.code)), planning)));
    section.append(chips);
    if (plan?.warnings.length) {
      const list = el('ul', undefined, 'reference-plan-warnings');
      plan.warnings.forEach(warning => {
        const text = ({prerequisites_not_verified: copy('Cần đối chiếu môn tiên quyết với bảng điểm đã xác minh.', 'Prerequisites must be checked against verified transcript outcomes.'),
          source_prerequisite_unresolved: copy('Tiên quyết trong nguồn chưa rõ hoặc mâu thuẫn.', 'Source prerequisites are unresolved or conflicting.'),
          graduation_requirements_not_verified: copy('Chưa kiểm tra điều kiện thực tập / tốt nghiệp.', 'Internship / graduation requirements have not been checked.'),
          group_target_exceeded: copy('Lựa chọn vượt số tín chỉ yêu cầu của nhóm; cần kiểm tra cách tính.', 'Selections exceed the group credit target; check the counting rules.')})[warning.code];
        list.append(el('li', `${warning.course_code || warning.group_id}: ${text}`));
      }); section.append(list);
    }
    return section;
  }
  function render() {
    modeButtons[0].textContent = copy('Tra cứu khung chương trình', 'Browse curricula');
    modeButtons[1].textContent = copy('Theo bảng điểm VNU', 'My VNU transcript');
    root.replaceChildren(); root.setAttribute('aria-busy', String(loading || planning));
    const heading = el('div', undefined, 'reference-heading');
    heading.append(el('h2', copy('Tra cứu điều kiện học', 'Explore course requirements')),
      el('p', copy('Chọn chương trình, xem điều kiện tiên quyết và xây dựng kế hoạch tín chỉ của bạn.', 'Choose a curriculum, explore prerequisites and build a credit plan.'))); root.append(heading);
    if (error) { const notice = el('p', errorMessage(error), 'reference-error'); notice.setAttribute('role', 'alert'); root.append(notice); }
    if (!index) {
      root.append(el('p', loading ? copy('Đang tải danh mục chương trình…', 'Loading curricula…') : copy('Chọn tra cứu để tải danh mục.', 'Open curriculum lookup to load the list.')));
      if (!loading) root.append(button(copy('Thử lại', 'Retry'), initialize)); return;
    }
    const toolbar = el('div', undefined, 'reference-selectors');
    toolbar.append(select(copy('Ngành và chương trình', 'Major and curriculum'), 'reference-program',
      [[copy('Chọn chương trình', 'Choose a curriculum'), ''], ...index.programs.map(value => [value.name, value.program_id])], program, value => { program = value; load(); }),
      select(copy('Khóa tuyển sinh', 'Admission cohort'), 'reference-cohort', index.cohorts.map(value => [`K${value.number} · ${value.admission_year}`, String(value.number)]), String(cohort), value => { cohort = Number(value); load(); })); root.append(toolbar);
    root.append(el('p', copy('Bộ khung ban hành năm 2023, áp dụng từ K67. Văn bản sửa đổi cho các khóa sau chưa được đối chiếu.', 'The 2023 curricula apply from K67. Later amendments for subsequent cohorts have not been checked.'), 'reference-scope'));
    if (loading) { root.append(el('p', copy('Đang tải khung chương trình…', 'Loading the curriculum…'))); return; }
    if (!curriculum) {
      const cards = el('div', undefined, 'reference-program-grid');
      index.programs.forEach(value => {
        const card = button('', () => { program = value.program_id; load(); }); card.classList.add('reference-program-card');
        card.append(el('strong', value.name), el('span', `${value.course_count} ${copy('học phần', 'courses')} · ${credits(value.total_credits)}`), el('small', value.decision)); cards.append(card);
      }); root.append(cards); return;
    }
    const facts = el('section', undefined, 'reference-facts');
    facts.append(el('h3', curriculum.name), el('p', `${credits(curriculum.total_credits)} · ${curriculum.course_count} ${copy('mã học phần', 'course codes')} · ${curriculum.source_occurrence_count} ${copy('dòng nguồn', 'source occurrences')} · ${curriculum.decision}`), sourceLink(null, copy('Mở PDF khung chương trình', 'Open the source curriculum PDF'))); root.append(facts);
    if (curriculum.issues.length) {
      const details = el('details', undefined, 'reference-source-issues'); details.append(el('summary', copy('Những điểm cần đối chiếu trong nguồn', 'Source issues requiring review')));
      const list = el('ul'); curriculum.issues.forEach(issue => list.append(el('li', issue))); details.append(list); root.append(details);
    }
    root.append(renderPlan());
    const filters = el('div', undefined, 'reference-filters'), searchLabel = el('label', copy('Tìm học phần', 'Find a course'));
    const search = el('input'); search.type = 'search'; search.id = 'reference-search'; search.value = query; search.placeholder = copy('Mã hoặc tên môn, có thể gõ không dấu', 'Course code or name');
    search.addEventListener('input', () => { query = search.value; root.querySelector('.reference-courses').replaceWith(renderTable()); }); searchLabel.append(search);
    filters.append(searchLabel,
      select(copy('Nhóm kiến thức', 'Knowledge group'), 'reference-group', [[copy('Tất cả nhóm', 'All groups'), ''], ...curriculum.groups.map(value => [value.name, value.id])], group, value => { group = value; render(); }),
      select(copy('Loại học phần', 'Course type'), 'reference-type', [[copy('Tất cả loại', 'All types'), ''], [copy('Bắt buộc', 'Required'), 'required'], [copy('Tự chọn', 'Elective'), 'elective'], [copy('Điều kiện, không tính tổng', 'Required, excluded'), 'required_excluded'], [copy('Tốt nghiệp', 'Graduation'), 'graduation']], type, value => { type = value; render(); }),
      select(copy('Điều kiện', 'Prerequisite filter'), 'reference-prerequisite', [[copy('Tất cả điều kiện', 'All prerequisites'), ''], [copy('Không ghi tiên quyết', 'No recorded prerequisite'), 'none'], [copy('Có tiên quyết', 'Has prerequisites'), 'has'], [copy('Cần đối chiếu nguồn', 'Needs source review'), 'unresolved']], prerequisite, value => { prerequisite = value; render(); })); root.append(filters, renderTable());
    const groups = el('details', undefined, 'reference-group-summary'); groups.append(el('summary', copy('Xem yêu cầu tín chỉ theo nhóm', 'View group credit requirements')));
    const list = el('ul'); curriculum.groups.forEach(value => list.append(el('li', `${value.name}: ${value.required_credits === null ? copy('chưa có chỉ tiêu', 'target unavailable') : credits(value.required_credits)}`))); groups.append(list); root.append(groups);
  }
  document.addEventListener('workspace:navigate', event => { if (event.detail === 'tab-rules' && mode === 'reference' && !index && !loading) initialize(); });
  document.addEventListener('workspace:language-change', render);
  render();
  if (new URLSearchParams(location.search).get('course-mode') === 'personal') setMode('personal');
  else if (document.documentElement.dataset.view === 'tab-rules') initialize();
})();
