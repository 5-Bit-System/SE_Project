from tests.support.catalog_fixtures import create_catalog_fixture
from tools.build_catalogs import prerequisite_clauses


def test_small_fixture_is_independent_and_preserves_domain_contract(tmp_path):
    from app.catalog import list_catalogs, load_catalog
    from app.profiles import _read_profiles, validate_profile
    from app.rules import evaluate_eligibility

    root, profiles_path = create_catalog_fixture(tmp_path, envelope=True)
    catalogs = list_catalogs(root)
    assert len(catalogs) == 4
    assert all(len(cat.courses) < 25 for cat in catalogs)
    profiles = _read_profiles(profiles_path)
    assert len(profiles) == 12
    for profile in profiles:
        validate_profile(profile, load_catalog(profile.program_id, root))
    catalog = load_catalog("khdl", root)
    blocked = {
        c.code for c in evaluate_eligibility(catalog, {"PHI1006", "MAT2505"}).blocked_courses
    }
    assert {"AND101", "CONFLICT101", "EXT101"} <= blocked
    assert "MAT3399" not in {c.code for c in load_catalog("toan_hoc", root).courses}
    assert catalog.metadata_schema_version == "1.0"
    assert catalog.courses[0].field_evidence


def test_parenthesized_and_or_prerequisites_preserve_meaning():
    clauses = prerequisite_clauses("(MAT3507\nMAT1202)/\nMAT3304")
    for passed, expected in [
        ({"MAT3507"}, False),
        ({"MAT1202"}, False),
        ({"MAT3507", "MAT1202"}, True),
        ({"MAT3304"}, True),
    ]:
        assert all(any(code in passed for code in group) for group in clauses) is expected


def test_fixture_source_rows_validate_and_conflict_variants_survive(catalog_root):
    import json

    from app.catalog import list_catalogs
    from tools.build_catalogs import build_courses, check_curriculum

    for catalog in list_catalogs(catalog_root):
        directory = catalog_root / catalog.program.program_id
        program = json.loads((directory / "curriculum.json").read_text(encoding="utf-8"))
        rows = json.loads((directory / "source_rows.json").read_text(encoding="utf-8"))
        assert check_curriculum(program, rows, build_courses(program, rows))["status"] == "passed"
        conflict = next(course for course in catalog.courses if course.code == "CONFLICT101")
        assert conflict.prerequisite_status in {"conflict", "source_conflict"}
        assert conflict.source_rows == [9, 15]
        assert conflict.prerequisite_variants == [[["PHI1006"]], [["MAT2400"]]]
        assert (
            next(course for course in catalog.courses if course.code == "CME1000").counted_in_total
            is False
        )


def test_fixture_enforces_track_graduation_and_external_reference_rules(catalog_root):
    from app.catalog import load_catalog
    from app.rules import evaluate_eligibility

    catalog = load_catalog("khdl", catalog_root)
    before = evaluate_eligibility(catalog, {"PHI1006", "MAT2505"})
    eligible = {course.code for course in before.eligible_courses}
    assert "OR101" in eligible
    assert "AND101" not in eligible
    assert "EXT101" not in eligible
    quota = evaluate_eligibility(
        catalog,
        {"PHI1006", "MAT2505", "ELECT101"},
        selected_track_id="synthetic_track",
        selected_graduation_path_id="thesis",
    )
    blocked = {course.code: course for course in quota.blocked_courses}
    assert any(reason.kind == "choice_group_full" for reason in blocked["ELECT102"].reasons)
    assert "THESIS101" in {course.code for course in quota.eligible_courses}
    assert "THESIS102" in blocked
