"""Chấm điểm xác suất mềm theo sở thích và nhu cầu học vụ từ bảng điểm."""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from app.models import Catalog, Course, RankingWeights, StructuredPreference
from app.progress import CurriculumProgress, calculate_progress, counts_toward_total
from app.recommendation.constraint_parser import fold
from app.recommendation.vocabulary import (
    format_career_label,
    format_enum_label,
    format_topic_label,
)
from app.rules import _prepare_selection_context

_ORDINAL_LEVELS = {
    "difficulty": {"easy": 0, "moderate": 1, "advanced": 2},
    "workload": {"light": 0, "moderate": 1, "heavy": 2},
}
_ORIENTATION_MATRIX = {
    ("theory", "theory"): 1.0,
    ("practice", "practice"): 1.0,
    ("research", "research"): 1.0,
    ("theory", "research"): 0.5,
    ("research", "theory"): 0.5,
    ("practice", "research"): 0.45,
    ("research", "practice"): 0.45,
    ("theory", "practice"): 0.15,
    ("practice", "theory"): 0.15,
}
_SIGMA = 0.85


@dataclass
class TranscriptContext:
    """Thông tin học vụ dẫn xuất từ bảng điểm và khung chương trình."""

    progress: CurriculumProgress
    failed_codes: set[str] = field(default_factory=set)
    group_gap_ratios: dict[str, float] = field(default_factory=dict)
    group_remaining: dict[str, int] = field(default_factory=dict)
    group_required: dict[str, int] = field(default_factory=dict)
    group_earned: dict[str, int] = field(default_factory=dict)
    group_names: dict[str, str] = field(default_factory=dict)
    unlock_counts: dict[str, int] = field(default_factory=dict)
    max_unlock: int = 1
    path_prereq_codes: set[str] = field(default_factory=set)
    remaining_total_credits: int | None = None
    target_remaining_terms: int | None = None
    unpassed_required_credits: int = 0
    unpassed_required_unlockers: int = 0
    unmet_group_credits: int = 0
    unpassed_non_grad_credits: int = 0


def _metadata(course: Course) -> dict:
    return course.model_dump()


def _as_text(value: object) -> str:
    if isinstance(value, list | tuple | set):
        return " ".join(str(item) for item in value)
    return str(value) if value is not None else ""


def _set_similarity(wanted: list[str], actual: list[str] | None, *, fallback_hits: int = 0) -> float:
    if not wanted:
        return 0.0
    wanted_set = set(wanted)
    actual_set = set(actual or [])
    overlap = len(wanted_set & actual_set)
    if overlap:
        recall = overlap / len(wanted_set)
        jaccard = overlap / len(wanted_set | actual_set)
        return min(1.0, 0.7 * recall + 0.3 * jaccard)
    if fallback_hits > 0:
        return min(0.35, 0.25 * (fallback_hits / len(wanted_set)))
    return 0.0


def _ordinal_similarity(field: str, expected: str | None, actual: str | None) -> float:
    if not expected or not actual:
        return 0.0
    mapping = _ORDINAL_LEVELS[field]
    if expected not in mapping or actual not in mapping:
        return 0.0
    diff = abs(mapping[expected] - mapping[actual])
    return round(math.exp(-(diff * diff) / (2.0 * _SIGMA * _SIGMA)), 4)


def _orientation_similarity(expected: str | None, actual: str | None) -> float:
    if not expected or not actual:
        return 0.0
    return _ORIENTATION_MATRIX.get((expected.casefold(), actual.casefold()), 0.0)


def _searchable_text(course: Course, metadata: dict) -> str:
    return fold(
        " ".join(
            [
                course.code,
                course.name,
                str(metadata.get("name_en") or ""),
                course.block,
                str(metadata.get("requirement_type") or ""),
                _as_text(metadata.get("topics")),
                _as_text(metadata.get("orientation")),
            ]
        )
    )


