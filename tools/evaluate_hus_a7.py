"""A7 v4: frozen request-only, provider-free evaluation and exact saved review."""
from __future__ import annotations

import argparse
import json
import os
from collections import Counter
from copy import deepcopy
from pathlib import Path
from time import perf_counter
from unittest.mock import patch

import httpx

from app.schemas.hus import HUSQuestion
from tools.evaluate_hus_chatbot import TracedRetrieverV2, capture_http, current_snapshot
from tools.evaluate_hus_diagnostic import observe_route
from tools.evaluate_hus_rag import digest, write_json
from tools.hus_llm_measurement import read_sealed, reserve, seal
from tools.hus_rag_metrics import collect_predictions
from tools.hus_rag_metrics_v2 import digest_json, evaluate
from tools.validate_hus_holdout import ROOT

KIND = 'hus-a7-v4-1.0'
MAJORS = {'computer_science', 'data_science', 'mathematics', 'mathematics_informatics'}
BASE = ROOT / 'data/hus/evaluation'


def validate_structure(pack):
    questions, gold, evidence = (pack[k] for k in ('questions', 'gold', 'evidence'))
    ids = [q['question_id'] for q in questions]
    if (pack['kind'] != KIND or len(ids) != 48 or len(set(ids)) != 48
            or ids != [g['question_id'] for g in gold]
            or pack['holdout_eligible'] is not False
            or pack['exposure']['author_kind'] != 'ai'
            or pack['exposure']['actual_human_reviews'] != 0
            or pack['exposure']['runtime_and_sources_seen'] is not True
            or pack['exposure']['eligible_for_independent_acceptance'] is not False):
        raise ValueError('A7 cohort or exposure declarations differ')
    by_major = Counter(q['request']['major'] for q in questions)
    if dict(by_major) != dict.fromkeys(MAJORS, 12):
        raise ValueError('A7 requires 12 questions in each of four majors')
    eids = {e['evidence_id'] for e in evidence}
    if len(eids) != len(evidence):
        raise ValueError('Duplicate evidence ID')
    for major in MAJORS:
        categories = Counter(g['category'] for q, g in zip(questions, gold, strict=True)
                             if q['request']['major'] == major)
        if any(categories[family] != 3 for family in ('f1', 'f2', 'f3')):
            raise ValueError('A7 requires three positives per family per major')
    for q, g in zip(questions, gold, strict=True):
        HUSQuestion.model_validate(q['request'])
        if (set(q['request']) - {'question', 'major', 'version', 'allow_generated_reference', 'allow_llm_rewrite'}
                or bool(g['evidence_ids']) != (g['category'] in {'f1', 'f2', 'f3'})
                or any(eid not in eids for eid in g['evidence_ids'])):
            raise ValueError('Request hints or source target binding invalid')
    return {'questions': 48, 'by_major': dict(by_major), 'retrieval_eligible': 24,
            'f2_lookups': 12, 'controls': 12}


def collect_requests(questions, execute):
    def observed(request):
        original = deepcopy(request)
        started = perf_counter()
        try:
            result = execute(request)
        except Exception as exc:
            result = {'http_status': 0, 'response': {}, 'retrieval_calls': [],
                      'execution_error': type(exc).__name__}
        return {**result,
                'latency_ms': result.get('latency_ms', (perf_counter() - started) * 1000),
                'effective_request': result.get('effective_request', HUSQuestion.model_validate(original).model_dump(mode='json')),
                'effective_request_observed': result.get('effective_request_observed', False)}

    return collect_predictions(questions, observed)


def scoring_questions(pack, observations):
    if [o['question_id'] for o in observations] != [q['question_id'] for q in pack['questions']]:
        raise ValueError('Prediction IDs must join every frozen request')
    result = []
    for q, o in zip(pack['questions'], observations, strict=True):
        if o['request'] != q['request']:
            raise ValueError('Raw request binding changed')
        original = HUSQuestion.model_validate(q['request']).model_dump(mode='json')
        allowed = [original]
        route = o.get('routing_observation') or {}
        if (route.get('dataset') == 'f1' and original['dataset'] == 'auto'
                and original['version'] == pack['submission']['versions'][original['major']]):
            allowed.append({**original, 'version': None})
        effective = o['effective_request']
        if effective not in allowed:
            raise ValueError('Unobserved/invalid effective request mapping')
        result.append({**q, 'request': deepcopy(effective)})
    return result


