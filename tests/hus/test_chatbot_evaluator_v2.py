"""Immutable A2 runs and cache-only review overlays."""

import importlib
import importlib.util
import json
from copy import deepcopy
from pathlib import Path

import pytest


def runner():
    assert importlib.util.find_spec('tools.evaluate_hus_chatbot') is not None, 'A2 runner is not implemented'
    return importlib.import_module('tools.evaluate_hus_chatbot')


def test_fresh_output_only_and_nested_old_run_is_protected(tmp_path, monkeypatch):
    m = runner()
    monkeypatch.setattr(m, 'ROOT', tmp_path)
    out = tmp_path / 'data/hus/evaluation/runs/new'
    m.reserve_output(out)
    with pytest.raises(ValueError):
        m.reserve_output(out)
    (out / 'manifest.json').write_text('{}')
    with pytest.raises(ValueError):
        m.reserve_output(out / 'child')
    with pytest.raises(ValueError):
        m.reserve_output(tmp_path / 'data/hus/rag/overwrite')


def test_http_failures_are_timed_and_preserved():
    m = runner()
    def fail(_):
        raise RuntimeError('synthetic transport failure')
    result = m.timed_execute({}, fail)
    assert result['http_status'] == 0 and result['latency_ms'] >= 0
    assert result['execution_error'].startswith('RuntimeError:')


def test_http_latency_excludes_json_and_trace_capture(monkeypatch):
    import httpx

    m = runner()
    assert callable(getattr(m, 'capture_http', None)), 'HTTP/capture timing boundary missing'
    clock = {'now': 0}
    monkeypatch.setattr(m, 'perf_counter_ns', lambda: clock['now'])
    class Client:
        def post(self, *args, **kwargs):
            clock['now'] += 1_000_000
            return httpx.Response(200, json={'mode': 'hus_rag'})
    original = m.capture_response
    def expensive_capture(response, calls):
        clock['now'] += 1_000_000_000
        return original(response, calls)
    monkeypatch.setattr(m, 'capture_response', expensive_capture)
    result = m.capture_http({}, Client(), [])
    assert result['latency_ms'] == 1 and result['http_status'] == 200


@pytest.fixture
def tiny_pack(tmp_path, monkeypatch, historical_v3_data, historical_v3_auditor):
    from app.hus.answering import HUSAnswerer

    answerer = HUSAnswerer(historical_v3_data)
    monkeypatch.setattr('app.services.hus_service.get_hus_answerer', lambda: answerer)
    monkeypatch.setattr('app.hus.demo.get_hus_answerer', lambda: answerer)
    m = runner()
    actual = Path(__file__).resolve().parents[2] / 'data/hus/evaluation/ai_reviewed_exposed_v1'
    source = {name: [json.loads(line) for line in (actual / name).read_text(encoding='utf-8').splitlines()]
              for name in ['questions.jsonl', 'gold.jsonl', 'evidence.jsonl']}
    q = next(q for q in source['questions.jsonl'] if q['question_id'] == 'H2-Q048')
    g = next(g for g in source['gold.jsonl'] if g['question_id'] == q['question_id'])
    evidence = [e for e in source['evidence.jsonl'] if e['evidence_id'] in g['evidence_ids']]
    pack = tmp_path / 'data/hus/evaluation/tiny'
    pack.mkdir(parents=True)
    for name, values in [('questions.jsonl', [q]), ('gold.jsonl', [g]), ('evidence.jsonl', evidence)]:
        (pack / name).write_text(''.join(json.dumps(v, ensure_ascii=False) + '\n' for v in values), encoding='utf-8')
    manifest = {'holdout_eligible': False, 'exposed': True, 'files_sha256':
                {p.name: m.digest(p) for p in pack.iterdir()}}
    (pack / 'manifest.json').write_text(json.dumps(manifest), encoding='utf-8')
    monkeypatch.setattr(m, 'ROOT', tmp_path)
    return m, pack, tmp_path / 'data/hus/evaluation/runs/tiny'


def test_live_source_unknown_and_cache_verification_without_new_inference(tiny_pack, monkeypatch):
    m, pack, out = tiny_pack
    report = m.run_evaluation(pack, out)
    assert report['result']['metrics']['raw_legacy']['f2_lookup_success']['value'] == 0
    assert report['result']['metrics']['f2']['source_contract_success']['value'] == 1
    monkeypatch.setattr(m, 'run_evaluation', lambda *a, **kw: pytest.fail('Cached verification must not execute runtime'))
    assert m.verify_run(out)['reproduced'] is True
    with (out / 'predictions.jsonl').open('a', encoding='utf-8') as stream:
        stream.write('\n')
    with pytest.raises(ValueError):
        m.verify_run(out)


