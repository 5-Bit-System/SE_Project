
import json
import subprocess

import pytest

from app.models import RankingWeights, RecommendationRequest, StructuredPreference
from app.recommendation.feature_extractor import CatalogFeatureExtractor
from app.recommendation.preference import extract_structured_preference
from app.schemas.advisor import AdvisorMessage, AdvisorRequest
from app.schemas.study_intent import FormInput
from app.services.advisor_service import chat_advisor
from app.services.recommendation_service import recommend
from app.services.study_intent_service import resolve_study_intent
from tests.recommendations.test_recommendations import sample_catalog


@pytest.mark.parametrize("output", ["{}", '{"target_credits":30,"target_course_count":20}',
                                   '{"target_credits":1,"target_course_count":1}'])
def test_valid_model_json_cannot_change_explicit_limits(output):
    cat = sample_catalog()
    extractor = CatalogFeatureExtractor(cat, lambda _: output)
    response = recommend(cat, RecommendationRequest(program_id="demo", max_credits=20,
        limit=20, goal="Tối đa 3 tín chỉ và 1 môn"), preference_extractor=extractor)
    assert response.intent.status == "ready"
    assert response.preference.target_credits == 3
    assert len(response.recommendations) == 1
    assert sum(c.credits for c in response.recommendations) <= 3


def test_legacy_preference_cannot_bypass_text_extraction():
    calls = []
    class Extractor:
        def extract(self, message):
            calls.append(message)
            return StructuredPreference(orientation="practice")
    result = recommend(sample_catalog(), RecommendationRequest(program_id="demo",
        goal="Tối đa 3 tín chỉ và 1 môn", max_credits=20, limit=20,
        preference=StructuredPreference(target_credits=20)), preference_extractor=Extractor())
    assert calls
    assert result.preference.orientation == "practice"
    assert len(result.recommendations) == 1


@pytest.mark.parametrize("message", ["Tôi muốn học lập trình để phát triển phần mềm", "Ưu tiên thực hành nhé"])
def test_accented_connectives_are_not_preferences(message):
    result = extract_structured_preference(message)
    assert result.difficulty is None and result.workload is None


@pytest.mark.parametrize(("message", "topics"), [
    ("khoa học dữ liệu", ["data_science"]), ("data science", ["data_science"]),
    ("data_science", ["data_science"]), ("cơ sở dữ liệu", ["databases"]),
    ("Tôi muốn lập trình nhưng giờ chuyển sang học máy", ["machine_learning"]),
    ("lập trình và học máy", ["programming", "machine_learning"]),
    ("không thích machine learning", []),
])
def test_topics_and_replacements(message, topics):
    assert extract_structured_preference(message).interest_topics == topics


def test_software_alias_unknown_field_rollback_and_extension_isolation():
    cat = sample_catalog()
    before = cat.model_dump()
    cat.vocabulary = {"topics": ["local_topic"]}
    local = CatalogFeatureExtractor(cat, lambda _: '{"interest_topics":["local_topic"]}')
    assert resolve_study_intent("local", cat, extractor=local).preference.interest_topics == ["local_topic"]
    other = sample_catalog()
    invalid = CatalogFeatureExtractor(other, lambda _: '{"orientation":"practice","interest_topics":["local_topic"]}')
    result = resolve_study_intent("hello", other, extractor=invalid)
    assert result.diagnostics.extraction_source == "fallback"
    assert result.preference.orientation is None
    assert not result.preference.interest_topics
    assert other.model_dump() == before


def test_valid_model_label_cannot_invert_explicit_negation():
    cat = sample_catalog()
    extractor = CatalogFeatureExtractor(cat, lambda _: '{"interest_topics":["machine_learning"],"course_type":"elective"}')
    result = resolve_study_intent("không thích machine learning; không muốn môn tự chọn", cat, extractor=extractor)
    assert result.preference.interest_topics == []
    assert result.preference.course_type is None


def test_history_and_timeout_keep_limits_and_allow_corrections():
    cat = sample_catalog()
    history = [AdvisorMessage(role="user", content="Tối đa 3 tín chỉ và 1 môn, thích phát triển phần mềm")]
    class Timeout:
        def extract(self, _):
            raise TimeoutError()
    result = resolve_study_intent("Ưu tiên thực hành nhé", cat, history=history, extractor=Timeout())
    assert result.preference.target_credits == 3 and result.preference.target_course_count == 1
    assert result.preference.interest_topics == ["software_engineering"]
    assert result.preference.workload is None
    changed = resolve_study_intent("Đổi thành 6 tín chỉ và 2 môn", cat, previous_state=result.state)
    assert changed.preference.target_credits == 6 and changed.preference.target_course_count == 2
    cleared = resolve_study_intent("xóa chủ đề", cat, previous_state=changed.state)
    assert cleared.preference.interest_topics == [] and cleared.preference.target_credits == 6


