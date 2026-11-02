import pytest

from app.models import Catalog, Course, Program
from app.transcript import StudentTranscript


def test_transcript_summary_api_exposes_group_progress_without_counting_excluded(verified_client):
    response = verified_client.post(
        "/transcript/summary",
        json={
            "program_id": "khdl",
            "selected_track_id": "synthetic_track",
            "selected_graduation_path_id": "thesis",
            "records": [
                {"course_code": "PHI1006", "grade": 8},
                {"course_code": "CME1000", "grade": 9},
            ],
        },
    )
    assert response.status_code == 200
    result = response.json()
    assert result["progress"] is not None
    assert result["earned_credits"] == result["progress"]["total"]["earned_credits"] == 3
    assert result["progress"]["track"]["id"] == "synthetic_track"
    assert result["progress"]["graduation_path"]["id"] == "thesis"
    assert result["progress"]["warnings"]


def test_profile_summary_domain_exposes_progress_but_unowned_http_route_is_closed(verified_client):
    from app.api.routes import profile_transcript_summary
    from app.schemas.profile import TranscriptSummary
    assert verified_client.get('/profiles/khdl_01/transcript/summary').status_code == 410
    result = TranscriptSummary.model_validate(profile_transcript_summary('khdl_01')).model_dump()
    assert result["progress"] is not None
    assert result["progress"]["total"]["earned_credits"] == result["earned_credits"]


def progress_catalog():
    return Catalog(
        program=Program(
            program_id="test",
            name="Test",
            total_credits=12,
            catalog_status="draft_unverified",
            source_file="test",
            source_pages="1",
            blocks=[
                {
                    "id": "core",
                    "name": "Core",
                    "required_credits": 6,
                    "course_codes": ["A", "B", "X"],
                },
                {"id": "unknown", "name": "Unknown", "course_codes": []},
            ],
            choice_groups=[
                {"id": "g1", "name": "Group 1", "required_credits": 3},
                {"id": "g2", "name": "Group 2", "required_credits": 3},
            ],
            track_selection={
                "mode": "exactly_one_track",
                "tracks": [
                    {"id": "t1", "name": "Track 1", "choice_group_ids": ["g1"]},
                    {"id": "t2", "name": "Track 2", "choice_group_ids": ["g2"]},
                ],
            },
            graduation_selection={
                "mode": "exactly_one_path",
                "required_credits": 3,
                "paths": [
                    {
                        "id": "p",
                        "name": "Project",
                        "course_codes": ["B"],
                        "allowed_track_ids": ["t1"],
                    }
                ],
            },
        ),
        courses=[
            Course(
                code="A",
                name="A",
                credits=6,
                block="core",
                choice_group_ids=["g1", "g2"],
                counted_in_total=True,
            ),
            Course(code="B", name="B", credits=3, block="core", counted_in_total=True),
            Course(code="X", name="X", credits=3, block="core", counted_in_total=False),
        ],
    )


def test_counted_in_total_false_never_adds_earned_credits():
    catalog = progress_catalog()
    transcript = StudentTranscript(program_id="test", records=[{"course_code": "X", "grade": 9}])
    assert transcript.calculate_earned_credits(catalog) == 0
    assert transcript.calculate_gpa(catalog) is None
    assert transcript.calculate_gpa_10(catalog) is None


def test_passed_without_grade_does_not_invent_gpa():
    transcript = StudentTranscript(program_id="test", records=[{"course_code": "A"}])
    assert transcript.calculate_earned_credits(progress_catalog()) == 6
    assert transcript.calculate_gpa(progress_catalog()) is None


@pytest.mark.parametrize(
    "other",
    [
        {"course_code": "a", "grade": 9, "term": 1},
        {"course_code": " A ", "grade": 3, "term": 2},
    ],
)
def test_duplicate_transcript_rejected_without_guessing_retakes(other):
    with pytest.raises(ValueError, match="duplicate_course_code"):
        StudentTranscript(
            program_id="test", records=[{"course_code": "A", "grade": 9, "term": 1}, other]
        )


def test_progress_counts_total_once_and_preserves_group_memberships():
    from app.progress import calculate_progress

    progress = calculate_progress(progress_catalog(), {"A", "X"})
    assert progress.total.earned_credits == 6
    assert progress.total.remaining_credits == 6
    assert [g.earned_credits for g in progress.choice_groups] == [6, 6]
    assert [g.remaining_credits for g in progress.choice_groups] == [0, 0]
    assert progress.blocks[0].earned_credits == 6
    assert progress.blocks[1].required_credits is None
    assert progress.blocks[1].remaining_credits is None
    assert progress.track is None
    assert progress.graduation_path is None
    assert progress.warnings


def test_progress_track_path_and_draft_warning():
    from app.progress import calculate_progress

    progress = calculate_progress(progress_catalog(), {"A", "B"}, "t1", "p")
    assert progress.track.id == "t1"
    assert progress.track.earned_credits == 6
    assert progress.track.required_credits == 3
    assert progress.graduation_path.earned_credits == 3
    assert progress.graduation_path.remaining_credits == 0
    assert any("draft" in warning for warning in progress.warnings)


@pytest.mark.parametrize(
    "codes,track,path,error",
    [
        ({"FOREIGN"}, None, None, "unknown_passed_course_codes"),
        (set(), "bad", None, "invalid_track_id"),
        (set(), None, "bad", "invalid_graduation_path_id"),
        (set(), "t2", "p", "incompatible_track_graduation_path"),
    ],
)
def test_progress_rejects_invalid_catalog_selection(codes, track, path, error):
    from app.progress import calculate_progress

    with pytest.raises(ValueError, match=error):
        calculate_progress(progress_catalog(), codes, track, path)
