"""Versioned interpretations of the published VNU 3626/2022 grade rules.

This is not a program binding, a source completeness declaration or a GPA
calculator. Those are separate decisions. See docs/policies/README.md.
"""

from app.academic_context import AcademicPolicy
from app.catalog_contracts import EXPECTED_PROGRAM_IDS

POLICY_VERSION = "vnu-3626-2022-grades-v1"
POLICY_SOURCE = "docs/policies/vnu_3626_2022.pdf#page=42"
VNU_2022 = AcademicPolicy(
    version=POLICY_VERSION,
    source_ref=POLICY_SOURCE,
    program_ids=tuple(sorted(EXPECTED_PROGRAM_IDS)),
    letter_bands={
        "A+": (9, 10, 4), "A": (8.5, 8.9, 3.7), "B+": (8, 8.4, 3.5),
        "B": (7, 7.9, 3), "C+": (6.5, 6.9, 2.5), "C": (5.5, 6.4, 2),
        "D+": (5, 5.4, 1.5), "D": (4, 4.9, 1), "F": (0, 3.9, 0),
        "P": (5, 10, None),
    },
    min_cohort=67,
    # Article 21(4–5): F retakes and D/D+ improvements. Only a later, published
    # final grade in an unambiguous source term can replace an earlier result.
    retake_strategy="later_final_after_f_d_or_d_plus",
)
POLICIES = {POLICY_VERSION: VNU_2022}
