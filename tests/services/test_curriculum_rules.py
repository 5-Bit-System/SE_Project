"""Unit tests for prerequisite and study-condition editing logic."""

from app.curriculum.rule_service import validate_prerequisite_rules


def test_self_reference_rejected():
    courses = [
        {"code": "MAT1001", "name": "Giải tích 1", "credits": 3, "prerequisites": []},
    ]
    # MAT1001 requires itself
    is_valid, errors = validate_prerequisite_rules(
        target_code="MAT1001",
        new_prerequisites=[["MAT1001"]],
        all_courses=courses,
    )
    assert is_valid is False
    assert any("không thể tự làm tiên quyết cho chính mình" in err for err in errors)


def test_cycle_detection_in_rule_update():
    courses = [
        {"code": "MAT1001", "name": "Giải tích 1", "credits": 3, "prerequisites": []},
        {"code": "MAT1002", "name": "Giải tích 2", "credits": 3, "prerequisites": [["MAT1001"]]},
    ]
    # Updating MAT1001 to require MAT1002 creates cycle MAT1001 -> MAT1002 -> MAT1001
    is_valid, errors = validate_prerequisite_rules(
        target_code="MAT1001",
        new_prerequisites=[["MAT1002"]],
        all_courses=courses,
    )
    assert is_valid is False
    assert any("Chu trình tiên quyết" in err for err in errors)


def test_valid_and_or_conditions():
    courses = [
        {"code": "MAT1001", "name": "Giải tích 1", "credits": 3, "prerequisites": []},
        {"code": "MAT1002", "name": "Giải tích 2", "credits": 3, "prerequisites": []},
        {"code": "MAT1003", "name": "Giải tích 3", "credits": 3, "prerequisites": []},
        {"code": "MAT2001", "name": "Giải tích nâng cao", "credits": 3, "prerequisites": []},
    ]
    # MAT2001 requires MAT1001 AND (MAT1002 OR MAT1003)
    new_prereqs = [["MAT1001"], ["MAT1002", "MAT1003"]]
    is_valid, errors = validate_prerequisite_rules(
        target_code="MAT2001",
        new_prerequisites=new_prereqs,
        all_courses=courses,
    )
    assert is_valid is True
    assert len(errors) == 0
