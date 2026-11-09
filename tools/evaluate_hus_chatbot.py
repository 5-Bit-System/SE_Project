"""A2: fresh pinned BM25/extractive runs and cache-only AI review overlays."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import uuid
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter_ns

from tools.evaluate_hus_diagnostic import (
    artifact_hashes,
    collect_run,
    environment_snapshot,
    evaluation_hashes,
    observe_route,
)
from tools.evaluate_hus_rag import TracedRetriever, capture_response, digest, write_json, write_rows
from tools.hus_rag_metrics_v2 import SCHEMA, digest_json, evaluate
from tools.validate_hus_holdout import ROOT, rows


def reserve_output(out):
    out = Path(out).resolve()
    runs = (ROOT / 'data/hus/evaluation/runs').resolve()
    if not out.is_relative_to(runs) or out == runs or out.exists():
        raise ValueError('Choose a fresh directory under data/hus/evaluation/runs')
    if any((parent / 'manifest.json').exists() for parent in out.parents if parent.is_relative_to(runs)):
        raise ValueError('Cannot create output inside a frozen run')
    out.mkdir(parents=True)
    return out


def _manifest_files(folder):
    manifest = json.loads((folder / 'manifest.json').read_bytes())
    identities = manifest.get('files_sha256', manifest.get('files'))
    if not isinstance(identities, dict):
        raise ValueError('Missing manifest file hashes')
    for name, expected in identities.items():
        path = (folder / name).resolve()
        expected = expected['sha256'] if isinstance(expected, dict) else expected
        if not path.is_relative_to(folder) or not path.is_file() or digest(path) != expected:
            raise ValueError('File manifest mismatch: ' + name)
    return manifest


def load_pack(pack):
    pack = Path(pack).resolve()
    if not pack.is_relative_to((ROOT / 'data/hus/evaluation').resolve()):
        raise ValueError('Evaluation pack must be inside the workspace evaluation tree')
    manifest = _manifest_files(pack)
    if manifest.get('holdout_eligible') is not False:
        raise ValueError('A2 measures exposed development only, never certifies holdout')
    evidence_pack = pack
    parent = None
    if not (pack / 'evidence.jsonl').exists():
        parent = (ROOT / manifest['source_pack']).resolve()
        if not parent.is_relative_to((ROOT / 'data/hus/evaluation').resolve()):
            raise ValueError('Parent evidence escapes evaluation tree')
        _manifest_files(parent)
        evidence_pack = parent
    questions, gold, evidence = rows(pack / 'questions.jsonl'), rows(pack / 'gold.jsonl'), rows(evidence_pack / 'evidence.jsonl')
    ids = [q['question_id'] for q in questions]
    if len(ids) != len(set(ids)) or ids != [g['question_id'] for g in gold]:
        raise ValueError('Question and gold IDs must join exactly')
    eids = [e['evidence_id'] for e in evidence]
    if len(eids) != len(set(eids)) or any(eid not in eids for g in gold for eid in g['evidence_ids']):
        raise ValueError('Evidence IDs do not join')
    files = {p for folder in [pack, evidence_pack] for p in folder.iterdir() if p.is_file()}
    manifests = [manifest]
    if parent:
        manifests.append(json.loads((parent / 'manifest.json').read_bytes()))
    for name, expected in manifest.get('parents', {}).items():
        path = (ROOT / name / 'manifest.json').resolve()
        if not path.is_relative_to((ROOT / 'data/hus/evaluation').resolve()) or digest(path) != expected:
            raise ValueError('Parent contract manifest changed')
        files.add(path)
        manifests.append(json.loads(path.read_bytes()))
    identities = []
    for meta in manifests:
        identity = meta.get('source_release', meta.get('release'))
        if isinstance(identity, dict):
            identities.append({k: identity[k] for k in ['release_id', 'release_sha256'] if k in identity})
        elif isinstance(identity, str):
            path = (ROOT / identity / 'manifest.json').resolve()
            if not path.is_relative_to((ROOT / 'data/hus/rag/releases').resolve()):
                raise ValueError('Declared source release escapes release tree')
            if meta.get('source_release_manifest_sha256') and digest(path) != meta['source_release_manifest_sha256']:
                raise ValueError('Declared source release manifest changed')
            release_manifest = json.loads(path.read_bytes())
            identities.append({k: release_manifest[k] for k in ['release_id', 'release_sha256']})
            files.add(path)
    for item in evidence:
        match = re.search(r'data/hus/rag/releases/([^/]+)/', item.get('source_ref', {}).get('path', ''))
        if match:
            identities.append({'release_id': match[1]})
    expected_release = {}
    for key in ['release_id', 'release_sha256']:
        values = {identity[key] for identity in identities if key in identity}
        if len(values) > 1:
            raise ValueError('Pack declares conflicting source releases')
        if values:
            expected_release[key] = values.pop()
    if not expected_release:
        raise ValueError('Pack must identify its frozen source release')
    return {'pack': pack.relative_to(ROOT).as_posix(), 'questions': questions, 'gold': gold, 'evidence': evidence,
            'expected_release': expected_release,
            'input_sha256': {p.relative_to(ROOT).as_posix(): digest(p) for p in sorted(files)},
            'legacy_applicable': manifest.get('legacy_scorer_applicable', True),
            'split': manifest.get('split', 'ai_reviewed_exposed'), 'holdout_eligible': False}


def current_snapshot():
    extra = {f'tools/{name}': digest(Path(__file__).with_name(name)) for name in
             ['evaluate_hus_chatbot.py', 'hus_rag_metrics_v2.py', 'hus_chatbot_source_audit.py']}
    return {'artifacts': artifact_hashes(), 'evaluators': {**evaluation_hashes(), **extra},
            'environment': environment_snapshot()}


def timed_execute(request, execute):
    start = perf_counter_ns()
    try:
        result = execute(request)
    except Exception as exc:
        result = {'http_status': 0, 'response': {}, 'retrieval_calls': [],
                  'execution_error': f'{type(exc).__name__}: {str(exc)[:300]}'}
    return {**result, 'latency_ms': (perf_counter_ns() - start) / 1_000_000}


def capture_http(request, client, calls):
    timed = timed_execute(request, lambda value: {'_response': client.post('/hus/chat', json=value)})
    response = timed.pop('_response', None)
    return {**timed, **capture_response(response, calls)} if response is not None else timed


class TracedRetrieverV2(TracedRetriever):
    def search(self, *args, **kwargs):
        hits = super().search(*args, **kwargs)
        for saved, hit in zip(self.calls[-1]['hits'], hits, strict=True):
            meta = hit.chunk.metadata
            saved.update(program_variant=meta.get('program_variant'), review_status=meta.get('review_status'),
                         content_origin=meta.get('content_origin'))
        return hits


def _seal(out):
    write_json(out / 'manifest.json', {'schema_version': SCHEMA,
               'files_sha256': {p.name: digest(p) for p in sorted(out.iterdir()) if p.is_file() and p.name != 'manifest.json'}})


def run_evaluation(pack, out):
    bundle = load_pack(pack)
    before = current_snapshot()
    out = reserve_output(out)
    write_json(out / 'inputs.json', bundle)
    write_json(out / 'input_snapshot.json', before)
    # Imports and all requests are confined to the collection command.
    from fastapi.testclient import TestClient

    from app.hus.demo import app
    from app.hus.question_routing import question_intent
    from app.services.hus_service import get_hus_answerer
    from tools.hus_chatbot_source_audit import SourceAuditor

    start = perf_counter_ns()
    answerer = get_hus_answerer()
    initialization_ms = (perf_counter_ns() - start) / 1_000_000
    if any(answerer.data.release_identity.get(k) != v for k, v in bundle['expected_release'].items()):
        raise ValueError('Loaded runtime release differs from frozen evaluation pack')
    measurement_id = uuid.uuid4().hex
    original = answerer.retriever
    if type(original).__name__ != 'HUSRAGRetriever':
        raise ValueError('A2 baseline requires the existing BM25 retriever')
    traced = TracedRetrieverV2(original)
    answerer.retriever = traced
    try:
        with TestClient(app, raise_server_exceptions=False) as client:
            warm = {'question': 'Xin chào', 'major': 'data_science', 'version': 'QD3569-2023'}
            start = perf_counter_ns()
            warm_response = client.post('/hus/chat', json=warm)
            warmup = {'request': warm, 'http_status': warm_response.status_code,
                      'latency_ms': (perf_counter_ns() - start) / 1_000_000, 'excluded_from_metrics': True}

            def execute(request):
                route = observe_route(request['question'], question_intent)
                traced.calls.clear()
                result = capture_http(request, client, traced.calls)
                return {**result, 'routing_observation': route}

            observations = collect_run(bundle['questions'], out, execute)
            # No targets reach execute; all predictions are on disk before audit.
            auditor = SourceAuditor()
            by_id = {e['evidence_id']: e for e in bundle['evidence']}
            audits = [auditor.audit(o, g, by_id, client) for o, g in zip(observations, bundle['gold'], strict=True)]
    finally:
        answerer.retriever = original
    write_rows(out / 'citation_audits.jsonl', audits)
    result = evaluate(bundle['questions'], bundle['gold'], bundle['evidence'], observations, audits,
                      legacy_applicable=bundle['legacy_applicable'])
    if before != current_snapshot() or bundle != load_pack(ROOT / bundle['pack']):
        raise ValueError('Code/data/evaluation inputs changed during measurement')
    template = {'schema_version': SCHEMA, 'source_inputs_sha256': digest_json(bundle['input_sha256']),
                'measurement_id': measurement_id, 'source_run': out.relative_to(ROOT).as_posix(),
                'input_snapshot_sha256': digest_json(before), 'predictions_sha256': digest(out / 'predictions.jsonl'),
                'citation_audits_sha256': digest(out / 'citation_audits.jsonl'),
                'release': answerer.data.release_identity, 'actual_human_reviews': 0, 'cases': []}
    for q, g, o, a in zip(bundle['questions'], bundle['gold'], observations, audits, strict=True):
        template['cases'].append({'question_id': q['question_id'], 'reviewer_kind': 'ai', 'reviewer': '',
            'request_sha256': digest_json(q['request']), 'response_sha256': digest_json(o.get('response', {})),
            'gold_sha256': digest_json(g), 'audit_sha256': digest_json(a),
            'entailment': 'pending', 'completeness': 'pending', 'notes': ''})
    write_json(out / 'review_template.json', template)
    report = {'schema_version': SCHEMA, 'kind': 'measurement', 'pack': bundle['pack'],
              'measurement_id': measurement_id,
              'pipeline': 'BM25+extractive_F1_F3_and_structured_F2_no_vector_no_LLM',
              'base_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
              'git_state': 'uncommitted_worktree_pinned_by_hash', 'created_at': datetime.now(timezone.utc).isoformat(),
              'holdout_eligible': False, 'independent_holdout_accepted': False, 'actual_human_reviews': 0,
              'release': answerer.data.release_identity, 'input_pins_stable': True,
              'initialization_ms': initialization_ms, 'warmup': warmup,
              'source_binary_checks': auditor.binary_checks, 'result': result,
              'limits': ['Exposed development only, including previously tuned H2 questions.',
                         'Local warmed TestClient wall times, not network/production/load-test latency.',
                         'Raw historical scoring stays separate from F2 source contracts and exact-response-bound AI semantic review.']}
    write_json(out / 'report.json', report)
    _seal(out)
    return report


def _read_run(run):
    run = Path(run).resolve()
    _manifest_files(run)
    report = json.loads((run / 'report.json').read_bytes())
    if report['schema_version'] != SCHEMA:
        raise ValueError('Unsupported evaluator version')
    return run, report


def _verify_measurement(run, report):
    bundle = json.loads((run / 'inputs.json').read_bytes())
    if bundle != load_pack(ROOT / bundle['pack']):
        raise ValueError('Frozen evaluation input pack changed')
    result = evaluate(bundle['questions'], bundle['gold'], bundle['evidence'], rows(run / 'predictions.jsonl'),
                      rows(run / 'citation_audits.jsonl'), legacy_applicable=bundle['legacy_applicable'])
    if result != report['result']:
        raise ValueError('Cached scores differ from recomputed observations')
    return bundle


def score_saved(source_run, review_path, out):
    source_run, source_report = _read_run(source_run)
    if source_report['kind'] != 'measurement':
        raise ValueError('Review must bind an original measurement')
    bundle = _verify_measurement(source_run, source_report)
    review = json.loads(Path(review_path).read_bytes())
    expected_template = json.loads((source_run / 'review_template.json').read_bytes())
    if (review.get('schema_version') != SCHEMA or review.get('actual_human_reviews') != 0
            or review.get('source_inputs_sha256') != digest_json(bundle['input_sha256'])
            or review.get('release') != source_report['release']):
        raise ValueError('Semantic review input/release binding differs')
    if {k: v for k, v in review.items() if k != 'cases'} != {k: v for k, v in expected_template.items() if k != 'cases'}:
        raise ValueError('Semantic review metadata differs from template')
    result = evaluate(bundle['questions'], bundle['gold'], bundle['evidence'], rows(source_run / 'predictions.jsonl'),
                      rows(source_run / 'citation_audits.jsonl'), review=review['cases'], legacy_applicable=bundle['legacy_applicable'])
    out = reserve_output(out)
    write_json(out / 'review.json', review)
    report = {'schema_version': SCHEMA, 'kind': 'review_score', 'holdout_eligible': False,
              'source_run': source_run.relative_to(ROOT).as_posix(),
              'source_run_manifest_sha256': digest(source_run / 'manifest.json'),
              'actual_human_reviews': 0, 'result': result}
    write_json(out / 'report.json', report)
    _seal(out)
    return report


def verify_run(run):
    run, report = _read_run(run)
    if report['kind'] == 'measurement':
        _verify_measurement(run, report)
    elif report['kind'] == 'review_score':
        source_run = (ROOT / report['source_run']).resolve()
        if not source_run.is_relative_to((ROOT / 'data/hus/evaluation/runs').resolve()):
            raise ValueError('Source run escapes immutable runs tree')
        source_run, source_report = _read_run(source_run)
        if digest(source_run / 'manifest.json') != report['source_run_manifest_sha256']:
            raise ValueError('Source measurement manifest differs')
        bundle = _verify_measurement(source_run, source_report)
        review = json.loads((run / 'review.json').read_bytes())
        template = json.loads((source_run / 'review_template.json').read_bytes())
        if {k: v for k, v in review.items() if k != 'cases'} != {k: v for k, v in template.items() if k != 'cases'}:
            raise ValueError('Cached semantic review metadata changed')
        result = evaluate(bundle['questions'], bundle['gold'], bundle['evidence'], rows(source_run / 'predictions.jsonl'),
                          rows(source_run / 'citation_audits.jsonl'), review=review['cases'], legacy_applicable=bundle['legacy_applicable'])
        if result != report['result']:
            raise ValueError('Cached semantic scores differ')
    else:
        raise ValueError('Invalid run kind')
    pin_dir = run if report['kind'] == 'measurement' else source_run
    old_snapshot = json.loads((pin_dir / 'input_snapshot.json').read_bytes())
    current = current_snapshot()
    return {'reproduced': True, 'new_rag_inference': False, 'kind': report['kind'],
            'current_artifacts_match_recorded': old_snapshot['artifacts'] == current['artifacts'],
            'current_evaluators_match_recorded': old_snapshot['evaluators'] == current['evaluators'],
            'schema_version': SCHEMA, 'holdout_eligible': False}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument('--pack', type=Path)
    action.add_argument('--score-run', type=Path)
    action.add_argument('--verify-run', type=Path)
    parser.add_argument('--review', type=Path)
    parser.add_argument('--out', type=Path)
    args = parser.parse_args(argv)
    if args.verify_run:
        if args.out or args.review:
            parser.error('--verify-run is read-only')
        result = verify_run(args.verify_run)
    else:
        if not args.out:
            parser.error('--out is required and must be fresh')
        if args.score_run and not args.review:
            parser.error('--score-run requires --review')
        report = score_saved(args.score_run, args.review, args.out) if args.score_run else run_evaluation(args.pack, args.out)
        result = {'out': str(args.out), 'schema_version': SCHEMA, 'metrics': report['result']['metrics']}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
