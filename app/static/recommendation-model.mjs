/* Pure presentation/request helpers. Academic decisions remain server-owned. */
export const VARIANTS = ['balanced', 'graduation', 'direction'];
const WEIGHTS = {
  balanced: {topic: .35, keyword: .2, course_type: .35, workload: .1},
  graduation: {topic: .15, keyword: .15, course_type: .65, workload: .05},
  direction: {topic: .65, keyword: .25, course_type: .05, workload: .05},
};

export function defaultTerm(date = new Date()) {
  const autumn = date.getMonth() >= 7;
  return {year: date.getFullYear(), semester: autumn ? 2 : 1};
}

export function recommendationPayload(board, answers, variant, revision) {
  const credits = Number(answers.credits);
  if (!board?.program_id || !revision || !WEIGHTS[variant]
      || !Number.isInteger(credits) || credits < 1 || credits > 30) {
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
