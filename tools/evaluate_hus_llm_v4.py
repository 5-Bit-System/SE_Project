"""Fresh exposed L5 v4 cohort; lexical A once, unchanged rewriting of frozen A for B."""

from __future__ import annotations

import argparse
import json
import re
import time
from copy import deepcopy
from dataclasses import replace
from pathlib import Path

from app.hus.llm import HUSLLMError, HUSLLMSettings
from app.hus.llm.contracts import HUSRewriteContext
from app.hus.llm.evidence import build_evidence as build_bundle
from app.hus.llm.prompts import build_prompt
from app.schemas.hus import HUSAnswer, HUSQuestion
from tools import evaluate_hus_llm as engine
from tools.evaluate_hus_chatbot import TracedRetrieverV2, current_snapshot, load_pack
from tools.evaluate_hus_rag import digest, write_json
from tools.hus_llm_measurement import eligible, read_sealed, reserve, seal
from tools.hus_llm_v4_audit import RELEASE, RELEASE_SHA, V4EvidenceOracle, rendered_parts
from tools.hus_rag_layer_metrics import canonical_field
from tools.validate_hus_holdout import ROOT

KIND = 'hus-llm-v4-exposed-development-1.0'
EVALUATION = ROOT / 'data/hus/evaluation'
RUNS = EVALUATION / 'runs'


def build_pack():
    oracle = V4EvidenceOracle()
    old = [load_pack(EVALUATION / name) for name in ('diagnostic_dev_v1', 'a2_contracts_v1')]
    cases = []
    for index, (question, target) in enumerate(engine.select_cases(*old), 1):
        qid = f'L5V4-Q{index:03d}'
        request, gold = deepcopy(question['request']), deepcopy(target)
        gold['question_id'] = qid
        gold['expected_field'] = canonical_field(gold.get('expected_field', ''))
        request['allow_llm_rewrite'] = False
        case = {'question_id': qid, 'request': request, 'gold': gold,
                'inherited_exposed_question_id': question['question_id'], 'gold_evidence': []}
        if gold['category'] == 'f3':
            major = request['major']
            if gold['expected_field'] == 'content':
                options = [(len(part), row['record_id'], number, part, row)
                           for row in oracle.f3_records.values() if row['major'] == major
                           for number, part in enumerate(rendered_parts(row, 'content')[1:])]
                _, _, number, text, source = max(options, key=lambda item: item[:3])
                title = source['profile']['units'][number]['title']
                request.update(question=f"Nội dung {source['course_code']}: {title}?",
                               course_code=source['course_code'], dataset='f3', field='content')
                case['long_unit'] = {'record_id': source['record_id'], 'unit_index': number,
                                     'title': title, 'source_chars': len(text)}
            else:
                code = re.search(r'\b[A-Z]{3}\d{4}[A-Z]?\b', request['question'])[0]
                source = next(r for r in oracle.f3_records.values()
                              if r['course_code'] == code and r['major'] == major)
                text = rendered_parts(source, 'objectives')[0]
            gold.update(expected_answer=text, evidence_ids=[qid + '-source'])
            case['gold_evidence'] = [{'evidence_id': qid + '-source', 'value': text,
                'source_ref': {'path': f'data/hus/rag/releases/{RELEASE}/f3_records.jsonl',
                               'sha256': digest(oracle.root / 'f3_records.jsonl'),
                               'record_id': source['record_id'], 'field': gold['expected_field']}}]
        else:
            inventory = {e['evidence_id']: e for pack in old for e in pack['evidence']}
            case['gold_evidence'] = [deepcopy(inventory[eid]) for eid in gold.get('evidence_ids', [])]
            for entry in case['gold_evidence']:
                entry['inheritance_note'] = 'Exposed v3 F1/F2 source unchanged in v4; not independent gold.'
        cases.append(case)
    return {'schema_version': KIND, 'release': {'release_id': RELEASE, 'release_sha256': RELEASE_SHA},
            'model': engine.MODEL, 'retrieval': 'lexical', 'holdout_eligible': False,
            'reviewer_kind': 'ai', 'actual_human_reviews': 0,
            'selection_policy': '24 positives/12 controls; prior F1/F2/objectives requests; longest rendered '
                                'non-overview F3 content unit per major, ties by record_id/unit_index; no outcome selection.',
            'source_inputs': {k: v for pack in old for k, v in pack['input_sha256'].items()}, 'cases': cases}


