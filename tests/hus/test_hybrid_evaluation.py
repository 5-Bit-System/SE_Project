"""Final parent top5, not the candidate pool, defines V5 retrieval metrics."""
import importlib
from copy import deepcopy
from dataclasses import asdict

import pytest

from app.hus.hybrid_retrieval import POLICY, HybridTrace, ParentRank
from app.hus.vector_contract import encoded


def metrics():
    return importlib.import_module('tools.hus_rag_metrics_v3')


@pytest.fixture
def case():
    scope = dict(dataset='f1', major='data_science', version='2023', course_code=None,
                 field='careers', program_variant=None, allow_generated=False)
    question = {'question_id': 'q1', 'request': {'question': 'nghề nghiệp', 'major': 'data_science'},
                'v5_tags': ['paraphrase']}
    gold = {'question_id': 'q1', 'category': 'f1', 'expected_dataset': 'f1',
            'expected_field': 'careers', 'evidence_ids': ['e1']}
    evidence = [{'evidence_id': 'e1', 'major': 'data_science', 'version': '2023',
                 'source_ref': {'identity_field': 'chunk_id', 'identity': 'p6'}}]
    parents = tuple(ParentRank('p' + str(i), i, 10.0 - i) for i in range(1, 9))
    trace = HybridTrace('lexical', 'lexical', 'release', 'sha', encoded(scope).decode(),
        encoded(asdict(POLICY)).decode(), POLICY.sha256, lexical=parents,
        candidate_union=tuple(sorted(r.parent_id for r in parents)),
        final_top5=tuple(r.parent_id for r in parents[:5]))
    def hit(row):
        return {'chunk_id': row.parent_id, 'score': row.raw_score, 'dataset': 'f1',
                'major': 'data_science', 'version': '2023', 'field': 'careers',
                'program_variant': None, 'course_code': None, 'review_status': 'include',
                'content_origin': 'reviewed_source'}
    observation = {'question_id': 'q1', 'http_status': 200, 'latency_ms': 2.0,
        'retrieval_calls': [{'parameters': scope | {'top_k': 5}, 'hits': [hit(r) for r in parents[:5]],
            'v5_trace': asdict(trace), 'leg_hits': {'lexical': [hit(r) for r in parents], 'vector': []}}]}
    return question, gold, evidence, observation


def test_candidate_hit_at_rank6_does_not_inflate_final_recall(case):
    result = metrics().retrieval_case(*case)
    assert result['recall_at_5'] == result['mrr_at_5'] == 0
    assert result['candidate_recall'] == 1 and result['retrieval_called']


def test_recall_is_fraction_of_unique_gold_parents_and_mrr_first_rank(case):
    q, g, e, o = case
    e.append({'evidence_id': 'e2', 'major': 'data_science', 'version': '2023',
              'source_ref': {'identity_field': 'chunk_id', 'identity': 'p2'}})
    g['evidence_ids'] = ['e1', 'e2']
    result = metrics().retrieval_case(q, g, e, o)
    assert result['recall_at_5'] == 0.5 and result['mrr_at_5'] == 0.5


def test_no_call_positive_stays_in_denominator(case):
    q, g, e, o = case
    o['retrieval_calls'] = []
    result = metrics().retrieval_case(q, g, e, o)
    assert result['retrieval_eligible'] and result['recall_at_5'] == 0
    assert not result['retrieval_called']


@pytest.mark.parametrize('fault', ['final_pool', 'policy', 'rank', 'union', 'score', 'scope'])
def test_bad_or_mismatched_trace_is_rejected(case, fault):
    q, g, e, o = case
    call = o['retrieval_calls'][0]
    if fault == 'final_pool':
        call['hits'] += deepcopy(call['leg_hits']['lexical'][5:])
    elif fault == 'policy':
        call['v5_trace']['policy_sha256'] = 'forged'
    elif fault == 'rank':
        call['v5_trace']['lexical'][0]['rank'] = 0
    elif fault == 'union':
        call['v5_trace']['candidate_union'] = []
    elif fault == 'score':
        call['hits'][0]['score'] = 9e9
    else:
        call['v5_trace']['filter_json'] = '{}'
    with pytest.raises(ValueError):
        metrics().retrieval_case(q, g, e, o)


