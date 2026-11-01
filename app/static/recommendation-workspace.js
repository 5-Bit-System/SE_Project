import {VARIANTS, comparePlans, constrainRecommendations, defaultTerm, recommendationPayload} from './recommendation-model.mjs';

const root = document.getElementById('recommendation-workspace');
const tools = document.getElementById('academic-plan-tools');
const copy = (vi, en) => window.workspaceI18n.language === 'en' ? en : vi;
const reduced = matchMedia('(prefers-reduced-motion: reduce)');
const node = (tag, text, cls) => {
  const element = document.createElement(tag);
  if (text !== undefined) element.textContent = text;
  if (cls) element.className = cls;
  return element;
};
const paths = {
  spark: 'm12 2 2.8 7.2L22 12l-7.2 2.8L12 22l-2.8-7.2L2 12l7.2-2.8L12 2Z',
  arrow: 'M5 12h14m-6-6 6 6-6 6',
  send: 'm5 12 7-7 7 7M12 5v15',
  check: 'm5 12 4 4L19 6',
  branch: 'M6 3v12a5 5 0 0 0 5 5h7M6 7h7a5 5 0 0 1 5 5v8',
  layers: 'm12 3 10 5-10 5L2 8l10-5ZM2 12l10 5 10-5M2 16l10 5 10-5',
  close: 'm6 6 12 12M18 6 6 18',
  clock: 'M12 7v5l3 2M22 12a10 10 0 1 1-20 0 10 10 0 0 1 20 0Z',
  leaf: 'M20 3c-11 0-17 4-15 11s12 7 15-11ZM4 21 15 10',
  waves: 'M2 7c4-5 6 5 10 0s6 5 10 0M2 12c4-5 6 5 10 0s6 5 10 0M2 17c4-5 6 5 10 0s6 5 10 0',
};
function icon(name) {
  const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
  svg.setAttribute('viewBox', '0 0 24 24'); svg.setAttribute('fill', 'none');
  svg.setAttribute('stroke', 'currentColor'); svg.setAttribute('stroke-width', '1.6');
  svg.setAttribute('stroke-linecap', 'round'); svg.setAttribute('stroke-linejoin', 'round');
  svg.setAttribute('aria-hidden', 'true');
  const path = document.createElementNS(svg.namespaceURI, 'path');
  path.setAttribute('d', paths[name] || paths.spark); svg.append(path);
  return svg;
}
function button(text, action, cls = 'rec-button') {
  const result = node('button', text, cls); result.type = 'button';
  result.addEventListener('click', action); return result;
}
const titleFor = id => ({balanced: copy('Cân bằng', 'Balanced'),
  graduation: copy('Ưu tiên tốt nghiệp', 'Graduation focus'),
  direction: copy('Sát định hướng', 'Interest focus')})[id];
const hintFor = id => ({balanced: copy('Hài hòa mục tiêu và môn bắt buộc', 'Balance interests and required courses'),
  graduation: copy('Tăng ưu tiên môn bắt buộc còn thiếu', 'Give remaining required courses more weight'),
  direction: copy('Tăng ưu tiên chủ đề bạn quan tâm', 'Give your interests more weight')})[id];
let live = window.workspacePlanning?.snapshot() || {};
let identity = live.identity || '';
let answers, step = 0, results = {}, selected = 'balanced', busy = false, error = '';
let requestEpoch = 0, requestController, generationRevision = '', catalog = new Map();
let catalogProgram = '', catalogSequence = 0, saved = new Set(), draftText = '';
const uncertainSaves = new Set();
let generationPassed = new Set();
let pendingSave = false, introShown = false, reviewMode = false;
let planningStateKey = '';
const animations = new Set();
const dialog = node('dialog', undefined, 'rec-dialog');
document.body.append(dialog);
dialog.addEventListener('click', event => { if (event.target === dialog && !pendingSave) dialog.close(); });
dialog.addEventListener('cancel', event => { if (pendingSave) event.preventDefault(); });
dialog.addEventListener('close', () => { if (!dialog.open) dialog.replaceChildren(); });

function initialAnswers() {
  const term = defaultTerm();
  return {direction: '', directionLabel: '', workload: 'moderate', credits: 20,
    track: live.track || '', path: live.path || '', goal: '',
    targetYear: new Date().getFullYear() + 1, targetSemester: 2,
    year: term.year, semester: term.semester, confirmedWorkload: false, confirmedDeadline: false};
}
answers = initialAnswers();
function animate(element, frames, options = {}) {
  if (reduced.matches || document.hidden || document.documentElement.dataset.view !== 'tab-recommend' || !element?.animate) return;
  const animation = element.animate(frames, {duration: 350, easing: 'cubic-bezier(.2,.8,.2,1)', ...options});
  animations.add(animation);
  animation.finished.then(() => animations.delete(animation), () => animations.delete(animation));
  return animation;
}
function cancelMotion() {
  animations.forEach(animation => animation.cancel()); animations.clear();
  document.querySelectorAll('.rec-flying-chip').forEach(element => element.remove());
}
function clearResults() {
  requestEpoch++; requestController?.abort(); busy = false; generationRevision = '';
  results = {}; saved.clear(); uncertainSaves.clear(); error = '';
  generationPassed.clear();
}
function steps() {
  const result = ['direction', 'workload', 'deadline'];
  if (live.board?.selections?.path_required || live.board?.selections?.paths?.length) result.push('graduation');
  return result;
}
function answered(key) {
  return {direction: Boolean(answers.direction) && (!live.board?.selections?.track_required || Boolean(answers.track)), workload: answers.confirmedWorkload,
    deadline: answers.confirmedDeadline, graduation: Boolean(answers.path)}[key];
}
function readyToGenerate() { return steps().every(answered); }
function currentStep() { return steps()[Math.min(step, steps().length - 1)]; }
function workloadLabel() {
  return ({light: copy('Nhẹ nhàng', 'Light'), moderate: copy('Cân bằng', 'Moderate'), heavy: copy('Tập trung', 'Intensive')})[answers.workload];
}
function courseName(course) {
  return window.workspaceI18n.language === 'en' && course?.name_en ? course.name_en : course?.name || course?.code || '';
}
function openTools() {
  tools.open = true;
  tools.scrollIntoView({behavior: reduced.matches ? 'instant' : 'smooth', block: 'start'});
  tools.querySelector('summary').focus({preventScroll: true});
}
function flyChoice(rect, text, key) {
  const destination = root.querySelector(`[data-rec-answer="${key}"]`);
  if (!rect || !destination || reduced.matches || document.hidden || innerWidth < 900) return;
  const target = destination.getBoundingClientRect();
  const chip = node('div', text, 'rec-flying-chip'); chip.setAttribute('aria-hidden', 'true'); chip.inert = true;
  Object.assign(chip.style, {left: `${rect.left}px`, top: `${rect.top}px`, width: `${Math.min(rect.width, 280)}px`});
  document.body.append(chip);
  const movement = animate(chip, [{transform: 'translate(0,0) scale(1)', opacity: .9},
    {transform: `translate(${target.left - rect.left}px,${target.top - rect.top}px) scale(.72)`, opacity: 0}], {duration: 480});
  if (movement) movement.finished.then(() => chip.remove(), () => chip.remove()); else chip.remove();
}
function choose(key, value, element) {
  const rect = element?.getBoundingClientRect(); clearResults();
  if (key === 'direction') {
    answers.direction = value.id; answers.directionLabel = value.label;
    if (value.track) { answers.track = value.track; answers.path = ''; }
  }
  if (key === 'workload') { answers.workload = value; answers.confirmedWorkload = true; }
  if (key === 'deadline') answers.confirmedDeadline = true;
  if (key === 'graduation') answers.path = value;
  step = Math.min(step + 1, steps().length - 1);
  reviewMode = readyToGenerate();
  render(true); flyChoice(rect, key === 'direction' ? answers.directionLabel : key === 'workload' ? workloadLabel() : copy('Đã chọn', 'Selected'), key);
}

