"""One resolver for form/text/model/history; no course facts or storage writes."""

import re
from dataclasses import dataclass

from app.models import Catalog, StructuredPreference
from app.recommendation.constraint_parser import fold, parse_constraints
from app.recommendation.preference import preference_updates
from app.recommendation.vocabulary import preference_vocabulary
from app.schemas.study_intent import FormInput, IntentDiagnostics, StudyIntentState

LIMITS = {"target_credits": 30, "target_course_count": 20}
WORKLOAD_RANGES = {"light": (14, 17), "moderate": (18, 20), "heavy": (21, 30)}
# Folded text that does not, by itself, carry a study goal.
_NOOP_PREFIX = re.compile(
    r"^\s*(?:chao|cam on|thanks|thank you|ok|oke|uh|u|vang|da|duoc|hello|hi|hey|help|giup)\b")
_GENERIC_REQUEST = re.compile(r"\b(?:goi y|recommend|suggest|tu van|help|giup)\b")
_STUDY_HINT = re.compile(
    r"\b(?:hoc|mon|tin chi|ky toi|ki toi|dinh huong|nganh|chuong trinh|"
    r"xay dung|he thong|muon|thich|career|course|credit|study|learn|build|system)\b")


@dataclass
class ResolvedStudyIntent:
    preference: StructuredPreference
    max_credits: int
    max_courses: int
    diagnostics: IntentDiagnostics
    state: StudyIntentState