def pref_fit_score(
    course: Course,
    preference: StructuredPreference,
    weights: RankingWeights | None = None,
) -> float:
    """Tính độ gần xác suất [0, 1] theo sở thích và trọng số phương án."""
    metadata = _metadata(course)
    searchable = _searchable_text(course, metadata)
    topic_keyword_hits = sum(
        1
        for topic in preference.interest_topics
        if topic.casefold().replace("_", " ") in searchable
    )
    topic_score = _set_similarity(
        preference.interest_topics,
        course.topics,
        fallback_hits=topic_keyword_hits,
    )
    career_score = _set_similarity(preference.career_paths, course.career_paths)

    if preference.course_type:
        type_score = 1.0 if metadata.get("requirement_type") == preference.course_type else 0.0
    else:
        type_score = 0.0

    orientation_score = _orientation_similarity(preference.orientation, course.orientation)
    difficulty_score = _ordinal_similarity("difficulty", preference.difficulty, course.difficulty)
    workload_score = _ordinal_similarity("workload", preference.workload, course.workload)

    goal_words = {
        word
        for word in fold(preference.raw_goal or "").split()
        if len(word) > 2
    }
    name_score = (
        min(sum(word in searchable for word in goal_words) / len(goal_words), 1.0)
        if goal_words
        else 0.0
    )

    weights = weights or RankingWeights()
    components: list[tuple[float, float, bool]] = [
        (weights.topic, topic_score, bool(preference.interest_topics)),
        (weights.career, career_score, bool(preference.career_paths)),
        (weights.keyword, name_score, bool(goal_words)),
        (weights.course_type, type_score, bool(preference.course_type)),
        (weights.orientation, orientation_score, bool(preference.orientation)),
        (weights.difficulty, difficulty_score, bool(preference.difficulty)),
        (weights.workload, workload_score, bool(preference.workload)),
    ]
    active_weight = sum(w for w, _, active in components if active)
    if active_weight <= 0:
        active_weight = sum(weights.model_dump().values())
    weighted_total = sum(w * score for w, score, active in components if active)
    return round(min(1.0, max(0.0, weighted_total / active_weight)), 4)


def score_course(
    course: Course,
    preference: StructuredPreference,
    weights: RankingWeights | None = None,
) -> float:
    """Trả về điểm độ gần [0, 1]; giữ tương thích ngược cho mọi caller."""
    return pref_fit_score(course, preference, weights)


