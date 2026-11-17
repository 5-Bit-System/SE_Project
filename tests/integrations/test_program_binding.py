"""Explicit curriculum confirmation is per owner, never a global K68 default."""

import copy

import pytest
from fastapi.testclient import TestClient

from app.academic_policies import POLICY_VERSION
from app.auth import portal as account_portal
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
def client(monkeypatch, fake_accounts):
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

    def authenticated_save(value, binding, digest, scope):
        fake_accounts.check(value)
        return save(value.owner, value.generation, binding, digest, scope)

    monkeypatch.setattr(account_portal, "save_academic_binding", authenticated_save)
    with TestClient(app, base_url="http://127.0.0.1:8000") as value:
        value.headers["origin"] = "http://127.0.0.1:8000"
        value.data, value.writes = data, writes
        value.fake_accounts = fake_accounts
        yield value
    runtime.sessions.clear()


def authenticate(client, owner):
    client.fake_accounts.issue(client, owner, "synthetic-only", linked=True)


def confirmation(client, selected_program=None):
    setup = client.get("/me/academic-program").json()
    program = next(item for item in setup["programs"]
                   if item["program_id"] == (selected_program or setup["suggested_program_id"]))
    return {"program_id": program["program_id"], "cohort": setup["suggested_cohort"],
            "expected_catalog_revision": program["catalog_revision"],
            "expected_snapshot_digest": setup["snapshot_digest"],
            "expected_source_scope": setup["source_scope"], "confirm": True}


def use_reviewed_catalogs(monkeypatch):
    import app.program_bindings as bindings
    from app.api import academic
    from tests.support.catalog_fixtures import mark_catalog_reviewed_for_test

    list_catalogs = bindings.list_catalogs
    load_catalog = academic.load_catalog
    monkeypatch.setattr(
        bindings,
        "list_catalogs",
        lambda: [mark_catalog_reviewed_for_test(catalog) for catalog in list_catalogs()],
    )
    monkeypatch.setattr(
        academic,
        "load_catalog",
        lambda program_id: mark_catalog_reviewed_for_test(load_catalog(program_id)),
    )


def test_two_accounts_keep_different_programs_cohorts_and_completed_facts(client, monkeypatch):
    use_reviewed_catalogs(monkeypatch)
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
        client.fake_accounts.sessions.clear()
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
    assert data["courses"] is not None
    assert "program_binding_unverified" not in data["blocking_reasons"]
    assert client.writes == ["owner-a"]


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
    ("Toán học chương trình chuẩn", "toan_hoc_7460101_2022", 67),
    ("Toán tin", "toan_tin_7460117_2022", 69),
    ("Khoa học dữ liệu", KHDL, 70),
    ("Khoa học máy tính và thông tin", KHMT, 68),
])
def test_each_supported_program_uses_its_own_source_enrollment(client, monkeypatch, name, program, cohort):
    use_reviewed_catalogs(monkeypatch)
    authenticate(client, "owner-a")
    client.data["owner-a"]["profile"].update(program=name, cohort=str(cohort))
    body = confirmation(client, program)
    assert (body["program_id"], body["cohort"]) == (program, cohort)
    assert client.post("/me/academic-program", json=body).status_code == 200
    context = client.get(f"/me/academic-context?program_id={program}").json()
    assert context["status"] == "ready"
    assert context["program_id"] == program


def test_mathematics_requires_disambiguation_and_unsupported_program_is_not_published(client):
    from app.program_bindings import TALENT_PROGRAM_ID

    authenticate(client, "owner-a")
    client.data["owner-a"]["profile"].update(program="Toán học", cohort="68")
    setup = client.get("/me/academic-program").json()
    assert setup["suggested_program_id"] is None
    assert len(setup["programs"]) == 4
    assert TALENT_PROGRAM_ID in setup["program_candidates"]
    assert TALENT_PROGRAM_ID not in {item["program_id"] for item in setup["programs"]}
    body = confirmation(client, "toan_hoc_7460101_2022")
    body["program_id"] = TALENT_PROGRAM_ID
    assert client.post("/me/academic-program", json=body).json()["detail"] == "academic_program_not_supported"
    assert client.writes == []


def test_confirmation_requires_current_app_csrf(client):
    authenticate(client, "owner-a")
    body = confirmation(client)
    client.headers.pop('x-csrf-token')
    assert client.post('/me/academic-program', json=body).status_code == 403
    assert client.writes == []


@pytest.mark.parametrize('route', ['/me/academic-program', '/me/course-status'])
def test_owner_link_change_during_source_read_cannot_return_previous_owner_metadata(client, monkeypatch, route):
    authenticate(client, 'owner-a')

    def changed(owner):
        for link in client.fake_accounts.links.values():
            if link['owner'] == owner:
                link['owner'] = 'different-owner'
        return copy.deepcopy(client.data[owner])

    monkeypatch.setattr(store, 'profile', changed)
    response = client.get(route)
    assert response.status_code == 409
    assert response.json()['detail'] == 'vnu_not_connected'
    assert 'source_program' not in response.json()