function directionOptions() {
  const tracks = live.board?.selections?.tracks || [];
  if (live.board?.selections?.track_required && tracks.length) {
    return tracks.map(track => ({id: track.id, track: track.id, label: track.name,
      hint: copy('Hướng trong chương trình của bạn', 'A track in your curriculum'), icon: 'branch'}));
  }
  const id = live.board?.program_id || '';
  const math = id.startsWith('toan_hoc');
  return math ? [
    {id: 'applied', label: copy('Toán ứng dụng', 'Applied mathematics'), hint: copy('Mô hình hóa và bài toán thực tế', 'Models and real-world problems'), icon: 'branch'},
    {id: 'research', label: copy('Nghiên cứu', 'Research'), hint: copy('Lý thuyết và nền tảng chuyên sâu', 'Theory and deeper foundations'), icon: 'spark'},
    {id: 'data', label: copy('Dữ liệu & thống kê', 'Data & statistics'), hint: copy('Xác suất và phân tích dữ liệu', 'Probability and data analysis'), icon: 'layers'},
    {id: 'explore', label: copy('Mình chưa rõ', 'Still exploring'), hint: copy('Bắt đầu từ nền tảng còn thiếu', 'Start with remaining foundations'), icon: 'waves'},
  ] : [
    {id: 'ai', label: copy('Trí tuệ nhân tạo', 'Artificial intelligence'), hint: copy('Học máy, dữ liệu và ứng dụng AI', 'Machine learning, data and AI'), icon: 'spark'},
    {id: 'software', label: copy('Phát triển phần mềm', 'Software development'), hint: copy('Xây dựng sản phẩm và hệ thống', 'Build products and systems'), icon: 'branch'},
    {id: 'data', label: copy('Khoa học dữ liệu', 'Data science'), hint: copy('Phân tích, thống kê và mô hình', 'Analysis, statistics and models'), icon: 'layers'},
    {id: 'explore', label: copy('Mình chưa rõ', 'Still exploring'), hint: copy('Cân bằng các lựa chọn phù hợp', 'Explore suitable options'), icon: 'waves'},
  ];
}

function readiness() {
  if (!live.sourceAvailable) return copy('Kết nối hồ sơ VNU để gợi ý dựa trên quá trình học của bạn.', 'Connect your VNU profile for suggestions based on your studies.');
  if (live.loading) return copy('Đang đối chiếu chương trình và bảng điểm…', 'Checking your curriculum and transcript…');
  if (live.failed) return copy('Chưa đọc được dữ liệu học vụ. Bạn vẫn có thể chuẩn bị mục tiêu rồi thử lại.', 'Academic data could not be loaded. Set your goals and try again.');
  if (!live.board?.courses) return copy('Cần xác nhận bảng điểm và chương trình trước khi tạo gợi ý.', 'Confirm your transcript and curriculum before generating suggestions.');
  if (live.board.preview_only) return copy('Khung chương trình đang chờ xác minh. Bạn có thể chuẩn bị mục tiêu; gợi ý và lưu sẽ mở khi dữ liệu đủ điều kiện.', 'Your curriculum is awaiting verification. Set your goals now; generation and saving require verified data.');
  if (live.board.status === 'partial') {
    const blockers = live.board.blocking_reasons || [];
    if (blockers.length && blockers.every(reason => reason === 'track_selection_required' ? answers.track
      : reason === 'graduation_selection_required' ? answers.path : false)) return '';
    return copy('Một phần dữ liệu hoặc hướng học cần đối chiếu. Các lựa chọn dưới đây được giữ để bạn hoàn tất sau.', 'Some data or selections need review. Your choices below remain available to complete later.');
  }
  return '';
}

function render(transition = false) {
  cancelMotion(); root.replaceChildren();
  const heading = node('header', undefined, 'rec-heading');
  const intro = node('div');
  intro.append(node('p', copy('Một học kỳ, nhiều khả năng.', 'One semester. More possibilities.'), 'rec-kicker'),
    node('h2', copy('Kỳ tới, học theo cách của bạn.', 'Your next semester, your way.')),
    node('p', copy('Nói về mục tiêu. Cùng tìm những môn đưa bạn đến gần hơn.', 'Share your goals. Find the courses that move you forward.')));
  const history = button(copy('Phương án đã lưu', 'Saved alternatives'), openTools, 'rec-button rec-secondary');
  history.prepend(icon('layers')); heading.append(intro, history); root.append(heading);
  const shell = node('div', undefined, 'rec-shell');
  const conversation = node('section', undefined, 'rec-conversation');
  conversation.setAttribute('aria-label', copy('Tư vấn môn học', 'Course consultation'));
  const top = node('div', undefined, 'rec-conversation-top');
  const mark = node('span', undefined, 'rec-advisor-mark'); mark.append(icon('spark'));
  const identity = node('div'); identity.append(node('strong', copy('Cố vấn học tập', 'Study companion')),
    node('span', live.profile?.program || copy('Từ mục tiêu đến lộ trình', 'From goals to a study path')));
  top.append(mark, identity, node('span', copy('Dành riêng cho bạn', 'Made for you'), 'rec-live-label'));
  conversation.append(top);
  const notice = readiness();
  if (notice) {
    const status = node('div', undefined, 'rec-source-status'); status.setAttribute('role', 'status');
    status.append(node('p', notice), button(copy('Kiểm tra dữ liệu', 'Review data'), openTools, 'rec-text-button'));
    conversation.append(status);
  }
  conversation.append(renderTranscript(), renderQuestion(), renderComposer());
  const footer = node('div', undefined, 'rec-conversation-foot');
  footer.append(node('span', copy('Bảng điểm của bạn là điểm bắt đầu.', 'Your transcript is the starting point.')),
    button(copy('Làm lại', 'Start over'), () => { clearResults(); answers = initialAnswers(); step = 0; draftText = ''; reviewMode = false; render(); }, 'rec-text-button'));
  conversation.append(footer);
  shell.append(conversation, renderRoadmap()); root.append(shell);
  const resultsArea = node('section', undefined, 'rec-results'); resultsArea.id = 'rec-results'; root.append(resultsArea);
  renderResults();
  const mobile = button(copy('Xem lộ trình của bạn', 'View your study path'), openMobileRoadmap, 'rec-mobile-roadmap');
  mobile.prepend(icon('branch')); root.append(mobile);
  const toolsLabel = document.querySelector('[data-rec-tools-label]');
  if (toolsLabel) toolsLabel.textContent = copy('Dữ liệu học vụ & phương án đã lưu', 'Academic data & saved alternatives');
  if (transition && document.documentElement.dataset.view === 'tab-recommend') {
    const question = root.querySelector('.rec-question');
    animate(question, [{opacity: 0, transform: 'translateY(12px)'}, {opacity: 1, transform: 'translateY(0)'}], {duration: 300});
    question.querySelector('h3')?.focus({preventScroll: true});
  }
  reveal();
}
function reveal() {
  if (introShown || document.documentElement.dataset.view !== 'tab-recommend' || !root.getClientRects().length) return;
  introShown = true;
  animate(root.querySelector('.rec-conversation'), [{opacity: 0, transform: 'translateY(20px)'}, {opacity: 1, transform: 'translateY(0)'}], {duration: 650});
  animate(root.querySelector('.rec-roadmap'), [{opacity: 0, transform: 'translateY(24px) rotate(2deg)'}, {opacity: 1, transform: 'translateY(0) rotate(0)'}], {duration: 800, delay: 90});
}

