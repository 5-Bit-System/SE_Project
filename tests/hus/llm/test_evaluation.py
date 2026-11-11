"""L5 paired measurement and cache-only semantic review, no external requests."""

import json
from copy import deepcopy

import httpx
import pytest

from app.hus.llm import HUSLLMSettings
from tests.hus.llm.fixtures import (
    FIRST,
    SECOND,
    compact_text_output,
    context,
    facts_output,
    text_output,
)
from tests.hus.llm.test_pipeline import completion


def evaluator():
    from tools import evaluate_hus_llm
    return evaluate_hus_llm


@pytest.fixture
def prepared(tmp_path, monkeypatch):
    e = evaluator()
    monkeypatch.setattr(e, 'current_pins', lambda: {'synthetic': 'frozen'})
    records = []
    for number, family in enumerate(['f1', 'f2', 'f3'], 1):
        ctx = context(family)
        ctx.question.allow_llm_rewrite = False
        records.append({'question_id': f'L5-{number}', 'request': ctx.question.model_dump(),
            'effective_request': ctx.question.model_dump(),
            'gold': {'category': family, 'expected_status': 'answered', 'expected_answer': FIRST + SECOND},
            'gold_evidence': [], 'baseline': {'mode': 'hus_rag', 'reply': ctx.answer.reply,
                'hus_answer': ctx.answer.model_dump()}, 'baseline_latency_ms': 1.0,
            'retrieval_calls': [], 'source_audit': {'passed': True, 'synthetic': True}})
    control = deepcopy(records[0])
    control.update(question_id='L5-control', gold={'category': 'basic_chat'},
                   baseline={'mode': 'basic_chat', 'reply': 'Xin chào', 'hus_answer': None})
    records.append(control)
    folder = tmp_path / 'prepared'
    e.save_prepared(records, folder, provenance={'kind': 'synthetic_test'})
    return folder


def settings():
    return HUSLLMSettings(enabled=True, api_key='synthetic-eval-key')


def good(request):
    bundle = json.loads(json.loads(request.content)['messages'][1]['content'])
    output = facts_output() if bundle['scope']['dataset'] == 'f2' else compact_text_output()
    return httpx.Response(200, json=completion(output))


def test_missing_evaluator_is_a_real_feature_gap():
    assert callable(evaluator().run)


def test_paired_run_keeps_canonical_and_counts_only_used_output(prepared, tmp_path):
    e = evaluator()
    calls = []

    def respond(request):
        calls.append(request)
        return good(request)

    report = e.run(prepared, tmp_path / 'run', settings(),
                   transport_factory=lambda: httpx.MockTransport(respond), min_interval=0)
    assert len(calls) == 3
    assert report['metrics']['used'] == 3
    assert report['metrics']['fallback'] == 0
    assert report['metrics']['guard_skipped'] == 1
    assert report['metrics']['provider_requests'] == 3
    assert report['metrics']['actual_models'] == {'actual-model-version': 3}
    assert report['metrics']['token_usage']['total_tokens'] == 39
    assert report['semantic_review'] == 'pending'
    assert report['recommended_enabled'] is False
    assert e.replay(tmp_path / 'run')['reproduced'] is True
    saved = e.read_sealed(tmp_path / 'run')['observations.json']
    assert saved[0]['a']['hus_answer'] == saved[0]['b']['hus_answer']
    assert saved[1]['b']['reply'].endswith(saved[1]['a']['reply'])
    assert all(o['trace']['prompt_sha256'] for o in saved[:3])
    assert 'synthetic-eval-key' not in json.dumps(saved)


def test_rejected_output_retains_actual_model_usage_and_separate_fallback(prepared, tmp_path):
    e = evaluator()

    def reject(request):
        body = completion({'kind': 'invalid'})
        return httpx.Response(200, json=body)

    report = e.run(prepared, tmp_path / 'run', settings(),
                   transport_factory=lambda: httpx.MockTransport(reject), min_interval=0)
    metrics = report['metrics']
    assert metrics['used'] == 0 and metrics['fallback'] == 3
    assert metrics['provider_requests'] == 3
    assert metrics['actual_models'] == {'actual-model-version': 3}
    assert metrics['token_usage']['total_tokens'] == 39
    assert metrics['fallback_reasons'] == {'invalid_output': 3}
    for o in e.read_sealed(tmp_path / 'run')['observations.json'][:3]:
        assert o['a'] == {k: v for k, v in o['b'].items() if k != 'generation'}


@pytest.mark.parametrize('finish,tokens', [('length', 5), ('stop', 1025)])
def test_envelope_rejection_still_records_safe_observed_usage(prepared, tmp_path, finish, tokens):
    e = evaluator()

    def respond(request):
        body = completion(text_output())
        body['choices'][0]['finish_reason'] = finish
        body['usage']['completion_tokens'] = tokens
        return httpx.Response(200, json=body)

    result = e.run(prepared, tmp_path / 'run', settings(),
                   transport_factory=lambda: httpx.MockTransport(respond), min_interval=0)
    assert result['metrics']['used'] == 0
    assert result['metrics']['token_usage']['completion_tokens'] == tokens * 3


