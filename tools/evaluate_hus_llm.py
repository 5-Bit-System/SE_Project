"""L5 frozen paired RAG/Gemini measurement; live collection is explicitly opt-in."""

from __future__ import annotations

import argparse
import json
import os
import re
import time
import uuid
from contextlib import contextmanager
from dataclasses import replace
from pathlib import Path

import httpx

from app.hus.llm import HUSLLMClient, HUSLLMError, HUSLLMSettings
from app.hus.llm.adapter import HUSGroundedAdapter
from app.hus.llm.contracts import HUSRewriteContext
from app.hus.llm.diagnostics import HUSLLMDiagnostic, envelope_diagnostic
from app.hus.llm.evidence import build_evidence as build_bundle
from app.hus.llm.generation import generate_reply
from app.hus.llm.prompts import build_prompt
from app.hus.llm.usage import HUSUsage
from app.schemas.hus import HUSAnswer, HUSQuestion
from tools.evaluate_hus_chatbot import current_snapshot, load_pack
from tools.evaluate_hus_rag import digest, write_json
from tools.hus_llm_measurement import (
    SCHEMA,
    eligible,
    metrics,
    read_sealed,
    reserve,
    review_template,
    seal,
    semantic_scores,
)
from tools.hus_rag_layer_metrics import canonical_field
from tools.hus_rag_metrics_v2 import digest_json
from tools.validate_hus_holdout import ROOT

MODEL = 'gemini-3.5-flash-lite'
BASE_URL = 'https://generativelanguage.googleapis.com/v1beta/openai'


def current_pins():
    snapshot = current_snapshot()
    snapshot['evaluators'].update({f'tools/{name}': digest(ROOT / 'tools' / name)
        for name in ('evaluate_hus_llm.py', 'hus_llm_measurement.py')})
    snapshot['source_packs'] = {name: checksum for pack in ('diagnostic_dev_v1', 'a2_contracts_v1')
        for name, checksum in load_pack(ROOT / 'data/hus/evaluation' / pack)['input_sha256'].items()}
    snapshot['llm_protocol'] = {'f1_f3': 'hus-llm-document-v3', 'f2': 'hus-llm-evidence-v1',
        'prompt_chars': 12000, 'raw_output_chars': 8192, 'output_tokens': 1024,
        'max_leaves': 64, 'max_units': 128, 'max_leaf_chars': 3000}
    return snapshot


def save_prepared(records, out, *, provenance, model=MODEL, pin_reader=None):
    read_pins = pin_reader or current_pins
    pins = read_pins()
    ids = [r['question_id'] for r in records]
    if not records or len(ids) != len(set(ids)):
        raise ValueError('Prepared IDs must be unique and nonempty')
    for record in records:
        request = HUSQuestion.model_validate(record['effective_request'])
        if request.allow_llm_rewrite or record['request'].get('allow_llm_rewrite', False):
            raise ValueError('Baseline must have rewrite disabled')
        record['prompt'] = {}
        if eligible(record):
            ctx = HUSRewriteContext(question=request.model_copy(update={'allow_llm_rewrite': True}),
                    answer=HUSAnswer.model_validate(record['baseline']['hus_answer']), requested_model=model)
            try:
                prompt = build_prompt(build_bundle(ctx))
                record['prompt'] = {'sha256': prompt.sha256, 'chars': len(prompt.system) + len(prompt.user)}
            except HUSLLMError as error:
                record['prompt'] = {'error': error.code}
    if read_pins() != pins:
        raise ValueError('Pins changed while preparing prompts')
    out = reserve(out)
    prepared = {'schema_version': SCHEMA, 'kind': 'prepared', 'model': model, 'base_url': BASE_URL,
                'pins': pins, 'provenance': provenance, 'records': records,
                'holdout_eligible': False, 'actual_human_reviews': 0}
    write_json(out / 'prepared.json', prepared)
    if read_pins() != pins:
        raise ValueError('Pins changed during save; prepared artifact remains unsealed')
    seal(out)
    return prepared