function renderTranscript() {
  const transcript = node('div', undefined, 'rec-transcript');
  const labels = {direction: copy('Định hướng', 'Direction'), workload: copy('Tải học', 'Study load'),
    deadline: copy('Mốc tốt nghiệp', 'Graduation goal'), graduation: copy('Hướng tốt nghiệp', 'Graduation path')};
  steps().forEach((key, index) => {
    if (!answered(key)) return;
    const value = key === 'direction' ? answers.directionLabel : key === 'workload'
      ? `${workloadLabel()} · ${answers.credits} ${copy('tín chỉ', 'credits')}`
      : key === 'deadline' ? `${copy('HK', 'Sem ')}${answers.targetSemester} · ${answers.targetYear}–${answers.targetYear + 1}`
      : live.board?.selections?.paths?.find(path => path.id === answers.path)?.name || answers.path;
    const row = button('', () => { step = index; reviewMode = false; clearResults(); render(true); }, 'rec-answer');
    row.append(node('span', labels[key]), node('strong', value), node('span', copy('Sửa', 'Edit'), 'rec-answer-edit'));
    row.setAttribute('aria-label', `${copy('Sửa', 'Edit')} ${labels[key]}: ${value}`);
    transcript.append(row);
  });
  if (answers.goal) {
    const message = button('', () => {
      const input = root.querySelector('#rec-goal'); draftText = answers.goal; input.value = draftText; input.focus();
    }, 'rec-answer rec-free-goal');
    message.append(node('span', copy('Bạn nhắn', 'Your note')), node('strong', answers.goal)); transcript.append(message);
  }
  return transcript;
}

function renderQuestion() {
  const section = node('div', undefined, 'rec-question'); section.dataset.step = currentStep();
  const progress = node('div', undefined, 'rec-step-progress');
  steps().forEach((key, index) => {
    const part = button('', () => { step = index; reviewMode = false; render(true); }, 'rec-step-dot');
    part.classList.toggle('is-done', answered(key)); part.classList.toggle('is-current', index === step);
    part.setAttribute('aria-label', `${copy('Bước', 'Step')} ${index + 1}`);
    part.setAttribute('aria-current', index === step ? 'step' : 'false'); progress.append(part);
  });
  const key = currentStep();
  const titles = {direction: copy('Bạn muốn đi theo hướng nào?', 'Where would you like to go?'),
    workload: copy('Một học kỳ như thế nào là vừa?', 'What pace feels right for you?'),
    deadline: copy('Bạn muốn chạm mốc tốt nghiệp khi nào?', 'When would you like to graduate?'),
    graduation: copy('Bạn chọn hướng tốt nghiệp nào?', 'Which graduation path suits you?')};
  const reviewing = readyToGenerate() && reviewMode;
  const title = node('h3', reviewing ? copy('Mong muốn của bạn đã rõ hơn rồi.', 'Your goals are coming into focus.') : titles[key]); title.tabIndex = -1; title.id = 'rec-question-title';
  section.append(progress, title);
  if (reviewing) {
    section.classList.add('rec-review');
    section.append(node('p', copy('Cùng đối chiếu các lựa chọn này với quá trình học và khám phá ba cách sắp xếp học kỳ tới.', 'Let’s check these preferences against your academic data and explore three approaches to next semester.'), 'rec-question-hint'));
  } else if (key === 'direction') {
    section.append(node('p', copy('Chọn một hướng hoặc kể thêm điều bạn muốn thử.', 'Choose a direction or describe what you want to explore.'), 'rec-question-hint'));
    const grid = node('div', undefined, 'rec-choices');
    directionOptions().forEach(option => {
      const card = button('', event => choose('direction', option, event.currentTarget), 'rec-choice');
      card.dataset.recDirection = option.id; card.setAttribute('aria-pressed', String(answers.direction === option.id));
      const mark = node('span', undefined, 'rec-choice-icon'); mark.append(icon(option.icon));
      card.append(mark, node('strong', option.label), node('span', option.hint), icon('arrow')); grid.append(card);
    }); section.append(grid);
  } else if (key === 'workload') {
    const loads = node('div', undefined, 'rec-load-options');
    for (const [value, vi, en, image] of [['light', 'Nhẹ nhàng', 'Light', 'leaf'], ['moderate', 'Cân bằng', 'Moderate', 'waves'], ['heavy', 'Tập trung', 'Intensive', 'spark']]) {
      const option = button('', () => { answers.workload = value; clearResults(); render(); }, 'rec-load-choice');
      option.setAttribute('aria-pressed', String(answers.workload === value)); option.dataset.recLoad = value;
      option.append(icon(image), node('span', copy(vi, en))); loads.append(option);
    }
    const budget = node('div', undefined, `rec-budget rec-load-${answers.workload}`);
    const label = node('label', copy('Tín chỉ kỳ tới', 'Next-term credits')); label.htmlFor = 'rec-credit-budget';
    const number = node('input'); number.id = 'rec-credit-budget'; number.type = 'number';
    number.min = '1'; number.max = '30'; number.step = '1'; number.value = answers.credits;
    const slider = node('input'); slider.type = 'range'; slider.min = '1'; slider.max = '30'; slider.step = '1'; slider.value = answers.credits;
    slider.setAttribute('aria-label', copy('Điều chỉnh tín chỉ kỳ tới', 'Adjust next-term credits'));
    function update(value) {
      const next = Number(value); if (!Number.isInteger(next) || next < 1 || next > 30) return;
      answers.credits = next; number.value = next; slider.value = next; clearResults(); updateRoadmap(); renderResults();
    }
    number.addEventListener('input', () => update(number.value)); slider.addEventListener('input', () => update(slider.value));
    budget.append(label, number, node('span', copy('tín chỉ', 'credits')), slider);
    section.append(loads, budget, node('p', copy('Mặc định 20 tín chỉ. Mức tải là mong muốn của bạn; độ nặng từng môn còn phụ thuộc dữ liệu chương trình.', 'Default: 20 credits. Study load is your preference; course workload depends on available metadata.'), 'rec-question-hint'),
      button(copy('Đúng nhịp của mình', 'This pace works for me'), event => {
        if (!number.reportValidity()) return; choose('workload', answers.workload, event.currentTarget);
      }, 'rec-button rec-primary'));
  } else if (key === 'deadline') {
    section.append(node('p', copy('Đây là mục tiêu để tham khảo, chưa phải thời điểm tốt nghiệp được xác nhận.', 'This is a planning goal, not a confirmed graduation date.'), 'rec-question-hint'));
    const form = node('form', undefined, 'rec-deadline-form');
    form.append(termSelect('rec-target-semester', copy('Học kỳ', 'Semester'), answers.targetSemester, value => { answers.targetSemester = value; }, 3),
      yearSelect('rec-target-year', copy('Năm học bắt đầu', 'Academic year starts'), answers.targetYear, value => { answers.targetYear = value; }));
    const confirm = node('button', copy('Ghi nhận mục tiêu', 'Set my goal'), 'rec-button rec-primary'); confirm.type = 'submit';
    form.append(confirm); form.onsubmit = event => { event.preventDefault(); choose('deadline', null, confirm); }; section.append(form);
  } else {
    const paths = (live.board?.selections?.paths || []).filter(path => !answers.track || !path.allowed_track_ids?.length || path.allowed_track_ids.includes(answers.track));
    section.append(node('p', copy('Các lựa chọn dưới đây lấy từ đúng chương trình áp dụng cho bạn.', 'These options come from your applicable curriculum.'), 'rec-question-hint'));
    const grid = node('div', undefined, 'rec-choices');
    paths.forEach(path => {
      const option = button('', event => choose('graduation', path.id, event.currentTarget), 'rec-choice');
      option.dataset.recPath = path.id; option.setAttribute('aria-pressed', String(answers.path === path.id));
      option.append(icon('branch'), node('strong', path.name), node('span', copy('Xem môn phù hợp với nhánh này', 'Find courses for this path'))); grid.append(option);
    }); section.append(grid);
    if (!paths.length) section.append(button(copy('Kiểm tra hướng chuyên ngành', 'Review study track'), openTools));
  }
  if (readyToGenerate()) {
    const action = button('', generate, 'rec-button rec-primary rec-generate'); action.id = 'rec-generate';
    action.disabled = busy || live.loading || !live.sourceAvailable;
    action.append(icon('spark'), node('span', busy ? copy('Đang đối chiếu…', 'Checking your options…') : copy('Tìm phương án cho mình', 'Find my study options')));
    section.append(action);
  }
  return section;
}