def test_quota_stops_further_http_without_becoming_llm_success(prepared, tmp_path):
    e = evaluator()
    calls = []

    def respond(request):
        calls.append(request)
        return httpx.Response(429, text='private-quota synthetic-eval-key')

    result = e.run(prepared, tmp_path / 'run', settings(),
                   transport_factory=lambda: httpx.MockTransport(respond), min_interval=0)
    assert len(calls) == 1
    assert result['metrics']['used'] == 0 and result['metrics']['fallback'] == 3
    assert result['metrics']['provider_requests'] == 1
    assert result['metrics']['eligible_not_attempted'] == 2
    assert result['collection_complete'] is False
    assert 'private-quota' not in (tmp_path / 'run/observations.json').read_text()


def test_quota_headers_close_circuit_even_when_body_read_times_out(prepared, tmp_path):
    e = evaluator()
    calls = []

    class BrokenBody(httpx.SyncByteStream):
        def __iter__(self):
            raise httpx.ReadTimeout('private-provider-body')
            yield b''

    def respond(request):
        calls.append(request)
        return httpx.Response(429, stream=BrokenBody())

    result = e.run(prepared, tmp_path / 'run', settings(),
                   transport_factory=lambda: httpx.MockTransport(respond), min_interval=0)
    assert len(calls) == 1
    assert result['metrics']['http_status'] == {'429': 1}
    assert result['metrics']['eligible_not_attempted'] == 2


def test_budget_caps_http_and_restores_original_server_flags(prepared, tmp_path, monkeypatch):
    import os

    e = evaluator()
    monkeypatch.setenv('HUS_LLM_ENABLED', 'false')
    monkeypatch.setenv('HUS_LLM_API_KEY', 'private-original')
    result = e.run(prepared, tmp_path / 'run', settings(), max_calls=1,
                   transport_factory=lambda: httpx.MockTransport(good), min_interval=0)
    assert result['metrics']['provider_requests'] == 1
    assert result['metrics']['eligible_not_attempted'] == 2
    assert os.environ['HUS_LLM_ENABLED'] == 'false'
    assert os.environ['HUS_LLM_API_KEY'] == 'private-original'


def test_budget_spaces_attempts_without_retrying():
    e = evaluator()
    now, waits = [0.0], []

    def sleep(seconds):
        waits.append(seconds)
        now[0] += seconds

    budget = e.Budget(2, 5, clock=lambda: now[0], sleep=sleep)
    budget.reserve()
    now[0] = 2
    budget.reserve()
    assert waits == [3]
    with pytest.raises(Exception):
        budget.reserve()
    assert budget.attempts == 2


def test_real_frozen_suite_has_prerequisites_and_controls_before_generation(
    tmp_path, monkeypatch, historical_v3_data, historical_v3_auditor
):
    e = evaluator()
    from app.hus.rag_loader import HUSRAGData
    from tools.hus_rag_layer_metrics import canonical_field

    # Reproduce v3 prerequisites/controls without relabelling old gold as v4.
    monkeypatch.setattr(HUSRAGData, 'load_current', lambda: historical_v3_data)
    monkeypatch.setattr(e, 'current_pins', lambda: {
        'kind': 'historical_v3_test_fixture', 'release': historical_v3_data.release_identity,
    })
    result = e.prepare(tmp_path / 'real-prepared')
    records = result['records']
    assert len(records) == 36
    f2 = [r for r in records if r['gold']['category'] == 'f2']
    assert sum(canonical_field(r['gold']['expected_field']) == 'prerequisites' for r in f2) == 4
    assert all(r['source_audit']['passed'] for r in records)
    assert all(not r['request'].get('allow_llm_rewrite', False) for r in records)
    assert len([r for r in records if r['baseline']['mode'] == 'basic_chat']) == 2


def test_frozen_v3_suite_rejects_selected_v4_before_generation(tmp_path):
    with pytest.raises(ValueError, match='release differs from frozen source packs'):
        evaluator().prepare(tmp_path / 'must-not-exist')
    assert not (tmp_path / 'must-not-exist').exists()


def test_unknown_usage_does_not_become_zero_tokens(prepared, tmp_path):
    e = evaluator()

    def respond(request):
        body = json.loads(good(request).content)
        del body['usage']
        return httpx.Response(200, json=body)

    result = e.run(prepared, tmp_path / 'run', settings(),
                   transport_factory=lambda: httpx.MockTransport(respond), min_interval=0)
    assert result['metrics']['token_usage']['total_tokens'] is None
    assert result['metrics']['token_counter_unknown_requests']['total_tokens'] == 3


def test_identical_fallback_cannot_be_reviewed_as_better(prepared, tmp_path):
    e = evaluator()
    out = tmp_path / 'run'
    e.run(prepared, out, settings(), max_calls=0,
          transport_factory=lambda: httpx.MockTransport(good), min_interval=0)
    saved = e.read_sealed(out)
    review = deepcopy(saved['review_template.json'])
    for row in review['cases']:
        positive = row['question_id'] != 'L5-control'
        row.update(reviewer='Synthetic reviewer', notes='Same canonical reply, no generated output.',
                   readability='better' if positive else 'not_applicable')
        for key in ('a_entailment', 'a_completeness', 'b_entailment', 'b_completeness'):
            row[key] = 'pass' if positive else 'not_applicable'
    path = tmp_path / 'review.json'
    path.write_text(json.dumps(review), encoding='utf-8')
    with pytest.raises(ValueError, match='identical'):
        e.score(out, path, tmp_path / 'scored')