def resolve_study_intent(message: str, catalog: Catalog, *, form_input: FormInput | None = None,
                         legacy_preference: StructuredPreference | None = None,
                         previous_state: StudyIntentState | None = None,
                         history=(), extractor=None, max_credits=18, max_courses=5) -> ResolvedStudyIntent:
    state = previous_state.model_copy(deep=True) if previous_state else StudyIntentState()
    diagnostics = IntentDiagnostics()
    # Compatibility for standalone callers: bounded ordered user-only replay.
    # Authenticated APIs supply server state instead, never trust client history as state.
    if previous_state is None:
        if len(history) >= 20:
            state.questions.append("history: lịch sử bị giới hạn; hãy xác nhận lại giới hạn học kỳ.")
        for item in history[-20:]:
            if item.role != "user":
                continue
            replay = resolve_study_intent(item.content[:1000], catalog, previous_state=state,
                                          max_credits=max_credits, max_courses=max_courses)
            state = replay.state
    previous = StructuredPreference.model_validate(state.values)
    rules = preference_updates(message)
    constraints = parse_constraints(message)
    ruled_fields = {u.field for u in [*rules, *constraints.updates]}
    excluded = set(state.excluded_topics)
    if legacy_preference is not None and previous_state is None:
        # Legacy preference is an input, never a reason to skip the current text.
        for field in legacy_preference.model_fields_set - {"raw_goal", "career_goal"}:
            value = getattr(legacy_preference, field)
            if value is not None and value != []:
                state.values[field] = value
                state.field_sources[field] = "legacy_form"
    if form_input:
        state.workload_policy = state.workload_policy or form_input.values.workload is not None
        for field in form_input.explicit_fields:
            value = getattr(form_input.values, field)
            state.values[field] = value
            state.field_sources[field] = "explicit_form"
            state.questions = [q for q in state.questions if not q.startswith(field + ":")]

    applied_any = False
    if extractor:
        before_proposal = state.model_copy(deep=True)
        try:
            proposed = (extractor.extract_update(message, previous) if hasattr(extractor, "extract_update")
                        else extractor.extract(message))
            if isinstance(proposed, dict):
                from app.recommendation.feature_extractor import ChatFeatures
                proposed = ChatFeatures.model_validate(proposed)
            if not isinstance(proposed, StructuredPreference):
                raise ValueError("Invalid extractor contract")
            diagnostics.extraction_source = "llm"
            for field in proposed.model_fields_set - {"raw_goal"}:
                value = getattr(proposed, field)
                if field in LIMITS:
                    if value is not None and field not in ruled_fields:
                        state.questions.append(f"{field}: hãy xác nhận giới hạn bằng số nguyên và đơn vị rõ ràng.")
                    continue  # A model never sets or removes a hard limit.
                if field == "course_type_mode" and value == "only" and field not in ruled_fields:
                    diagnostics.questions.append("course_type: hãy xác nhận bạn chỉ muốn loại môn này hay chỉ ưu tiên.")
                    continue
                if value is None or value == []:
                    continue
                if field in {"interest_topics", "career_paths"}:
                    allowed = preference_vocabulary(catalog)["topics" if field == "interest_topics" else "career_paths"]
                    if not set(value) <= set(allowed):
                        raise ValueError("Unknown label")
                    if field == "interest_topics":
                        value = [v for v in value if v not in excluded]
                    if not value:
                        continue
                    if form_input and field in form_input.explicit_fields:
                        form_value = getattr(form_input.values, field) or []
                        extra = [v for v in value if v not in form_value]
                        if extra and not re.search(r"\b(?:thêm|cũng|và|them|cung|va|also|and)\b", message.casefold()):
                            diagnostics.questions.append(
                                f"{field}: câu nhập bổ sung lựa chọn khác biểu mẫu; hãy xác nhận lại.")
                            continue
                    merged = list(dict.fromkeys([*(state.values.get(field) or []), *value]))[:20]
                    if merged != (state.values.get(field) or []):
                        state.values[field] = merged
                        state.field_sources[field] = "llm"
                        applied_any = True
                    continue
                if field in ruled_fields:
                    continue
                if form_input and field in form_input.explicit_fields and getattr(form_input.values, field) != value:
                    diagnostics.questions.append(f"{field}: câu nhập và lựa chọn biểu mẫu khác nhau; hãy chọn lại.")
                    continue
                state.values[field] = value
                state.field_sources[field] = "llm"
                applied_any = True
        except Exception as exc:
            # Roll back the entire proposal, including partial valid fields.
            state = before_proposal
            applied_any = False
            diagnostics.extraction_source = "fallback"
            diagnostics.warnings.append(f"Bộ trích xuất không khả dụng ({type(exc).__name__}); đã dùng quy tắc và trạng thái trước.")

    for update in [*rules, *constraints.updates]:
        field, value = update.field, update.value
        if form_input and field in form_input.explicit_fields:
            form_value = getattr(form_input.values, field)
            conflict = update.operation != "add" and form_value != value
            if update.operation == "remove":
                conflict = bool(set(form_value or []) & set(value)) if isinstance(value, list) else form_value == value
            if update.operation == "add" and form_value and set(value) != set(form_value):
                conflict = not bool(re.search(r"\b(?:thêm|cũng|và|them|cung|va|also|and)\b", message.casefold()))
            if conflict:
                diagnostics.questions.append(f"{field}: lựa chọn biểu mẫu mâu thuẫn câu nhập; hãy xác nhận lại.")
        before = state.values.get(field)
        if update.operation == "clear":
            state.values[field] = [] if field in {"interest_topics", "career_paths"} else None
            if field == "interest_topics":
                excluded.update(preference_vocabulary(catalog)["topics"])
        elif update.operation == "remove":
            if isinstance(value, list):
                state.values[field] = [v for v in (state.values.get(field) or []) if v not in value]
            elif state.values.get(field) == value:
                state.values[field] = None
            if field == "interest_topics":
                excluded.update(value)
        elif update.operation == "add":
            state.values[field] = list(dict.fromkeys([*(state.values.get(field) or []), *value]))[:20]
            excluded.difference_update(value)
        else:
            state.values[field] = value
            if field == "interest_topics":
                excluded.difference_update(value)
        if state.values.get(field) != before or field not in state.field_sources:
            state.field_sources[field] = "text_rule"
        applied_any = True
        state.questions = [q for q in state.questions if not q.startswith(field + ":")]
    state.questions.extend(constraints.questions)
    policy_workload = state.values.get("workload") or (form_input.values.workload if form_input else None)
    if state.workload_policy and policy_workload and state.values.get("target_credits"):
        low, high = WORKLOAD_RANGES[policy_workload]
        if not low <= state.values["target_credits"] <= high:
            diagnostics.questions.append("target_credits: yêu cầu nằm ngoài khoảng tải học đã chọn; hãy sửa tải học hoặc số tín chỉ.")
    if form_input:
        for field, value in form_input.values.model_dump().items():
            if field not in state.values and value is not None and value != []:
                state.values[field] = value
                state.field_sources[field] = "form_default"
    vocab = preference_vocabulary(catalog)
    for field, key in (("interest_topics", "topics"), ("career_paths", "career_paths")):
        unknown = set(state.values.get(field, []) or []) - set(vocab[key])
        if unknown and state.field_sources.get(field) == "explicit_form":
            diagnostics.questions.append(f"{field}: lựa chọn có nhãn chưa được hỗ trợ; hãy chọn lại hoặc mô tả bằng câu nhập.")
        elif unknown:
            diagnostics.warnings.append(f"{field}: đã bỏ nhãn không thuộc từ điển hiện tại.")
        state.values[field] = list(dict.fromkeys(v for v in state.values.get(field, []) if v in vocab[key]))[:20]
    folded_message = fold(message).strip()
    if (not applied_any and not state.values.get("interest_topics")
            and not state.values.get("career_paths") and folded_message
            and not _NOOP_PREFIX.match(folded_message)
            and not _GENERIC_REQUEST.search(folded_message)
            and _STUDY_HINT.search(folded_message)):
        diagnostics.questions.append(
            "goal: chưa nhận diện được chủ đề, môn học, tải học hoặc giới hạn cụ thể từ câu nhập; "
            "hãy nêu rõ mong muốn hoặc chọn từ biểu mẫu.")
    state.excluded_topics = sorted(excluded)
    state.questions = list(dict.fromkeys([*state.questions, *diagnostics.questions]))
    diagnostics.questions = state.questions.copy()
    diagnostics.status = "needs_clarification" if diagnostics.questions else "ready"
    diagnostics.field_sources = state.field_sources.copy()
    preference = StructuredPreference.model_validate({**state.values, "raw_goal": message[:500]})
    missing = [metadata for pref, metadata in (("interest_topics", "topics"), ("career_paths", "career_paths"),
               ("orientation", "orientation"), ("difficulty", "difficulty"), ("workload", "workload"))
               if getattr(preference, pref) and not any(getattr(c, metadata) for c in catalog.courses)]
    if missing:
        diagnostics.warnings.append("Catalog thiếu metadata tư vấn cho các trường: " + ", ".join(missing)
                                    + "; chưa đủ căn cứ đánh giá mức phù hợp theo các trường này.")
    return ResolvedStudyIntent(preference, min(max_credits, preference.target_credits or max_credits),
                               min(max_courses, preference.target_course_count or max_courses), diagnostics, state)