class Budget:
    def __init__(self, max_calls, min_interval, *, clock=time.monotonic, sleep=time.sleep):
        if type(max_calls) is not int or not 0 <= max_calls <= 24 or not 0 <= min_interval <= 60:
            raise ValueError('Evaluation budget must be 0..24 calls and 0..60 seconds spacing')
        self.max_calls, self.min_interval = max_calls, min_interval
        self.clock, self.sleep = clock, sleep
        self.attempts, self.last, self.quota = 0, None, False

    def reserve(self):
        if self.quota or self.attempts >= self.max_calls:
            raise HUSLLMError('provider_error')
        wait = max(0, self.min_interval - (self.clock() - self.last)) if self.last is not None else 0
        if wait:
            self.sleep(wait)
        self.last = self.clock()
        self.attempts += 1
        return wait * 1000


class ObservedTransport(httpx.BaseTransport):
    def __init__(self, inner, trace, budget, secret):
        self.inner, self.trace, self.budget, self.secret = inner, trace, budget, secret

    def handle_request(self, request):
        response = self.inner.handle_request(request)
        self.trace['http_status'] = response.status_code
        if response.status_code == 429:
            self.budget.quota = True
        try:
            response.read()
        except BaseException:
            response.close()
            raise
        if 200 <= response.status_code < 300:
            try:
                body = response.json()
                self.trace['provider_envelope'] = envelope_diagnostic(body).model_dump(exclude_none=True)
                model = body.get('model')
                if (isinstance(model, str) and re.fullmatch(r'[A-Za-z0-9._:/-]{1,100}', model)
                        and self.secret not in model):
                    self.trace['actual_model'] = model
                usage = body.get('usage')
                if isinstance(usage, dict):
                    counters = {k: v for k, v in usage.items() if k in HUSUsage.model_fields}
                    if counters:
                        self.trace['usage'] = HUSUsage.model_validate(counters).model_dump(exclude_none=True)
            except (ValueError, TypeError, AttributeError):
                pass  # Preserve unknown rather than invent counters/model from requested configuration.
        return response

    def close(self):
        self.inner.close()


class ObservedClient:
    def __init__(self, settings, trace, budget, factory):
        self.settings, self.trace, self.budget, self.factory = settings, trace, budget, factory

    def complete_result(self, messages):
        if digest_json(messages) != self.trace['prompt_sha256']:
            raise ValueError('Provider messages differ from frozen prompt')
        try:
            self.trace['pacing_ms'] = self.budget.reserve()
        except HUSLLMError:
            self.trace['evaluation_stop'] = 'quota' if self.budget.quota else 'call_budget'
            raise
        self.trace['attempted'] = True
        started = time.perf_counter()
        try:
            transport = ObservedTransport(self.factory(), self.trace, self.budget, self.settings.api_key)
            return HUSLLMClient(self.settings, transport=transport).complete_result(messages)
        except HUSLLMError as error:
            self.trace['error'] = error.code
            raise
        finally:
            self.trace['provider_ms'] = (time.perf_counter() - started) * 1000


class ObservedAdapter(HUSGroundedAdapter):
    def __call__(self, context):
        try:
            return super().__call__(context)
        except HUSLLMError as error:
            if error.diagnostic is not None:
                safe = HUSLLMDiagnostic.model_validate(error.diagnostic.model_dump())
                self.client.trace['validation'] = safe.model_dump(exclude_none=True)
            raise