def save_pack(out):
    out = Path(out).resolve()
    if not out.is_relative_to(EVALUATION) or out.is_relative_to(RUNS):
        raise ValueError('Source pack must be a new evaluation directory outside runs')
    document = build_pack()
    reserve(out)
    write_json(out / 'pack.json', document)
    seal(out)
    return document


def checked_pack(path):
    path = Path(path).resolve()
    if not path.is_relative_to(EVALUATION) or path.is_relative_to(RUNS):
        raise ValueError('Invalid v4 source pack path')
    saved = read_sealed(path)
    if set(saved) != {'pack.json'} or saved['pack.json'] != build_pack():
        raise ValueError('Source pack differs from pinned deterministic v4 cohort')
    return saved['pack.json']


def current_pins(pack):
    snapshot = current_snapshot()
    snapshot['evaluators'].update({f'tools/{name}': digest(ROOT / 'tools' / name) for name in (
        'evaluate_hus_llm.py', 'hus_llm_measurement.py', 'evaluate_hus_llm_v4.py', 'hus_llm_v4_audit.py')})
    path = Path(pack).resolve()
    snapshot['v4_source_pack'] = {p.relative_to(ROOT).as_posix(): digest(p) for p in sorted(path.iterdir())}
    snapshot['measurement'] = {'model': engine.MODEL, 'base_url': engine.BASE_URL, 'retrieval': 'lexical',
                               'prompt_chars': 12000, 'raw_output_chars': 8192, 'output_tokens': 1024,
                               'f1_f3_protocol': 'hus-llm-document-v3', 'f2_protocol': 'hus-llm-evidence-v1',
                               'max_leaves': 64, 'max_units': 128, 'max_leaf_chars': 3000}
    return snapshot


def prepare(pack, out):
    from app.hus.answering import HUSAnswerer
    from app.hus.chat import chat
    from app.hus.rag_loader import HUSRAGData

    source = checked_pack(pack)
    pins = current_pins(pack)
    answerer, oracle = HUSAnswerer(HUSRAGData.load_current()), V4EvidenceOracle()
    assert answerer.data.release_identity['release_sha256'] == RELEASE_SHA
    tracer = TracedRetrieverV2(answerer.retriever)
    answerer.retriever = tracer
    effective = []

    class Capture:
        programs = answerer.programs

        def answer(self, request):
            effective.append(request.model_dump(mode='json'))
            return answerer.answer(request)

    records = []
    for case in source['cases']:
        request = HUSQuestion.model_validate(case['request'])
        tracer.calls.clear()
        effective.clear()
        start = time.perf_counter()
        base = chat(request, Capture()).model_dump(mode='json')
        record = {**deepcopy(case), 'effective_request': effective[0] if effective else request.model_dump(mode='json'),
                  'baseline': base, 'baseline_latency_ms': (time.perf_counter() - start) * 1000,
                  'retrieval_calls': deepcopy(tracer.calls)}
        audit = oracle.audit(record)
        if not audit['passed']:
            raise ValueError(f"Source audit failed before generation: {case['question_id']} ({audit['error']})")
        record['source_audit'] = audit
        records.append(record)
    if current_pins(pack) != pins:
        raise ValueError('Pins changed during v4 preparation')
    def unchanged_pins():
        if current_pins(pack) != pins:
            raise ValueError('Pins changed after baseline preparation')
        return pins

    return engine.save_prepared(records, out, pin_reader=unchanged_pins, provenance={
        'kind': 'AI-authored exposed v4 development', 'source_pack': Path(pack).resolve().relative_to(ROOT).as_posix(),
        'source_pack_manifest_sha256': digest(Path(pack) / 'manifest.json'), 'release': source['release'],
        'review_scope': 'Requested intent and selected evidence; not exhaustive course retrieval acceptance.'})


