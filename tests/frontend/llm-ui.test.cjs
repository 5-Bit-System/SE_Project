const test = require('node:test');
const assert = require('node:assert/strict');
const {generationInfo} = require('../../app/static/hus-rag-demo.js');

function answer(generation, status = 'answered') {
  return {mode: 'hus_rag', hus_answer: {status}, generation};
}

test('default and non-answer replies have no generation badge', () => {
  assert.equal(generationInfo(answer(undefined), false), null);
  assert.equal(generationInfo(answer({used: false, fallback_reason: 'not_answered'}, 'no_information'), true), null);
  assert.equal(generationInfo(answer({used: false}, 'needs_clarification'), true), null);
  assert.equal(generationInfo({mode: 'basic_chat', generation: {used: false}}, true), null);
});

test('AI badge requires actual use, answered RAG and explicit request consent', () => {
  const used = answer({used: true, model: 'actual-model', fallback_reason: null});
  assert.equal(generationInfo(used, true).kind, 'used');
  assert.equal(generationInfo(used, true).label, 'AI diễn đạt từ nguồn');
  assert.throws(() => generationInfo(used, false));
  assert.throws(() => generationInfo({...used, mode: 'basic_chat'}, true));
  assert.throws(() => generationInfo(answer(used.generation, 'no_information'), true));
  assert.throws(() => generationInfo(answer({used: true, model: ''}), true));
  assert.throws(() => generationInfo(answer({used: true, model: 'm', fallback_reason: 'timeout'}), true));
  assert.throws(() => generationInfo(answer({used: 'true'}), true));
});

test('requested canonical fallbacks use stable, safe human messages', () => {
  const cases = [
    [{used: false, fallback_reason: 'busy'}, /bận/],
    [{used: false, fallback_reason: 'timeout'}, /thời gian/],
    [{used: false, fallback_reason: 'http_error', http_status: 429}, /hạn mức/],
    [{used: false, fallback_reason: 'http_error', http_status: 503}, /kết nối/],
    [{used: false, fallback_reason: 'prompt_budget'}, /giới hạn/],
    [{used: false, fallback_reason: 'output_budget'}, /giới hạn/],
    [{used: false, fallback_reason: 'invalid_output'}, /kiểm tra/],
    [{used: false, fallback_reason: '<private-body-key>'}, /sẵn sàng/],
    [undefined, /sẵn sàng/],
  ];
  for (const [metadata, note] of cases) {
    const info = generationInfo(answer(metadata), true);
    assert.equal(info.kind, 'fallback');
    assert.equal(info.label, 'Bản trích nguồn');
    assert.match(info.note, note);
    assert.doesNotMatch(JSON.stringify(info), /private-body-key/);
  }
});