@contextmanager
def evaluation_environment(settings):
    values = {'HUS_LLM_ENABLED': 'true', 'HUS_LLM_API_KEY': settings.api_key,
              'HUS_LLM_BASE_URL': settings.base_url, 'HUS_LLM_MODEL': settings.model}
    old = {key: os.environ.get(key) for key in values}
    try:
        os.environ.update(values)
        yield
    finally:
        for key, value in old.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def run(prepared, out, settings, *, transport_factory=None, allow_live=False, max_calls=24, min_interval=5,
        pin_reader=None):
    if transport_factory is None and not allow_live:
        raise ValueError('Explicit live authorization is required')
    if allow_live and min_interval < 5:
        raise ValueError('Live spacing must be at least 5 seconds')
    document = read_sealed(prepared)['prepared.json']
    if (not settings.enabled or settings.model != document['model'] or settings.base_url != BASE_URL
            or settings.api_key in settings.model):
        raise ValueError('Enabled Google configuration/model differs from prepared run')
    read_pins = pin_reader or current_pins
    if read_pins() != document['pins']:
        raise ValueError('Code/source/environment pins changed before collection')
    budget = Budget(max_calls, min_interval)
    out = reserve(out)
    write_json(out / 'prepared.json', document)
    observations = []
    factory = transport_factory or (lambda: httpx.HTTPTransport(retries=0, trust_env=False))
    with evaluation_environment(settings):
        for record in document['records']:
            trace = {'attempted': False, 'prompt_sha256': record['prompt'].get('sha256'),
                     'actual_model': None, 'usage': None, 'http_status': None,
                     'error': None, 'evaluation_stop': None, 'provider_ms': 0.0, 'pacing_ms': 0.0}
            request = HUSQuestion.model_validate(record['effective_request']).model_copy(update={'allow_llm_rewrite': True})
            base = record['baseline']
            answer = HUSAnswer.model_validate(base['hus_answer']) if base.get('hus_answer') else None
            adapter = ObservedAdapter(ObservedClient(settings, trace, budget, factory))
            start = time.perf_counter()
            reply, generation = generate_reply(request, answer, base['reply'], rewriter=adapter)
            elapsed = (time.perf_counter() - start) * 1000
            b = {**base, 'reply': reply, 'generation': generation.model_dump()}
            observations.append({'question_id': record['question_id'], 'prepared_case_sha256': digest_json(record),
                'a': base, 'b': b, 'trace': trace, 'rewrite_ms': max(0, elapsed - trace['pacing_ms'])})
            # Checkpoint each completed pair, never overwrite an older measurement.
            write_json(out / 'observations.json', observations)
    if read_pins() != document['pins']:
        raise ValueError('Code/source/environment pins changed during collection; run remains unsealed')
    measured = metrics(document['records'], observations)
    run_id = uuid.uuid4().hex
    report = {'schema_version': SCHEMA, 'kind': 'measurement', 'measurement_id': run_id,
        'prepared_sha256': digest_json(document), 'requested_model': settings.model, 'base_url': settings.base_url,
        'transport': 'live_google' if transport_factory is None else 'synthetic_transport',
        'max_calls': max_calls, 'min_interval_seconds': min_interval,
        'collection_complete': not any(o['trace']['evaluation_stop'] for o in observations),
        'metrics': measured, 'semantic_review': 'pending', 'recommended_enabled': False,
        'holdout_eligible': False, 'actual_human_reviews': 0,
        'latency_definition': 'Local baseline; incremental validated rewrite/provider wall time excludes evaluation pacing. Not production SLO.'}
    write_json(out / 'report.json', report)
    write_json(out / 'review_template.json', review_template(run_id, document['records'], observations))
    seal(out)
    return report


