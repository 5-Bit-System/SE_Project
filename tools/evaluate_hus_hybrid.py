"""V5 fresh three-mode measurements and cache-only replay; no provider calls."""
from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import asdict
from pathlib import Path
from time import perf_counter

from app.hus.hybrid_retrieval import POLICY, HUSHybridRetriever
from app.hus.vector_contract import ROOT, digest, digest_json
from tools.evaluate_hus_chatbot import load_pack
from tools.evaluate_hus_diagnostic import (
    artifact_hashes,
    environment_snapshot,
    evaluation_hashes,
    observe_route,
)
from tools.evaluate_hus_rag import capture_response, write_json, write_rows
from tools.hus_rag_metrics_v3 import SCHEMA, evaluate, retrieval_case
from tools.validate_hus_holdout import rows

RUN_ROOT = ROOT / 'data/hus/evaluation/runs'


def reserve_output(out):
    logical = RUN_ROOT.absolute()
    folder = Path(out).resolve()
    if (logical.resolve() != logical or folder == logical or not folder.is_relative_to(logical)
            or folder.exists() or any((p / 'manifest.json').exists() for p in folder.parents
                                      if p.is_relative_to(logical))):
        raise ValueError('Choose a fresh non-nested output under evaluation/runs')
    folder.mkdir(parents=True)
    return folder


def load_suite(packs):
    packs = [Path(p).resolve() for p in packs]
    if len(packs) != len(set(packs)):
        raise ValueError('Duplicate evaluation pack in suite')
    questions, gold, evidence, hashes, releases = [], [], [], {}, []
    legacy = True
    for number, pack in enumerate(packs):
        bundle = load_pack(pack)
        prefix = f'p{number}:'
        questions += [dict(q, question_id=prefix + q['question_id']) for q in bundle['questions']]
        gold += [dict(g, question_id=prefix + g['question_id'],
                      evidence_ids=[prefix + eid for eid in g['evidence_ids']]) for g in bundle['gold']]
        evidence += [dict(e, evidence_id=prefix + e['evidence_id']) for e in bundle['evidence']]
        hashes.update(bundle['input_sha256'])
        releases.append(bundle['expected_release'])
        legacy &= bundle['legacy_applicable']
    if not packs or any(release != releases[0] for release in releases):
        raise ValueError('Packs must identify the same release')
    result = dict(questions=questions, gold=gold, evidence=evidence, input_sha256=hashes,
                  packs=[str(Path(p).resolve().relative_to(ROOT)) for p in packs],
                  expected_release=releases[0], legacy_applicable=legacy, holdout_eligible=False)
    # Validate joins/positive anchors without executing a query or forwarding targets to retrieval.
    for q, g in zip(questions, gold, strict=True):
        retrieval_case(q, g, evidence, {'retrieval_calls': []})
    return result


def current_pins(bundle, settings):
    evaluators = evaluation_hashes()
    for name in ('evaluate_hus_hybrid.py', 'hus_rag_metrics_v3.py', 'evaluate_hus_chatbot.py',
                 'hus_rag_metrics_v2.py', 'hus_chatbot_source_audit.py', 'compare_hus_hybrid.py'):
        evaluators['tools/' + name] = digest(ROOT / 'tools' / name)
    index = Path(settings.index_path)
    extra = [ROOT / 'requirements-rag-vector-lock.txt', ROOT / 'requirements-rag-vector.in',
             *sorted((ROOT / 'data/hus/vector_profiles').rglob('*')),
             ROOT / 'data/hus/vector_contracts/e5_small_v1_20261105/manifest.json',
             ROOT / 'data/hus/vector_passages/e5_small_v2_20261105/manifest.json',
             ROOT / 'data/hus/vector_passages/e5_small_v2_20261105/passages.jsonl']
    return {'artifacts': artifact_hashes(), 'evaluators': evaluators,
            'suite_sha256': digest_json(bundle),
            'vector_inputs': {str(p.relative_to(ROOT)): digest(p) for p in extra if p.is_file()},
            'index_files': {name: digest(index / name) for name in ('manifest.json', 'vectors.jsonl')},
            'expected_index_id': settings.expected_index_id,
            'model_artifact_expected': json.loads((index / 'manifest.json').read_bytes())['encoder']['artifacts_verified'],
            'pack_inputs': {p: digest(ROOT / p) for p in bundle['input_sha256']},
            'policy': asdict(POLICY), 'policy_sha256': POLICY.sha256,
            'environment': environment_snapshot()}