def test_course_board_resolves_source_without_confirmation_or_writes(client, monkeypatch):
    use_reviewed_catalogs(monkeypatch)
    authenticate(client, "owner-a")
    before = copy.deepcopy(client.data)
    first = client.get("/me/course-status").json()
    second = client.get("/me/course-status").json()
    assert first["courses"] is not None
    assert first["program_id"] == KHMT
    assert "program_binding_unverified" not in first["blocking_reasons"]
    assert "program_selection" not in first
    assert first["context_revision"] == second["context_revision"]
    assert first["plan_basis"] == second["plan_basis"]
    assert client.data == before
    assert client.writes == []


def test_catalog_fingerprint_change_automatically_refreshes_source_binding(client, monkeypatch):
    from app.api import academic
    from app.program_bindings import source_binding

    use_reviewed_catalogs(monkeypatch)
    authenticate(client, "owner-a")
    selections = {"selected_track_id": "synthetic_track", "selected_graduation_path_id": "thesis"}
    before = client.get("/me/course-status", params=selections).json()
    assert before["status"] == "ready"
    metadata = client.data["owner-a"]["profile"]
    original_binding = source_binding(metadata, academic.load_catalog(KHMT))
    metadata["academic_binding"] = {**original_binding, "program_id": KHDL,
                                    "catalog_revision": "0" * 64}
    load_catalog = academic.load_catalog
    publication_revision = load_catalog(KHMT).program.catalog_revision

    def changed(program_id):
        catalog = load_catalog(program_id).model_copy(deep=True)
        catalog.program.name += " (synthetic metadata revision)"
        return catalog

    monkeypatch.setattr(academic, "load_catalog", changed)
    assert academic.load_catalog(KHMT).program.catalog_revision == publication_revision
    after = client.get("/me/course-status", params=selections).json()
    assert after["status"] == "ready"
    assert after["program_id"] == KHMT
    assert after["courses"] == before["courses"]
    assert after["context_revision"] != before["context_revision"]
    assert after["plan_basis"] != before["plan_basis"]
    binding = source_binding(metadata, academic.load_catalog(KHMT))
    assert binding["catalog_revision"] != original_binding["catalog_revision"]
    assert binding["confirmation_method"] == "portal_source_enrollment"
    assert "confirmed_at" not in binding
    assert client.writes == []


@pytest.mark.parametrize("source_change,reason", [
    ({"completeness": "unknown"}, "source_incomplete"),
    ({"attempts": "invalid"}, "source_rows_invalid"),
    ({"schema_version": 2}, "source_schema_unsupported"),
])
def test_automatic_curriculum_cannot_bypass_invalid_source(client, monkeypatch, source_change, reason):
    use_reviewed_catalogs(monkeypatch)
    authenticate(client, "owner-a")
    client.data["owner-a"]["snapshot"].update(source_change)
    response = client.get("/me/course-status")
    assert response.status_code == 200
    result = response.json()
    assert result["status"] == "needs_source_review"
    assert reason in result["blocking_reasons"]
    assert "program_binding_unverified" not in result["blocking_reasons"]
    assert "program_selection" not in result
    assert result["courses"] is result["progress"] is result["plan"] is None
    assert client.writes == []


@pytest.mark.parametrize("enrollment", [
    {"program": "Unsupported program", "cohort": "68"},
    {"program": "Toan hoc", "cohort": "68"},
    {"program": "Toan hoc tai nang", "cohort": "68"},
    {"program": "Khoa hoc du lieu", "cohort": None},
    {"program": None, "cohort": "68"},
])
def test_unresolved_enrollment_never_falls_back_to_stored_binding(client, monkeypatch, enrollment):
    use_reviewed_catalogs(monkeypatch)
    authenticate(client, "owner-a")
    client.data["owner-a"]["profile"]["academic_binding"] = {
        "program_id": KHMT, "verified": True, "evidence_ref": "synthetic:old"}
    client.data["owner-a"]["profile"].update(enrollment)
    result = client.get("/me/course-status").json()
    assert result["courses"] is None
    assert "source_enrollment_unresolved" in result["blocking_reasons"]
    assert "program_selection" not in result
    assert client.writes == []


def test_requested_program_cannot_override_source_enrollment(client, monkeypatch):
    use_reviewed_catalogs(monkeypatch)
    authenticate(client, "owner-a")
    response = client.get("/me/academic-context", params={"program_id": KHDL})
    assert response.status_code == 200
    context = response.json()
    assert context["status"] == "needs_source_review"
    assert "academic_program_source_mismatch" in context["blocking_reasons"]
    assert context["completed_course_codes"] == []
    assert client.get("/me/eligibility", params={"program_id": KHDL}).status_code == 409
    assert client.writes == []
