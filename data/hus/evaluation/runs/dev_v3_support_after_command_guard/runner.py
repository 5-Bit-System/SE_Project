"""Pinned API measurement of exposed support-gate dev requests, never holdout."""
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from tools.evaluate_hus_diagnostic import (
    artifact_hashes, audit_development_prediction, build_layers, build_scores,
    collect_run, environment_snapshot, evaluation_hashes, observe_route, runtime_hashes,
)
from tools.evaluate_hus_rag import TracedRetriever, capture_response, write_json, write_rows

ROOT = Path.cwd()
PACK = ROOT / 'data/hus/evaluation/diagnostic_dev_v3_support'
WORK = ROOT / 'backups/support_gate_v3'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_bytes())


def rows(path):
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line]


def validate():
    manifest = read(PACK / 'manifest.json')
    for name, expected in manifest['files_sha256'].items():
        assert sha(PACK / name) == expected, name
    for name, expected in manifest['parent_inputs_sha256'].items():
        assert sha(ROOT / name) == expected, name
    for name, expected in read(WORK / 'protected_before.json').items():
        assert sha(ROOT / name) == expected, name
    return manifest


def snapshot():
    return {'runtime_sha256': runtime_hashes(), 'artifact_sha256': artifact_hashes(),
            'evaluator_sha256': evaluation_hashes(), 'environment': environment_snapshot(),
            'runner_sha256': sha(Path(__file__))}


def score(predictions, audits):
    questions, gold, evidence = [rows(PACK / name) for name in ('questions.jsonl', 'gold.jsonl', 'evidence.jsonl')]
    cases, metrics = build_scores(questions, gold, evidence, predictions, audits)
    layers = build_layers(questions, gold, evidence, predictions, audits)
    summary = {'questions': 20, 'answered': sum(p['response']['hus_answer']['status'] == 'answered' for p in predictions),
               'routed_correctly': sum([p['routing_observation']['dataset'], p['routing_observation']['field']]
                                       == [g['expected_dataset'], g['expected_field']]
                                       for p, g in zip(predictions, gold, strict=True)),
               'source_supported_success': sum(c['source_supported_success'] for c in cases),
               'not_independent_acceptance': True}
    return cases, metrics, layers, summary


def run(out):
    validate()
    before = snapshot()
    out = out.resolve()
    assert out.is_relative_to(ROOT / 'data/hus/evaluation/runs') and not out.exists()
    out.mkdir()
    (out / 'runner.py').write_bytes(Path(__file__).read_bytes())
    write_json(out / 'input_snapshot.json', before)
    from fastapi.testclient import TestClient
    from app.hus.demo import app
    from app.hus.question_routing import question_intent
    from app.services.hus_service import get_hus_answerer
    from tools.verify_hus_e2e import EvidenceOracle

    answerer = get_hus_answerer()
    original = answerer.retriever
    traced = TracedRetriever(original)
    answerer.retriever = traced
    try:
        with TestClient(app, raise_server_exceptions=False) as client:
            def execute(request):
                traced.calls.clear()
                route = observe_route(request['question'], question_intent)
                response = client.post('/hus/chat', json=request)
                return {**capture_response(response, traced.calls), 'routing_observation': route}
            predictions = collect_run(rows(PACK / 'questions.jsonl'), out, execute)
    finally:
        answerer.retriever = original
    # Gold/evidence are consulted only after responses have been persisted.
    gold, evidence = rows(PACK / 'gold.jsonl'), rows(PACK / 'evidence.jsonl')
    by_id, binary, oracle = {e['evidence_id']: e for e in evidence}, {}, EvidenceOracle()
    with TestClient(app, raise_server_exceptions=False) as client:
        audits = [audit_development_prediction(p, g, by_id, oracle, client, binary)
                  for p, g in zip(predictions, gold, strict=True)]
    cases, metrics, layers, summary = score(predictions, audits)
    write_rows(out / 'citation_audits.jsonl', audits)
    write_rows(out / 'scored_cases.jsonl', cases)
    write_json(out / 'layered_metrics.json', layers)
    assert before == snapshot()
    validate()
    write_json(out / 'report.json', {'status': 'exposed_development_support_gate_slice',
               'created_at': datetime.now(timezone.utc).isoformat(), 'pack': PACK.relative_to(ROOT).as_posix(),
               'pack_manifest_sha256': sha(PACK / 'manifest.json'), 'summary': summary, 'metrics': metrics,
               'source_binary_checks': binary, 'inputs_unchanged_during_run': True,
               'holdout_eligible': False, 'semantic_independence_claimed': False})
    write_json(out / 'manifest.json', {'files_sha256': {p.name: sha(p) for p in sorted(out.iterdir()) if p.is_file()}})
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, required=True)
    print(json.dumps(run(parser.parse_args().out), indent=2))