def replay(folder):
    saved = read_sealed(folder)
    report, document = saved['report.json'], saved['prepared.json']
    observations = saved['observations.json']
    expected = {'schema_version': SCHEMA, 'requested_model': document['model'],
                'base_url': document['base_url'], 'actual_human_reviews': 0,
                'recommended_enabled': False, 'holdout_eligible': False,
                'collection_complete': not any(o['trace']['evaluation_stop'] for o in observations)}
    if (any(type(report.get(k)) is not type(v) or report[k] != v for k, v in expected.items())
            or report.get('kind') not in {'measurement', 'review_score'}
            or report.get('transport') not in {'live_google', 'synthetic_transport'}
            or report.get('semantic_review') != ('exact_response_bound_ai'
                if report['kind'] == 'review_score' else 'pending')):
        raise ValueError('Cached measurement metadata differs')
    Budget(report['max_calls'], report['min_interval_seconds'])
    if (sum(o['trace']['attempted'] for o in observations) > report['max_calls']
            or (report['transport'] == 'live_google' and report['min_interval_seconds'] < 5)):
        raise ValueError('Cached measurement budget metadata differs')
    if (report['prepared_sha256'] != digest_json(document)
            or metrics(document['records'], observations) != report['metrics']
            or review_template(report['measurement_id'], document['records'], observations) != saved['review_template.json']):
        raise ValueError('Cached measurement/report binding differs')
    if report.get('kind') == 'review_score':
        result = semantic_scores(document['records'], observations, saved['review_template.json'], saved['review.json'])
        if result != report['semantic']:
            raise ValueError('Cached semantic scores differ')
    return {'reproduced': True, 'new_provider_calls': 0, 'new_retrieval_calls': 0,
            'metrics': report['metrics']}


def score(folder, review_path, out):
    replay(folder)
    saved = read_sealed(folder)
    review = json.loads(Path(review_path).read_bytes())
    semantic = semantic_scores(saved['prepared.json']['records'], saved['observations.json'], saved['review_template.json'], review)
    out = reserve(out)
    report = {**saved['report.json'], 'kind': 'review_score', 'semantic': semantic,
              'semantic_review': 'exact_response_bound_ai', 'recommended_enabled': False,
              'source_manifest_sha256': digest(Path(folder) / 'manifest.json')}
    for name, value in saved.items():
        write_json(out / name, report if name == 'report.json' else value)
    write_json(out / 'review.json', review)
    seal(out)
    return report


def select_cases(dev, contracts):
    pairs = list(zip(dev['questions'], dev['gold'], strict=True))
    selected = []
    preferences = {'f1': ['introduction', 'careers'], 'f2': ['credits', 'prerequisites'],
                   'f3': ['content', 'objectives']}
    majors = sorted({q['request']['major'] for q, _ in pairs})
    for major in majors:
        for family, fields in preferences.items():
            group = [(q, g) for q, g in pairs if q['request']['major'] == major and g['category'] == family]
            chosen = []
            for field in fields:
                match = next(((q, g) for q, g in group if canonical_field(g['expected_field']) == field
                              and (q, g) not in chosen), None)
                if match:
                    chosen.append(match)
            chosen += [p for p in group if p not in chosen][:2 - len(chosen)]
            if len(chosen) != 2:
                raise ValueError('Missing planned major/family cell')
            selected += chosen
        controls = ['opt_in_required', 'missing_evidence' if majors.index(major) < 2 else 'out_of_scope']
        selected += [next((q, g) for q, g in pairs if q['request']['major'] == major and g['category'] == category)
                     for category in controls]
    selected += [(q, g) for q, g in zip(contracts['questions'], contracts['gold'], strict=True)
                 if g['category'] == 'clarification_required'][:2]
    for i, text in enumerate(['Xin chào', 'Bạn có thể làm gì?']):
        selected.append(({'question_id': f'L5-BASIC-{i + 1}', 'request': {'question': text, 'major': 'data_science'}},
                         {'question_id': f'L5-BASIC-{i + 1}', 'category': 'basic_chat', 'evidence_ids': [],
                          'expected_status': 'basic_chat', 'author': 'AI-authored exposed control'}))
    return selected