function renderComposer() {
  const form = node('form', undefined, 'rec-composer');
  const label = node('label', copy('Chia sẻ thêm mong muốn', 'Tell us more')); label.htmlFor = 'rec-goal'; label.className = 'sr-only';
  const input = node('textarea'); input.id = 'rec-goal'; input.rows = 1; input.maxLength = 400;
  input.value = draftText; input.placeholder = copy('Ví dụ: mình muốn có thời gian thực tập, ưu tiên học máy…', 'For example: leave time for an internship, focus on machine learning…');
  input.addEventListener('input', () => { draftText = input.value; input.style.height = 'auto'; input.style.height = `${Math.min(input.scrollHeight, 140)}px`; });
  const send = node('button', undefined, 'rec-send'); send.type = 'submit'; send.append(icon('send')); send.setAttribute('aria-label', copy('Ghi nhận mong muốn', 'Add my preferences'));
  form.append(label, input, send); form.onsubmit = event => {
    event.preventDefault(); answers.goal = draftText.trim(); draftText = ''; clearResults();
    if (answers.goal && !answers.direction && !live.board?.selections?.track_required) {
      answers.direction = 'custom'; answers.directionLabel = copy('Định hướng của mình', 'My own direction'); step = 1;
    }
    render(true);
  };
  input.addEventListener('keydown', event => { if (event.key === 'Enter' && !event.shiftKey && !event.isComposing) { event.preventDefault(); form.requestSubmit(); } });
  return form;
}

function termSelect(id, labelText, value, update, max = 3) {
  const label = node('label', labelText), select = node('select'); select.id = id;
  for (let term = 1; term <= max; term++) select.append(new Option(`${copy('Học kỳ', 'Semester')} ${term}`, term));
  select.value = value; select.onchange = () => { update(Number(select.value)); updateRoadmap(); }; label.append(select); return label;
}
function yearSelect(id, labelText, value, update) {
  const label = node('label', labelText), select = node('select'); select.id = id;
  const year = new Date().getFullYear();
  for (let start = year; start <= year + 5; start++) select.append(new Option(`${start}–${start + 1}`, start));
  select.value = value; select.onchange = () => { update(Number(select.value)); updateRoadmap(); }; label.append(select); return label;
}

