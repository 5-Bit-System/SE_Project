/* Descriptive source statistics only. No GPA policy, pass inference or catalog matching. */
export function sourceNumber(value, max = Infinity) {
  const raw = String(value ?? '').trim();
  if (!/^\d+(?:[.,]\d+)?$/.test(raw)) return null;
  const number = Number(raw.replace(',', '.'));
  return Number.isFinite(number) && number <= max ? number : null;
}

export function sourceStatistics(attempts, year = '') {
  const terms = new Map(), letters = new Map();
  let count = 0, missingGrades = 0, missingGrades4 = 0, invalidCredits = 0;
  let weightedPoints10 = 0, weightedCredits10 = 0, weightedPoints4 = 0, weightedCredits4 = 0;
  for (const attempt of attempts) {
    const term = String(attempt.term || '');
    const match = term.match(/(\d{4})\s*[-–]\s*(\d{4})/);
    const academicYear = match ? `${match[1]}–${match[2]}` : '';
    if (year && academicYear !== year) continue;
    count++;
    if (!terms.has(term)) terms.set(term, {term, year: academicYear, count: 0,
      grades: [], grades4: [], credits: 0, knownCredits: 0,
      weightedPoints10: 0, weightedCredits10: 0, weightedPoints4: 0, weightedCredits4: 0,
      order: match ? Number(match[1]) * 10 + Number(term.match(/K[ỲÌ]\s*(\d+)/i)?.[1] || 0) : Infinity});
    const group = terms.get(term); group.count++;
    const credits = sourceNumber(attempt.credits);
    const grade = sourceNumber(attempt.grade10, 10);
    if (grade === null) missingGrades++;
    else {
      group.grades.push(grade);
      if (credits > 0) {
        group.weightedPoints10 += grade * credits; group.weightedCredits10 += credits;
        weightedPoints10 += grade * credits; weightedCredits10 += credits;
      }
    }
    const grade4 = sourceNumber(attempt.grade4, 4);
    if (grade4 === null) missingGrades4++;
    else {
      group.grades4.push(grade4);
      if (credits > 0) {
        group.weightedPoints4 += grade4 * credits; group.weightedCredits4 += credits;
        weightedPoints4 += grade4 * credits; weightedCredits4 += credits;
      }
    }
    if (credits === null) invalidCredits++; else { group.credits += credits; group.knownCredits++; }
    const letter = String(attempt.letter ?? '').trim();
    letters.set(letter, (letters.get(letter) || 0) + 1);
  }
  const groups = [...terms.values()].sort((a, b) => a.order - b.order || a.term.localeCompare(b.term));
  groups.forEach(group => {
    group.mean = group.weightedCredits10 ? group.weightedPoints10 / group.weightedCredits10 : null;
    group.mean4 = group.weightedCredits4 ? group.weightedPoints4 / group.weightedCredits4 : null;
  });
  const rank = ['A+', 'A', 'B+', 'B', 'C+', 'C', 'D+', 'D', 'F'];
  return {count, missingGrades, missingGrades4, invalidCredits, groups,
    weightedMean10: weightedCredits10 ? weightedPoints10 / weightedCredits10 : null,
    weightedMean4: weightedCredits4 ? weightedPoints4 / weightedCredits4 : null,
    weightedCredits10, weightedCredits4,
    letters: [...letters].sort(([a], [b]) => {
      const x = rank.indexOf(a), y = rank.indexOf(b);
      return (x < 0 ? 99 : x) - (y < 0 ? 99 : y) || a.localeCompare(b);
    })};
}

