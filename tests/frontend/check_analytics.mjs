import assert from 'node:assert/strict';
import {sourceNumber, sourceStatistics} from '../../app/static/analytics.js';

const rows = [
  {term: 'HỌC KỲ 1 - 2099-2100', code: 'TEST001E', grade10: '8,5', grade4: '3,5', letter: 'B+', credits: '3'},
  {term: 'HỌC KỲ 1 - 2099-2100', code: 'TEST001E', grade10: '0', grade4: '0', letter: 'F', credits: '3'},
  {term: 'HỌC KỲ 2 - 2099-2100', code: 'TEST002', grade10: '', grade4: '', letter: '', credits: ''},
  {term: 'HỌC KỲ 1 - 2100-2101', code: 'TEST003', grade10: '12', grade4: '5', letter: 'I', credits: '2,5'},
  {term: null, code: 'TEST004', grade10: 'Miễn', grade4: '4', letter: 'Miễn', credits: '2'},
];
const original = JSON.stringify(rows);
const result = sourceStatistics(rows);
assert.equal(result.count, 5);
assert.equal(result.missingGrades, 3);
assert.equal(result.missingGrades4, 2);
assert.equal(result.invalidCredits, 1);
assert.equal(result.groups[0].mean, 4.25);
assert.equal(result.groups[0].mean4, 1.75);
assert.equal(result.groups[0].grades4.length, 2);
assert.equal(result.groups[0].credits, 6); // Both attempts retained.
assert.equal(result.groups[1].mean, null); // Missing grades must not become zero.
assert.equal(result.groups[1].mean4, null);
assert.equal(result.groups[2].mean4, null); // Out-of-range source grades are ignored.
assert.equal(result.groups[3].mean4, 4); // Grade 4 is independent of grade 10.
assert.equal(result.groups[1].knownCredits, 0);
assert.equal(result.groups[2].credits, 2.5);
assert.equal(result.groups[3].term, '');
assert.deepEqual(new Map(result.letters).get('I'), 1);
assert.deepEqual(new Map(result.letters).get(''), 1);
assert.equal(sourceStatistics(rows, '2099–2100').count, 3);
assert.equal(sourceStatistics([], '2099–2100').groups.length, 0);
assert.equal(sourceNumber('0', 10), 0);
assert.equal(sourceNumber('4', 4), 4);
assert.equal(sourceNumber('4,1', 4), null);
assert.equal(sourceStatistics(rows, '2099–2100').groups[0].mean4, 1.75);
for (const value of ['', ' ', 'null', null, 'NaN', '11', '-1', '8/10', '1e1', Infinity]) {
  assert.equal(sourceNumber(value, 10), null);
}
assert.equal(JSON.stringify(rows), original);

const weighted = sourceStatistics([
  {term: 'HỌC KỲ 1 - 2099-2100', grade10: '8', grade4: '3', credits: '3'},
  {term: 'HỌC KỲ 1 - 2099-2100', grade10: '4', grade4: '1', credits: '1'},
  {term: 'HỌC KỲ 1 - 2100-2101', grade10: '10', grade4: '4', credits: '2'},
  {term: 'HỌC KỲ 2 - 2100-2101', grade10: '2', grade4: '0', credits: ''},
  {term: 'HỌC KỲ 2 - 2100-2101', grade10: '4', grade4: '1', credits: '0'},
]);
assert.equal(weighted.groups[0].mean, 7);
assert.equal(weighted.groups[0].mean4, 2.5);
assert.equal(weighted.groups[0].weightedCredits10, 4);
assert.equal(weighted.groups[0].weightedCredits4, 4);
assert.equal(weighted.weightedMean10, 8);
assert.equal(weighted.weightedMean4, 3);
assert.equal(weighted.weightedCredits10, 6);
assert.equal(weighted.weightedCredits4, 6);
assert.equal(weighted.zeroCreditAttempts, 1);
assert.equal(sourceStatistics([
  {term: 'HỌC KỲ 1 - 2099-2100', grade10: '8', grade4: '3', credits: '3'},
  {term: 'HỌC KỲ 1 - 2099-2100', grade10: '4', grade4: '1', credits: '1'},
], '2099–2100').weightedMean10, 7);
assert.equal(sourceStatistics([
  {term: 'HỌC KỲ 1 - 2099-2100', grade10: '8', grade4: '3', credits: '3'},
  {term: 'HỌC KỲ 1 - 2099-2100', grade10: '4', grade4: '1', credits: '1'},
], '2099–2100').weightedMean4, 2.5);
console.log('Analytics aggregation: retakes, comma grades, zero, unknowns, credits, year filter passed');