function renderRoadmap(mobile = false) {
  const aside = node('aside', undefined, 'rec-roadmap');
  if (!mobile) aside.id = 'rec-roadmap';
  aside.setAttribute('aria-label', copy('Lộ trình của bạn', 'Your study path'));
  const header = node('div', undefined, 'rec-roadmap-heading');
  header.append(icon('branch'), node('h3', copy('Lộ trình của bạn', 'Your study path')));
  aside.append(header, node('p', copy('Từng lựa chọn, một hướng đi rõ hơn.', 'Each choice brings your path into focus.'), 'rec-roadmap-caption'));
  const summary = node('div', undefined, 'rec-profile-summary');
  const definitions = [
    ['direction', copy('Định hướng', 'Direction'), answers.directionLabel || copy('Cùng khám phá', 'Let’s explore')],
    ['workload', copy('Tải học', 'Study load'), `${workloadLabel()} · ${answers.credits} ${copy('TC', 'credits')}`],
    ['deadline', copy('Mục tiêu', 'Goal'), answers.confirmedDeadline
      ? `${copy('HK', 'Sem ')}${answers.targetSemester} · ${answers.targetYear}–${answers.targetYear + 1}` : copy('Chọn mốc của bạn', 'Choose your milestone')],
  ];
  definitions.forEach(([key, label, value]) => {
    const row = button('', () => {
      if (dialog.open) dialog.close(); step = Math.max(0, steps().indexOf(key)); reviewMode = false; clearResults(); render(true);
    }, 'rec-summary-choice');
    row.dataset.recAnswer = key; row.append(node('span', label), node('strong', value)); summary.append(row);
  }); aside.append(summary);
  const timeline = node('div', undefined, 'rec-timeline');
  const start = node('div', undefined, 'rec-milestone rec-milestone-start');
  start.append(node('span', '', 'rec-milestone-dot'), node('span', copy('Từ quá trình học của bạn', 'From your studies so far')));
  const total = live.board?.progress?.total;
  if (total) start.append(node('strong', `${total.earned_credits}/${total.required_credits} ${copy('TC', 'credits')}`),
    node('small', live.board.preview_only ? copy('Tạm tính, chờ xác minh', 'Estimate awaiting verification') : copy('Theo dữ liệu đã đối chiếu', 'From reviewed academic data')));
  timeline.append(start);
  const upcoming = node('div', undefined, 'rec-milestone rec-milestone-next');
  upcoming.append(node('span', '', 'rec-milestone-dot'), node('span', copy('Học kỳ sắp tới', 'Your next semester')));
  const plan = results[selected];
  if (plan?.status === 'done' && plan.rows.length) {
    upcoming.append(node('strong', `${plan.credits} ${copy('tín chỉ', 'credits')} · ${titleFor(selected)}`));
    plan.rows.slice(0, 3).forEach(course => {
      const row = button('', () => openCourse(course), 'rec-timeline-course');
      row.append(node('span', course.code), node('strong', courseName(course))); upcoming.append(row);
    });
    if (plan.rows.length > 3) upcoming.append(node('small', copy(`Và ${plan.rows.length - 3} môn khác`, `And ${plan.rows.length - 3} more courses`)));
  } else {
    const sketch = node('div', undefined, 'rec-paper-sketch'); sketch.setAttribute('aria-hidden', 'true');
    for (let index = 0; index < 3; index++) sketch.append(node('i'));
    upcoming.append(sketch, node('small', busy ? copy('Đang tìm các lựa chọn phù hợp…', 'Finding suitable choices…') : copy('Phương án của bạn sẽ hiện ở đây', 'Your course plan will appear here')));
  }
  timeline.append(upcoming);
  const end = node('div', undefined, 'rec-milestone rec-milestone-goal');
  end.append(node('span', '', 'rec-milestone-dot'), icon('spark'),
    node('strong', copy('Mốc tốt nghiệp mong muốn', 'Your graduation goal')),
    node('small', answers.confirmedDeadline ? `${copy('HK', 'Sem ')}${answers.targetSemester} · ${answers.targetYear}–${answers.targetYear + 1}`
      : copy('Cùng đặt một mục tiêu', 'Set a milestone together')));
  timeline.append(end); aside.append(timeline);
  aside.append(node('p', copy('Mốc tương lai là mong muốn của bạn. Lịch mở lớp và tiến độ tốt nghiệp cần được đối chiếu với nhà trường.', 'Future milestones reflect your goals. Confirm course offerings and graduation progress with the university.'), 'rec-roadmap-note'));
  return aside;
}
function updateRoadmap() {
  const previous = root.querySelector('#rec-roadmap');
  if (previous) previous.replaceWith(renderRoadmap());
}
function modal(title, cls = '') {
  if (dialog.open) dialog.close();
  dialog.className = `rec-dialog ${cls}`;
  const header = node('header', undefined, 'rec-dialog-heading');
  const heading = node('h2', title); heading.id = 'rec-dialog-title';
  const close = button('', () => { if (!pendingSave) dialog.close(); }, 'rec-icon-button');
  close.append(icon('close')); close.setAttribute('aria-label', copy('Đóng', 'Close'));
  header.append(heading, close); dialog.append(header); dialog.setAttribute('aria-labelledby', heading.id);
  const content = node('div', undefined, 'rec-dialog-content'); dialog.append(content);
  return content;
}
function openMobileRoadmap() {
  const content = modal(copy('Lộ trình của bạn', 'Your study path'), 'rec-roadmap-sheet');
  content.append(renderRoadmap(true)); dialog.showModal();
}
function openCourse(course) {
  const content = modal(`${course.code} · ${courseName(course)}`, 'rec-course-dialog');
  content.append(node('p', `${course.credits} ${copy('tín chỉ', 'credits')} · ${copy('Thuộc phương án', 'In alternative')} ${titleFor(selected)}`, 'rec-dialog-meta'));
  const why = node('section'); why.append(node('h3', copy('Vì sao gợi ý môn này?', 'Why this course?')),
    node('p', course.reason || copy('Chưa có giải thích chi tiết từ hệ thống.', 'No detailed explanation was returned.')));
  if (course.fit_reason) why.append(node('p', course.fit_reason)); content.append(why);
  const entry = catalog.get(course.code);
  const prerequisites = node('section'); prerequisites.append(node('h3', copy('Điều kiện tiên quyết', 'Prerequisites')));
  if (!entry) prerequisites.append(node('p', copy('Chưa đọc được chi tiết tiên quyết từ catalog. Kết quả gợi ý vẫn được xét điều kiện ở server.', 'Detailed catalog prerequisites are unavailable. Server eligibility checks still apply.')));
  else if (!entry.prerequisites?.length) prerequisites.append(node('p', copy('Không ghi nhận môn tiên quyết trong khung.', 'No prerequisites are recorded in the curriculum.')));
  else {
    const graph = node('div', undefined, 'rec-prerequisite-graph');
    entry.prerequisites.forEach(group => {
      const row = node('div', undefined, 'rec-prerequisite-clause');
      group.forEach((code, index) => {
        if (index) row.append(node('span', copy('hoặc', 'or'), 'rec-prerequisite-or'));
        const prerequisite = catalog.get(code) || live.board?.prerequisite_courses?.[code];
        const label = node('span', undefined, 'rec-prerequisite-node');
        const completed = generationPassed.has(code); label.classList.toggle('is-completed', completed);
        label.append(icon(completed ? 'check' : 'clock'), node('span', `${code}${prerequisite ? ': ' + courseName(prerequisite) : ''}`));
        label.setAttribute('title', completed ? copy('Đã hoàn thành', 'Completed') : copy('Không ghi nhận hoàn thành', 'Not recorded as completed')); row.append(label);
      }); graph.append(row);
    });
    const connector = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    connector.setAttribute('viewBox', '0 0 300 36'); connector.setAttribute('aria-hidden', 'true');
    const path = document.createElementNS(connector.namespaceURI, 'path');
    path.setAttribute('d', 'M150 0v32m-5-5 5 5 5-5');
    path.setAttribute('fill', 'none'); path.setAttribute('stroke', 'currentColor');
    path.setAttribute('stroke-width', '1.5'); path.setAttribute('pathLength', '1'); connector.append(path);
    const target = node('strong', `${course.code}: ${courseName(course)}`, 'rec-prerequisite-target');
    graph.append(connector, target); prerequisites.append(graph,
      node('p', copy('Các dòng là điều kiện “và”; các mã trong cùng một dòng là lựa chọn “hoặc”.', 'Rows are AND conditions; alternatives in the same row are OR conditions.'), 'rec-question-hint'));
    animate(path, [{strokeDasharray: 1, strokeDashoffset: 1}, {strokeDasharray: 1, strokeDashoffset: 0}], {duration: 700});
  }
  content.append(prerequisites, node('p', copy('Môn đủ điều kiện theo dữ liệu đang xét. Chưa xác nhận môn sẽ mở ở kỳ tới.', 'Eligible under the current academic data. Next-term availability is not confirmed.'), 'rec-dialog-meta'));
  dialog.showModal();
}

