"""Explicit curriculum confirmation is per owner, never a global K68 default."""

import copy

import pytest
from fastapi.testclient import TestClient

from app.academic_policies import POLICY_VERSION
from app.integrations.daotao import runtime, store
from app.integrations.daotao.snapshot import PortalFailure
from app.main import app
from app.program_bindings import binding_current, source_cohort, source_program, source_scope

KHMT = "khmtt_7480113qtd_2022"
KHDL = "khdl_7460108_2022"


def source(program, cohort, digest, grade="7.5", letter="B", grade4="3"):
    return {"subject": "synthetic-only", "profile": {"program": program, "cohort": cohort},
            "snapshot": {"schema_version": 1, "digest": digest, "completeness": "complete",
                         "unknown_rows": [], "attempts": [{"row_key": "1", "code": "PHI1006",
                             "credits": "3", "grade10": grade, "letter": letter,
                             "grade4": grade4, "term": "HỌC KỲ 1 - 2023-2024"}]},
            "fetched_at": None}


@pytest.fixture
def client(monkeypatch):
    runtime.sessions.clear()
    data = {"owner-a": source("Khoa học máy tính và thông tin", "68", "source-a"),
            "owner-b": source("Khoa học dữ liệu", "67", "source-b", "0", "F", "0")}
    writes = []
    monkeypatch.setattr(store, "profile", lambda owner: copy.deepcopy(data[owner]))

    def save(owner, generation, binding, digest, scope):
        current = data[owner]
        if (current["snapshot"]["digest"] != digest
                or source_scope(current["profile"]) != scope):
            raise PortalFailure("context_changed")
        current["profile"]["academic_binding"] = copy.deepcopy(binding)
        writes.append(owner)
        return "confirmed"

    monkeypatch.setattr(store, "save_academic_binding", save)
    with TestClient(app, base_url="http://127.0.0.1:8000") as value:
        value.headers["origin"] = "http://127.0.0.1:8000"
        value.data, value.writes = data, writes
        yield value
    runtime.sessions.clear()


def authenticate(client, owner):
    token = runtime.new_session(owner, "synthetic-only", 0)
    client.cookies.set("study_portal_session", token)


def confirmation(client, selected_program=None):
    setup = client.get("/me/academic-program").json()
    program = next(item for item in setup["programs"]
                   if item["program_id"] == (selected_program or setup["suggested_program_id"]))
    return {"program_id": program["program_id"], "cohort": setup["suggested_cohort"],
            "expected_catalog_revision": program["catalog_revision"],
            "expected_snapshot_digest": setup["snapshot_digest"],
            "expected_source_scope": setup["source_scope"], "confirm": True}


def test_two_accounts_keep_different_programs_cohorts_and_completed_facts(client):
    assert client.get("/me/academic-program").status_code == 401
    for owner, program, cohort, expected in [("owner-a", KHMT, 68, ["PHI1006"]),
                                             ("owner-b", KHDL, 67, [])]:
        authenticate(client, owner)
        body = confirmation(client)
        assert (body["program_id"], body["cohort"]) == (program, cohort)
        assert owner not in client.writes  # Reading/suggesting never confirms automatically.
        response = client.post("/me/academic-program", json=body)
        assert response.status_code == 200
        context = client.get(f"/me/academic-context?program_id={program}").json()
        assert context["status"] == "ready"
        assert context["completed_course_codes"] == expected
        assert client.data[owner]["profile"]["academic_binding"]["policy_version"] == POLICY_VERSION
    assert client.writes == ["owner-a", "owner-b"]
    assert client.data["owner-a"]["profile"]["academic_binding"]["program_id"] == KHMT


def test_cross_account_and_wrong_program_confirmation_cannot_change_other_enrollment(client):
    authenticate(client, "owner-a")
    a = confirmation(client)
    authenticate(client, "owner-b")
    assert client.post("/me/academic-program", json=a).status_code == 409
    b = confirmation(client)
    other = client.get("/me/academic-program").json()["programs"][0]
    b.update(program_id=KHMT, expected_catalog_revision=other["catalog_revision"])
    assert client.post("/me/academic-program", json=b).status_code == 409
    assert client.writes == []
    assert all("academic_binding" not in value["profile"] for value in client.data.values())


@pytest.mark.parametrize("change", ["snapshot", "enrollment", "catalog"])
def test_stale_confirmation_is_rejected(client, change):
    authenticate(client, "owner-a")
    body = confirmation(client)
    if change == "snapshot":
        client.data["owner-a"]["snapshot"]["digest"] = "new-source"
    elif change == "enrollment":
        client.data["owner-a"]["profile"]["cohort"] = "69"
    else:
        body["expected_catalog_revision"] = "0" * 64
    response = client.post("/me/academic-program", json=body)
    assert response.status_code == 409
    assert response.json()["detail"] == "context_changed"
    assert client.writes == []


