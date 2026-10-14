"""Small invented catalogs for tests; never copies curriculum/PDF datasets."""

import json
from pathlib import Path

from app.models import Catalog, Course, Program
from app.transcript import PROGRAM_ALIASES
from tools.build_catalogs import build_courses

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
FIXTURE_CATALOGS_ROOT = FIXTURES_DIR / "catalogs"
FIXTURE_PROFILES_PATH = FIXTURES_DIR / "demo_profiles.json"


def create_catalog_fixture(root: Path, *, envelope: bool = False) -> tuple[Path, Path]:
    """Write four synthetic programs and twelve profiles under a caller-owned root."""
    catalogs_root = root / "catalogs"
    profiles = []
    for alias in ("khdl", "khmtt", "toan_hoc", "toan_tin"):
        program_id = PROGRAM_ALIASES[alias]
        directory = catalogs_root / program_id
        directory.mkdir(parents=True, exist_ok=True)
        specs = [
            ("PHI1006", 3, ""),
            ("MAT2505", 3, ""),
            ("PEC1008", 2, ""),
            ("MAT2400", 3, ""),
            ("CME1000", 3, ""),
            ("AND101", 3, "PHI1006 MAT2400"),
            ("OR101", 3, "PHI1006/MAT2400"),
            ("EXT101", 3, "EXT9999"),
            ("CONFLICT101", 3, "PHI1006"),
            ("ELECT101", 3, ""),
            ("ELECT102", 3, ""),
            ("THESIS101", 3, "MAT2505"),
            ("THESIS102", 3, "MAT2400"),
            ("MAT3399" if alias == "khdl" else f"{alias.upper()}101", 3, "MAT2505"),
        ]
        rows = [
            dict(
                source_row=i,
                source_page=1,
                code=code,
                name=f"Synthetic {code}",
                name_en=None,
                credits=credits,
                hours={"lecture": 15, "practice": None, "self_study": 30},
                prerequisites_raw=prereq,
            )
            for i, (code, credits, prereq) in enumerate(specs, 1)
        ]
        rows.append({**rows[8], "source_row": len(rows) + 1, "prerequisites_raw": "MAT2400"})
        groups = [
            dict(
                id="elective_a",
                name="Synthetic elective A",
                required_credits=3,
                selection_mode="choose_credits",
                course_codes=["ELECT101", "ELECT102"],
                listed_credits=6,
                source_rows=[10, 11],
            )
        ]
        program = dict(
            program_id=program_id,
            name=f"Synthetic {alias}",
            total_credits=32,
            catalog_revision="synthetic-v1",
            catalog_status="draft_unverified",
            source_file="synthetic-test-data (not a university curriculum)",
            source_pages="1-1",
            choice_groups=groups,
            excluded_from_total=["CME1000"],
            blocks=[
                dict(
                    id="field",
                    required_credits=32,
                    course_codes=[s[0] for s in specs],
                    required_course_codes=[
                        code
                        for code, _, _ in specs
                        if code not in {"CME1000", "ELECT101", "ELECT102", "THESIS101", "THESIS102"}
                    ],
                )
            ],
            major_credit_structure=dict(required=26, elective=3, graduation=3),
            track_selection=dict(
                mode="exactly_one_track",
                tracks=[
                    dict(
                        id="synthetic_track",
                        name="Synthetic track",
                        choice_group_ids=["elective_a"],
                    )
                ],
            ),
            graduation_selection=dict(
                mode="exactly_one_path",
                required_credits=3,
                paths=[
                    dict(
                        id="thesis",
                        name="Synthetic thesis",
                        course_codes=["THESIS101"],
                        allowed_track_ids=["synthetic_track"],
                    ),
                    dict(
                        id="project",
                        name="Synthetic project",
                        course_codes=["THESIS102"],
                        allowed_track_ids=["synthetic_track"],
                    ),
                ],
            ),
            digitization=dict(
                numbered_source_rows=len(rows),
                source_course_entries=len(rows),
                unnumbered_course_rows=0,
                unique_course_codes=len(specs),
                status="complete",
                review_status="synthetic",
            ),
            source_issues=[],
            notes=["Invented fixture. No claim of curriculum completeness or source verification."],
        )
        courses = build_courses(program, rows)
        document = courses
        if envelope:
            program.update(metadata_schema_version="1.0", vocabulary_version="1.0")
            evidence_fields = (
                "code",
                "name",
                "credits",
                "block",
                "requirement_type",
                "counted_in_total",
                "hours",
                "prerequisites",
                "choice_group_ids",
                "graduation_path_ids",
                "source_page",
            )
            for course in courses:
                course["prerequisite_status"] = (
                    "conflict"
                    if course["prerequisite_status"] == "source_conflict"
                    else "unresolved_external"
                    if course["external_prerequisite_codes"]
                    else "draft_unverified"
                )
                course["source_status"] = "draft_unverified"
                course["offering_status"] = "unknown"
                course["topics"] = None
                course["field_evidence"] = {
                    field: [
                        dict(
                            source_ref="synthetic-fixture",
                            locator=f"source row {course['source_rows'][0]}",
                            method="transcription",
                            status="draft_unverified",
                        )
                    ]
                    for field in evidence_fields
                }
                if course["prerequisite_status"] == "conflict":
                    course["field_evidence"]["prerequisites"].append(
                        dict(
                            source_ref="synthetic-fixture",
                            locator="source row 15",
                            method="transcription",
                            status="conflict",
                        )
                    )
            courses[0]["topics"] = ["synthetic_foundation"]
            courses[0]["field_evidence"]["topics"] = [
                dict(
                    source_ref="synthetic-fixture",
                    locator="test specification",
                    method="curated_mapping",
                    rubric_ref="synthetic-topics-v1",
                    status="draft_unverified",
                )
            ]
            document = dict(
                metadata_schema_version="1.0",
                vocabulary_version="1.0",
                program_id=program_id,
                catalog_revision="synthetic-v1",
                courses=courses,
            )
            _write(
                directory / "vocabulary.json",
                dict(vocabulary_version="1.0", topics=["synthetic_foundation"], career_paths=[]),
            )
        _write(directory / "curriculum.json", program)
        _write(directory / "source_rows.json", rows)
        _write(directory / "courses.json", document)
        for index in range(1, 4):
            records = [dict(course_code="PHI1006", grade=8.0, term=1)]
            if index >= 2:
                records.append(dict(course_code="MAT2505", grade=9.0, term=1))
            if index == 3:
                records.append(
                    dict(
                        course_code="MAT3399" if alias == "khdl" else f"{alias.upper()}101",
                        grade=7.0,
                        term=2,
                    )
                )
            profiles.append(
                dict(
                    profile_id=f"{alias}_{index:02}",
                    program_id=program_id,
                    label=f"Synthetic {alias} profile {index}",
                    current_term=3,
                    target_track="synthetic_track",
                    preferences={},
                    records=records,
                )
            )
    profiles_path = root / "demo_profiles.json"
    _write(profiles_path, profiles)
    return catalogs_root, profiles_path


def _write(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def get_toy_catalog() -> Catalog:
    return Catalog(
        program=Program(
            program_id="toy",
            name="Toy Program",
            total_credits=12,
            catalog_status="draft_unverified",
            source_file="test",
            source_pages="1",
        ),
        courses=[
            Course(code="TOY101", name="Intro Toy", credits=3, block="general"),
            Course(
                code="TOY102", name="Adv Toy", credits=3, block="major", prerequisites=[["TOY101"]]
            ),
        ],
    )