def test_cli_cannot_write_into_runtime_source_tree(monkeypatch):
    e = evaluator()
    monkeypatch.setattr(e, 'prepare', lambda *args: pytest.fail('Preparation should not start'))
    with pytest.raises(SystemExit):
        e.main(['--prepare', '--out', str(e.ROOT / 'data/hus/rag/new-measurement')])


@pytest.mark.parametrize('key,value', [('requested_model', 'invented'),
    ('actual_human_reviews', 12), ('recommended_enabled', True), ('collection_complete', False)])
def test_replay_rejects_changed_measurement_claims(prepared, tmp_path, key, value):
    e = evaluator()
    out = tmp_path / 'run'
    e.run(prepared, out, settings(), transport_factory=lambda: httpx.MockTransport(good), min_interval=0)
    report = json.loads((out / 'report.json').read_bytes())
    report[key] = value
    (out / 'report.json').write_text(json.dumps(report), encoding='utf-8')
    e.seal(out)
    with pytest.raises(ValueError, match='metadata'):
        e.replay(out)


def test_live_is_explicit_and_configuration_matches_prepared_model(prepared, tmp_path):
    e = evaluator()
    with pytest.raises(ValueError, match='live'):
        e.run(prepared, tmp_path / 'run', settings())
    with pytest.raises(ValueError, match='model'):
        e.run(prepared, tmp_path / 'run2', HUSLLMSettings(enabled=True, api_key='fake', model='other'),
              transport_factory=lambda: httpx.MockTransport(good), min_interval=0)


def test_changed_pins_fail_before_any_provider_call(prepared, tmp_path, monkeypatch):
    e = evaluator()
    monkeypatch.setattr(e, 'current_pins', lambda: {'synthetic': 'changed'})
    with pytest.raises(ValueError, match='pins'):
        e.run(prepared, tmp_path / 'run', settings(),
              transport_factory=lambda: pytest.fail('Provider constructed despite changed pins'))


def test_review_is_exact_response_bound_and_scores_used_separately(prepared, tmp_path):
    e = evaluator()
    out = tmp_path / 'run'
    e.run(prepared, out, settings(), transport_factory=lambda: httpx.MockTransport(good), min_interval=0)
    template = e.read_sealed(out)['review_template.json']
    review = deepcopy(template)
    for row in review['cases']:
        row.update(reviewer_kind='ai', reviewer='Synthetic test reviewer', notes='Synthetic supported fixture.')
        applicable = row['question_id'] != 'L5-control'
        for key in ('a_entailment', 'a_completeness', 'b_entailment', 'b_completeness'):
            row[key] = 'pass' if applicable else 'not_applicable'
        row['readability'] = 'same' if applicable else 'not_applicable'
    path = tmp_path / 'review.json'
    path.write_text(json.dumps(review), encoding='utf-8')
    scored = e.score(out, path, tmp_path / 'scored')
    assert scored['semantic']['used_only']['count'] == 3
    assert scored['semantic']['used_only']['b_entailment_pass'] == 3
    assert scored['actual_human_reviews'] == 0 and scored['recommended_enabled'] is False
    assert e.replay(tmp_path / 'scored')['reproduced'] is True
    review['cases'][0]['pair_sha256'] = '0' * 64
    path.write_text(json.dumps(review), encoding='utf-8')
    with pytest.raises(ValueError, match='binding'):
        e.score(out, path, tmp_path / 'bad-review')


@pytest.mark.parametrize('mutation', ['reorder', 'duplicate', 'missing', 'response', 'report', 'extra'])
def test_replay_rejects_tampering_even_with_resealed_inventory(prepared, tmp_path, mutation):
    e = evaluator()
    out = tmp_path / 'run'
    e.run(prepared, out, settings(), transport_factory=lambda: httpx.MockTransport(good), min_interval=0)
    observations = json.loads((out / 'observations.json').read_bytes())
    if mutation == 'reorder':
        observations.reverse()
    elif mutation == 'duplicate':
        observations[1] = observations[0]
    elif mutation == 'missing':
        observations.pop()
    elif mutation == 'response':
        observations[0]['b']['hus_answer']['facts']['invented'] = 999
    elif mutation == 'report':
        report = json.loads((out / 'report.json').read_bytes())
        report['metrics']['used'] = 999
        (out / 'report.json').write_text(json.dumps(report), encoding='utf-8')
    else:
        (out / 'extra.json').write_text('{}', encoding='utf-8')
    if mutation not in {'report', 'extra'}:
        (out / 'observations.json').write_text(json.dumps(observations), encoding='utf-8')
    if mutation != 'extra':
        e.seal(out)
    with pytest.raises(ValueError):
        e.replay(out)
