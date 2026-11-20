"""A7 measurement must retain failures, scope bindings and honest exposure."""
import importlib
import importlib.util
import json
from copy import deepcopy

import pytest

from app.schemas.hus import HUSQuestion


def evaluator():
    assert importlib.util.find_spec('tools.evaluate_hus_a7') is not None, 'A7 evaluator is missing'
    return importlib.import_module('tools.evaluate_hus_a7')


def pack():
    questions, gold, evidence = [], [], []
    majors = ['computer_science', 'data_science', 'mathematics', 'mathematics_informatics']
    for major in majors:
        for index in range(12):
            qid = f'{major}-{index}'
            category = ['f1', 'f2', 'f3', 'missing_evidence'][index // 3]
            questions.append({'question_id': qid, 'request': {'question': f'Fresh question {qid}',
                'major': major, 'version': 'QD-2023', 'allow_generated_reference': category == 'f3',
                'allow_llm_rewrite': False}})
            eid = qid + '-source'
            field = {'f1': 'introduction', 'f2': 'credits', 'f3': 'content', 'missing_evidence': 'suggested_assessment'}[category]
            gold.append({'question_id': qid, 'category': category, 'expected_dataset': category if category != 'missing_evidence' else 'f3',
                'expected_field': field, 'expected_status': 'answered' if category != 'missing_evidence' else 'no_information',
                'expected_facts': {}, 'evidence_ids': [eid] if category != 'missing_evidence' else []})
            if category != 'missing_evidence':
                evidence.append({'evidence_id': eid, 'major': major, 'version': 'QD-2023', 'value': 'Source text',
                    'source_ref': {'identity_field': 'chunk_id' if category != 'f2' else 'record_id',
                                   'identity': qid, 'path': 'synthetic'}})
    return {'kind': 'hus-a7-v4-1.0', 'questions': questions, 'gold': gold, 'evidence': evidence,
            'holdout_eligible': False, 'exposure': {'author_kind': 'ai', 'actual_human_reviews': 0,
                'runtime_and_sources_seen': True, 'eligible_for_independent_acceptance': False},
            'submission': {'versions': dict.fromkeys(majors, 'QD-2023')}}


def observations(source):
    return [{'question_id': q['question_id'], 'request': deepcopy(q['request']),
             'effective_request': HUSQuestion.model_validate(q['request']).model_dump(mode='json'),
             'http_status': 200, 'response': {'mode': 'hus_rag', 'reply': 'No source',
                 'hus_answer': {'status': 'no_information', 'dataset': g['expected_dataset'],
                     'major': q['request']['major'], 'version': 'QD-2023', 'citations': [], 'facts': {}}},
             'retrieval_calls': [], 'latency_ms': 1.0,
             'routing_observation': {'dataset': g['expected_dataset'], 'field': g['expected_field'],
                                    'stage': 'classifier_before_scope_and_evidence_guards'}}
            for q, g in zip(source['questions'], source['gold'], strict=True)]


def test_cohort_balance_and_honest_exposure():
    result = evaluator().validate_structure(pack())
    assert result['questions'] == 48 and result['by_major'] == dict.fromkeys(
        ['computer_science', 'data_science', 'mathematics', 'mathematics_informatics'], 12)
    assert result['retrieval_eligible'] == 24 and result['f2_lookups'] == 12


@pytest.mark.parametrize('damage', ['omission', 'duplicate', 'major', 'gold_order', 'holdout', 'human'])
def test_unbalanced_or_false_acceptance_pack_is_rejected(damage):
    source = pack()
    if damage == 'omission':
        source['questions'].pop()
    elif damage == 'duplicate':
        source['questions'][1] = deepcopy(source['questions'][0])
    elif damage == 'major':
        source['questions'][0]['request']['major'] = 'data_science'
    elif damage == 'gold_order':
        source['gold'].reverse()
    elif damage == 'holdout':
        source['holdout_eligible'] = True
    else:
        source['exposure']['actual_human_reviews'] = 1
    with pytest.raises(ValueError):
        evaluator().validate_structure(source)


def test_request_only_execution_gets_defensive_copy_and_keeps_errors():
    source = pack()
    before = deepcopy(source)
    calls = []

    def execute(request):
        assert set(request) == set(source['questions'][0]['request'])
        assert 'question_id' not in request and 'gold' not in request
        calls.append(deepcopy(request))
        request['major'] = 'changed locally'
        if len(calls) == 2:
            raise RuntimeError('synthetic execution failure')
        return {'http_status': 200, 'response': {}, 'retrieval_calls': []}

    result = evaluator().collect_requests(source['questions'], execute)
    assert len(calls) == len(result) == 48 and source == before
    assert result[1]['http_status'] == 0 and result[1]['request'] == source['questions'][1]['request']


def test_all_positive_no_search_misses_remain_in_denominators():
    source = pack()
    obs = observations(source)
    audits = [{'question_id': q['question_id'], 'passed': True} for q in source['questions']]
    result = evaluator().score_observations(source, obs, audits)
    metric = result['metrics']['retrieval']['routed_recall_at_5']
    assert metric == {'numerator': 0, 'denominator': 24, 'value': 0}
    assert result['metrics']['abstention']['false_abstention']['denominator'] == 36
    assert result['metrics']['abstention']['false_abstention']['numerator'] == 36
    assert evaluator().technical_gates(result)['recall_at_5_met'] is False


def test_real_f1_decision_version_mapping_is_observed_not_gold_forced():
    source = pack()
    obs = observations(source)
    obs[0]['effective_request']['version'] = None
    effective = evaluator().scoring_questions(source, obs)
    assert effective[0]['request']['version'] is None
    assert source['questions'][0]['request']['version'] == 'QD-2023'


@pytest.mark.parametrize('damage', ['raw', 'question', 'major', 'consent', 'f2_version', 'missing'])
def test_effective_scope_cannot_hide_request_or_consent_tampering(damage):
    source = pack()
    obs = observations(source)
    if damage == 'raw':
        obs[0]['request']['question'] = 'Changed original'
    elif damage == 'f2_version':
        obs[3]['effective_request']['version'] = None
    elif damage == 'missing':
        obs.pop()
    else:
        key = {'question': 'question', 'major': 'major', 'consent': 'allow_generated_reference'}[damage]
        obs[0]['effective_request'][key] = True if damage == 'consent' else 'changed'
    with pytest.raises(ValueError):
        evaluator().scoring_questions(source, obs)


def test_successful_retrieval_alone_is_not_final_acceptance():
    e = evaluator()
    result = e.score_observations(pack(), observations(pack()), [
        {'question_id': q['question_id'], 'passed': True} for q in pack()['questions']])
    result['metrics']['retrieval']['routed_recall_at_5']['value'] = 1.0
    gates = e.technical_gates(result)
    assert gates['recall_at_5_met'] is True and gates['all_technical_gates_met'] is False
    assert gates['independent_or_human_acceptance'] is False


@pytest.fixture(scope='module')
def actual_pack():
    from tools.hus_a7_cases import build_pack

    return build_pack()


@pytest.mark.parametrize('damage', ['identity_field', 'pointer', 'course', 'value', 'facts_type', 'field'])
def test_source_freeze_rejects_wrong_identity_intent_or_facts(actual_pack, damage):
    source = deepcopy(actual_pack)
    if damage in {'identity_field', 'pointer'}:
        key = 'identity_field' if damage == 'identity_field' else 'json_pointer'
        source['evidence'][0]['source_ref'][key] = 'invented'
    elif damage == 'course':
        source['questions'][3]['request']['question'] = 'Số tín chỉ MAT3500 trong chương trình này?'
    elif damage == 'value':
        source['evidence'][0]['value'] = 'Invented quote'
    elif damage == 'facts_type':
        source['gold'][3]['v2_expected_facts']['value'] = float(source['gold'][3]['v2_expected_facts']['value'])
    else:
        source['gold'][0]['expected_field'] = 'careers'
    with pytest.raises((ValueError, AssertionError)):
        evaluator().check_sources(source)


def test_review_cannot_bind_different_raw_effective_or_displayed_response():
    e = evaluator()
    source = pack()
    obs = observations(source)
    audits = [{'question_id': q['question_id'], 'passed': True} for q in source['questions']]
    template = e.review_template(source, obs, audits)
    obs[0]['response']['reply'] = 'Different actual displayed response'
    assert template[0]['response_sha256'] != e.review_template(source, obs, audits)[0]['response_sha256']
    assert template[0]['raw_request_sha256'] != template[0]['request_sha256']  # effective defaults are also bound


def test_legacy_source_facts_do_not_equate_float_or_bool_to_canonical_integer():
    from tools.hus_a7_cases import strict_fact_values

    expected = {'field': 'credits', 'value': 1, 'prerequisite_status': 'unknown'}
    assert strict_fact_values(expected, expected)
    assert not strict_fact_values({**expected, 'value': 1.0}, expected)
    assert not strict_fact_values({**expected, 'value': True}, expected)


@pytest.mark.parametrize('settings', [{'HUS_LLM_ENABLED': 'true'}, {'HUS_RETRIEVAL_MODE': 'hybrid'}, {'HUS_RAG_ROOT': 'other'}])
def test_submission_gates_reject_other_configuration_before_collection(monkeypatch, settings):
    monkeypatch.setenv('HUS_LLM_ENABLED', 'false')
    monkeypatch.setenv('HUS_RETRIEVAL_MODE', 'lexical')
    monkeypatch.delenv('HUS_RAG_ROOT', raising=False)
    for key, value in settings.items():
        monkeypatch.setenv(key, value)
    with pytest.raises(ValueError):
        evaluator().require_submission_settings()


def test_executor_exception_still_yields_complete_scored_cohort():
    e = evaluator()
    source = pack()

    def broken(request):
        raise RuntimeError('synthetic failure')

    obs = e.collect_requests(source['questions'], broken)
    assert all('effective_request' in o and 'latency_ms' in o for o in obs)
    assert all(o['effective_request'] == HUSQuestion.model_validate(o['request']).model_dump(mode='json') for o in obs)
    audits = [{'question_id': o['question_id'], 'passed': False} for o in obs]
    result = e.score_observations(source, obs, audits)
    assert result['metrics']['abstention']['http_errors'] == 48
    assert result['metrics']['retrieval']['routed_recall_at_5']['denominator'] == 24


def test_status_only_controls_cannot_pass_when_independent_audits_fail():
    e = evaluator()
    source = pack()
    obs = observations(source)
    audits = [{'question_id': q['question_id'], 'passed': g['category'] in {'f1', 'f2', 'f3'}}
              for q, g in zip(source['questions'], source['gold'], strict=True)]
    result = e.score_observations(source, obs, audits)
    assert result['metrics']['abstention']['control_failures'] == 0
    assert e.technical_gates(result)['controls_all_correct'] is False


@pytest.mark.parametrize('display', ['', '   ', None])
def test_basic_control_requires_meaningful_display_text(display):
    from tools.hus_a7_cases import A7SourceAuditor

    auditor = object.__new__(A7SourceAuditor)
    result = auditor.audit({'question_id': 'synthetic', 'http_status': 200,
        'response': {'mode': 'basic_chat', 'reply': display, 'hus_answer': None}},
        {'category': 'basic_chat'}, {}, None)
    assert result['passed'] is False


@pytest.fixture
def sealed_measurement(tmp_path, monkeypatch):
    from tools.evaluate_hus_rag import digest, write_json
    from tools.hus_llm_measurement import seal

    e = evaluator()
    source = pack()
    source['pins'] = {'synthetic': True}
    from tools.hus_llm_v4_audit import RELEASE, RELEASE_SHA

    source['release'] = {'release_id': RELEASE, 'release_sha256': RELEASE_SHA}
    monkeypatch.setattr(e, 'ROOT', tmp_path)
    monkeypatch.setattr(e, 'BASE', tmp_path / 'data/hus/evaluation')
    monkeypatch.setattr(e, 'check_sources', lambda p: e.validate_structure(p))
    monkeypatch.setattr(e, 'pins', lambda: source['pins'])
    folder = e.BASE / 'candidate'
    folder.mkdir(parents=True)
    write_json(folder / 'pack.json', source)
    seal(folder)
    run = e.BASE / 'runs/measurement'
    run.mkdir(parents=True)
    obs = observations(source)
    audits = [{'question_id': q['question_id'], 'passed': True} for q in source['questions']]
    result = e.score_observations(source, obs, audits)
    report = {'kind': e.KIND, 'stage': 'measurement', 'pack_path': folder.relative_to(tmp_path).as_posix(),
              'pack_manifest_sha256': digest(folder / 'manifest.json'),
              'result': result, 'technical_gates': e.technical_gates(result)}
    template = e.review_template(source, obs, audits)
    for name, value in {'inputs.json': source, 'observations.json': obs, 'audits.json': audits,
                        'report.json': report, 'review_template.json': template}.items():
        write_json(run / name, value)
    seal(run)
    review = deepcopy(template)
    for row, g in zip(review, source['gold'], strict=True):
        row.update(reviewer='Synthetic AI review', notes='Synthetic cached observations, no inference.',
                   entailment='not_applicable', completeness='fail' if g['category'] in {'f1', 'f2', 'f3'} else 'not_applicable')
    review_path = e.BASE / 'review.json'
    write_json(review_path, review)
    return e, run, review_path


def test_review_overlay_replays_without_loading_runtime_or_provider(sealed_measurement, monkeypatch):
    from app.hus.llm.client import HUSLLMClient
    from app.hus.rag_loader import HUSRAGData

    e, run, review = sealed_measurement
    monkeypatch.setattr(HUSLLMClient, 'complete_result', lambda *a: pytest.fail('provider called'))
    monkeypatch.setattr(HUSRAGData, 'load_current', lambda *a: pytest.fail('retrieval runtime loaded'))
    out = e.BASE / 'runs/reviewed'
    e.score_saved(run, review, out)
    assert e.replay(out)['reproduced']
    assert e.replay(out)['new_rag_inference'] is False


def test_review_overlay_rejects_changed_source_run_manifest(sealed_measurement):
    from tools.evaluate_hus_rag import write_json
    from tools.hus_llm_measurement import seal

    e, run, review = sealed_measurement
    out = e.BASE / 'runs/reviewed'
    e.score_saved(run, review, out)
    report = json.loads((run / 'report.json').read_bytes())
    write_json(run / 'report.json', {**report, 'extra_mutation': True})
    seal(run)
    with pytest.raises(ValueError):
        e.replay(out)


@pytest.mark.parametrize('binding', ['response_sha256', 'raw_request_sha256', 'request_sha256', 'gold_sha256'])
def test_stale_exact_review_is_rejected_before_output_reservation(sealed_measurement, binding):
    from tools.evaluate_hus_rag import write_json

    e, run, review = sealed_measurement
    rows = json.loads(review.read_bytes())
    rows[0][binding] = 'a' * 64
    write_json(review, rows)
    out = e.BASE / 'runs/stale'
    with pytest.raises(ValueError):
        e.score_saved(run, review, out)
    assert not out.exists()


def test_collection_seals_all_rows_when_classifier_raises_once(sealed_measurement, monkeypatch):
    from app.hus import question_routing
    from tools.hus_llm_measurement import read_sealed

    e, run, _ = sealed_measurement
    source_path = e.BASE / 'candidate'
    monkeypatch.setenv('HUS_LLM_ENABLED', 'false')
    monkeypatch.setenv('HUS_RETRIEVAL_MODE', 'lexical')
    monkeypatch.delenv('HUS_RAG_ROOT', raising=False)
    original = question_routing.question_intent
    calls = []

    def classify(text):
        calls.append(text)
        if len(calls) == 1:
            raise RuntimeError('synthetic classifier failure')
        return original(text)

    monkeypatch.setattr(question_routing, 'question_intent', classify)
    out = e.BASE / 'runs/with_error'
    report = e.collect_run(source_path, out)
    saved = read_sealed(out)
    assert len(saved['observations.json']) == 48
    assert saved['observations.json'][0]['http_status'] == 0
    assert report['result']['metrics']['abstention']['http_errors'] == 1
    assert report['result']['metrics']['retrieval']['routed_recall_at_5']['denominator'] == 24