def test_pack_hash_tampering_is_rejected_before_inference(tiny_pack):
    m, pack, _ = tiny_pack
    with (pack / 'questions.jsonl').open('a') as stream:
        stream.write('\n')
    with pytest.raises(ValueError):
        m.load_pack(pack)


def test_pack_cannot_smuggle_escape_paths_or_independence(tiny_pack):
    m, pack, _ = tiny_pack
    manifest = json.loads((pack / 'manifest.json').read_bytes())
    manifest['files_sha256']['../external'] = '0' * 64
    (pack / 'manifest.json').write_text(json.dumps(manifest))
    with pytest.raises(ValueError):
        m.load_pack(pack)


def test_declared_source_release_must_match_loaded_runtime_before_questions(tiny_pack):
    m, pack, out = tiny_pack
    manifest = json.loads((pack / 'manifest.json').read_bytes())
    manifest['source_release'] = {'release_id': 'foreign', 'release_sha256': '0' * 64}
    (pack / 'manifest.json').write_text(json.dumps(manifest))
    with pytest.raises(ValueError):
        m.run_evaluation(pack, out)
    assert not (out / 'predictions.jsonl').exists()


def test_review_overlay_preserves_measurement_and_replays_without_http(tiny_pack, monkeypatch):
    m, pack, out = tiny_pack
    m.run_evaluation(pack, out)
    before = {p.name: m.digest(p) for p in out.iterdir() if p.is_file()}
    template = json.loads((out / 'review_template.json').read_bytes())
    for row in template['cases']:
        row.update(reviewer_kind='ai', reviewer='Synthetic test reviewer', entailment='pass', completeness='pass',
                   notes='Controlled integration test, not a real acceptance review')
    review = out.parent / 'review.json'
    review.write_text(json.dumps(template), encoding='utf-8')
    score_out = out.parent / 'reviewed'
    monkeypatch.setattr(m, 'run_evaluation', lambda *a, **kw: pytest.fail('Review scoring must not execute HTTP'))
    scored = m.score_saved(out, review, score_out)
    assert scored['result']['metrics']['citation_source_support']['ai_completeness']['value'] == 1
    assert before == {p.name: m.digest(p) for p in out.iterdir() if p.is_file()}
    assert m.verify_run(score_out)['reproduced'] is True


def test_review_cannot_be_reused_on_another_measurement(tiny_pack):
    m, pack, out = tiny_pack
    m.run_evaluation(pack, out)
    other = out.parent / 'other_measurement'
    m.run_evaluation(pack, other)
    review = json.loads((out / 'review_template.json').read_bytes())
    for row in review['cases']:
        row.update(reviewer_kind='ai', reviewer='Synthetic test reviewer', entailment='pass', completeness='pass', notes='test')
    review_path = out.parent / 'original_review.json'
    review_path.write_text(json.dumps(review), encoding='utf-8')
    with pytest.raises(ValueError):
        m.score_saved(other, review_path, out.parent / 'invalid_crossrun_score')


@pytest.mark.parametrize('tamper', ['release', 'citation_dataset', 'citation_source', 'metadata_release', 'markers', 'wrapper'])
def test_program_integrity_checks_envelope_release_and_citation_references(
    tamper, monkeypatch, historical_v3_data, historical_v3_auditor
):
    runner()
    from fastapi.testclient import TestClient

    from app.hus.answering import HUSAnswerer
    from app.hus.demo import app
    from tools.hus_chatbot_source_audit import SourceAuditor

    answerer = HUSAnswerer(historical_v3_data)
    monkeypatch.setattr('app.hus.demo.get_hus_answerer', lambda: answerer)
    request = {'question': 'Tổng tín chỉ chương trình?', 'major': 'data_science', 'version': 'QD3569-2023'}
    target = {'category': 'f2', 'expected_field': 'program_credits'}
    with TestClient(app) as client:
        observation = {'question_id': 'program-integrity', 'request': request, 'http_status': 200,
                       'response': client.post('/hus/chat', json=request).json()}
        auditor = SourceAuditor()
        assert auditor.audit(observation, target, {}, client)['passed'] is True
        changed = deepcopy(observation)
        answer = changed['response']['hus_answer']
        citation = answer['citations'][0]
        if tamper == 'release':
            answer.update(release_id='foreign', release_sha256='0' * 64)
        elif tamper == 'citation_dataset':
            citation['dataset'] = 'f1'
        elif tamper == 'citation_source':
            citation['source_id'] = 'foreign'
        elif tamper == 'metadata_release':
            citation['metadata']['release_sha256'] = '0' * 64
        elif tamper == 'markers':
            answer['reply'] = changed['response']['reply'] = 'No source marker'
        else:
            changed['response']['reply'] = 'Different wrapper reply'
        assert auditor.audit(changed, target, {}, client)['passed'] is False
