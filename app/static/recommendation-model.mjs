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

export function recommendationPayload(board, answers, variant, revision, options = {}) {
  const credits = Number(answers.credits);
  const limits = creditLimits(answers.workload);
  if (!board?.program_id || !revision || !WEIGHTS[variant]
      || !Number.isInteger(credits) || credits < limits.min || credits > limits.max
      || (answers.confirmedDeadline && !validGraduationGoal(answers.cohort, answers.targetYear, answers.targetSemester))) {
    throw new Error('invalid_recommendation_preferences');
  }
  const milestone = answers.confirmedDeadline
    ? `Graduation goal: semester ${answers.targetSemester}, academic year ${answers.targetYear}-${answers.targetYear + 1}` : '';
  let remainingTerms = null;
  if (answers.confirmedDeadline && Number.isInteger(Number(answers.targetYear)) && Number.isInteger(Number(answers.targetSemester))) {
    const nowTerm = defaultTerm();
    const diff = (Number(answers.targetYear) - nowTerm.year) * 2 + (Number(answers.targetSemester) - nowTerm.semester) + 1;
    if (diff >= 1 && diff <= 20) remainingTerms = diff;
  }
  // Translated labels are presentation only. Custom text remains free text.
  const goal = [answers.goal, answers.direction === 'custom' ? answers.customDirection : '', milestone].filter(Boolean).join('. ').slice(0, 500);
  const topics = ({ai: ['artificial_intelligence'], software: ['software_engineering'],
    data: ['data_science'], applied: ['mathematics']})[answers.direction] || [];
  const explicit = [];
  if (answers.confirmedWorkload) explicit.push('workload');
  if (answers.creditsExplicit) explicit.push('target_credits');
  if (topics.length) explicit.push('interest_topics');
  const weights = Object.fromEntries(Object.entries(WEIGHTS[variant]).map(([key, value]) => [key, value * .7]));
  const includeNarrative = Boolean(options?.includeNarrative ?? answers.includeNarrative);
  return {
    program_id: board.program_id, expected_revision: revision,
    selected_track_id: answers.track || null,
    selected_graduation_path_id: answers.path || null,
    max_credits: credits, credit_tolerance: 2, target_remaining_terms: remainingTerms, limit: 20, goal,
    include_narrative: includeNarrative,
    form_input: {values: {workload: answers.workload, target_credits: credits,
      interest_topics: topics, orientation: answers.direction === 'research' ? 'research' : null},
      explicit_fields: answers.direction === 'research' ? [...explicit, 'orientation'] : explicit},
    ranking_weights: {...weights, orientation: .1, difficulty: .1, career: .1},
  };
}

function normalizeStringList(items, limit = 5) {
  if (!Array.isArray(items)) return [];
  const result = [];
  for (const item of items) {
    if (typeof item !== 'string') continue;
    const text = item.trim();
    if (!text) continue;
    result.push(text);
    if (result.length >= limit) break;
  }
  return result;
}

function mentionsOmittedCode(text, omittedPatterns) {
  return omittedPatterns.some(pattern => pattern.test(text));
}

export function normalizePlanExplanation(raw, omittedCodes = []) {
  if (!raw || typeof raw !== 'object' || Array.isArray(raw)) return null;
  const headline = typeof raw.headline === 'string' ? raw.headline.trim() : '';
  const bundleRationale = typeof raw.bundle_rationale === 'string' ? raw.bundle_rationale.trim() : '';
  if (!headline || !bundleRationale) return null;
  const omittedPatterns = [...new Set((omittedCodes || []).filter(code => typeof code === 'string' && code.trim()))]
    .map(code => new RegExp(`(?<![\\p{L}\\p{N}_])${code.trim().replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}(?![\\p{L}\\p{N}_])`, 'u'));
  if (omittedPatterns.length && (mentionsOmittedCode(headline, omittedPatterns) || mentionsOmittedCode(bundleRationale, omittedPatterns))) {
    return null;
  }
  const highlights = normalizeStringList(raw.highlights, 5)
    .filter(item => !omittedPatterns.length || !mentionsOmittedCode(item, omittedPatterns));
  const caveats = normalizeStringList(raw.caveats, 5);
  const explanationSource = raw.explanation_source === 'llm_grounded' ? 'llm_grounded' : 'deterministic_fallback';
  return {
    headline,
    bundle_rationale: bundleRationale,
    highlights,
    caveats,
    explanation_source: explanationSource,
  };
}

export function constrainRecommendations(response, board, budget) {
  const available = new Map((board?.courses?.eligible || [])
    .filter(course => course.counted_in_total !== false && course.planning_eligible !== false
      && course.eligibility_basis !== 'available_prerequisites')
    .map(course => [course.code, course]));
  const tolerance = Number.isInteger(response?.credit_tolerance) ? response.credit_tolerance : 2;
  const maxBudget = Math.min(30, budget + tolerance);
  const seen = new Set(), used = new Map(), rows = [], omitted = [];
  let credits = 0;
  for (const recommendation of response?.recommendations || []) {
    const course = available.get(recommendation.code);
    if (!course || seen.has(course.code)) { omitted.push(recommendation.code); continue; }
    seen.add(course.code);
    const groups = (course.groups || []).filter(group => Number.isFinite(group.required_credits));
    if (credits + course.credits > maxBudget || (groups.length && groups.every(group =>
      group.earned_credits + (used.get(group.id) || 0) >= group.required_credits))) {
      omitted.push(course.code); continue;
    }
    rows.push({...recommendation, name: course.name, name_en: course.name_en,
      credits: course.credits, requirement_type: course.requirement_type});
    credits += course.credits;
    groups.forEach(group => used.set(group.id, (used.get(group.id) || 0) + course.credits));
  }
  const rowCodes = new Set(rows.map(row => row.code));
  const droppedCodes = omitted.filter(code => !rowCodes.has(code));
  const planExplanation = rows.length === 0 && (response?.recommendations || []).length > 0
    ? null
    : normalizePlanExplanation(response?.plan_explanation, droppedCodes);
  return {rows, credits, omitted, warnings: response?.warnings || [], planExplanation};
}

export function comparePlans(left, right) {
  const leftCodes = new Set((left?.rows || []).map(row => row.code));
  const rightCodes = new Set((right?.rows || []).map(row => row.code));
  return {shared: [...leftCodes].filter(code => rightCodes.has(code)),
    leftOnly: [...leftCodes].filter(code => !rightCodes.has(code)),
    rightOnly: [...rightCodes].filter(code => !leftCodes.has(code))};
}