def compute_transcript_context(
    catalog: Catalog,
    passed_codes: set[str],
    failed_codes: set[str] | None = None,
    selected_track_id: str | None = None,
    selected_graduation_path_id: str | None = None,
    target_remaining_terms: int | None = None,
) -> TranscriptContext:
    """Tổng hợp tiến độ tín chỉ, nhóm còn thiếu, DAG mở khóa và môn cần học lại."""
    progress = calculate_progress(
        catalog,
        passed_codes,
        selected_track_id,
        selected_graduation_path_id,
    )
    (
        _,
        _,
        selected_track_groups,
        all_track_groups,
        _,
        selected_path,
        selected_path_courses,
        path_course_ids,
    ) = _prepare_selection_context(
        catalog, selected_track_id, selected_graduation_path_id
    )

    in_scope_courses: dict[str, Course] = {}
    for course in catalog.courses:
        if course.code in passed_codes:
            continue
        if selected_track_id and course.choice_group_ids:
            track_groups = set(course.choice_group_ids) & all_track_groups
            if track_groups and not (track_groups & selected_track_groups):
                continue
        if (
            selected_graduation_path_id
            and course.code in path_course_ids
            and course.code not in selected_path_courses
        ):
            continue
        in_scope_courses[course.code] = course

    # Đồ thị xuôi: prereq -> các môn chưa học phụ thuộc trực tiếp vào prereq.
    dependents: dict[str, set[str]] = {code: set() for code in in_scope_courses}
    for code, course in in_scope_courses.items():
        for clause in course.prerequisites:
            for req_code in clause:
                if req_code in in_scope_courses:
                    dependents[req_code].add(code)

    unlock_counts: dict[str, int] = {}
    for code in in_scope_courses:
        visited: set[str] = set()
        stack = list(dependents.get(code, ()))
        while stack:
            nxt = stack.pop()
            if nxt in visited:
                continue
            visited.add(nxt)
            stack.extend(dependents.get(nxt, ()))
        unlock_counts[code] = len(visited)

    # Tìm các môn tiên quyết (trực tiếp/gián tiếp) cần cho nhánh tốt nghiệp đã chọn.
    path_prereq_codes: set[str] = set()
    if selected_path:
        frontier = [c for c in selected_path.course_codes if c in in_scope_courses]
        seen_path = set(frontier)
        while frontier:
            cur = frontier.pop()
            course = in_scope_courses.get(cur)
            if not course:
                continue
            for clause in course.prerequisites:
                for req in clause:
                    if req in in_scope_courses and req not in seen_path:
                        seen_path.add(req)
                        path_prereq_codes.add(req)
                        frontier.append(req)

    group_gap_ratios: dict[str, float] = {}
    group_remaining: dict[str, int] = {}
    group_required: dict[str, int] = {}
    group_earned: dict[str, int] = {}
    group_names: dict[str, str] = {}
    unmet_group_credits = 0
    for g in progress.choice_groups:
        group_earned[g.id] = g.earned_credits
        group_names[g.id] = g.name
        if g.required_credits is not None:
            group_required[g.id] = g.required_credits
            rem = g.remaining_credits or 0
            group_remaining[g.id] = rem
            group_gap_ratios[g.id] = (
                min(1.0, rem / g.required_credits) if g.required_credits > 0 else 0.0
            )
            if not (selected_track_id and g.id in all_track_groups and g.id not in selected_track_groups):
                unmet_group_credits += rem

    unpassed_required_courses = [
        c
        for c in in_scope_courses.values()
        if c.requirement_type == "required" and counts_toward_total(catalog, c)
    ]
    unpassed_required_credits = sum(c.credits for c in unpassed_required_courses)
    unpassed_non_grad_credits = sum(
        c.credits
        for c in in_scope_courses.values()
        if c.requirement_type != "graduation" and counts_toward_total(catalog, c)
    )
    req_or_path_targets = {c.code for c in unpassed_required_courses} | {
        c.code
        for c in in_scope_courses.values()
        if c.requirement_type == "graduation"
        and (not selected_graduation_path_id or c.code in selected_path_courses)
    }
    unpassed_required_unlockers = sum(
        1
        for c in unpassed_required_courses
        if any(dep in req_or_path_targets for dep in dependents.get(c.code, ()))
    )

    return TranscriptContext(
        progress=progress,
        failed_codes=set(failed_codes or ()),
        group_gap_ratios=group_gap_ratios,
        group_remaining=group_remaining,
        group_required=group_required,
        group_earned=group_earned,
        group_names=group_names,
        unlock_counts=unlock_counts,
        max_unlock=max([1, *unlock_counts.values()]),
        path_prereq_codes=path_prereq_codes,
        remaining_total_credits=progress.total.remaining_credits,
        target_remaining_terms=target_remaining_terms,
        unpassed_required_credits=unpassed_required_credits,
        unpassed_required_unlockers=unpassed_required_unlockers,
        unmet_group_credits=unmet_group_credits,
        unpassed_non_grad_credits=unpassed_non_grad_credits,
    )


def is_thesis_course(course: Course) -> bool:
    """Nhận diện học phần Khóa luận tốt nghiệp (thường đăng ký ở kỳ cuối)."""
    if course.requirement_type != "graduation":
        return False
    folded_name = fold(course.name)
    return "khoa luan" in folded_name or "thesis" in folded_name


