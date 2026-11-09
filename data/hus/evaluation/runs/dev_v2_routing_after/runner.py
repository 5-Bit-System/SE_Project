"""Measure/replay a frozen exposed dev slice with the existing collectors/oracle."""
from pathlib import Path
import sys
import argparse
import hashlib
import json
from datetime import datetime, timezone

ROOT=next(p for p in Path(__file__).resolve().parents if (p/'tools/evaluate_hus_diagnostic.py').is_file())
sys.path.insert(0,str(ROOT))
from tools.evaluate_hus_diagnostic import artifact_hashes,environment_snapshot,runtime_hashes,evaluation_hashes,collect_run,observe_route,audit_development_prediction,build_scores,build_layers
from tools.evaluate_hus_rag import TracedRetriever,capture_response,write_json,write_rows
PACK=ROOT/'data/hus/evaluation/diagnostic_dev_v2_routing'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
def rows(p):return [json.loads(l) for l in p.read_text(encoding='utf-8').splitlines() if l]
def validate():
    m=read(PACK/'manifest.json')
    for name,h in m['files_sha256'].items():assert sha(PACK/name)==h
    for name,h in m['parent_inputs_sha256'].items():assert sha(ROOT/name)==h
    for name,h in read(ROOT/'backups/routing_slice_v2/protected_before.json').items():assert sha(ROOT/name)==h,name
    assert m['question_count']==8 and not m['holdout_eligible']
    q,g,c=[rows(PACK/name) for name in ['questions.jsonl','gold.jsonl','cases.jsonl']]
    assert [x['question_id'] for x in q]==[x['question_id'] for x in g]==[x['question_id'] for x in c]
    return m
def snapshot():
    return {'runtime_sha256':runtime_hashes(),'artifact_sha256':artifact_hashes(),'evaluator_sha256':evaluation_hashes(),'environment':environment_snapshot(),'runner_sha256':sha(Path(__file__))}
def score(predictions,audits):
    q,g,e,c=[rows(PACK/name) for name in ['questions.jsonl','gold.jsonl','evidence.jsonl','cases.jsonl']]
    cases,metrics=build_scores(q,g,e,predictions,audits)
    layers=build_layers(q,g,e,predictions,audits)
    routing=sum([p['routing_observation']['dataset'],p['routing_observation']['field']]==x['expected_route'] for p,x in zip(predictions,c,strict=True))
    return cases,metrics,layers,{'routing_correct':routing,'routing_total':8,
        'name_answers_supported':sum(x['source_supported_success'] for x in cases if x['category']=='f2'),
        'preview_searches':sum(x['retrieval_called'] for x in cases if x['category']=='f3'),
        'preview_full_answers_supported':sum(x['source_supported_success'] for x in cases if x['category']=='f3'),
        'not_independent_acceptance':True}
def run(out):
    manifest=validate();before=snapshot();out=out.resolve()
    assert out.is_relative_to(ROOT/'data/hus/evaluation/runs') and not out.exists()
    out.mkdir();(out/'runner.py').write_bytes(Path(__file__).read_bytes())
    write_json(out/'input_snapshot.json',before)
    from fastapi.testclient import TestClient
    from app.hus.demo import app
    from app.hus.question_routing import question_intent
    from app.services.hus_service import get_hus_answerer
    from tools.verify_hus_e2e import EvidenceOracle
    answerer=get_hus_answerer();original=answerer.retriever;traced=TracedRetriever(original);answerer.retriever=traced
    try:
        with TestClient(app,raise_server_exceptions=False) as client:
            def execute(request):
                traced.calls.clear();route=observe_route(request['question'],question_intent)
                response=client.post('/hus/chat',json=request)
                return {**capture_response(response,traced.calls),'routing_observation':route}
            predictions=collect_run(rows(PACK/'questions.jsonl'),out,execute)
    finally:answerer.retriever=original
    # Targets are loaded only after all actual responses have been saved.
    gold,evidence=rows(PACK/'gold.jsonl'),rows(PACK/'evidence.jsonl')
    evidence_by_id={r['evidence_id']:r for r in evidence};binary={};oracle=EvidenceOracle()
    with TestClient(app,raise_server_exceptions=False) as client:
        audits=[audit_development_prediction(p,g,evidence_by_id,oracle,client,binary) for p,g in zip(predictions,gold,strict=True)]
    cases,metrics,layers,summary=score(predictions,audits)
    write_rows(out/'citation_audits.jsonl',audits);write_rows(out/'scored_cases.jsonl',cases)
    write_json(out/'layered_metrics.json',layers)
    assert snapshot()==before and validate()==manifest
    write_json(out/'report.json',{'status':'development_routing_slice_not_holdout_acceptance','recorded_at_utc':datetime.now(timezone.utc).isoformat(),
        'pack':PACK.relative_to(ROOT).as_posix(),'pack_manifest_sha256':sha(PACK/'manifest.json'),
        'summary':summary,'metrics':metrics,'source_binary_checks':binary,'inputs_unchanged_during_run':True,
        'holdout_eligible':False,'quality_scope':'Eight exposed routing failures; other gate/representation errors remain separate',
        'source_and_review_changed':False,'production_activated':False})
    write_json(out/'manifest.json',{'files_sha256':{p.name:sha(p) for p in sorted(out.iterdir()) if p.is_file()}})
    return summary
def verify(out):
    validate();m=read(out/'manifest.json')
    for name,h in m['files_sha256'].items():assert sha(out/name)==h
    cases,metrics,layers,summary=score(rows(out/'predictions.jsonl'),rows(out/'citation_audits.jsonl'))
    r=read(out/'report.json')
    assert r['pack_manifest_sha256']==sha(PACK/'manifest.json')
    assert cases==rows(out/'scored_cases.jsonl') and metrics==r['metrics'] and summary==r['summary']
    assert layers==read(out/'layered_metrics.json')
    return {'reproduced':True,'new_inference':False,'runtime_matches_recorded':runtime_hashes()==read(out/'input_snapshot.json')['runtime_sha256'],'summary':summary}
if __name__=='__main__':
    parser=argparse.ArgumentParser();mode=parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--out',type=Path);mode.add_argument('--verify-run',type=Path);args=parser.parse_args()
    print(json.dumps(run(args.out) if args.out else verify(args.verify_run),indent=2))