def test_positive_without_gold_parent_fails_preflight(case):
    q, g, e, o = case
    g['evidence_ids'] = []
    with pytest.raises(ValueError):
        metrics().retrieval_case(q, g, e, o)


def test_wrong_edition_hit_cannot_count_as_relevant(case):
    q, g, e, o = case
    e[0]['source_ref']['identity'] = 'p1'
    e[0]['version'] = '2015'
    assert metrics().retrieval_case(q, g, e, o)['recall_at_5'] == 0


def test_fallback_vector_trace_cannot_masquerade_as_a_second_rrf_leg(case):
    q, g, e, o = case
    call = o['retrieval_calls'][0]
    trace = call['v5_trace']
    trace.update(requested_mode='hybrid', actual_mode='hybrid', vector=deepcopy(trace['lexical']),
                 vector_trace={'mode_used': 'lexical', 'fallback_reason': 'index_missing'})
    call['leg_hits']['vector'] = deepcopy(call['leg_hits']['lexical'])
    trace['fused'] = [{'parent_id': r['parent_id'], 'lexical_rank': r['rank'],
        'vector_rank': r['rank'], 'rrf_score': 2 / (60 + r['rank'])} for r in trace['lexical']]
    for hit, row in zip(call['hits'], trace['fused']):
        hit['score'] = row['rrf_score']
    with pytest.raises(ValueError):
        metrics().retrieval_case(q, g, e, o)


def test_suite_order_and_multiplicity_are_bound_in_pins():
    from pathlib import Path

    from app.hus.retrieval_config import HUSRetrievalSettings
    from app.hus.vector_contract import digest_json
    from tools.evaluate_hus_hybrid import current_pins, load_suite

    packs = [Path('data/hus/evaluation/diagnostic_dev_v1'), Path('data/hus/evaluation/a2_contracts_v1')]
    settings = HUSRetrievalSettings('vector', 'data/hus/vector_indexes/e5_small_v3_20261109',
        'backups/vector_index_v3_20261109/model', '8dad2f0f719a5228403d87f2b0c36a95f64fada9b82bf26bf432d4fed2469f74')
    a = current_pins(load_suite(packs), settings)
    b = current_pins(load_suite(list(reversed(packs))), settings)
    assert digest_json(a) != digest_json(b)
    with pytest.raises(ValueError, match='Duplicate'):
        load_suite([packs[0], packs[0]])


def test_f2_is_not_a_retrieval_positive(case):
    q, g, e, o = case
    g.update(category='f2', evidence_ids=[])
    o['retrieval_calls'] = []
    assert not metrics().retrieval_case(q, g, e, o)['retrieval_eligible']


def test_runner_refuses_existing_or_outside_outputs(tmp_path, monkeypatch):
    runner = importlib.import_module('tools.evaluate_hus_hybrid')
    monkeypatch.setattr(runner, 'RUN_ROOT', tmp_path / 'runs')
    old = tmp_path / 'runs/old'
    old.mkdir(parents=True)
    with pytest.raises(ValueError):
        runner.reserve_output(old)
    with pytest.raises(ValueError):
        runner.reserve_output(tmp_path / 'outside')


def test_replay_rejects_changed_manifest_payload(tmp_path, monkeypatch):
    import json

    from app.hus.vector_contract import digest
    runner = importlib.import_module('tools.evaluate_hus_hybrid')
    monkeypatch.setattr(runner, 'RUN_ROOT', tmp_path)
    run = tmp_path / 'saved'
    run.mkdir()
    payload = run / 'report.json'
    payload.write_text('{}')
    (run / 'manifest.json').write_text(json.dumps({'files_sha256': {'report.json': digest(payload)}}))
    payload.write_text('tampered')
    with pytest.raises(ValueError, match='hash'):
        runner.replay(run)