def early_thesis_reason(course: Course, ctx: TranscriptContext) -> str | None:
    """Trả về lý do nếu là khóa luận nhưng sinh viên chưa ở kỳ tốt nghiệp cuối."""
    if not is_thesis_course(course):
        return None
    if ctx.target_remaining_terms is not None and ctx.target_remaining_terms > 1:
        return (
            "Học phần khóa luận tốt nghiệp thường đăng ký ở kỳ cuối; "
            f"đang bị giảm ưu tiên mạnh vì mục tiêu tốt nghiệp còn {ctx.target_remaining_terms} học kỳ."
        )
    earned_credits = ctx.progress.total.earned_credits
    required_credits = ctx.progress.total.required_credits
    if earned_credits == 0 and required_credits is not None and required_credits > course.credits:
        return (
            "Học phần khóa luận tốt nghiệp thường đăng ký ở kỳ cuối khi đã tích lũy phần lớn học phần; "
            "bảng điểm hiện chưa ghi nhận tín chỉ tích lũy."
        )
    non_thesis_remaining = (
        max(0, ctx.remaining_total_credits - course.credits)
        if ctx.remaining_total_credits is not None
        else 0
    )
    if non_thesis_remaining >= 12 and ctx.unpassed_non_grad_credits >= 12:
        return (
            "Học phần khóa luận tốt nghiệp thường đăng ký ở kỳ cuối khi gần hoàn tất chương trình; "
            f"bảng điểm hiện còn {non_thesis_remaining} tín chỉ học phần khác chưa hoàn thành."
        )
    if ctx.unpassed_required_credits >= 9 or (
        ctx.unpassed_required_credits >= 6 and non_thesis_remaining >= 10
    ):
        return (
            "Học phần khóa luận tốt nghiệp thường đăng ký ở kỳ cuối; "
            f"hiện còn {ctx.unpassed_required_credits} tín chỉ học phần bắt buộc chưa hoàn thành."
        )
    if ctx.unpassed_required_unlockers > 0:
        return (
            "Học phần khóa luận tốt nghiệp thường đăng ký ở kỳ cuối; "
            "hiện còn chuỗi học phần bắt buộc tiên quyết cần hoàn thành trước."
        )
    return None


def is_early_thesis(
    course: Course,
    context_or_terms: TranscriptContext | int | None,
) -> bool:
    """Trả True nếu là khóa luận nhưng người dùng chưa ở kỳ tốt nghiệp cuối."""
    if isinstance(context_or_terms, TranscriptContext):
        return early_thesis_reason(course, context_or_terms) is not None
    return (
        context_or_terms is not None
        and context_or_terms > 1
        and is_thesis_course(course)
    )


def transcript_need_score(
    course: Course,
    ctx: TranscriptContext,
) -> tuple[float, list[str]]:
    """Chấm mức độ cần thiết theo bảng điểm thực tế [0, 1] kèm lý do giải thích."""
    signals: list[str] = []
    thesis_block_reason = early_thesis_reason(course, ctx)
    early_thesis = thesis_block_reason is not None

    if thesis_block_reason is not None:
        req_score = 0.0
        signals.append(thesis_block_reason)
    elif course.code in ctx.path_prereq_codes or course.requirement_type == "graduation":
        req_score = 1.0
        if course.requirement_type == "graduation":
            signals.append("Thuộc nhóm học phần tốt nghiệp của nhánh bạn đã chọn.")
        else:
            signals.append("Là môn tiên quyết giúp mở đường cho học phần tốt nghiệp bạn đã chọn.")
    elif course.requirement_type == "required":
        req_score = 0.85
        signals.append("Học phần bắt buộc còn thiếu trong chương trình đào tạo.")
    elif course.requirement_type == "elective":
        req_score = 0.25
    else:
        req_score = 0.0

    unlocks = ctx.unlock_counts.get(course.code, 0)
    unlock_score = unlocks / ctx.max_unlock if unlocks > 0 else 0.0
    if ctx.target_remaining_terms is not None and ctx.target_remaining_terms <= 3 and unlocks > 0:
        unlock_score = min(1.0, unlock_score * 1.25)
    if unlocks > 0:
        signals.append(f"Giúp mở khóa {unlocks} học phần tiếp theo trong chương trình.")

    group_gaps = [
        ctx.group_gap_ratios[gid]
        for gid in course.choice_group_ids
        if gid in ctx.group_gap_ratios and ctx.group_remaining.get(gid, 0) > 0
    ]
    gap_score = max(group_gaps) if group_gaps else 0.0
    if gap_score > 0:
        unmet = [
            f"{ctx.group_names.get(gid, gid)} (còn thiếu {ctx.group_remaining[gid]} TC)"
            for gid in course.choice_group_ids
            if ctx.group_remaining.get(gid, 0) > 0
        ]
        if unmet:
            signals.append("Bổ sung tín chỉ cho nhóm tự chọn " + ", ".join(unmet) + ".")

    is_retake = course.code in ctx.failed_codes
    retake_score = 1.0 if is_retake else 0.0
    if is_retake:
        signals.insert(0, "Ưu tiên học lại học phần chưa đạt ở lần học trước (điểm F).")

    total = (
        0.35 * req_score
        + 0.30 * unlock_score
        + 0.20 * gap_score
        + 0.15 * retake_score
    )
    if early_thesis:
        total *= 0.05
    return round(min(1.0, max(0.0, total)), 4), signals