def peak_rss_bytes():
    if os.name == 'nt':
        import ctypes
        from ctypes import wintypes
        class Counters(ctypes.Structure):
            _fields_ = [('cb', wintypes.DWORD), ('PageFaultCount', wintypes.DWORD)] + [
                (name, ctypes.c_size_t) for name in ('PeakWorkingSetSize', 'WorkingSetSize',
                'QuotaPeakPagedPoolUsage', 'QuotaPagedPoolUsage', 'QuotaPeakNonPagedPoolUsage',
                'QuotaNonPagedPoolUsage', 'PagefileUsage', 'PeakPagefileUsage')]
        value = Counters()
        value.cb = ctypes.sizeof(value)
        ctypes.windll.kernel32.GetCurrentProcess.restype = ctypes.c_void_p
        fn = ctypes.windll.psapi.GetProcessMemoryInfo
        fn.argtypes = [ctypes.c_void_p, ctypes.POINTER(Counters), wintypes.DWORD]
        if not fn(ctypes.windll.kernel32.GetCurrentProcess(), ctypes.byref(value), value.cb):
            raise OSError('Cannot measure process peak RSS')
        return value.PeakWorkingSetSize
    import resource
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * (1 if sys.platform == 'darwin' else 1024)


def hit_row(hit):
    c, meta = hit.chunk, hit.chunk.metadata
    return {'chunk_id': c.chunk_id, 'score': hit.score, 'dataset': c.dataset, 'major': c.major,
            'version': c.version, **{k: meta.get(k) for k in ('field', 'program_variant', 'course_code',
                                                          'review_status', 'content_origin')}}


class CapturedRetriever:
    """Sequential measurement-only observer; production adapter has no shared traces."""

    def __init__(self, retriever, data):
        from app.hus.rag_loader import MAJOR_CODES
        self.retriever = retriever
        self.calls = []
        self.chunks = {c.chunk_id: c for family in ('f1', 'f3') for major in MAJOR_CODES.values()
                       for c in data.chunks(family, major=major, allow_generated=True)}

    def search(self, query, **kwargs):
        from app.hus.retrieval import RetrievalHit
        result = self.retriever.search_with_trace(query, **kwargs)
        legs = {leg: [hit_row(RetrievalHit(self.chunks[r.parent_id], r.raw_score, ()))
                      for r in getattr(result.trace, leg)] for leg in ('lexical', 'vector')}
        self.calls.append({'parameters': dict(kwargs), 'hits': [hit_row(h) for h in result.hits],
                           'v5_trace': asdict(result.trace), 'leg_hits': legs})
        return result.hits


def run(packs, out, mode, settings):
    bundle = load_suite(packs)
    before = current_pins(bundle, settings)
    out = reserve_output(out)
    write_json(out / 'inputs.json', bundle)
    write_json(out / 'input_pins.json', before)
    from fastapi.testclient import TestClient

    from app.hus import demo
    from app.hus.answering import HUSAnswerer
    from app.hus.question_routing import question_intent
    from app.hus.rag_loader import HUSRAGData
    from app.hus.vector_query import HUSVectorRetriever
    from app.hus.vector_runtime import LocalVectorRuntime
    from tools.hus_chatbot_source_audit import SourceAuditor

    started = perf_counter()
    data = HUSRAGData.load_current()
    if any(data.release_identity.get(k) != v for k, v in bundle['expected_release'].items()):
        raise ValueError('Canonical release differs from evaluation inputs')
    vector = None if mode == 'lexical' else HUSVectorRetriever(data,
        runtime_factory=lambda: LocalVectorRuntime(settings, data))
    captured = CapturedRetriever(HUSHybridRetriever(data, vector=vector, mode=mode), data)
    answerer = HUSAnswerer(data, retriever=captured)
    initialization_ms = (perf_counter() - started) * 1000
    original = demo.get_hus_answerer
    demo.get_hus_answerer = lambda: answerer
    predictions, audits = [], []
    try:
        with TestClient(demo.app, raise_server_exceptions=False) as client:
            warm = dict(question='Cơ hội nghề nghiệp của ngành là gì?', major='data_science',
                        dataset='f1', field='careers', allow_generated_reference=False)
            start = perf_counter()
            warm_response = client.post('/hus/chat', json=warm)
            cold = {'latency_ms': (perf_counter() - start) * 1000,
                    'http_status': warm_response.status_code, 'request': warm,
                    'traces': list(captured.calls), 'excluded_from_metrics': True}
            if warm_response.status_code != 200:
                raise ValueError('Cold/warmup request failed')
            for q in bundle['questions']:
                captured.calls.clear()
                start = perf_counter()
                response = client.post('/hus/chat', json=q['request'])
                elapsed = (perf_counter() - start) * 1000
                predictions.append({'question_id': q['question_id'], 'request': q['request'],
                    **capture_response(response, captured.calls), 'latency_ms': elapsed,
                    'routing_observation': observe_route(q['request']['question'], question_intent)})
            # Persist all predictions before handing any target to the source auditor/scorer.
            write_rows(out / 'predictions.jsonl', predictions)
            auditor = SourceAuditor()
            by_id = {e['evidence_id']: e for e in bundle['evidence']}
            audits = [auditor.audit(o, g, by_id, client)
                      for o, g in zip(predictions, bundle['gold'], strict=True)]
    finally:
        demo.get_hus_answerer = original
    write_rows(out / 'citation_audits.jsonl', audits)
    result = evaluate(bundle, predictions, audits)
    after = current_pins(bundle, settings)
    if before != after or load_suite(packs) != bundle:
        raise ValueError('Code/data/pack/policy/environment pins changed during measurement')
    report = {'schema_version': SCHEMA, 'mode': mode, 'kind': 'measurement',
              'policy': asdict(POLICY), 'policy_sha256': POLICY.sha256,
              'pins_sha256': digest_json(before), 'initialization_ms': initialization_ms,
              'cold_warmup': cold, 'peak_rss_bytes': peak_rss_bytes(), 'process_id': os.getpid(),
              'build_time': {'status': 'historical_not_remeasured', 'source': 'docs/acceptance/hus_offline_vector_index_v3_report.json'},
              'optional_modules_loaded': sorted({'torch', 'chromadb', 'transformers', 'tokenizers'} & sys.modules.keys()),
              'result': result, 'semantic_review': 'pending', 'holdout_eligible': False,
              'actual_human_reviews': 0, 'production_activation': False}
    write_json(out / 'report.json', report)
    write_json(out / 'manifest.json', {'schema_version': SCHEMA,
        'files_sha256': {p.name: digest(p) for p in sorted(out.iterdir()) if p.is_file()}})
    return report


