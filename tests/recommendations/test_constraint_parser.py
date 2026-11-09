import pytest

from app.recommendation.constraint_parser import parse_constraints


@pytest.mark.parametrize(("message", "credits", "count"), [
    ("Tối đa 3 tín chỉ; chương trình có tổng 120 tín chỉ", 3, None),
    ("Tối đa 3 tín chỉ; tôi đã tích lũy 99 tín chỉ", 3, None),
    ("Tôi đã tích lũy 99 tín chỉ và kỳ tới tối đa 3 tín chỉ", 3, None),
    ("Không muốn 12 tín chỉ, chỉ 9 tín chỉ thôi", 9, None),
    ("Không quá 12 tín chỉ và 4 môn", 12, 4),
    ("No more than 9 credits and 3 courses", 9, 3),
    ("9 tín chỉ, đổi thành 12 tín chỉ", 12, None),
    ("1 kỳ, 9 tín chỉ và 2 môn", 9, 2),
    ("Tối đa 12 tín chỉ và không quá 9 tín chỉ", 9, None),
])
def test_limits_in_context(message, credits, count):
    result = parse_constraints(message)
    assert not result.questions
    values = {u.field: u.value for u in result.updates}
    assert values.get("target_credits") == credits
    assert values.get("target_course_count") == count


@pytest.mark.parametrize("amount", ["0", "31", "112", "-2", "−2", "+2", "1.5", "1,5"])
def test_invalid_whole_number_never_becomes_valid_tail(amount):
    result = parse_constraints(f"Tối đa {amount} tín chỉ")
    assert result.questions
    assert not result.updates


@pytest.mark.parametrize("amount", ["0", "21", "-2", "1.5", "1,5"])
def test_invalid_course_counts(amount):
    result = parse_constraints(f"Tối đa {amount} môn")
    assert result.questions and not result.updates


def test_invalid_correction_is_not_absence():
    result = parse_constraints("12 tín chỉ, đổi thành 99 tín chỉ")
    assert result.questions


def test_lower_bound_requires_clarification():
    result = parse_constraints("Tôi muốn ít nhất 9 tín chỉ")
    assert result.questions and not result.updates


@pytest.mark.parametrize(("message", "credits", "count"), [
    ("Tôi không muốn vượt quá 3 tín chỉ", 3, None),
    ("Tôi muốn học không nhiều hơn 3 tín chỉ", 3, None),
    ("Tôi không muốn học quá 3 tín chỉ", 3, None),
    ("Tôi không muốn vượt quá là 3 tín chỉ", 3, None),
    ("Tôi không muốn vượt quá 2 môn", None, 2),
    ("Tôi muốn học 1-2 môn", None, 2),
    ("Tôi muốn học tối đa ba tín chỉ", 3, None),
])
def test_negated_ranges_and_written_numbers_are_parsed(message, credits, count):
    result = parse_constraints(message)
    assert not result.questions
    values = {u.field: u.value for u in result.updates}
    assert values.get("target_credits") == credits
    assert values.get("target_course_count") == count