def test_invalid_limit_stays_pending_until_corrected():
    cat = sample_catalog()
    invalid = resolve_study_intent("12 tín chỉ, đổi thành 99 tín chỉ", cat)
    assert invalid.diagnostics.status == "needs_clarification"
    pending = resolve_study_intent("thực hành nhé", cat, previous_state=invalid.state)
    assert pending.diagnostics.status == "needs_clarification"
    fixed = resolve_study_intent("đổi thành 9 tín chỉ", cat, previous_state=pending.state)
    assert fixed.diagnostics.status == "ready" and fixed.max_credits == 9


def test_default_form_does_not_override_text_but_explicit_conflict_blocks():
    cat = sample_catalog()
    default = FormInput(values={"target_credits": 20})
    result = resolve_study_intent("tối đa 9 tín chỉ", cat, form_input=default)
    assert result.max_credits == 9 and result.diagnostics.status == "ready"
    explicit = default.model_copy(update={"explicit_fields": ["target_credits"]})
    result = resolve_study_intent("tối đa 9 tín chỉ", cat, form_input=explicit)
    assert result.diagnostics.status == "needs_clarification"
    workload = FormInput(values={"workload": "moderate", "target_credits": 20}, explicit_fields=["workload"])
    result = resolve_study_intent("tối đa 3 tín chỉ", cat, form_input=workload)
    assert result.diagnostics.status == "needs_clarification"


def test_advisor_fallback_and_model_bundle_obey_limits(monkeypatch):
    cat = sample_catalog()
    monkeypatch.setattr('app.recommendation.llm.configured_adapters', lambda *_: (None, None))
    request = AdvisorRequest(program_id="demo", message="Ưu tiên thực hành nhé", history=[
        AdvisorMessage(role="user", content="tối đa 3 tín chỉ và 1 môn")])
    result = chat_advisor(cat, request, api_key="")
    assert result.intent.status == "ready" and len(result.suggested_courses) <= 1
    assert result.preference.target_credits == 3
    for course in cat.courses:
        if course.code in {"A", "E"}:
            course.code = {"A": "ABC1000", "E": "ABC2000"}[course.code]
    monkeypatch.setattr('app.services.advisor_service.call_gemini_api', lambda *_: "ABC1000 ABC2000")
    model_result = chat_advisor(cat, request, api_key="synthetic-key")
    assert model_result.mode == "heuristic_fallback"
    assert len(model_result.suggested_courses) <= 1


def test_synthetic_metadata_and_actual_ui_weights_affect_order():
    from app.recommendation.scoring import score_course
    cat = sample_catalog()
    a = cat.courses[0].model_copy(update={"topics": None, "orientation": "theory", "difficulty": "advanced"})
    b = a.model_copy(update={"orientation": "practice", "difficulty": "easy"})
    script = """
import {recommendationPayload} from './app/static/recommendation-model.mjs';
console.log(JSON.stringify(recommendationPayload({program_id:'demo'},
  {workload:'moderate',credits:20}, 'balanced', 'revision').ranking_weights));
"""
    weights = RankingWeights.model_validate(json.loads(subprocess.check_output(
        ['node', '--input-type=module', '-e', script], text=True)))
    preference = StructuredPreference(orientation="practice", difficulty="easy")
    assert score_course(b, preference, weights) > score_course(a, preference, weights)
    assert score_course(a.model_copy(update={"orientation": None, "difficulty": None}), preference, weights) == 0


def test_workload_policy_and_conflict_survive_followup():
    cat = sample_catalog()
    form = FormInput(values={"workload": "moderate", "target_credits": 20}, explicit_fields=["workload"])
    initial = resolve_study_intent("tối đa 3 tín chỉ", cat, form_input=form)
    followup = resolve_study_intent("thực hành", cat, previous_state=initial.state)
    assert followup.diagnostics.status == "needs_clarification"
    fixed = resolve_study_intent("đổi thành 19 tín chỉ", cat, previous_state=followup.state)
    assert fixed.diagnostics.status == "ready"