def test_confirmation_requires_consent_and_rejects_student_facts_or_review_flags(client):
    authenticate(client, "owner-a")
    body = confirmation(client)
    for flag in (False, "true", 1):
        assert client.post("/me/academic-program", json={**body, "confirm": flag}).status_code == 422
    for field in ("owner", "records", "passed_course_codes", "verified", "policy_version"):
        assert client.post("/me/academic-program", json={**body, field: "forged"}).status_code == 422
    assert client.writes == []


def test_logout_during_profile_read_prevents_program_confirmation(client, monkeypatch):
    authenticate(client, "owner-a")
    body = confirmation(client)

    def revoked(owner):
        runtime.sessions.clear()
        return copy.deepcopy(client.data[owner])

    monkeypatch.setattr(store, "profile", revoked)
    assert client.post("/me/academic-program", json=body).status_code == 401
    assert client.writes == []


def test_source_enrollment_change_invalidates_prior_owner_confirmation(client):
    authenticate(client, "owner-a")
    assert client.post("/me/academic-program", json=confirmation(client)).status_code == 200
    profile = client.data["owner-a"]["profile"]
    assert binding_current(profile)
    profile["cohort"] = "69"
    assert not binding_current(profile)
    data = client.get("/me/course-status").json()
    assert data["status"] == "needs_program_binding"
    assert data["courses"] is None


def test_unknown_or_unsupported_source_enrollment_has_no_default_program_or_cohort(client):
    authenticate(client, "owner-a")
    body = confirmation(client)
    client.data["owner-a"]["profile"].update(program="Invented unsupported major", cohort="unresolved")
    setup = client.get("/me/academic-program").json()
    assert setup["suggested_program_id"] is setup["suggested_cohort"] is None
    body["expected_source_scope"] = setup["source_scope"]
    assert client.post("/me/academic-program", json=body).json()["detail"] == "source_enrollment_unresolved"
    assert source_program({"program": "Khoa học máy tính & thông tin"}) == KHMT
    assert source_cohort({"cohort": "K68"}) == 68
    assert source_cohort({"cohort": "2023"}) == 68
    assert source_cohort({"cohort": "66"}) is None
    assert source_cohort({"cohort": "2099001"}) is None  # Never derive from an identifier.


def test_binding_does_not_override_unknown_completeness(client):
    authenticate(client, "owner-a")
    client.data["owner-a"]["snapshot"]["completeness"] = "unknown"
    assert client.post("/me/academic-program", json=confirmation(client)).status_code == 200
    result = client.get("/me/course-status").json()
    assert result["courses"] is None
    assert "source_incomplete" in result["blocking_reasons"]


@pytest.mark.parametrize("name,program,cohort", [
    ("Toán học", "toan_hoc_7460101_2022", 67),
    ("Toán tin", "toan_tin_7460117_2022", 69),
    ("Khoa học dữ liệu", KHDL, 70),
    ("Khoa học máy tính và thông tin", KHMT, 68),
])
def test_each_supported_program_uses_its_own_source_enrollment(client, name, program, cohort):
    authenticate(client, "owner-a")
    client.data["owner-a"]["profile"].update(program=name, cohort=str(cohort))
    body = confirmation(client, program)
    assert (body["program_id"], body["cohort"]) == (program, cohort)
    assert client.post("/me/academic-program", json=body).status_code == 200
    context = client.get(f"/me/academic-context?program_id={program}").json()
    assert context["status"] == "ready"
    assert context["program_id"] == program


def test_mathematics_requires_disambiguation_and_talented_rules_stay_explicitly_gated(client):
    from app.academic_catalogs import TALENT_PROGRAM_ID

    authenticate(client, "owner-a")
    client.data["owner-a"]["profile"].update(program="Toán học", cohort="68")
    setup = client.get("/me/academic-program").json()
    assert setup["suggested_program_id"] is None
    assert set(setup["program_candidates"]) == {"toan_hoc_7460101_2022", TALENT_PROGRAM_ID}
    body = confirmation(client, TALENT_PROGRAM_ID)
    assert client.post("/me/academic-program", json=body).status_code == 200
    context = client.get(f"/me/academic-context?program_id={TALENT_PROGRAM_ID}").json()
    assert context["status"] == "needs_policy_review"
    assert context["completed_course_codes"] == []
    assert "program_rules_review_required" in context["blocking_reasons"]
    board = client.get('/me/course-status?selected_graduation_path_id=thesis').json()
    assert board["status"] == "partial"
    assert board["can_plan"] is False
    assert [item["code"] for item in board["courses"]["completed"]] == ["PHI1006"]
    # Default availability is independent of the global planning pause.
    available = {course["code"]: course for course in board["courses"]["eligible"]}
    assert available["CME1000"]["eligibility_basis"] == "excluded_from_total"
    assert all(course["eligibility_basis"] in {
        "excluded_from_total", "no_prerequisites", "requested_default"
    } for course in available.values())
    assert all(course["suggested"] is False for course in available.values())
    assert "program_rules_review_required" in board["blocking_reasons"]
    assert board["plan"]["course_codes"] == []
    assert board["plan"]["suggested_credits"] == 0