function renderResults() {
  const area = root.querySelector('#rec-results'); if (!area) return;
  area.replaceChildren();
  if (error) {
    const notice = node('div', undefined, 'rec-error'); notice.setAttribute('role', 'alert');
    notice.append(node('p', error), button(copy('Kiểm tra dữ liệu học vụ', 'Review academic data'), openTools)); area.append(notice);
  }
  if (!Object.keys(results).length) return;
  const header = node('div', undefined, 'rec-results-heading');
  const intro = node('div'); intro.append(node('h3', copy('Ba góc nhìn cho một học kỳ.', 'Three ways to shape your semester.')),
    node('p', copy('Cùng điều kiện học vụ, khác cách ưu tiên. Bạn chọn phương án phù hợp với mình.', 'The same academic requirements, with different priorities. Choose what fits you.')));
  const compare = button(copy('So sánh phương án', 'Compare alternatives'), () => openComparison(), 'rec-button rec-secondary');
  compare.id = 'rec-compare'; compare.disabled = Object.values(results).filter(plan => plan.status === 'done').length < 2;
  header.append(intro, compare); area.append(header);
  const tabs = node('div', undefined, 'rec-variant-tabs'); tabs.setAttribute('role', 'tablist');
  tabs.setAttribute('aria-label', copy('Các phương án gợi ý', 'Study alternatives'));
  VARIANTS.forEach((id, index) => {
    const plan = results[id];
    const tab = button('', () => selectVariant(id), 'rec-variant-tab');
    tab.id = `rec-tab-${id}`; tab.dataset.recVariant = id; tab.setAttribute('role', 'tab');
    tab.setAttribute('aria-selected', String(selected === id)); tab.tabIndex = selected === id ? 0 : -1;
    tab.setAttribute('aria-controls', 'rec-plan-content');
    tab.append(node('span', `0${index + 1}`, 'rec-variant-number'), node('strong', titleFor(id)),
      node('small', plan?.status === 'done' ? `${plan.rows.length} ${copy('môn', 'courses')} · ${plan.credits} ${copy('TC', 'credits')}`
        : plan?.status === 'error' ? copy('Chưa tạo được', 'Unavailable') : copy('Đang đối chiếu…', 'Checking…')));
    tab.addEventListener('keydown', event => {
      const offset = {ArrowRight: 1, ArrowLeft: -1}[event.key];
      if (!offset) return; event.preventDefault();
      const next = VARIANTS[(index + offset + VARIANTS.length) % VARIANTS.length]; selectVariant(next);
      root.querySelector(`#rec-tab-${next}`)?.focus();
    }); tabs.append(tab);
  }); area.append(tabs);
  const panel = node('div', undefined, 'rec-plan-content'); panel.id = 'rec-plan-content';
  panel.setAttribute('role', 'tabpanel'); panel.setAttribute('aria-labelledby', `rec-tab-${selected}`);
  const plan = results[selected];
  if (!plan || plan.status === 'loading') {
    panel.setAttribute('aria-busy', 'true');
    const loading = node('div', undefined, 'rec-loading'); loading.setAttribute('role', 'status');
    const papers = node('div', undefined, 'rec-loading-papers'); papers.setAttribute('aria-hidden', 'true');
    for (let index = 0; index < 3; index++) papers.append(node('i'));
    loading.append(papers, node('strong', copy('Đang ghép một học kỳ phù hợp…', 'Putting your semester together…')),
      node('p', copy('Đối chiếu điều kiện môn học, mục tiêu và ngân sách tín chỉ.', 'Checking eligibility, interests and your credit budget.')));
    panel.append(loading);
  } else if (plan.status === 'error') panel.append(node('p', plan.error, 'rec-error'));
  else if (!plan.rows.length) panel.append(node('div', copy('Chưa tìm được môn phù hợp với điều kiện hiện tại. Kiểm tra dữ liệu hoặc điều chỉnh lựa chọn rồi tạo lại.', 'No suitable courses were found under the current requirements. Review your data or preferences and try again.'), 'rec-empty'));
  else {
    const caption = node('div', undefined, 'rec-plan-caption');
    caption.append(node('p', hintFor(selected)), node('strong', `${plan.credits} / ${answers.credits} ${copy('tín chỉ', 'credits')}`)); panel.append(caption);
    const grid = node('div', undefined, 'rec-course-grid');
    plan.rows.forEach(course => {
      const card = node('article', undefined, 'rec-course'); card.dataset.recCourse = course.code;
      const meta = node('div', undefined, 'rec-course-meta');
      meta.append(node('span', course.code), node('span', `${course.credits} ${copy('TC', 'credits')}`));
      const title = button(courseName(course), () => openCourse(course), 'rec-course-title');
      const reason = node('p', course.fit_reason || course.reason || '', 'rec-course-reason');
      const footer = node('div', undefined, 'rec-course-footer');
      footer.append(node('span', course.requirement_type === 'elective' ? copy('Tự chọn', 'Elective') : copy('Bắt buộc', 'Required')),
        button(copy('Vì sao môn này?', 'Why this course?'), () => openCourse(course), 'rec-text-button'));
      card.append(meta, title, reason, footer); grid.append(card);
    }); panel.append(grid);
    const actions = node('div', undefined, 'rec-plan-actions');
    const save = button('', () => openSave(), 'rec-button rec-primary'); save.id = 'rec-save';
    save.append(icon(saved.has(selected) ? 'check' : 'layers'), node('span', saved.has(selected) ? copy('Đã lưu phương án', 'Alternative saved')
      : uncertainSaves.has(selected) ? copy('Kiểm tra kết quả lưu', 'Check save outcome') : copy('Lưu phương án này', 'Save this alternative')));
    save.disabled = saved.has(selected) || pendingSave || live.loading || busy;
    const edit = button(copy('Chỉnh sửa phương án', 'Edit alternative'), () => {
      const adopted = window.workspacePlanning?.useDraft({codes: plan.rows.map(row => row.code),
        title: titleFor(selected), year: answers.year, semester: answers.semester});
      if (adopted) openTools(); else { error = copy('Dữ liệu đã đổi. Hãy tạo lại gợi ý trước khi chỉnh sửa.', 'Academic data changed. Generate new suggestions before editing.'); renderResults(); }
    }, 'rec-button rec-secondary');
    actions.append(save, edit); panel.append(actions);
    if (plan.omitted.length) panel.append(node('p', copy('Đã giữ lại các môn phù hợp với ngân sách, nhóm tín chỉ và điều kiện lập kế hoạch hiện tại.', 'Only courses within the current credit budget, group quotas and planning requirements are retained.'), 'rec-question-hint'));
    if (plan.warnings.length) {
      const warnings = node('details', undefined, 'rec-result-warnings');
      warnings.append(node('summary', copy('Thông tin cần đối chiếu', 'Information to confirm')));
      const list = node('ul'); plan.warnings.forEach(warning => list.append(node('li', warning))); warnings.append(list); panel.append(warnings);
    }
    const successful = Object.values(results).filter(value => value.status === 'done');
    if (successful.length > 1 && successful.every(value => {
      const difference = comparePlans(successful[0], value);
      return !difference.leftOnly.length && !difference.rightOnly.length;
    })) panel.append(node('p', copy('Các cách ưu tiên hiện cho cùng một tập môn. Hệ thống giữ nguyên kết quả, không tạo khác biệt giả.', 'These priorities currently produce the same course set. The results are kept as returned.'), 'rec-identical-note'));
  }
  area.append(panel);
}
function selectVariant(id) {
  const previous = new Map([...root.querySelectorAll('[data-rec-course]')].map(element => [element.dataset.recCourse, element.getBoundingClientRect()]));
  selected = id; renderResults(); updateRoadmap();
  root.querySelectorAll('[data-rec-course]').forEach((element, index) => {
    const old = previous.get(element.dataset.recCourse), next = element.getBoundingClientRect();
    animate(element, old ? [{transform: `translate(${old.left - next.left}px,${old.top - next.top}px)`}, {transform: 'translate(0,0)'}]
      : [{opacity: 0, transform: 'translateY(14px) rotateX(-5deg)'}, {opacity: 1, transform: 'translateY(0) rotateX(0)'}], {duration: 420, delay: Math.min(index * 55, 220)});
  });
}