def prepare(out):
    # Freeze selected targets before generating B; never change old evaluation packs.
    from fastapi.testclient import TestClient

    from app.hus.answering import HUSAnswerer
    from app.hus.chat import chat
    from app.hus.demo import app
    from app.hus.rag_loader import HUSRAGData
    from tools.evaluate_hus_chatbot import TracedRetrieverV2
    from tools.hus_chatbot_source_audit import SourceAuditor

    dev = load_pack(ROOT / 'data/hus/evaluation/diagnostic_dev_v1')
    contracts = load_pack(ROOT / 'data/hus/evaluation/a2_contracts_v1')
    selected = select_cases(dev, contracts)
    before = current_pins()
    answerer = HUSAnswerer(HUSRAGData.load_current())
    if any(answerer.data.release_identity.get(k) != v for pack in (dev, contracts)
           for k, v in pack['expected_release'].items()):
        raise ValueError('Prepared release differs from frozen source packs')
    traced = TracedRetrieverV2(answerer.retriever)
    answerer.retriever = traced
    effective = []

    class Capture:
        programs = answerer.programs

        def answer(self, request):
            effective.append(request.model_dump())
            return answerer.answer(request)

    evidence = {e['evidence_id']: e for pack in (dev, contracts) for e in pack['evidence']}
    auditor, records = SourceAuditor(), []
    with TestClient(app) as client:
        for q, gold in selected:
            request = HUSQuestion.model_validate(q['request']).model_copy(update={'allow_llm_rewrite': False})
            traced.calls.clear()
            effective.clear()
            start = time.perf_counter()
            base = chat(request, Capture()).model_dump()
            latency = (time.perf_counter() - start) * 1000
            obs = {'question_id': q['question_id'], 'request': request.model_dump(),
                   'http_status': 200, 'response': base, 'retrieval_calls': list(traced.calls)}
            audit = auditor.audit(obs, gold, evidence, client) if gold['category'] != 'basic_chat' else {'passed': True, 'kind': 'basic_chat_no_sources'}
            records.append({'question_id': q['question_id'], 'request': request.model_dump(),
                'effective_request': effective[0] if effective else request.model_dump(), 'gold': gold,
                'gold_evidence': [evidence[eid] for eid in gold.get('evidence_ids', [])],
                'baseline': base, 'baseline_latency_ms': latency,
                'retrieval_calls': list(traced.calls), 'source_audit': audit})
    if current_pins() != before:
        raise ValueError('Input pins changed during preparation')
    return save_prepared(records, out, provenance={'kind': 'AI-selected exposed development',
        'selection_policy': preferences_description(), 'source_inputs': {**dev['input_sha256'], **contracts['input_sha256']},
        'release': answerer.data.release_identity, 'actual_human_reviews': 0})


def preferences_description():
    return '2 per major/family preferring intro/careers, credits/prerequisites, content/objectives; 8 negative + 2 clarification + 2 basic controls'


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument('--prepare', action='store_true')
    action.add_argument('--run', type=Path)
    action.add_argument('--replay', type=Path)
    action.add_argument('--score', type=Path)
    parser.add_argument('--out', type=Path)
    parser.add_argument('--review', type=Path)
    parser.add_argument('--live', action='store_true')
    parser.add_argument('--env-file', type=Path)
    parser.add_argument('--max-calls', type=int, default=24)
    args = parser.parse_args(argv)
    runs = (ROOT / 'data/hus/evaluation/runs').resolve()
    if args.out and (args.out.resolve() == runs or not args.out.resolve().is_relative_to(runs)):
        parser.error('--out must be a fresh directory under data/hus/evaluation/runs')
    if args.replay:
        result = replay(args.replay)
    elif not args.out:
        parser.error('--out is required for fresh artifacts')
    elif args.prepare:
        result = {'prepared_cases': len(prepare(args.out)['records'])}
    elif args.score:
        if not args.review:
            parser.error('--score requires --review')
        result = score(args.score, args.review, args.out)
    else:
        if not args.live or not args.env_file:
            parser.error('--run requires --live and --env-file; no implicit provider call')
        from dotenv import dotenv_values

        values = {k: v for k, v in dotenv_values(args.env_file).items() if k.startswith('HUS_LLM_')}
        values['HUS_LLM_ENABLED'] = 'true'
        settings = replace(HUSLLMSettings.from_env(values), enabled=True)
        result = run(args.run, args.out, settings, allow_live=True, max_calls=args.max_calls)
    print(json.dumps(result.get('metrics', result.get('semantic', result)), ensure_ascii=True))


if __name__ == '__main__':
    main()
