import assert from 'node:assert/strict';
import {sourceNumber, sourceStatistics} from '../../app/static/analytics.js';

const rows = [
  {term: 'HỌC KỲ 1 - 2099-2100', code: 'TEST001E', grade10: '8,5', letter: 'B+', credits: '3'},
  {term: 'HỌC KỲ 1 - 2099-2100', code: 'TEST001E', grade10: '0', letter: 'F', credits: '3'},
  {term: 'HỌC KỲ 2 - 2099-2100', code: 'TEST002', grade10: '', letter: '', credits: ''},
  {term: 'HỌC KỲ 1 - 2100-2101', code: 'TEST003', grade10: '12', letter: 'I', credits: '2,5'},
  {term: null, code: 'TEST004', grade10: 'Miễn', letter: 'Miễn', credits: 'unknown'},
];
const original = JSON.stringify(rows);
const result = sourceStatistics(rows);
assert.equal(result.count, 5);
assert.equal(result.missingGrades, 3);
assert.equal(result.invalidCredits, 2);
assert.equal(result.groups[0].mean, 4.25);
assert.equal(result.groups[0].credits, 6); // Both attempts retained.
assert.equal(result.groups[1].mean, null); // Missing grades must not become zero.
assert.equal(result.groups[1].knownCredits, 0);
assert.equal(result.groups[2].credits, 2.5);
assert.equal(result.groups[3].term, '');
assert.deepEqual(new Map(result.letters).get('I'), 1);
assert.deepEqual(new Map(result.letters).get(''), 1);
assert.equal(sourceStatistics(rows, '2099–2100').count, 3);
assert.equal(sourceStatistics([], '2099–2100').groups.length, 0);
assert.equal(sourceNumber('0', 10), 0);
for (const value of ['', ' ', 'null', null, 'NaN', '11', '-1', '8/10', '1e1', Infinity]) {
  assert.equal(sourceNumber(value, 10), null);
}
assert.equal(JSON.stringify(rows), original);
console.log('Analytics aggregation: retakes, comma grades, zero, unknowns, credits, year filter passed');