def preference_blend_alpha(weights: RankingWeights | None) -> float:
    """Suy ra tỷ lệ cân bằng (alpha * PrefFit + (1 - alpha) * TranscriptNeed)."""
    w = weights or RankingWeights()
    pref_drive = w.topic + w.career + w.orientation + w.difficulty + w.workload + 0.5 * w.keyword
    grad_drive = w.course_type
    denom = pref_drive + grad_drive
    if denom <= 0:
        return 0.55
    ratio = pref_drive / denom
    # Khi ưu tiên tốt nghiệp (course_type cao) -> nghiêng về bảng điểm (alpha ~0.25);
    # Khi sát định hướng (topic cao) -> nghiêng về sở thích (alpha ~0.82).
    return round(min(0.85, max(0.25, 0.20 + 0.65 * ratio)), 4)


def combine_scores(
    pref_score: float,
    need_score: float,
    weights: RankingWeights | None = None,
    *,
    early_thesis_penalty: bool = False,
) -> float:
    alpha = preference_blend_alpha(weights)
    blended = alpha * pref_score + (1.0 - alpha) * need_score
    if early_thesis_penalty:
        blended *= 0.04
    return round(min(1.0, max(0.0, blended)), 4)


def softmax_probabilities(scores: list[float], temperature: float = 0.25) -> list[float]:
    if not scores:
        return []
    tau = max(temperature, 1e-6)
    peak = max(scores)
    exps = [math.exp((s - peak) / tau) for s in scores]
    total = sum(exps) or 1.0
    return [round(val / total, 4) for val in exps]


def fit_reason(course: Course, preference: StructuredPreference, score: float) -> str:
    metadata = _metadata(course)
    matches: list[str] = []
    searchable = _searchable_text(course, metadata)
    for topic in preference.interest_topics:
        if topic in (course.topics or []) or topic.casefold().replace("_", " ") in searchable:
            matches.append(format_topic_label(topic))
    if matches:
        return f"Phù hợp chủ đề bạn quan tâm: {', '.join(matches)}."
    if preference.career_paths and set(preference.career_paths) & set(course.career_paths or []):
        matched_careers = [
            format_career_label(cid)
            for cid in sorted(set(preference.career_paths) & set(course.career_paths or []))
        ]
        return f"Gắn với định hướng nghề nghiệp: {', '.join(matched_careers)}."
    near_notes = []
    for field_name in ("orientation", "difficulty", "workload"):
        expected = getattr(preference, field_name)
        actual = metadata.get(field_name)
        if expected and actual:
            sim = (
                _orientation_similarity(expected, actual)
                if field_name == "orientation"
                else _ordinal_similarity(field_name, expected, actual)
            )
            actual_label = format_enum_label(field_name, str(actual))
            expected_label = format_enum_label(field_name, str(expected))
            if sim >= 0.99:
                near_notes.append(actual_label)
            elif sim >= 0.45:
                near_notes.append(f"{actual_label} (gần với {expected_label})")
    if near_notes:
        return "Phù hợp phong cách học tập bạn chọn: " + ", ".join(near_notes) + "."
    if preference.course_type and metadata.get("requirement_type") == preference.course_type:
        req_label = format_enum_label("requirement_type", preference.course_type)
        return f"Thuộc nhóm học phần {req_label} đúng theo ưu tiên của bạn."
    if score > 0:
        return "Có nội dung liên quan một phần tới mục tiêu và cấu trúc chương trình."
    return "Catalog hiện chưa có metadata đủ để xác định mức độ phù hợp cụ thể cho lựa chọn này."
