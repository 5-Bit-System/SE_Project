import assert from 'node:assert/strict';
import {comparePlans, constrainRecommendations, recommendationPayload} from '../../app/static/recommendation-model.mjs';

const group = {id: 'elective', required_credits: 3, earned_credits: 0};
const course = (code, credits = 3, extra = {}) => ({code, credits, name: `Catalog ${code}`, groups: [], counted_in_total: true, ...extra});
const board = {program_id: 'invented', courses: {eligible: [course('A'), course('B', 3, {groups: [group]}),
  course('C', 3, {groups: [group]}), course('EXCLUDED', 2, {counted_in_total: false}),
  course('FOLLOW', 3, {planning_eligible: false, eligibility_basis: 'available_prerequisites'})]}};
const answers = {credits: 20, directionLabel: 'Invented interest', goal: 'Invented goal', workload: 'moderate', track: '', path: ''};
const payload = recommendationPayload(board, answers, 'balanced', 'invented-revision');
assert.equal(payload.max_credits, 20);
assert.equal(payload.expected_revision, 'invented-revision');
assert.equal(payload.preference.target_credits, 20);
assert.equal(payload.preference.course_type, 'required');
assert.equal(payload.preference.workload, 'moderate');
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
