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
  const month = date.getMonth();
  const year = date.getFullYear();
  if (month === 0) return {year: year - 1, semester: 2};
  if (month >= 8) return {year, semester: 2};
  return {year, semester: 1};
}

export function estimateRemainingTerms(targetYear, targetSemester, date = new Date()) {
  if (!Number.isInteger(Number(targetYear)) || !Number.isInteger(Number(targetSemester))) return null;
  const nowTerm = defaultTerm(date);
  const diff = (Number(targetYear) - nowTerm.year) * 2 + (Number(targetSemester) - nowTerm.semester) + 1;
  if (diff < 0 || diff > 20) return null;
  return Math.max(1, diff);
}

export function defaultGraduationGoal(cohort, remainingCredits = null, budget = 20, date = new Date()) {
  const window = graduationWindow(cohort, date);
  if (!window.years.length) return {targetYear: null, targetSemester: 2};
  const nominalYear = window.years.includes(window.admissionYear + 3) ? window.admissionYear + 3 : window.years[0];
  let targetYear = nominalYear;
  let targetSemester = 2;
  const remaining = Number(remainingCredits);
  const perTerm = Math.max(1, Number(budget) || 20);
  if (Number.isFinite(remaining) && remaining > 0) {
    const nowTerm = defaultTerm(date);
    const nominalTerms = (nominalYear - nowTerm.year) * 2 + (2 - nowTerm.semester) + 1;
    const neededTerms = Math.max(1, Math.ceil(remaining / perTerm));
    const goalTerms = Math.max(nominalTerms, neededTerms);
    if (goalTerms > nominalTerms) {
      const zeroBased = (nowTerm.year * 2 + (nowTerm.semester - 1)) + (goalTerms - 1);
      const computedYear = Math.floor(zeroBased / 2);
      const computedSemester = (zeroBased % 2) + 1;
      if (computedYear > window.lastYear) {
        targetYear = window.lastYear;
        targetSemester = 2;
      } else if (window.years.includes(computedYear)) {
        targetYear = computedYear;
        targetSemester = computedSemester;
      }
    }
  }
  return {targetYear, targetSemester};
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
  const remainingTerms = answers.confirmedDeadline
    ? estimateRemainingTerms(answers.targetYear, answers.targetSemester, options?.now)
    : null;
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
  const available = new Map();
  const baseEligible = new Set();
  for (const course of board?.courses?.eligible || []) {
    if (course.counted_in_total === false || course.planning_eligible === false) continue;
    if (course.eligibility_basis === 'available_prerequisites') {
      if (course.result_pending === true || !Array.isArray(course.prerequisite_clauses) || !course.prerequisite_clauses.length) {
        continue;
      }
    } else {
      baseEligible.add(course.code);
    }
    available.set(course.code, course);
  }
  const tolerance = Number.isInteger(response?.credit_tolerance) ? response.credit_tolerance : 2;
  const maxBudget = Math.min(30, budget + tolerance);
  const recommendations = response?.recommendations || [];
  const rejectedCo = new Set();
  let finalSelection = [];
  let finalCredits = 0;

  while (true) {
    const seen = new Set(), used = new Map(), picked = [];
    let credits = 0;
    for (const recommendation of recommendations) {
      const course = available.get(recommendation.code);
      if (!course || seen.has(course.code) || rejectedCo.has(course.code)) continue;
      seen.add(course.code);
      const groups = (course.groups || []).filter(group => Number.isFinite(group.required_credits));
      if (credits + course.credits > maxBudget || (groups.length && groups.every(group =>
        group.earned_credits + (used.get(group.id) || 0) >= group.required_credits))) {
        continue;
      }
      picked.push({...recommendation, name: course.name, name_en: course.name_en,
        credits: course.credits, requirement_type: course.requirement_type});
      credits += course.credits;
      groups.forEach(group => used.set(group.id, (used.get(group.id) || 0) + course.credits));
    }

    const pickedCodes = new Set(picked.map(row => row.code));
    const reached = new Set([...pickedCodes].filter(code => baseEligible.has(code) && !available.get(code)?.result_pending));
    let changed = true;
    while (changed) {
      changed = false;
      for (const row of picked) {
        if (reached.has(row.code)) continue;
        const course = available.get(row.code);
        if (!course || course.eligibility_basis !== 'available_prerequisites') continue;
        const clauses = course.prerequisite_clauses || [];
        if (clauses.length && clauses.every(clause => clause.some(req => reached.has(req)))) {
          reached.add(row.code);
          changed = true;
        }
      }
    }
    for (const code of pickedCodes) {
      if (baseEligible.has(code)) reached.add(code);
    }

    const invalid = picked.filter(row => !reached.has(row.code)).map(row => row.code);
    if (!invalid.length) {
      finalSelection = picked;
      finalCredits = credits;
      break;
    }
    invalid.forEach(code => rejectedCo.add(code));
  }

  const keptByCode = new Map(finalSelection.map(row => [row.code, row]));
  const seenOutput = new Set();
  const rows = [];
  const omitted = [];
  for (const recommendation of recommendations) {
    const kept = keptByCode.get(recommendation.code);
    if (kept && !seenOutput.has(recommendation.code)) {
      seenOutput.add(recommendation.code);
      rows.push(kept);
    } else {
      omitted.push(recommendation.code);
    }
  }
  const rowCodes = new Set(rows.map(row => row.code));
  const droppedCodes = omitted.filter(code => !rowCodes.has(code));
  const planExplanation = rows.length === 0 && recommendations.length > 0
    ? null
    : normalizePlanExplanation(response?.plan_explanation, droppedCodes);
  return {rows, credits: finalCredits, omitted, warnings: response?.warnings || [], planExplanation};
}

export function comparePlans(left, right) {
  const leftCodes = new Set((left?.rows || []).map(row => row.code));
  const rightCodes = new Set((right?.rows || []).map(row => row.code));
  return {shared: [...leftCodes].filter(code => rightCodes.has(code)),
    leftOnly: [...leftCodes].filter(code => !rightCodes.has(code)),
    rightOnly: [...rightCodes].filter(code => !leftCodes.has(code))};
}