def validate_prepared(document):
    pack = (ROOT / document['provenance']['source_pack']).resolve()
    source = checked_pack(pack)
    if digest(pack / 'manifest.json') != document['provenance']['source_pack_manifest_sha256']:
        raise ValueError('Prepared source pack binding changed')
    records = document['records']
    if (len(records) != len(source['cases']) or len(records) != 36
            or document['model'] != source['model'] or document['base_url'] != engine.BASE_URL
            or document['provenance']['release'] != source['release']):
        raise ValueError('Prepared cohort/model/release differs from source pack')
    oracle = V4EvidenceOracle()
    for record, case in zip(records, source['cases'], strict=True):
        if any(record.get(k) != v for k, v in case.items()):
            raise ValueError('Prepared case differs from source pack')
        original = HUSQuestion.model_validate(case['request'])
        effective = HUSQuestion.model_validate(record['effective_request'])
        if (effective.question != original.question or effective.major != original.major
                or effective.allow_llm_rewrite or effective.allow_generated_reference != original.allow_generated_reference
                or (original.version is not None and effective.version != original.version)):
            raise ValueError('Prepared effective request differs from frozen intent')
        audit = oracle.audit(record)
        if not audit['passed'] or record['source_audit'] != audit:
            raise ValueError('Prepared baseline fails independent source audit')
        expected_prompt = {}
        if eligible(record):
            context = HUSRewriteContext(question=effective.model_copy(update={'allow_llm_rewrite': True}),
                                        answer=HUSAnswer.model_validate(record['baseline']['hus_answer']),
                                        requested_model=document['model'])
            try:
                prompt = build_prompt(build_bundle(context))
                expected_prompt = {'sha256': prompt.sha256, 'chars': len(prompt.system) + len(prompt.user)}
            except HUSLLMError as error:
                expected_prompt = {'error': error.code}
        if record['prompt'] != expected_prompt:
            raise ValueError('Prepared prompt differs from frozen baseline')
    return pack


def run(prepared, out, settings, **kwargs):
    document = read_sealed(prepared)['prepared.json']
    pack = validate_prepared(document)
    return engine.run(prepared, out, settings, pin_reader=lambda: current_pins(pack), **kwargs)


def payloads(prepared, out):
    document = read_sealed(prepared)['prepared.json']
    validate_prepared(document)
    result = []
    for record in document['records']:
        if not eligible(record):
            continue
        ctx = HUSRewriteContext(
            question=HUSQuestion.model_validate(record['effective_request']).model_copy(update={'allow_llm_rewrite': True}),
            answer=HUSAnswer.model_validate(record['baseline']['hus_answer']), requested_model=document['model'])
        entry = {'question_id': record['question_id']}
        try:
            prompt = build_prompt(build_bundle(ctx))
            assert prompt.sha256 == record['prompt']['sha256']
            entry.update(prompt_sha256=prompt.sha256, prompt_chars=len(prompt.system) + len(prompt.user),
                         body={'model': document['model'], 'messages': prompt.messages,
                               'max_tokens': 1024, 'stream': False})
        except HUSLLMError as error:
            entry['preflight_fallback'] = error.code
        result.append(entry)
    out = reserve(out)
    write_json(out / 'payloads.json', result)
    seal(out)
    return {'positive_cases': len(result), 'possible_http_calls': sum('body' in r for r in result),
            'prompt_budget_fallbacks': sum('body' not in r for r in result), 'raw_headers_or_keys': False}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument('--build-pack', action='store_true')
    action.add_argument('--prepare', type=Path, metavar='PACK')
    action.add_argument('--payloads', type=Path, metavar='PREPARED')
    action.add_argument('--run', type=Path, metavar='PREPARED')
    action.add_argument('--replay', type=Path)
    action.add_argument('--score', type=Path)
    parser.add_argument('--out', type=Path)
    parser.add_argument('--review', type=Path)
    parser.add_argument('--live', action='store_true')
    parser.add_argument('--env-file', type=Path)
    parser.add_argument('--max-calls', type=int, default=24)
    args = parser.parse_args(argv)
    if args.replay:
        result = engine.replay(args.replay)
    elif not args.out:
        parser.error('--out is required')
    elif args.build_pack:
        result = {'prepared_cases': len(save_pack(args.out)['cases'])}
    elif args.payloads:
        if not args.out.resolve().is_relative_to(ROOT / 'backups'):
            parser.error('Payload audit output must be a new backups directory')
        result = payloads(args.payloads, args.out)
    else:
        if not args.out.resolve().is_relative_to(RUNS) or args.out.resolve() == RUNS:
            parser.error('Run output must be a new directory under evaluation/runs')
        if args.prepare:
            result = {'prepared_cases': len(prepare(args.prepare, args.out)['records'])}
        elif args.score:
            if not args.review:
                parser.error('--score requires --review')
            result = engine.score(args.score, args.review, args.out)
        else:
            if not args.live or not args.env_file:
                parser.error('--run requires explicit --live and --env-file')
            from dotenv import dotenv_values

            values = {k: v for k, v in dotenv_values(args.env_file).items() if k.startswith('HUS_LLM_')}
            values['HUS_LLM_ENABLED'] = 'true'
            settings = replace(HUSLLMSettings.from_env(values), enabled=True)
            result = run(args.run, args.out, settings, allow_live=True, max_calls=args.max_calls)
    print(json.dumps(result.get('metrics', result), ensure_ascii=True))


if __name__ == '__main__':
    main()
