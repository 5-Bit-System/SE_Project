/* Pure presentation/request helpers. Academic decisions remain server-owned. */
export const VARIANTS = ['balanced', 'graduation', 'direction'];
const WEIGHTS = {
  balanced: {topic: .35, keyword: .2, course_type: .35, workload: .1},
  graduation: {topic: .15, keyword: .15, course_type: .65, workload: .05},
  direction: {topic: .65, keyword: .25, course_type: .05, workload: .05},
};
const CREDIT_LIMITS = {
  light: {min: 14, max: 17},
  moderate: {min: 18, max: 20},
  heavy: {min: 21, max: 30},
};

export function creditLimits(workload) {
  const limits = Object.hasOwn(CREDIT_LIMITS, workload) ? CREDIT_LIMITS[workload] : null;
  if (!limits) throw new Error('invalid_workload');
  return {...limits};
}

export function creditsForWorkload(workload, credits = 20) {
  const {min, max} = creditLimits(workload);
  return Math.min(max, Math.max(min, Number.isInteger(Number(credits)) ? Number(credits) : min));
}

export function graduationWindow(cohort, date = new Date()) {
  const source = String(cohort ?? '').trim();
  const numbered = source.match(/^[Kk]?\s*(\d{2})$/);
  const admissionYear = numbered ? 2022 + Number(numbered[1]) - 67
    : /^20\d{2}$/.test(source) ? Number(source) : null;
  if (!admissionYear || admissionYear < 2022 || admissionYear > date.getFullYear()) {
    return {admissionYear: null, cohort: null, years: [], lastYear: null};
  }
  // UI academic-year rollover in August; this is a goal selector, not an exact legal deadline.
  const currentYear = date.getFullYear() - (date.getMonth() < 7 ? 1 : 0);
  const firstYear = Math.max(admissionYear, currentYear), lastYear = admissionYear + 5;
  return {admissionYear, cohort: admissionYear - 2022 + 67, lastYear,
    years: Array.from({length: Math.max(0, lastYear - firstYear + 1)}, (_, index) => firstYear + index)};
}

export function validGraduationGoal(cohort, year, semester, date = new Date()) {
  return [1, 2].includes(Number(semester)) && graduationWindow(cohort, date).years.includes(Number(year));
}

export function defaultTerm(date = new Date()) {
  const autumn = date.getMonth() >= 7;
  return {year: date.getFullYear(), semester: autumn ? 2 : 1};
}

export function recommendationPayload(board, answers, variant, revision) {
  const credits = Number(answers.credits);
  const limits = creditLimits(answers.workload);
  if (!board?.program_id || !revision || !WEIGHTS[variant]
      || !Number.isInteger(credits) || credits < limits.min || credits > limits.max
      || (answers.confirmedDeadline && !validGraduationGoal(answers.cohort, answers.targetYear, answers.targetSemester))) {
    throw new Error('invalid_recommendation_preferences');
  }
  const milestone = answers.confirmedDeadline
    ? `Graduation goal: semester ${answers.targetSemester}, academic year ${answers.targetYear}-${answers.targetYear + 1}` : '';
  const goal = [answers.directionLabel, answers.goal, milestone].filter(Boolean).join('. ').slice(0, 500);
  return {
    program_id: board.program_id, expected_revision: revision,
    selected_track_id: answers.track || null,
    selected_graduation_path_id: answers.path || null,
    max_credits: credits, limit: 20, goal,
    preference: {raw_goal: goal, workload: answers.workload, course_type: 'required',
      interest_topics: answers.directionLabel ? [answers.directionLabel] : [],
      target_credits: credits, career_goal: (answers.goal || '').slice(0, 200) || null},
    ranking_weights: {...WEIGHTS[variant], orientation: 0, difficulty: 0},
  };
}

export function constrainRecommendations(response, board, budget) {
  const available = new Map((board?.courses?.eligible || [])
    .filter(course => course.counted_in_total !== false && course.planning_eligible !== false
      && course.eligibility_basis !== 'available_prerequisites')
    .map(course => [course.code, course]));
  const seen = new Set(), used = new Map(), rows = [], omitted = [];
  let credits = 0;
  for (const recommendation of response?.recommendations || []) {
    const course = available.get(recommendation.code);
    if (!course || seen.has(course.code)) { omitted.push(recommendation.code); continue; }
    seen.add(course.code);
    const groups = (course.groups || []).filter(group => Number.isFinite(group.required_credits));
    if (credits + course.credits > budget || (groups.length && groups.every(group =>
      group.earned_credits + (used.get(group.id) || 0) >= group.required_credits))) {
      omitted.push(course.code); continue;
    }
    rows.push({...recommendation, name: course.name, name_en: course.name_en,
      credits: course.credits, requirement_type: course.requirement_type});
    credits += course.credits;
    groups.forEach(group => used.set(group.id, (used.get(group.id) || 0) + course.credits));
  }
  return {rows, credits, omitted, warnings: response?.warnings || []};
}

export function comparePlans(left, right) {
  const leftCodes = new Set((left?.rows || []).map(row => row.code));
  const rightCodes = new Set((right?.rows || []).map(row => row.code));
  return {shared: [...leftCodes].filter(code => rightCodes.has(code)),
    leftOnly: [...leftCodes].filter(code => !rightCodes.has(code)),
    rightOnly: [...rightCodes].filter(code => !leftCodes.has(code))};
}
