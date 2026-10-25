"""Published 3626/2022 rules; all attempts here are invented."""

import copy
import hashlib
from pathlib import Path

import pytest

from app.academic_context import _outcome
from app.academic_policies import VNU_2022


def attempt(letter="D", grade="4.5", grade4="1", term="HỌC KỲ 1 - 2023-2024"):
    return {"credits": "3", "letter": letter, "grade10": grade, "grade4": grade4, "term": term}


def test_policy_archive_is_the_reviewed_official_document():
    path = Path(__file__).resolve().parents[2] / "docs/policies/vnu_3626_2022.pdf"
    assert hashlib.sha256(path.read_bytes()).hexdigest() == "244addf2f614dec7a8804264a5ac966c3785bc7a49d8f23daf1069df05298f93"


@pytest.mark.parametrize("letter,grade,grade4,state", [
    ("A+", "9.0", "4", "completed"), ("A", "8.9", "3.7", "completed"),
    ("B+", "8.0", "3.5", "completed"), ("B", "7.0", "3", "completed"),
    ("C+", "6.5", "2.5", "completed"), ("C", "5.5", "2", "completed"),
    ("D+", "5.0", "1.5", "completed"), ("D", "4.0", "1", "completed"),
    ("F", "0", "0", "not_completed"), ("P", "5.0", "", "completed"),
    ("I", "", "", "unresolved"), ("X", "", "", "unresolved"),
    ("R", "", "", "unresolved"), ("B", "9", "3", "unresolved"),
    ("P", "5", "0", "unresolved"),
])
def test_source_grade_bands_and_unknowns_are_not_legacy_pass_defaults(letter, grade, grade4, state):
    assert _outcome([attempt(letter, grade, grade4)], 3, VNU_2022)[0] == state


def test_later_valid_f_d_improvement_is_used_instead_of_the_best_grade():
    rows = [attempt(), attempt("F", "0", "0", "HỌC KỲ 2 - 2023-2024")]
    original = copy.deepcopy(rows)
    assert _outcome(rows, 3, VNU_2022)[0] == "not_completed"
    assert rows == original
    rows.append(attempt("B", "7.0", "3", "HỌC KỲ 1 - 2024-2025"))
    assert _outcome(rows, 3, VNU_2022)[0] == "completed"


@pytest.mark.parametrize("rows", [
    [attempt(), attempt("B", "7", "3")],  # Same term: no ordering proof.
    [attempt(), attempt("B", "7", "3", "unknown")],
    [attempt("B", "7", "3"), attempt("A+", "9", "4", "HỌC KỲ 2 - 2023-2024")],
    [attempt(), attempt("I", "", "", "HỌC KỲ 2 - 2023-2024")],
])
def test_ambiguous_or_unsupported_retakes_remain_unresolved(rows):
    assert _outcome(rows, 3, VNU_2022)[0] == "unresolved"