function openComparison() {
  const available = VARIANTS.filter(id => results[id]?.status === 'done'); if (available.length < 2) return;
  const content = modal(copy('Đặt hai phương án cạnh nhau', 'Compare two alternatives'), 'rec-compare-dialog');
  let left = available[0], right = available[1];
  const controls = node('div', undefined, 'rec-compare-controls');
  [0, 1].forEach(index => {
    const label = node('label', index ? copy('Phương án bên phải', 'Right alternative') : copy('Phương án bên trái', 'Left alternative'));
    const select = node('select'); select.id = `rec-compare-${index}`;
    available.forEach(id => select.append(new Option(titleFor(id), id))); select.value = index ? right : left;
    select.onchange = () => { if (index) right = select.value; else left = select.value; draw(); }; label.append(select); controls.append(label);
  });
  const output = node('div', undefined, 'rec-comparison-output'); content.append(controls, output);
  function draw() {
    output.replaceChildren(); const diff = comparePlans(results[left], results[right]);
    const summary = node('p', copy(`${diff.shared.length} môn chung · ${diff.leftOnly.length + diff.rightOnly.length} môn khác biệt`, `${diff.shared.length} shared courses · ${diff.leftOnly.length + diff.rightOnly.length} different courses`));
    summary.setAttribute('role', 'status'); output.append(summary);
    const scroll = node('div', undefined, 'rec-compare-scroll'); scroll.tabIndex = 0;
    scroll.setAttribute('role', 'region'); scroll.setAttribute('aria-label', copy('Bảng so sánh học phần', 'Course comparison table'));
    const table = node('table'); const header = table.createTHead().insertRow();
    [copy('Học phần', 'Course'), titleFor(left), titleFor(right)].forEach(text => { const th = node('th', text); th.scope = 'col'; header.append(th); });
    const body = table.createTBody();
    const rows = new Map([...results[left].rows, ...results[right].rows].map(row => [row.code, row]));
    rows.forEach(course => {
      const tr = body.insertRow(); tr.insertCell().textContent = `${course.code} · ${courseName(course)}`;
      [left, right].forEach(id => {
        const cell = tr.insertCell(); const has = results[id].rows.some(row => row.code === course.code);
        cell.textContent = has ? `${course.credits} ${copy('TC', 'credits')}` : '—';
        cell.classList.toggle('rec-compare-included', has);
      });
    });
    const footer = table.createTFoot().insertRow(); footer.insertCell().textContent = copy('Tổng tín chỉ', 'Total credits');
    footer.insertCell().textContent = results[left].credits; footer.insertCell().textContent = results[right].credits;
    scroll.append(table); output.append(scroll); animate(output, [{opacity: .4}, {opacity: 1}], {duration: 250});
  }
  draw(); dialog.showModal();
}

function errorMessage(failure) {
  const planErrors = {
    semester_plan_budget_exceeded: copy('Phương án vượt ngân sách tín chỉ. Điều chỉnh tín chỉ hoặc bỏ bớt môn trước khi lưu.', 'This alternative exceeds the credit budget. Adjust the budget or remove courses before saving.'),
    semester_plan_group_full: copy('Lựa chọn đã vượt yêu cầu nhóm tự chọn. Kiểm tra lại các môn trong phương án.', 'The elective group requirement is already filled. Review the selected courses.'),
    semester_plan_course_unavailable: copy('Có môn không còn đủ điều kiện lập kế hoạch. Hãy tạo lại gợi ý.', 'A course is no longer eligible for planning. Generate new suggestions.'),
    semester_plan_limit: copy('Đã đạt giới hạn phương án. Xóa phương án không cần dùng trước khi lưu thêm.', 'The saved-plan limit was reached. Remove an unused alternative before saving another.'),
  };
  if (planErrors[failure?.message]) return planErrors[failure.message];
  if (failure?.status === 401) return copy('Phiên đăng nhập đã hết. Đăng nhập lại để tiếp tục.', 'Your session expired. Sign in again to continue.');
  if (failure?.message === 'academic_context_not_ready') return copy('Dữ liệu học vụ chưa đủ xác minh để tạo gợi ý. Mở phần kiểm tra dữ liệu để xem điều kiện cần hoàn tất.', 'Academic data needs review before suggestions can be generated. Open the data review for details.');
  if (failure?.status === 409) return copy('Bảng điểm hoặc lựa chọn chương trình đã thay đổi. Kiểm tra dữ liệu rồi tạo lại phương án.', 'Your transcript or curriculum selections changed. Review the data and generate again.');
  if (failure?.status === 403) return copy('Chưa xác minh được phiên thao tác. Tải lại trang và thử lại.', 'This request could not be verified. Reload the page and try again.');
  if (failure?.status === 429) return copy('Hệ thống đang bận. Giữ lại lựa chọn và thử lại sau.', 'The system is busy. Your preferences are retained; try again shortly.');
  if (failure?.name === 'AbortError') return copy('Yêu cầu chưa hoàn tất trong thời gian chờ. Bạn có thể thử tạo lại.', 'The request timed out. Try generating again.');
  return copy('Chưa tạo được phương án. Lựa chọn của bạn vẫn được giữ; hãy thử lại.', 'The alternative could not be generated. Your preferences are retained; please try again.');
}
async function request(url, {method = 'GET', body, signal} = {}) {
  const response = await fetch(url, {method, signal, credentials: 'same-origin', cache: 'no-store',
    headers: {...(body ? {'Content-Type': 'application/json'} : {}),
      ...(method !== 'GET' ? {'X-CSRF-Token': window.systemAuth?.csrf || ''} : {})},
    body: body ? JSON.stringify(body) : undefined});
  const result = await response.json();
  if (!response.ok) {
    if (response.status === 401 && url.startsWith('/me/')) document.dispatchEvent(new Event('workspace:session-expired'));
    const code = typeof result.detail === 'string' ? result.detail : result.detail?.code || 'recommendation_failed';
    throw Object.assign(new Error(code), {status: response.status});
  }
  return result;
}
async function generate() {
  if (busy || !readyToGenerate() || !live.sourceAvailable) return;
  clearResults(); const current = requestEpoch, owner = live.identity;
  busy = true; requestController = new AbortController(); const signal = requestController.signal;
  const timeout = setTimeout(() => { if (current === requestEpoch) requestController.abort(); }, 60000);
  render();
  try {
    const configured = await window.workspacePlanning.configure({credits: Number(answers.credits), trackId: answers.track, pathId: answers.path});
    if (current !== requestEpoch || owner !== live.identity) return;
    if (!configured.board?.program_id || configured.failed) throw new Error('academic_context_not_ready');
    const board = configured.board;
    if ((board.selections?.track_required && !answers.track) || (board.selections?.path_required && !answers.path)) {
      throw new Error('academic_context_not_ready');
    }
    const query = new URLSearchParams({program_id: board.program_id});
    if (answers.track) query.set('selected_track_id', answers.track);
    if (answers.path) query.set('selected_graduation_path_id', answers.path);
    const context = await request(`/me/academic-context?${query}`, {signal});
    if (current !== requestEpoch || owner !== live.identity) return;
    if (context.status !== 'ready') throw new Error('academic_context_not_ready');
    if (context.revision !== board.context_revision) throw Object.assign(new Error('context_changed'), {status: 409});
    generationRevision = context.revision;
    generationPassed = new Set(context.completed_course_codes || []);
    results = Object.fromEntries(VARIANTS.map(id => [id, {status: 'loading'}])); renderResults();
    await Promise.allSettled(VARIANTS.map(async id => {
      try {
        const response = await request('/me/recommendations', {method: 'POST', signal,
          body: recommendationPayload(board, answers, id, context.revision)});
        if (current !== requestEpoch || owner !== live.identity) return;
        if (response.context_revision !== context.revision) throw Object.assign(new Error('context_changed'), {status: 409});
        results[id] = {...constrainRecommendations(response, board, Number(answers.credits)), status: 'done'};
      } catch (failure) {
        if (current !== requestEpoch || owner !== live.identity) return;
        results[id] = {status: 'error', error: errorMessage(failure)};
      }
      if (current === requestEpoch) { renderResults(); updateRoadmap(); if (id === selected) selectVariant(id); }
    }));
  } catch (failure) {
    if (current === requestEpoch && owner === live.identity) error = errorMessage(failure);
  } finally {
    clearTimeout(timeout);
    if (current === requestEpoch) {
      busy = false; render();
      root.querySelectorAll('[data-rec-course]').forEach((element, index) =>
        animate(element, [{opacity: 0, transform: 'translateY(14px) rotateX(-4deg)'}, {opacity: 1, transform: 'translateY(0) rotateX(0)'}],
          {duration: 500, delay: Math.min(index * 70, 280)}));
    }
  }
}