def score_observations(pack, observations, audits, review=None):
    validate_structure(pack)
    questions = scoring_questions(pack, observations)
    result = evaluate(questions, pack['gold'], pack['evidence'], observations, audits,
                      review=review, legacy_applicable=False)
    controls = [c for c in result['cases'] if not c['positive']]
    result['metrics']['abstention']['control_audit_failures'] = sum(not c['source_integrity'] for c in controls)
    return result


def technical_gates(result):
    m = result['metrics']
    recall = m['retrieval']['routed_recall_at_5']['value']
    support = m['citation_source_support']
    checks = {
        'recall_at_5_met': recall is not None and recall >= .9,
        'no_scope_filter_errors': not any(m['filters']['errors'].values()),
        'f2_source_facts_all_correct': m['f2']['source_contract_success']['value'] == 1,
        'answered_source_integrity': support['integrity_among_answered_positive']['value'] == 1,
        'no_false_abstention': m['abstention']['false_abstention']['numerator'] == 0,
        'controls_all_correct': m['abstention']['control_failures'] == 0
            and m['abstention']['control_audit_failures'] == 0,
        'no_http_errors': m['abstention']['http_errors'] == 0,
        'ai_content_review_all_complete': support['ai_review_coverage']['value'] == 1
            and (support['ai_completeness'] or {}).get('value') == 1
            and (support['ai_entailment'] or {}).get('value') == 1,
    }
    return {**checks, 'all_technical_gates_met': all(checks.values()),
            'independent_or_human_acceptance': False}


def pins():
    from app.hus.llm.prompts import SYSTEM_PROMPT, SYSTEM_PROMPT_V3

    snapshot = current_snapshot()
    snapshot['evaluators'].update({name: digest(ROOT / name) for name in (
        'tools/evaluate_hus_a7.py', 'tools/hus_a7_cases.py', 'tools/hus_llm_v4_audit.py',
        'tests/hus/test_a7_evaluation.py')})
    snapshot['configuration'] = {'retrieval': 'lexical', 'index': None, 'llm_enabled': False,
        'model': 'gemini-3.5-flash-lite', 'actual_model': None, 'model_inference': 'not_run',
        'dormant_prompt_sha256': digest_json(SYSTEM_PROMPT_V3),
        'dormant_legacy_f2_prompt_sha256': digest_json(SYSTEM_PROMPT),
        'f1_f3_protocol': 'hus-llm-document-v3', 'f2_protocol': 'hus-llm-evidence-v1',
        'entrypoint': 'app.hus.demo:app'}
    return snapshot


def require_submission_settings():
    from app.hus.llm.config import HUSLLMSettings

    if (HUSLLMSettings.read_enabled() or os.environ.get('HUS_RETRIEVAL_MODE', 'lexical') != 'lexical'
            or os.environ.get('HUS_RAG_ROOT')):
        raise ValueError('A7 requires shared CURRENT, lexical and LLM disabled')


def check_sources(pack):
    from tools.hus_a7_cases import check_source_evidence

    validate_structure(pack)
    check_source_evidence(pack)


def read_pack(folder):
    saved = read_sealed(folder)
    if set(saved) != {'pack.json'}:
        raise ValueError('Unexpected A7 pack inventory')
    check_sources(saved['pack.json'])
    return saved['pack.json']


def fresh_output(folder, *, run):
    folder = Path(folder).resolve()
    base = BASE / 'runs' if run else BASE
    if (not folder.is_relative_to(base) or folder == base
            or (not run and folder.is_relative_to(BASE / 'runs'))):
        raise ValueError('Choose a fresh A7 directory in evaluation tree')
    return reserve(folder)


def freeze(folder):
    from tools.hus_a7_cases import build_pack

    require_submission_settings()
    before = pins()
    pack = build_pack()
    check_sources(pack)
    pack['pins'] = before
    if before != pins():
        raise ValueError('Pins changed while freezing A7')
    out = fresh_output(folder, run=False)
    write_json(out / 'pack.json', pack)
    seal(out)
    return validate_structure(pack)


