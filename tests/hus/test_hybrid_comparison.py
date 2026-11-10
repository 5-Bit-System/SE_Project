"""A retrieval improvement alone cannot authorize switching the default."""
import importlib


def report(recall=0.8, mrr=0.7, reviewed=False):
    return {'semantic_review': 'exact_response_bound_ai' if reviewed else 'pending',
        'result': {'semantic_review': 'exact_response_bound_ai' if reviewed else 'pending',
            'metrics': {'recall_at_5': {'value': recall}, 'mrr_at_5': {'value': mrr},
            'false_refusals': 1, 'scope_error_cases': 0, 'http_errors': 0, 'source_audit_failures': 0,
            'vector_live': 5}, 'by_major': {}, 'source_and_answer_metrics_v2': {'metrics': {
                'abstention': {'correct_missing_or_out_of_scope': {'value': 1.0},
                    'correct_opt_in_clarification': {'value': 1.0}},
                'citation_source_support': {
                    'ai_review_coverage': {'value': 1.0, 'numerator': 10, 'denominator': 10},
                    'ai_entailment': {'value': 1.0}, 'ai_completeness': {'value': 1.0},
                    'ai_end_to_end_supported_complete': {'value': 1.0},
                    'integrity_among_answered_positive': {'value': 1.0}},
                'f2': {'source_contract_success': {'value': 1.0}}}}}}


def test_pending_semantic_review_keeps_lexical_even_if_recall_improves():
    m = importlib.import_module('tools.compare_hus_hybrid')
    result = m.recommend(report(), report(recall=0.9))
    assert result['recommended_mode'] == 'lexical'
    assert 'semantic_review_pending' in result['reasons']


def test_quality_regression_blocks_switch():
    m = importlib.import_module('tools.compare_hus_hybrid')
    hybrid = report(recall=0.9, reviewed=True)
    hybrid['result']['metrics']['false_refusals'] = 2
    assert m.recommend(report(reviewed=True), hybrid)['recommended_mode'] == 'lexical'


def test_equal_recall_better_mrr_can_only_recommend_with_review():
    m = importlib.import_module('tools.compare_hus_hybrid')
    result = m.recommend(report(reviewed=True), report(mrr=0.9, reviewed=True))
    assert result['recommended_mode'] == 'hybrid'
    assert result['changes_runtime_default'] is False


def test_all_fallback_hybrid_cannot_be_recommended():
    m = importlib.import_module('tools.compare_hus_hybrid')
    hybrid = report(recall=0.9, reviewed=True)
    hybrid['result']['metrics']['vector_live'] = 0
    assert m.recommend(report(reviewed=True), hybrid)['recommended_mode'] == 'lexical'


def test_reviewed_semantic_regression_blocks_recommendation():
    m = importlib.import_module('tools.compare_hus_hybrid')
    hybrid = report(recall=0.9, reviewed=True)
    source = hybrid['result']['source_and_answer_metrics_v2']['metrics']['citation_source_support']
    for key in ('ai_entailment', 'ai_completeness', 'ai_end_to_end_supported_complete'):
        source[key]['value'] = 0.0
    assert m.recommend(report(reviewed=True), hybrid)['recommended_mode'] == 'lexical'


def test_review_marker_without_complete_review_coverage_is_insufficient():
    m = importlib.import_module('tools.compare_hus_hybrid')
    hybrid = report(recall=0.9, reviewed=True)
    hybrid['result']['source_and_answer_metrics_v2']['metrics']['citation_source_support']['ai_review_coverage']['value'] = 0.5
    assert m.recommend(report(reviewed=True), hybrid)['recommended_mode'] == 'lexical'