function openSave() {
  const plan = results[selected]; if (plan?.status !== 'done' || !plan.rows.length || pendingSave) return;
  if (uncertainSaves.has(selected)) { document.dispatchEvent(new Event('workspace:plans-changed')); openTools(); return; }
  const variant = selected, epoch = requestEpoch, owner = live.identity;
  const content = modal(copy('Giữ lại phương án của bạn', 'Save your study alternative'), 'rec-save-dialog');
  const form = node('form', undefined, 'rec-save-form');
  const label = node('label', copy('Tên phương án', 'Alternative name')); label.htmlFor = 'rec-plan-name';
  const title = node('input'); title.id = 'rec-plan-name'; title.required = true; title.maxLength = 100;
  title.value = titleFor(variant); label.append(title); form.append(label);
  form.append(termSelect('rec-save-semester', copy('Lưu cho học kỳ', 'Save for semester'), answers.semester, value => { answers.semester = value; }),
    yearSelect('rec-save-year', copy('Năm học bắt đầu', 'Academic year starts'), answers.year, value => { answers.year = value; }));
  form.append(node('p', copy('Đây là phương án cá nhân, không phải đăng ký môn VNU.', 'This saves a personal alternative, not a VNU course registration.'), 'rec-question-hint'));
  const status = node('p'); status.id = 'rec-save-status'; status.setAttribute('role', 'status');
  const submit = node('button', copy('Xác nhận lưu', 'Confirm save'), 'rec-button rec-primary'); submit.type = 'submit';
  form.append(status, submit); content.append(form);
  form.onsubmit = async event => {
    event.preventDefault(); if (pendingSave || !form.reportValidity()) return;
    if (epoch !== requestEpoch || owner !== live.identity || live.board?.context_revision !== generationRevision) {
      status.textContent = copy('Dữ liệu đã đổi. Đóng cửa sổ và tạo lại phương án.', 'Academic data changed. Close this window and generate again.'); return;
    }
    pendingSave = true; submit.disabled = true; status.textContent = copy('Đang lưu phương án…', 'Saving your alternative…');
    dialog.querySelector('.rec-icon-button').disabled = true;
    try {
      await request('/me/semester-plans', {method: 'POST', signal: AbortSignal.timeout(60000), body: {
        title: title.value.trim(), academic_year_start: Number(answers.year), semester: Number(answers.semester),
        max_credits: Number(answers.credits), selected_track_id: answers.track || null,
        selected_graduation_path_id: answers.path || null, course_codes: plan.rows.map(row => row.code),
        expected_basis: live.board.plan_basis,
      }});
      if (epoch !== requestEpoch || owner !== live.identity) return;
      saved.add(variant); status.replaceChildren(icon('check'), node('span', copy('Đã lưu phương án.', 'Alternative saved.')));
      status.className = 'rec-save-success'; submit.remove();
      content.append(button(copy('Xem phương án đã lưu', 'View saved alternatives'), () => { dialog.close(); openTools(); }, 'rec-button rec-secondary'));
      animate(status, [{opacity: 0, transform: 'scale(.94)'}, {opacity: 1, transform: 'scale(1)'}], {duration: 420});
      document.dispatchEvent(new Event('workspace:plans-changed')); renderResults();
    } catch (failure) {
      if (epoch === requestEpoch && owner === live.identity) {
        status.textContent = failure.status ? errorMessage(failure) : copy('Chưa xác nhận được kết quả lưu. Kiểm tra danh sách phương án trước khi thử lại.', 'The save outcome could not be confirmed. Check saved alternatives before retrying.');
        if (!failure.status) {
          uncertainSaves.add(variant); document.dispatchEvent(new Event('workspace:plans-changed')); renderResults();
          content.append(button(copy('Kiểm tra phương án đã lưu', 'Check saved alternatives'), () => { dialog.close(); openTools(); }));
        }
        submit.disabled = !failure.status;
      }
    } finally {
      if (epoch === requestEpoch && owner === live.identity) {
        pendingSave = false; const close = dialog.querySelector('.rec-icon-button'); if (close) close.disabled = false;
        renderResults();
      }
    }
  };
  dialog.showModal(); title.focus();
}

async function loadCatalog(program) {
  if (!program || catalogProgram === program) return;
  const current = ++catalogSequence; catalogProgram = program; catalog.clear();
  try {
    const rows = await request(`/courses?${new URLSearchParams({program_id: program})}`);
    if (current === catalogSequence && Array.isArray(rows)) catalog = new Map(rows.map(course => [course.code, course]));
  } catch { /* Detailed catalog labels are optional; server checks are mandatory. */ }
}
function resetSession() {
  clearResults(); cancelMotion(); catalogSequence++; catalogProgram = ''; catalog.clear();
  if (dialog.open) dialog.close(); pendingSave = false;
  step = 0; draftText = ''; reviewMode = false; answers = initialAnswers();
}
document.addEventListener('workspace:planning-state', event => {
  const next = event.detail;
  const stateKey = JSON.stringify([next.identity, next.sourceAvailable, next.loading, next.failed,
    next.budget, next.track, next.path, next.profile, next.board?.context_revision,
    next.board?.plan_basis, next.board?.status, next.board?.blocking_reasons]);
  if (stateKey === planningStateKey) { live = next; return; }
  planningStateKey = stateKey;
  const changedOwner = identity !== (next.identity || '');
  const changedProgram = next.board?.program_id && catalogProgram && next.board.program_id !== catalogProgram;
  const changedSelection = !busy && (live.track !== next.track || live.path !== next.path);
  live = next;
  if (changedOwner) { identity = next.identity || ''; resetSession(); }
  else if (!next.sourceAvailable || (generationRevision && (!next.board || next.board.context_revision !== generationRevision))) {
    clearResults(); if (dialog.open) dialog.close();
  }
  if (!changedOwner && changedProgram) {
    answers.direction = ''; answers.directionLabel = ''; answers.track = next.track || ''; answers.path = next.path || '';
    step = 0; reviewMode = false; clearResults();
  } else if (!changedOwner && changedSelection) {
    answers.track = next.track || ''; answers.path = next.path || '';
    if (next.track) {
      const track = next.board?.selections?.tracks?.find(track => track.id === next.track);
      if (track) { answers.direction = track.id; answers.directionLabel = track.name; }
    }
  }
  if (next.board?.program_id) loadCatalog(next.board.program_id);
  render();
});
document.addEventListener('workspace:session-expired', () => { live = {}; identity = ''; planningStateKey = ''; resetSession(); render(); });
document.addEventListener('workspace:language-change', () => { if (dialog.open && !pendingSave) dialog.close(); render(); });
function syncMotionVisibility() {
  const paused = document.hidden || document.documentElement.dataset.view !== 'tab-recommend';
  root.dataset.paused = String(paused);
  for (const animation of animations) { if (paused) animation.pause(); else animation.play(); }
}
document.addEventListener('workspace:navigate', event => {
  syncMotionVisibility();
  if (event.detail === 'tab-recommend') reveal();
  else { cancelMotion(); if (dialog.open && !pendingSave) dialog.close(); }
});
document.addEventListener('visibilitychange', () => {
  syncMotionVisibility();
});
reduced.addEventListener('change', () => { if (reduced.matches) cancelMotion(); });
window.addEventListener('pagehide', () => { requestController?.abort(); cancelMotion(); });
render(); syncMotionVisibility(); if (live.board?.program_id) loadCatalog(live.board.program_id);