def review_template(pack, observations, audits):
    questions = scoring_questions(pack, observations)
    return [{'question_id': q['question_id'], 'reviewer_kind': 'ai', 'reviewer': '',
             'request_sha256': digest_json(q['request']),
             'raw_request_sha256': digest_json(raw['request']),
             'response_sha256': digest_json(o['response']), 'gold_sha256': digest_json(g),
             'audit_sha256': digest_json(a), 'entailment': 'pending',
             'completeness': 'pending', 'notes': ''}
            for raw, q, g, o, a in zip(pack['questions'], questions, pack['gold'], observations, audits, strict=True)]


def collect_run(pack_path, out):
    from fastapi.testclient import TestClient

    from app.hus import demo
    from app.hus.llm.client import HUSLLMClient
    from app.hus.question_routing import question_intent
    from app.services.hus_service import get_hus_answerer
    from tools.hus_a7_cases import A7SourceAuditor

    require_submission_settings()
    pack = read_pack(pack_path)
    before = pins()
    if pack['pins'] != before:
        raise ValueError('Code/data/config changed after freezing A7')
    get_hus_answerer.cache_clear()
    answerer = get_hus_answerer()
    if (any(answerer.data.release_identity.get(k) != v for k, v in pack['release'].items())
            or type(answerer.retriever).__name__ != 'HUSRAGRetriever'):
        raise ValueError('Submission data/retrieval differs from frozen A7')
    out = fresh_output(out, run=True)
    original = answerer.retriever
    traced = TracedRetrieverV2(original)
    answerer.retriever = traced
    effective = []

    class ObserveAnswerer:
        def __getattr__(self, name):
            return getattr(answerer, name)

        def answer(self, request):
            effective.append(request.model_dump(mode='json'))
            return answerer.answer(request)

    external_attempts = []

    def forbid_network(*args, **kwargs):
        external_attempts.append(True)
        raise AssertionError('A7 forbids external transport/provider calls')

    try:
        with (patch.object(demo, 'get_hus_answerer', lambda: ObserveAnswerer()),
              patch.object(httpx.HTTPTransport, 'handle_request', forbid_network),
              patch.object(HUSLLMClient, 'complete_result', forbid_network),
              TestClient(demo.app, raise_server_exceptions=False) as client):
            config_response = client.get('/hus/config')
            assert config_response.status_code == 200
            actual_config = config_response.json()

            def execute(request):
                traced.calls.clear()
                effective.clear()
                route = observe_route(request['question'], question_intent)
                result = capture_http(request, client, traced.calls)
                return {**result, 'routing_observation': route,
                        'effective_request_observed': bool(effective),
                        'effective_request': deepcopy(effective[0]) if effective else
                            HUSQuestion.model_validate(request).model_dump(mode='json')}

            observations = collect_requests(pack['questions'], execute)
            # Every exact prediction is persisted before targets enter the audit/scorer.
            write_json(out / 'observations.json', observations)
            auditor = A7SourceAuditor()
            by_id = {e['evidence_id']: e for e in pack['evidence']}
            audits = [auditor.audit({**o, 'request': o['effective_request']}, g, by_id, client)
                      for o, g in zip(observations, pack['gold'], strict=True)]
    finally:
        answerer.retriever = original
        get_hus_answerer.cache_clear()
    if external_attempts or before != pins() or pack != read_pack(pack_path):
        raise ValueError('A7 pins/inputs changed or outbound call attempted')
    result = score_observations(pack, observations, audits)
    report = {'kind': KIND, 'stage': 'measurement', 'release': pack['release'],
        'pack_path': Path(pack_path).resolve().relative_to(ROOT).as_posix(),
        'pack_manifest_sha256': digest(Path(pack_path) / 'manifest.json'),
        'result': result, 'technical_gates': technical_gates(result),
        'holdout_eligible': False, 'human_reviews': 0, 'provider_calls': 0,
        'external_transport_attempts': 0, 'submission_config': actual_config,
        'source_binary_checks': auditor.binary_checks, 'pins_stable': True,
        'latency_scope': 'Local TestClient HTTP wall time; cold first request retained; excludes source auditing/review.',
        'llm_model_or_quality_measured': False}
    for name, value in {'inputs.json': pack, 'audits.json': audits, 'report.json': report,
                        'review_template.json': review_template(pack, observations, audits)}.items():
        write_json(out / name, value)
    seal(out)
    return report