def replay(folder):
    folder = Path(folder).resolve()
    if not folder.is_relative_to(RUN_ROOT.resolve()):
        raise ValueError('Replay path must be under evaluation/runs')
    manifest = json.loads((folder / 'manifest.json').read_bytes())
    expected = set(manifest['files_sha256']) | {'manifest.json'}
    if {p.name for p in folder.iterdir()} != expected:
        raise ValueError('Unexpected/missing run payload')
    for name, wanted in manifest['files_sha256'].items():
        path = (folder / name).resolve()
        if path.parent != folder or not path.is_file() or digest(path) != wanted:
            raise ValueError('Saved run hash mismatch: ' + name)
    bundle = json.loads((folder / 'inputs.json').read_bytes())
    report = json.loads((folder / 'report.json').read_bytes())
    pins = json.loads((folder / 'input_pins.json').read_bytes())
    if digest_json(pins) != report['pins_sha256']:
        raise ValueError('Saved input pins differ')
    if digest_json(bundle) != pins.get('suite_sha256') or load_suite([ROOT / p for p in bundle['packs']]) != bundle:
        raise ValueError('Saved ordered suite differs from pinned source packs')
    if any(digest(ROOT / path) != wanted for path, wanted in pins['pack_inputs'].items()):
        raise ValueError('Frozen source pack changed')
    result = evaluate(bundle, rows(folder / 'predictions.jsonl'), rows(folder / 'citation_audits.jsonl'))
    if result != report['result']:
        raise ValueError('Saved metric report differs from replay')
    return {'reproduced': True, 'cases': len(result['cases']), 'mode': report['mode'], 'new_inference': False}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pack', action='append', type=Path)
    parser.add_argument('--out', type=Path)
    parser.add_argument('--mode', choices=['lexical', 'vector', 'hybrid'])
    parser.add_argument('--index', type=Path)
    parser.add_argument('--model-cache', type=Path)
    parser.add_argument('--expected-index-id')
    parser.add_argument('--replay', type=Path)
    args = parser.parse_args(argv)
    if args.replay:
        print(json.dumps(replay(args.replay)))
    else:
        from app.hus.retrieval_config import HUSRetrievalSettings
        if not args.pack or not args.out or not args.mode or not args.index or not args.model_cache or not args.expected_index_id:
            parser.error('Measurement requires packs/output/mode/index/model cache/expected ID')
        report = run(args.pack, args.out, args.mode,
                     HUSRetrievalSettings('vector', str(args.index), str(args.model_cache), args.expected_index_id))
        print(json.dumps({'mode': args.mode, 'metrics': report['result']['metrics']}))


if __name__ == '__main__':
    main()
