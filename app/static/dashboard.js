/* Dashboard reads the manual study plan only. Portal records stay in the profile. */
(() => {
  const $ = id => document.getElementById(`dashboard-${id}`);
  const translate = (vi, en) => window.workspaceI18n.language === 'en' ? en : vi;
  function node(tag, className, text) {
    const element = document.createElement(tag); element.className = className;
    element.textContent = text; return element;
  }
  function render() {
    const program = state.programs.find(item => item.program_id === state.currentProgramId);
    if (!program) return;
    const earned = Number(dom.kpiCredits.textContent) || 0;
    const required = Number(program.total_credits) || 0;
    $('program').textContent = dom.programSelect.selectedOptions[0]?.textContent || '';
    $('earned').textContent = earned;
    $('required').textContent = translate(`/ ${required || '—'} tín chỉ`, `/ ${required || '—'} credits`);
    $('progress').value = required ? Math.min(100, earned / required * 100) : 0;
    $('progress').setAttribute('aria-valuetext', `${earned} / ${required || '—'}`);
    $('terms').replaceChildren();
    const terms = new Map();
    state.transcript.forEach(record => { const key = record.term || ''; terms.set(key, (terms.get(key) || 0) + 1); });
    const order = key => { const t = state.transcriptTerms.get(key); return t ? t.year * 10 + t.semester : 0; };
    if (!terms.size) {
      $('terms').append(node('p', 'dashboard-empty', translate('Chưa ghi nhận học phần. Thêm kết quả đã học để bắt đầu theo dõi.', 'No courses recorded. Add your results to start tracking your study plan.')));
    }
    [...terms].sort(([a], [b]) => order(b) - order(a)).slice(0, 3).forEach(([key, count]) => {
      const row = node('div', 'dashboard-term-row', '');
      row.append(node('span', '', termLabel(state.transcriptTerms.get(key))), node('strong', '', translate(`${count} học phần`, `${count} courses`)));
      $('terms').append(row);
    });
    $('courses').replaceChildren();
    const eligible = /^\d+$/.test(dom.kpiEligibleCount.textContent.trim()) ? state.eligibleCourses : [];
    eligible.slice(0, 4).forEach(course => {
      const metadata = state.courses.find(item => item.code === course.code);
      const row = node('div', 'dashboard-course', ''); row.dataset.courseCode = course.code;
      const info = node('div', '', '');
      info.append(node('span', 'dashboard-course-code', course.code), node('strong', '', state.courseLanguage === 'en' && metadata?.name_en ? metadata.name_en : course.name));
      row.append(info, node('span', 'dashboard-course-credits', translate(`${course.credits ?? '—'} TC`, `${course.credits ?? '—'} cr`)));
      $('courses').append(row);
    });
    if (!eligible.length) $('courses').append(node('p', 'dashboard-empty', translate('Chưa có kết quả điều kiện học. Xem mục Điều kiện học để kiểm tra.', 'No eligibility results yet. Open Eligibility to review.')));
  }
  document.querySelectorAll('[data-navigate]').forEach(button => {
    button.addEventListener('click', () => window.workspaceNavigate(button.dataset.navigate));
  });
  document.getElementById('course-language-select').addEventListener('change', render);
  document.addEventListener('workspace:navigate', render);
  let scheduled = false;
  const observer = new MutationObserver(() => {
    if (scheduled) return;
    scheduled = true; requestAnimationFrame(() => { scheduled = false; render(); });
  });
  ['kpi-credits', 'kpi-eligible-count', 'kpi-total-credits-sub', 'kpi-passed-count'].forEach(id => {
    observer.observe(document.getElementById(id), {childList: true, characterData: true, subtree: true});
  });
  render();
})();