def verify_saved(folder):
    saved = read_sealed(folder)
    pack, observations, audits = (saved[k] for k in ('inputs.json', 'observations.json', 'audits.json'))
    report = saved['report.json']
    if report['kind'] != KIND or report['stage'] not in {'measurement', 'ai_review_overlay'}:
        raise ValueError('Unsupported A7 report stage')
    if report['stage'] == 'ai_review_overlay':
        parent = (ROOT / report['source_run']).resolve()
        if (not parent.is_relative_to(BASE / 'runs')
                or digest(parent / 'manifest.json') != report['source_run_manifest_sha256']):
            raise ValueError('Original measurement manifest changed')
        original = read_sealed(parent)
        if (original['report.json']['stage'] != 'measurement'
                or any(original[k] != saved[k] for k in ('inputs.json', 'observations.json', 'audits.json', 'review_template.json'))
                or 'review.json' not in saved):
            raise ValueError('Review overlay differs from original measurement')
    if pack != read_pack(ROOT / report['pack_path']) or digest(ROOT / report['pack_path'] / 'manifest.json') != report['pack_manifest_sha256']:
        raise ValueError('Frozen pack binding changed')
    review = saved.get('review.json')
    if review is not None:
        expected = review_template(pack, observations, audits)
        if len(review) != len(expected):
            raise ValueError('Review must cover every exact response')
        for row, base in zip(review, expected, strict=True):
            if any(row.get(k) != base[k] for k in base if k.endswith('_sha256') or k == 'question_id'):
                raise ValueError('Review exact-response binding changed')
    result = score_observations(pack, observations, audits, review)
    if result != report['result'] or technical_gates(result) != report['technical_gates']:
        raise ValueError('Saved A7 metrics do not reproduce')
    return saved


def score_saved(source, review_path, out):
    saved = verify_saved(source)
    if saved['report.json']['stage'] != 'measurement':
        raise ValueError('Review must overlay an original measurement')
    review = json.loads(Path(review_path).read_bytes())
    # Validate against the sealed template before creating an output directory.
    expected = saved['review_template.json']
    if len(review) != len(expected) or any(any(r.get(k) != t[k] for k in t
            if k.endswith('_sha256') or k == 'question_id') for r, t in zip(review, expected, strict=True)):
        raise ValueError('Review bindings differ from exact saved responses')
    result = score_observations(saved['inputs.json'], saved['observations.json'], saved['audits.json'], review)
    report = {**saved['report.json'], 'stage': 'ai_review_overlay', 'result': result,
              'technical_gates': technical_gates(result), 'source_run': Path(source).resolve().relative_to(ROOT).as_posix(),
              'source_run_manifest_sha256': digest(Path(source) / 'manifest.json'),
              'review_sha256': digest(review_path), 'review_kind': 'AI nonblind, exposed; human0',
              'new_provider_calls': 0, 'new_rag_inference': False}
    out = fresh_output(out, run=True)
    for name, value in {**saved, 'review.json': review, 'report.json': report}.items():
        write_json(out / name, value)
    seal(out)
    verify_saved(out)
    return report


def replay(folder):
    saved = verify_saved(folder)
    return {'reproduced': True, 'new_provider_calls': 0, 'new_rag_inference': False,
            'current_pins_match': saved['inputs.json']['pins'] == pins(),
            'technical_gates': saved['report.json']['technical_gates']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument('--freeze', type=Path)
    action.add_argument('--run', type=Path)
    action.add_argument('--score', type=Path)
    action.add_argument('--replay', type=Path)
    parser.add_argument('--out', type=Path)
    parser.add_argument('--review', type=Path)
    args = parser.parse_args()
    if args.freeze:
        result = freeze(args.freeze)
    elif args.replay:
        result = replay(args.replay)
    elif args.run and args.out:
        result = collect_run(args.run, args.out)['technical_gates']
    elif args.score and args.review and args.out:
        result = score_saved(args.score, args.review, args.out)['technical_gates']
    else:
        parser.error('Collection/scoring require a fresh --out; scoring also requires --review')
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