def test_only_and_prefer_are_distinct_without_changing_eligibility():
    cat = sample_catalog()
    for c in cat.courses:
        c.requirement_type = "elective" if c.code == "E" else "required"
    request = RecommendationRequest(program_id="demo", goal="chỉ môn tự chọn", max_credits=20, limit=20)
    result = recommend(cat, request)
    assert [c.code for c in result.recommendations] == ["E"]
    assert result.preference.course_type_mode == "only"
    preferred = recommend(cat, request.model_copy(update={"goal": "ưu tiên môn tự chọn"}))
    assert preferred.preference.course_type_mode == "prefer"
    assert len(preferred.recommendations) > 1


def test_soft_negation_removes_previous_value_without_adding_the_opposite():
    cat = sample_catalog()
    old = resolve_study_intent("thích lý thuyết", cat)
    new = resolve_study_intent("không còn thích lý thuyết", cat, previous_state=old.state)
    assert new.preference.orientation is None
    assert new.diagnostics.status == "ready"


def test_missing_model_limits_and_unbacked_numeric_proposal_differ():
    cat = sample_catalog()
    state = resolve_study_intent("tối đa 3 tín chỉ", cat).state
    result = resolve_study_intent("thực hành", cat, previous_state=state,
        extractor=CatalogFeatureExtractor(cat, lambda _: '{}'))
    assert result.preference.target_credits == 3 and result.diagnostics.status == "ready"
    invented = resolve_study_intent("thực hành", cat,
        extractor=CatalogFeatureExtractor(cat, lambda _: '{"target_credits":30}'))
    assert invented.diagnostics.status == "needs_clarification"


def test_form_topic_conflict_is_not_silently_merged():
    cat = sample_catalog()
    form = FormInput(values={"interest_topics": ["software_engineering"]}, explicit_fields=["interest_topics"])
    conflict = resolve_study_intent("Tôi thích học máy", cat, form_input=form)
    assert conflict.diagnostics.status == "needs_clarification"
    addition = resolve_study_intent("Tôi cũng thích học máy", cat, form_input=form)
    assert addition.diagnostics.status == "ready"
    assert set(addition.preference.interest_topics) == {"software_engineering", "machine_learning"}


def test_change_of_mind_replaces_course_type_without_merging():
    cat = sample_catalog()
    result = resolve_study_intent("Tôi muốn môn tự chọn, đổi thành môn bắt buộc", cat)
    assert result.preference.course_type == "required"
    assert result.preference.course_type_mode == "prefer"
    assert result.diagnostics.status == "ready"


def test_unknown_explicit_label_requires_confirmation():
    result = resolve_study_intent("", sample_catalog(), form_input=FormInput(
        values={"interest_topics": ["not_a_label"]}, explicit_fields=["interest_topics"]))
    assert result.diagnostics.status == "needs_clarification"


def test_model_topic_conflicting_with_explicit_form_is_not_merged():
    class Extractor:
        def extract(self, _):
            return StructuredPreference(interest_topics=["machine_learning"])
    form = FormInput(values={"interest_topics": ["software_engineering"]}, explicit_fields=["interest_topics"])
    result = resolve_study_intent(
        "kỳ tới tôi muốn xây dựng một hệ thống bán hàng",
        sample_catalog(), form_input=form, extractor=Extractor())
    assert result.diagnostics.status == "needs_clarification"
    assert result.preference.interest_topics == ["software_engineering"]


def test_model_can_add_topic_when_parser_found_same_field():
    class Extractor:
        def extract(self, _):
            return StructuredPreference(interest_topics=["machine_learning", "software_engineering"])
    result = resolve_study_intent(
        "tôi thích học máy và muốn xây dựng một hệ thống quản lý bán hàng",
        sample_catalog(), extractor=Extractor())
    assert set(result.preference.interest_topics) == {"machine_learning", "software_engineering"}


def test_model_addition_does_not_resurrect_negated_topic():
    class Extractor:
        def extract(self, _):
            return StructuredPreference(interest_topics=["machine_learning", "software_engineering"])
    result = resolve_study_intent(
        "không thích học máy, chỉ thích phát triển phần mềm",
        sample_catalog(), extractor=Extractor())
    assert result.preference.interest_topics == ["software_engineering"]


def test_model_addition_does_not_override_explicit_topic_switch():
    class Extractor:
        def extract(self, _):
            return StructuredPreference(interest_topics=["machine_learning", "software_engineering"])
    result = resolve_study_intent("chuyển sang học máy", sample_catalog(), extractor=Extractor())
    assert result.preference.interest_topics == ["machine_learning"]
