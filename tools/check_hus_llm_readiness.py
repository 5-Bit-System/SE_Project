"""Read-only L6 evidence assessment. Never enables a flag or calls a provider."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from tools.evaluate_hus_llm import BASE_URL, MODEL, current_pins, read_sealed, replay
from tools.evaluate_hus_rag import digest, write_json
from tools.hus_llm_measurement import reserve
from tools.hus_rag_metrics_v2 import digest_json
from tools.validate_hus_holdout import ROOT


def evidence_pins(prepared: dict) -> tuple[dict, dict]:
    """Bind v4 source identity without rebuilding historical prompts or running RAG."""
    provenance = prepared.get('provenance', {})
    is_v4 = ('v4_source_pack' in prepared['pins']
             or 'source_pack' in provenance or 'v4' in provenance.get('kind', ''))
    if not is_v4:
        return current_pins(), {'evidence_version': 'legacy'}
    from tools import evaluate_hus_llm_v4 as v4

    if (provenance.get('kind') != 'AI-authored exposed v4 development'
            or not isinstance(provenance.get('source_pack'), str)):
        raise ValueError('Missing or unknown v4 source pack provenance')
    pack = (ROOT / provenance['source_pack']).resolve()
    source = v4.checked_pack(pack)
    if (digest(pack / 'manifest.json') != provenance.get('source_pack_manifest_sha256')
            or provenance.get('release') != source['release']):
        raise ValueError('V4 source pack/release binding changed')
    records = prepared['records']
    if (len(records) != len(source['cases']) or prepared['model'] != source['model']
            or prepared['base_url'] != BASE_URL):
        raise ValueError('V4 prepared cohort/model differs from pack')
    oracle = v4.V4EvidenceOracle()
    for record, case in zip(records, source['cases'], strict=True):
        if any(record.get(key) != value for key, value in case.items()):
            raise ValueError('V4 prepared case differs from source pack')
        original = v4.HUSQuestion.model_validate(case['request'])
        effective = v4.HUSQuestion.model_validate(record['effective_request'])
        if (effective.question != original.question or effective.major != original.major
                or effective.allow_llm_rewrite
                or effective.allow_generated_reference != original.allow_generated_reference
                or (original.version is not None and effective.version != original.version)):
            raise ValueError('V4 effective request differs from frozen cohort intent')
        audit = oracle.audit(record)
        if not audit['passed'] or record.get('source_audit') != audit:
            raise ValueError('V4 prepared baseline fails source audit')
    # Prompt hashes remain bound to the saved responses by replay(). Comparing
    # current pins below blocks reuse after a protocol/code/source change, rather
    # than trying to validate an old prompt with the new prompt builder.
    return v4.current_pins(pack), {
        'evidence_version': 'v4', 'source_pack': pack.relative_to(ROOT).as_posix(),
        'source_pack_manifest_sha256': digest(pack / 'manifest.json'),
        'source_release': source['release'],
    }


def assess(folder: Path, *, model: str = MODEL) -> dict:
    """Only verified, current, live, semantically reviewed evidence can qualify.

    Qualifying means ready for an operator to review alongside rollback and
    latency acceptance, never permission to change a running server's flags.
    """
    replay(folder)  # Validate exact pairs, targets, review and recomputed metrics first.
    saved = read_sealed(folder)
    report, prepared = saved['report.json'], saved['prepared.json']
    metrics = report['metrics']
    reasons, blocked = set(), []
    reviewed = report['kind'] == 'review_score' and report['semantic_review'] == 'exact_response_bound_ai'
    if not reviewed:
        reasons.add('content_review_missing')
    if report['transport'] != 'live_google':
        reasons.add('no_live_measurement')
    if report['requested_model'] != model:
        reasons.add('requested_model_changed')
    if not metrics['actual_models'] or set(metrics['actual_models']) != {model}:
        reasons.add('observed_model_changed')
    if report.get('base_url') != BASE_URL:
        reasons.add('google_https_endpoint_required')
    pins, evidence = evidence_pins(prepared)
    if pins != prepared['pins']:
        reasons.add('pins_changed')
    if not report['collection_complete'] or metrics['eligible_not_attempted']:
        reasons.add('collection_incomplete')
    if not metrics['used'] or not metrics['provider_requests']:
        reasons.add('no_generated_output')
    for family in ('f1', 'f2', 'f3'):
        if not metrics['by_family'].get(family, {}).get('used', 0):
            reasons.add('no_used_output_' + family)
    for key, reason in [('source_audit_failures', 'source_audit_failed'),
                        ('control_status_mismatches', 'control_contract_failed'),
                        ('baseline_false_refusals', 'positive_answer_missing')]:
        if metrics[key]:
            reasons.add(reason)
    semantic = report.get('semantic', {})
    used_review = semantic.get('used_only', {})
    if used_review.get('count') != metrics['used']:
        reasons.add('used_review_incomplete')
    if used_review.get('b_entailment_pass') != metrics['used']:
        reasons.add('generated_entailment_failed')
    if used_review.get('b_completeness_pass') != metrics['used']:
        reasons.add('generated_completeness_failed')
    final_review = semantic.get('all_positive', {})
    final_count = final_review.get('count', 0)
    for dimension in ('entailment', 'completeness'):
        if not final_count or final_review.get('b_' + dimension + '_pass') != final_count:
            reasons.add('final_' + dimension + '_failed')

    observations = {o['question_id']: o for o in saved['observations.json']}
    gain = 0
    for row in saved.get('review.json', {}).get('cases', []):
        used = observations[row['question_id']]['b']['generation']['used']
        arm = 'generated' if used else 'fallback'
        for key, prefix in [('b_entailment', 'unsupported_'), ('b_completeness', 'incomplete_')]:
            if row[key] == 'fail':
                blocked.append({'question_id': row['question_id'], 'reason': prefix + arm + '_answer'})
        if not used:
            continue  # Check fallback safety, but never credit it as generated success/gain.
        supported = row['b_entailment'] == row['b_completeness'] == 'pass'
        gain += supported and row['readability'] == 'better'
        if row['readability'] == 'worse':
            reasons.add('readability_regressed')
    if not gain:
        reasons.add('no_supported_readability_gain')
    latency = metrics['latency']['rewrite_used']
    samples = [latency.get('p50_ms'), latency.get('p95_ms')]
    if (latency.get('count') != metrics['used'] or not metrics['used']
            or any(type(v) not in {int, float} or not math.isfinite(v) or v < 0 for v in samples)
            or (all(type(v) in {int, float} for v in samples) and samples[1] < samples[0])):
        reasons.add('latency_unavailable')
    qualifies = not reasons and not blocked
    return {'schema_version': 'hus-llm-readiness-1.0', **evidence,
        'scope': 'L5 evidence readiness only; operator rollback/latency acceptance remains separate',
        'source_manifest_sha256': digest(Path(folder) / 'manifest.json'),
        'assessor_sha256': digest(Path(__file__)),
        'recorded_pins_sha256': digest_json(prepared['pins']), 'current_pins_sha256': digest_json(pins),
        'requested_model': model, 'observed_models': metrics['actual_models'],
        'eligible_for_manual_acceptance': qualifies,
        'recommended_action': 'operator_review_required' if qualifies else 'keep_disabled',
        'activation_performed': False, 'changes_environment': False,
        'new_provider_calls': 0, 'new_retrieval_calls': 0,
        'reasons': sorted(reasons), 'blocked_cases': blocked,
        'used': metrics['used'], 'fallback': metrics['fallback'], 'provider_requests': metrics['provider_requests'],
        'token_usage': metrics['token_usage'], 'used_latency': latency,
        'fallback_latency': metrics['latency'].get('rewrite_fallback'),
        'fallback_reasons': metrics.get('fallback_reasons', {}),
        'supported_complete_readability_gains': gain,
        'reviewer_kind': semantic.get('reviewer_kind'), 'actual_human_reviews': report['actual_human_reviews'],
        'independent_holdout_accepted': False,
        'limits': ['No production SLO or total20s deadline inferred.',
                   'Evidence assessment does not perform activation or replace operator acceptance.']}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--review-run', required=True, type=Path)
    parser.add_argument('--model', default=MODEL)
    parser.add_argument('--out', required=True, type=Path)
    args = parser.parse_args(argv)
    runs = (ROOT / 'data/hus/evaluation/runs').resolve()
    if args.out.resolve() == runs or not args.out.resolve().is_relative_to(runs):
        parser.error('--out must be a fresh directory under data/hus/evaluation/runs')
    result = assess(args.review_run, model=args.model)
    out = reserve(args.out)
    write_json(out / 'assessment.json', result)
    write_json(out / 'manifest.json', {'schema_version': result['schema_version'],
               'files_sha256': {'assessment.json': digest(out / 'assessment.json')}})
    print(json.dumps({key: result[key] for key in
        ('eligible_for_manual_acceptance', 'recommended_action', 'reasons', 'blocked_cases')}))


if __name__ == '__main__':
    main()
