"""Source-owned course states and constrained views of independently resolved facts."""

from app.academic_context import AcademicContextError, require_ready
from app.models import Catalog, Course
from app.progress import calculate_progress, counts_toward_total
from app.rules import evaluate_eligibility


def _default_eligibility_basis(catalog: Catalog, course: Course) -> str | None:
    """Board defaults requested by the user; never evidence of completion."""
    if not counts_toward_total(catalog, course):
        return "excluded_from_total"
    if (not course.prerequisites and not course.external_prerequisite_codes
            and not any(course.prerequisite_variants)
            and course.prerequisite_status not in {"unknown", "conflict", "source_conflict"}):
        return "no_prerequisites"
    # The user also explicitly requested this internship on 2026-10-28.
    # Only called for courses already allowed by the prerequisite rule engine.
    if course.code == "MAT3374":
        return "requested_default"
    return None


def course_board(
    catalog: Catalog, context: dict, max_credits: int = 20,
    selected_track_id: str | None = None,
    selected_graduation_path_id: str | None = None,
) -> dict:
    passed = require_ready(context)
    return _assemble_board(catalog, passed, context["revision"], max_credits,
                           selected_track_id, selected_graduation_path_id)


def _assemble_board(catalog: Catalog, passed: set[str], context_revision: str,
                    max_credits: int, selected_track_id: str | None,
                    selected_graduation_path_id: str | None) -> dict:
    eligibility = evaluate_eligibility(
        catalog, passed, max_credits=30, selected_track_id=selected_track_id,
        selected_graduation_path_id=selected_graduation_path_id,
    )
    progress = calculate_progress(catalog, passed, selected_track_id, selected_graduation_path_id)
    groups = {group.id: group for group in progress.choice_groups}
    used = {group.id: group.earned_credits for group in progress.choice_groups}
    blocked = {course.code: course for course in eligibility.blocked_courses}
    eligible = {course.code for course in eligibility.eligible_courses}
    rows: dict[str, list[dict]] = {"completed": [], "eligible": [], "blocked": []}
    # Eligibility remains independent of the semester budget. The budget only
    # limits the suggested bundle, never turns an otherwise eligible course red.
    ordered = sorted(catalog.courses, key=lambda course: (
        course.requirement_type not in {"required", "required_excluded"}, course.code,
    ))
    suggested: list[str] = []
    suggested_credits = 0
    for course in ordered:
        state = "completed" if course.code in passed else (
            "eligible" if course.code in eligible else "blocked"
        )
        memberships = [groups[key] for key in course.choice_group_ids if key in groups]
        item = {
            "code": course.code, "name": course.name, "name_en": course.name_en,
            "credits": course.credits, "requirement_type": course.requirement_type,
            "counted_in_total": counts_toward_total(catalog, course),
            "groups": [group.model_dump(mode="json") for group in memberships],
            "reasons": [reason.model_dump(mode="json")
                        for reason in blocked[course.code].reasons] if state == "blocked" else [],
            "eligibility_basis": _default_eligibility_basis(catalog, course)
            if state == "eligible" else None,
            "suggested": False,
        }
        if (state == "eligible" and suggested_credits + course.credits <= max_credits
                and (not memberships or any(
                    used[group.id] < group.required_credits for group in memberships))):
            item["suggested"] = True
            suggested.append(course.code)
            suggested_credits += course.credits
            for group in memberships:
                used[group.id] += course.credits
        rows[state].append(item)
    return {
        "status": "ready", "context_revision": context_revision,
        "program_id": catalog.program.program_id, "program_name": catalog.program.name,
        "catalog_status": catalog.program.catalog_status, "blocking_reasons": [],
        "courses": rows, "progress": progress.model_dump(mode="json"),
        "plan": {"max_credits": max_credits, "suggested_credits": suggested_credits,
                 "course_codes": suggested, "offering_status": "unknown"},
    }


def reviewed_course_board(catalog: Catalog, context: dict, max_credits: int = 20,
                         selected_track_id: str | None = None,
                         selected_graduation_path_id: str | None = None,
                         selection_blockers: list[str] | None = None) -> dict:
    """View independently resolved courses while keeping strict academic APIs gated.

    Requires complete collection, valid program binding and applicable policy.
    Unresolved courses cannot satisfy prerequisites. Otherwise eligible courses
    without prerequisites, excluded from earned credits or explicitly requested
    by the user remain available when their own outcome still needs review.
    Any out-of-catalog code pauses the entire bundle until equivalence is reviewed.
    """
    allowed = {"course_outcomes_unresolved", "program_rules_review_required"}
    if set(context.get("blocking_reasons", [])) - allowed:
        raise AcademicContextError("academic_context_not_ready")
    if context.get("status") not in {"ready", "needs_policy_review"}:
        raise AcademicContextError("academic_context_not_ready")
    completed = {outcome["code"] for outcome in context["outcomes"]
                 if outcome["state"] == "completed"}
    unresolved = {outcome["code"] for outcome in context["outcomes"]
                  if outcome["state"] == "unresolved"}
    outside = any(outcome["state"] == "out_of_catalog" for outcome in context["outcomes"])
    # A separate view calculation; the AcademicContext remains unready for the
    # strict recommendation/advisor/progress APIs. No readiness flag is changed.
    view = _assemble_board(catalog, completed, context["revision"], max_credits,
                           selected_track_id, selected_graduation_path_id)
    pause_plan = outside or bool(selection_blockers) or bool(getattr(catalog.program, "planning_blockers", []))
    kept, moved = [], []
    for course in view["courses"]["eligible"]:
        course["result_pending"] = course["code"] in unresolved
        if (pause_plan or course["result_pending"]) and not course["eligibility_basis"]:
            course["suggested"] = False
            course["reasons"] = [{"kind": "academic_review_required",
                "message": "Kết quả hoặc lựa chọn chương trình cần được đối chiếu.",
                "missing_prerequisites": []}]
            moved.append(course)
        else:
            kept.append(course)
    view["courses"]["eligible"] = kept
    view["courses"]["blocked"].extend(moved)
    # Classification is independent of global planning gates. Defaults may stay
    # yellow while selections/outside mappings still pause the suggested bundle.
    selected, total, used = [], 0, {item.id: item.earned_credits for item in
        calculate_progress(catalog, completed, selected_track_id,
                           selected_graduation_path_id).choice_groups}
    for course in kept:
        course["suggested"] = False
        if (not pause_plan and total + course["credits"] <= max_credits
                and (not course["groups"] or any(
                used[group["id"]] < group["required_credits"] for group in course["groups"]))):
            course["suggested"] = True
            selected.append(course["code"])
            total += course["credits"]
            for group in course["groups"]:
                used[group["id"]] += course["credits"]
    view.update(status="partial", can_plan=not pause_plan, progress_is_lower_bound=True,
                blocking_reasons=[*context["blocking_reasons"], *(selection_blockers or [])],
                review_items=[outcome for outcome in context["outcomes"]
                              if outcome["state"] in {"unresolved", "out_of_catalog"}])
    view["plan"].update(course_codes=selected, suggested_credits=total)
    return view
