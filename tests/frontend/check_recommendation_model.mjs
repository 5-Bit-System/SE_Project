import assert from 'node:assert/strict';
import {comparePlans, constrainRecommendations, creditLimits, creditsForWorkload,
  graduationWindow, recommendationPayload, validGraduationGoal} from '../../app/static/recommendation-model.mjs';

const group = {id: 'elective', required_credits: 3, earned_credits: 0};
const course = (code, credits = 3, extra = {}) => ({code, credits, name: `Catalog ${code}`, groups: [], counted_in_total: true, ...extra});
const board = {program_id: 'invented', courses: {eligible: [course('A'), course('B', 3, {groups: [group]}),
  course('C', 3, {groups: [group]}), course('EXCLUDED', 2, {counted_in_total: false}),
  course('FOLLOW', 3, {planning_eligible: false, eligibility_basis: 'available_prerequisites'})]}};
const answers = {credits: 20, directionLabel: 'Invented interest', goal: 'Invented goal', workload: 'moderate', track: '', path: ''};
const payload = recommendationPayload(board, answers, 'balanced', 'invented-revision');
assert.equal(payload.max_credits, 20);
assert.equal(payload.expected_revision, 'invented-revision');
assert.equal(payload.form_input.values.target_credits, 20);
assert.equal(payload.preference, undefined);
assert.equal(payload.form_input.values.course_type, undefined);
assert.equal(payload.form_input.values.workload, 'moderate');
assert.ok(payload.ranking_weights.workload > 0);
assert.equal(payload.selected_track_id, null);
assert.equal(payload.passed_course_codes, undefined);
assert.equal(payload.owner, undefined);
assert.notDeepEqual(payload.ranking_weights, recommendationPayload(board, answers, 'direction', 'invented-revision').ranking_weights);
const graduation = recommendationPayload(board, answers, 'graduation', 'invented-revision');
assert.ok(graduation.ranking_weights.course_type > payload.ranking_weights.course_type);
for (const variant of ['balanced', 'graduation', 'direction']) {
  const request = recommendationPayload(board, answers, variant, 'invented-revision');
  assert.ok(Math.abs(Object.values(request.ranking_weights).reduce((sum, value) => sum + value, 0) - 1) < 1e-9);
}
for (const credits of [0, 31, 2.5, NaN]) assert.throws(() => recommendationPayload(board, {...answers, credits}, 'balanced', 'revision'));
for (const [workload, min, max] of [['light', 14, 17], ['moderate', 18, 20], ['heavy', 21, 30]]) {
  assert.deepEqual(creditLimits(workload), {min, max});
  for (const credits of [min, max]) assert.equal(recommendationPayload(board, {...answers, workload, credits}, 'balanced', 'revision').max_credits, credits);
  for (const credits of [min - 1, max + 1, min + .5]) assert.throws(() => recommendationPayload(board, {...answers, workload, credits}, 'balanced', 'revision'));
}
assert.equal(creditsForWorkload('light', 20), 17);
assert.equal(creditsForWorkload('heavy', 17), 21);
assert.equal(creditsForWorkload('moderate', 30), 20);
assert.throws(() => creditLimits('unknown'));
assert.throws(() => creditLimits('toString'));
const now = new Date(2026, 10, 4);
for (const cohort of ['K68', 'k 68', '68', 68, '2023']) {
  assert.deepEqual(graduationWindow(cohort, now), {cohort: 68, admissionYear: 2023, lastYear: 2028, years: [2026, 2027, 2028]});
}
assert.deepEqual(graduationWindow('K67', now).years, [2026, 2027]);
assert.deepEqual(graduationWindow('K69', now).years, [2026, 2027, 2028, 2029]);
assert.deepEqual(graduationWindow('K68', new Date(2029, 8, 1)).years, []);
assert.deepEqual(graduationWindow('K68', new Date(2027, 0, 1)).years, [2026, 2027, 2028]);
for (const missing of ['', null, 'unknown', 'K66', 'K79', '2099']) assert.equal(graduationWindow(missing, now).admissionYear, null);
assert.equal(validGraduationGoal('K68', 2028, 2, now), true);
assert.equal(validGraduationGoal('K68', 2029, 2, now), false);
assert.equal(validGraduationGoal('K68', 2028, 3, now), false);
const response = {recommendations: ['EXCLUDED', 'FOREIGN', 'FOLLOW', 'A', 'A', 'B', 'C'].map(code => ({code, credits: 99, name: '<img>', reason: 'Synthetic reason'}))};
const result = constrainRecommendations(response, board, 20);
assert.deepEqual(result.rows.map(row => row.code), ['A', 'B']);
assert.equal(result.credits, 6);
assert.equal(result.rows[0].name, 'Catalog A');
assert.deepEqual(constrainRecommendations(response, board, 3).rows.map(row => row.code), ['A']);
assert.deepEqual(comparePlans({rows: [course('A'), course('B')]}, {rows: [course('B'), course('C')]}),
  {shared: ['B'], leftOnly: ['A'], rightOnly: ['C']});
assert.deepEqual(board.courses.eligible[1].groups[0], group);
assert.equal(response.recommendations[0].credits, 99);
console.log('Recommendation model: source-owned payload, bounds, budget, quotas, excluded/conditional/duplicate rows and real comparison passed');

const software = recommendationPayload(board, {...answers, direction: 'software', directionLabel: 'Phần mềm', confirmedWorkload: true}, 'balanced', 'revision');
const english = recommendationPayload(board, {...answers, direction: 'software', directionLabel: 'Software', confirmedWorkload: true}, 'balanced', 'revision');
assert.deepEqual(software.form_input, english.form_input);
assert.deepEqual(software.form_input.values.interest_topics, ['software_engineering']);
assert.ok(software.form_input.explicit_fields.includes('workload'));
assert.ok(!software.form_input.explicit_fields.includes('target_credits'));
assert.ok(software.ranking_weights.orientation > 0 && software.ranking_weights.difficulty > 0);
assert.equal(software.goal.includes('Phần mềm'), false);