if (typeof document !== 'undefined') {
  const $ = id => document.getElementById(`analytics-${id}`);
  const t = (vi, en) => window.workspaceI18n.language === 'en' ? en : vi;
  const number = value => value === null ? '—' : new Intl.NumberFormat(
    window.workspaceI18n.language === 'en' ? 'en' : 'vi', {maximumFractionDigits: 2}).format(value);
  const colors = ['#6485e8', '#35b6a3', '#a08aef', '#e2ae52', '#d780ad', '#79a7d2', '#95b66b', '#b68d6c', '#d5747b', '#8492a9'];
  let source = null;
  function element(tag, text, cls = '') {
    const node = document.createElement(tag); node.textContent = text; node.className = cls; return node;
  }
  function svgElement(tag, attrs = {}) {
    const node = document.createElementNS('http://www.w3.org/2000/svg', tag);
    Object.entries(attrs).forEach(([key, value]) => node.setAttribute(key, String(value)));
    return node;
  }
  const termLabel = group => {
    if (!group.term) return t('Chưa xếp học kỳ', 'Unassigned semester');
    const semester = group.term.match(/K[ỲÌ]\s*(\d+)/i)?.[1];
    return semester && group.year ? `${t('HK', 'S')}${semester} · ${group.year}` : group.term;
  };
  function svgRoot(label, width, height) {
    const root = svgElement('svg', {viewBox: `0 0 ${width} ${height}`, role: 'img', 'aria-label': label});
    return root;
  }
  function empty(target, message) { target.replaceChildren(element('p', message, 'analytics-empty')); }
  function trend(stats, scale) {
    const four = scale === 4, meanKey = four ? 'mean4' : 'mean', gradesKey = four ? 'grades4' : 'grades';
    const container = $(four ? 'trend4' : 'trend'); container.replaceChildren();
    if (!stats.groups.some(group => group[meanKey] !== null)) {
      empty(container, four ? t('Chưa có điểm hệ 4 hợp lệ để vẽ biểu đồ.', 'No valid 4-point grades to plot.')
        : t('Chưa có điểm hệ 10 hợp lệ để vẽ biểu đồ.', 'No valid 10-point grades to plot.')); return;
    }
    const width = Math.max(620, stats.groups.length * 110 + 140), height = 285, left = 70, right = width - 70;
    const svg = svgRoot(four ? t('Điểm trung bình cộng các lượt theo học kỳ, thang 0 đến 4', 'Arithmetic mean by semester, from 0 to 4')
      : t('Điểm trung bình cộng các lượt theo học kỳ, thang 0 đến 10', 'Arithmetic mean by semester, from 0 to 10'), width, height);
    svg.setAttribute('role', 'group');
    for (const value of four ? [0, 1, 2, 3, 4] : [0, 2, 4, 6, 8, 10]) {
      const y = 218 - value * 180 / scale;
      svg.append(svgElement('line', {x1: left, x2: right, y1: y, y2: y, class: 'chart-grid-line'}));
      const label = svgElement('text', {x: left - 30, y: y + 4, 'text-anchor': 'end', class: 'chart-axis'});
      label.textContent = value; svg.append(label);
    }
    const xAt = i => stats.groups.length === 1 ? (left + right) / 2 : left + i * (right - left) / (stats.groups.length - 1);
    let segment = [];
    function flush() {
      if (segment.length > 1) svg.append(svgElement('polyline', {points: segment.join(' '), class: 'chart-trend-line'}));
      segment = [];
    }
    stats.groups.forEach((group, index) => {
      const x = xAt(index);
      const label = svgElement('text', {x, y: 255, 'text-anchor': 'middle', class: 'chart-axis'});
      label.textContent = termLabel(group); svg.append(label);
      // No numeric zero or connecting line is invented for a semester without grades.
      if (group[meanKey] === null) { flush(); return; }
      segment.push(`${x},${218 - group[meanKey] * 180 / scale}`);
    }); flush();
    stats.groups.forEach((group, index) => {
      if (group[meanKey] === null) return;
      const x = xAt(index), y = 218 - group[meanKey] * 180 / scale;
      const dot = svgElement('circle', {cx: x, cy: y, r: 5, tabindex: group.term ? 0 : -1,
        ...(group.term ? {role: 'button'} : {}), class: 'chart-point',
        'aria-label': `${termLabel(group)}: ${number(group[meanKey])} / ${scale}; ${group[gradesKey].length} ${t('lượt có điểm', 'graded attempts')}${group.term ? `; ${t('Mở bảng điểm học kỳ', 'Open semester transcript')}` : ''}`});
      if (group.term) {
        const openTranscript = () => document.dispatchEvent(new CustomEvent('workspace:open-transcript-term', {detail: {term: group.term}}));
        dot.addEventListener('click', openTranscript);
        dot.addEventListener('keydown', event => {
          if (event.key !== 'Enter' && event.key !== ' ') return;
          event.preventDefault(); openTranscript();
        });
      }
      const title = svgElement('title'); title.textContent = dot.getAttribute('aria-label'); dot.append(title);
      const label = svgElement('text', {x, y: y - 14, 'text-anchor': 'middle', class: 'chart-point-label'});
      label.textContent = number(group[meanKey]); svg.append(dot, label);
    }); container.append(svg);
  }
  function credits(stats) {
    const container = $('credits'); container.replaceChildren();
    const max = Math.max(1, ...stats.groups.map(group => group.credits));
    if (!stats.groups.some(group => group.knownCredits)) {
      empty(container, t('Chưa có tín chỉ hợp lệ để vẽ biểu đồ.', 'No valid credit values to plot.')); return;
    }
    stats.groups.forEach(group => {
      const row = element('div', '', 'credit-chart-row');
      const title = element('span', termLabel(group), 'credit-chart-term');
      const track = element('div', '', 'credit-chart-track');
      const value = group.knownCredits ? group.credits : null;
      const bar = element('div', '', 'credit-chart-bar'); bar.style.width = `${value === null ? 0 : value / max * 100}%`;
      track.append(bar);
      row.setAttribute('aria-label', `${termLabel(group)}: ${number(value)} ${t('tín chỉ', 'credits')}; ${group.knownCredits}/${group.count} ${t('lượt có tín chỉ', 'attempts with credits')}`);
      row.append(title, track, element('strong', number(value))); container.append(row);
    });
  }
  function distribution(stats) {
    const container = $('distribution'); container.replaceChildren();
    if (!stats.count) { empty(container, t('Chưa có lượt học để thống kê.', 'No attempts available.')); return; }
    const layout = element('div', '', 'distribution-layout');
    const svg = svgRoot(t('Phân bố ký hiệu điểm nguồn theo lượt học', 'Distribution of source grade labels by attempt'), 200, 200);
    const radius = 69, circumference = 2 * Math.PI * radius;
    svg.append(svgElement('circle', {cx: 100, cy: 100, r: radius, fill: 'none', 'stroke-width': 22, class: 'chart-ring-bg'}));
    let offset = 0;
    const legend = element('ul', '', 'distribution-legend');
    stats.letters.forEach(([letter, count], index) => {
      const length = count / stats.count * circumference, color = colors[index % colors.length];
      const segment = svgElement('circle', {cx: 100, cy: 100, r: radius, fill: 'none', stroke: color,
        'stroke-width': 22, 'stroke-dasharray': `${length} ${circumference - length}`,
        'stroke-dashoffset': -offset, transform: 'rotate(-90 100 100)'});
      offset += length;
      const label = letter || t('Chưa có điểm chữ', 'No letter grade');
      const title = svgElement('title'); title.textContent = `${label}: ${count}`; segment.append(title); svg.append(segment);
      const item = element('li', '');
      const swatch = element('span', '', 'legend-swatch'); swatch.style.backgroundColor = color;
      item.append(swatch, element('span', label), element('strong', `${count} · ${number(count / stats.count * 100)}%`)); legend.append(item);
    });
    const total = svgElement('text', {x: 100, y: 99, 'text-anchor': 'middle', class: 'chart-ring-total'}); total.textContent = stats.count;
    const caption = svgElement('text', {x: 100, y: 122, 'text-anchor': 'middle', class: 'chart-axis'}); caption.textContent = t('lượt học', 'attempts');
    svg.append(total, caption); layout.append(svg, legend); container.append(layout);
  }
  function render() {
    const attempts = source?.snapshot?.attempts || [], year = $('year').value;
    const years = [...new Set(attempts.map(row => row.term?.match(/\d{4}\s*[-–]\s*\d{4}/)?.[0].replace(/\s/g, '').replace('-', '–')).filter(Boolean))].sort().reverse();
    $('year').replaceChildren(new Option(t('Tất cả năm học', 'All academic years'), ''));
    years.forEach(value => $('year').add(new Option(value, value))); $('year').value = years.includes(year) ? year : '';
    $('year').disabled = !attempts.length;
    const stats = sourceStatistics(attempts, $('year').value);
    $('status').textContent = source ? t('Nguồn: bảng điểm VNU đã lưu', 'Source: saved VNU transcript')
      + (source.fetched_at ? ` · ${t('Cập nhật', 'Updated')}: ${new Date(source.fetched_at).toLocaleString(window.workspaceI18n.language === 'en' ? 'en-GB' : 'vi-VN')}` : '')
      + (source.snapshot?.completeness !== 'complete' ? t(' · Chưa xác minh độ đầy đủ', ' · Completeness unverified') : '')
      : t('Đăng nhập VNU để xem biểu đồ từ bảng điểm đã lưu trong hồ sơ của bạn.', 'Sign in with VNU to view charts from your saved transcript.');
    $('source-totals').replaceChildren();
    (source?.snapshot?.source_summary || []).forEach(row => $('source-totals').append(element('p', window.workspaceI18n.formatSourceSummary(row))));
    $('source-totals').hidden = !$('source-totals').childElementCount;
    $('count').textContent = `${stats.count} ${t('lượt học', 'attempts')} · ${stats.count - stats.missingGrades} ${t('lượt có điểm hệ 10', 'attempts with numeric 10-point grades')} · ${stats.count - stats.missingGrades4} ${t('lượt có điểm hệ 4', 'attempts with numeric 4-point grades')}`;
    trend(stats, 10); trend(stats, 4); distribution(stats); credits(stats);
    $('method').textContent = t('Giữ mọi lần học, không chọn điểm cao nhất hoặc quy đổi thang điểm.', 'Every attempt is retained; no best-attempt selection or grade conversion.')
      + ` ${stats.missingGrades} ${t('lượt thiếu/không có điểm hệ 10 hợp lệ;', 'attempts lack valid 10-point grades;')}`
      + ` ${stats.missingGrades4} ${t('lượt thiếu/không có điểm hệ 4 hợp lệ;', 'attempts lack valid 4-point grades;')}`
      + ` ${stats.invalidCredits} ${t('lượt thiếu/không có tín chỉ hợp lệ. Giá trị chưa rõ không được thay bằng 0.', 'attempts lack valid credits. Unknown values are not replaced with zero.')}`;
    const table = $('table'); table.replaceChildren();
    const header = table.createTHead().insertRow();
    [t('Học kỳ', 'Semester'), t('Lượt học', 'Attempts'), t('Lượt có điểm hệ 10', 'Graded / 10'), t('TB hệ 10', 'Mean / 10'), t('Lượt có điểm hệ 4', 'Graded / 4'), t('TB hệ 4', 'Mean / 4'), t('TC ghi trên lượt học', 'Credits on attempts')].forEach(label => {
      const cell = document.createElement('th'); cell.scope = 'col'; cell.textContent = label; header.append(cell);
    });
    const body = table.createTBody();
    stats.groups.forEach(group => {
      const row = body.insertRow(); [termLabel(group), group.count, group.grades.length, number(group.mean), group.grades4.length, number(group.mean4), number(group.knownCredits ? group.credits : null)].forEach(value => {
        row.insertCell().textContent = value;
      });
    });
  }
  document.addEventListener('workspace:portal-data', event => { source = event.detail; if (!source) $('year').value = ''; render(); });
  document.addEventListener('workspace:language-change', render);
  $('year').addEventListener('change', render);
  render();
  const refresh = () => document.dispatchEvent(new CustomEvent('workspace:portal-refresh'));
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', refresh, {once: true}); else refresh();
}
