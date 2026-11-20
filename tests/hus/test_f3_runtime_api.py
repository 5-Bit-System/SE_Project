"""Real API with explicit v4 snapshot, synthetic provider and isolated rollback."""

import json
import shutil

import httpx
import pytest
from fastapi.testclient import TestClient

from app.hus.answering import HUSAnswerer
from app.hus.demo import app
from app.hus.rag_loader import HUSRAGData
from tests.hus.llm.test_pipeline import transport
from tests.hus.llm.test_rollback import reply_from_bundle
from tests.hus.test_f3_runtime_release import CANDIDATE, PARENT, save

MAJORS = [
    ("mathematics", "QD3565-2023"),
    ("mathematics_informatics", "QD3567-2023"),
    ("computer_science", "QD3568-2023"),
    ("data_science", "QD3569-2023"),
]


@pytest.fixture(scope="module")
def pair(tmp_path_factory, historical_v3_data):
    from app.hus.f3_runtime_release import build_release, stage_preview

    root = tmp_path_factory.mktemp("f3-api")
    release = save(build_release(PARENT, CANDIDATE), root / "v4")
    stage_preview(release, root / "preview")
    return historical_v3_data, HUSRAGData.load_current(root / "preview"), root / "preview"


@pytest.fixture(autouse=True)
def config(monkeypatch):
    monkeypatch.setenv("HUS_LLM_ENABLED", "false")
    monkeypatch.setenv("HUS_RETRIEVAL_MODE", "lexical")
    monkeypatch.setenv("HUS_LLM_API_KEY", "synthetic-v4-key")
    monkeypatch.setenv("HUS_LLM_MODEL", "gemini-3.5-flash-lite")
    monkeypatch.setenv(
        "HUS_LLM_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai"
    )
    from app.services.hus_service import get_hus_answerer

    get_hus_answerer.cache_clear()
    yield
    get_hus_answerer.cache_clear()


@pytest.fixture
def client(pair, monkeypatch):
    monkeypatch.setattr("app.hus.demo.get_hus_answerer", lambda: HUSAnswerer(pair[1]))
    with TestClient(app) as value:
        yield value


def payload(major="data_science", version="QD3569-2023", field="content"):
    return {
        "question": ("Nội dung" if field == "content" else "Mục tiêu") + " CME1000?",
        "major": major,
        "version": version,
        "allow_generated_reference": True,
        "allow_llm_rewrite": True,
    }


@pytest.mark.parametrize("major,version", MAJORS)
def test_selected_default_v4_uses_real_service_and_preserves_parent_contracts(
    monkeypatch, historical_v3_data, major, version
):
    """Exercise shared CURRENT, without replacing the answerer or data loader."""
    from app.hus.chat import chat
    from app.hus.question_catalog import question_catalog
    from app.schemas.hus import HUSQuestion
    from app.services.hus_service import get_hus_answerer

    monkeypatch.delenv("HUS_RAG_ROOT", raising=False)
    calls = transport(monkeypatch, lambda r: pytest.fail("Disabled LLM called provider"))
    get_hus_answerer.cache_clear()
    with TestClient(app) as cli:
        config = cli.get("/hus/config").json()
        assert config["release_id"] == "hus-data-20261111-v4"
        assert config["llm_rewrite_available"] is False
        menu = cli.get("/hus/questions", params={"major": major, "version": version}).json()
        old_menu = question_catalog(historical_v3_data, major=major, version=version)
        for group in ("f1", "f2", "help"):
            assert next(g for g in menu["groups"] if g["id"] == group) == next(
                g for g in old_menu["groups"] if g["id"] == group
            )
        ai_questions = next(g for g in menu["groups"] if g["id"] == "f3")["questions"]
        assert {q["request"]["field"] for q in ai_questions} == {"content", "objectives"}
        for question in ("Giới thiệu ngành", "Tín chỉ CME1000?", "Tiên quyết CME1000?"):
            request = {"question": question, "major": major, "version": version}
            original = chat(HUSQuestion(**request), HUSAnswerer(historical_v3_data))
            response = cli.post("/hus/chat", json=request)
            assert response.status_code == 200
            value = response.json()
            assert value["reply"] == original.reply
            assert value["hus_answer"]["facts"] == original.hus_answer.model_dump(mode="json")["facts"]
            assert value["hus_answer"]["release_id"] == "hus-data-20261111-v4"
        denied = cli.post("/hus/chat", json={**payload(major, version), "allow_generated_reference": False})
        assert denied.json()["hus_answer"]["status"] == "needs_clarification"
        for field in ("content", "objectives"):
            value = cli.post("/hus/chat", json=payload(major, version, field)).json()
            assert set(value) == {"mode", "reply", "hus_answer"}
            answer = value["hus_answer"]
            assert answer["status"] == "answered" and answer["release_id"] == config["release_id"]
            assert all(c["display_label"] == "kiến thức AI" and c["open_url"] is None
                       for c in answer["citations"])
        absent = cli.post("/hus/chat", json={**payload(major, version), "question": "Gợi ý đánh giá CME1000?"})
        assert absent.json()["hus_answer"]["status"] == "no_information"
        assert calls == []


@pytest.mark.parametrize("major,version", MAJORS)
@pytest.mark.parametrize("field", ["content", "objectives"])
def test_real_api_two_fields_preserves_exact_source_unit_locators(
    client, pair, major, version, field
):
    from app.hus.f3_detail import section_texts

    source = {
        r["record_id"]: r
        for r in map(json.loads, (CANDIDATE / "records.jsonl").read_bytes().splitlines())
    }
    result = client.post("/hus/chat", json=payload(major, version, field))
    assert result.status_code == 200
    value = result.json()
    answer = value["hus_answer"]
    assert (
        answer["status"] == "answered"
        and answer["release_id"] == pair[1].release_identity["release_id"]
    )
    assert set(value) == {"mode", "reply", "hus_answer"}
    for citation in answer["citations"]:
        assert citation["evidence_kind"] == "ai" and citation["display_label"] == "kiến thức AI"
        assert citation["open_url"] is None and citation["metadata"]["field"] == field
        loc = citation["locator"]
        record = source[loc["record_id"]]
        assert (
            citation["quote"] == section_texts(record)[field][loc["start_char"] : loc["end_char"]]
        )


@pytest.mark.parametrize("major,version", MAJORS)
def test_menu_only_two_fields_and_f1_f2_menu_is_unchanged(client, pair, major, version):
    from app.hus.question_catalog import question_catalog

    old = question_catalog(pair[0], major=major, version=version)
    current = client.get("/hus/questions", params={"major": major, "version": version}).json()
    for group in ("f1", "f2", "help"):
        assert next(g for g in old["groups"] if g["id"] == group) == next(
            g for g in current["groups"] if g["id"] == group
        )
    questions = next(g for g in current["groups"] if g["id"] == "f3")["questions"]
    assert {q["request"]["field"] for q in questions} == {"content", "objectives"}
    assert len(questions) == 2 * len(pair[1].f2_courses(major=major, version=version))
    assert all(
        "allow_generated_reference" not in q["request"] and q["requires_ai"] for q in questions
    )


@pytest.mark.parametrize("major,version", MAJORS)
@pytest.mark.parametrize(
    "question", ["Giới thiệu ngành", "CME1000 có bao nhiêu tín chỉ?", "Tiên quyết CME1000?"]
)
def test_f1_f2_reply_facts_and_source_hashes_preserved(client, pair, major, version, question):
    from app.hus.chat import chat
    from app.schemas.hus import HUSQuestion

    request = {"question": question, "major": major, "version": version}
    old = chat(HUSQuestion(**request), HUSAnswerer(pair[0])).model_dump(mode="json")
    new = client.post("/hus/chat", json=request).json()
    assert new["reply"] == old["reply"] and new["hus_answer"]["facts"] == old["hus_answer"]["facts"]
    fields = ("quote", "source_url", "review_status", "document_sha256", "pdf_pages")
    assert [[c[k] for k in fields] for c in new["hus_answer"]["citations"]] == [
        [c[k] for k in fields] for c in old["hus_answer"]["citations"]
    ]


@pytest.mark.parametrize(
    "question", ["Gợi ý đánh giá CME1000?", "CME1000 thi cuối kỳ bao nhiêu phần trăm?", "Xin chào"]
)
def test_absent_assessment_and_basic_never_call_model(client, monkeypatch, question):
    monkeypatch.setenv("HUS_LLM_ENABLED", "true")
    calls = transport(monkeypatch, lambda r: pytest.fail("No evidence must not call provider"))
    result = client.post("/hus/chat", json={**payload(), "question": question})
    assert result.status_code == 200 and calls == []
    if question != "Xin chào":
        assert result.json()["hus_answer"]["status"] == "no_information"
        assert result.json()["hus_answer"]["citations"] == []


@pytest.mark.parametrize("consent", ["allow_generated_reference", "allow_llm_rewrite"])
def test_two_permissions_remain_independent(client, monkeypatch, consent):
    monkeypatch.setenv("HUS_LLM_ENABLED", "true")
    calls = transport(monkeypatch, lambda r: pytest.fail("Missing consent called provider"))
    response = client.post("/hus/chat", json={**payload(), consent: False}).json()
    assert calls == []
    if consent == "allow_generated_reference":
        assert response["hus_answer"]["status"] == "needs_clarification"
    else:
        assert response["hus_answer"]["status"] == "answered" and "generation" not in response


@pytest.mark.parametrize("failure", ["quota", "timeout", "invalid"])
def test_mock_provider_failures_preserve_canonical(client, monkeypatch, failure):
    original = client.post("/hus/chat", json=payload()).json()

    def fail(request):
        if failure == "timeout":
            raise httpx.ReadTimeout("synthetic timeout", request=request)
        return httpx.Response(429 if failure == "quota" else 200, json={})

    calls = transport(monkeypatch, fail)
    monkeypatch.setenv("HUS_LLM_ENABLED", "true")
    value = client.post("/hus/chat", json=payload()).json()
    assert len(calls) == 1 and value["generation"]["used"] is False
    assert value["reply"] == original["reply"] and value["hus_answer"] == original["hus_answer"]


def test_mock_success_and_rollback_restore_original(client, monkeypatch):
    original = client.post("/hus/chat", json=payload()).json()
    calls = transport(monkeypatch, reply_from_bundle)
    monkeypatch.setenv("HUS_LLM_ENABLED", "true")
    rewritten = client.post("/hus/chat", json=payload()).json()
    assert rewritten["generation"]["used"] is True and len(calls) == 1
    assert rewritten["hus_answer"] == original["hus_answer"]
    monkeypatch.setenv("HUS_LLM_ENABLED", "false")
    assert client.post("/hus/chat", json=payload()).json() == original and len(calls) == 1


@pytest.mark.parametrize("major,version", MAJORS)
def test_isolated_root_v3_v4_v3_restores_exact_api_and_menu(
    pair, tmp_path, monkeypatch, major, version
):
    from app.hus.data_release import encoded
    from app.services.hus_service import get_hus_answerer

    root = tmp_path / "rag"
    shutil.copytree(pair[2], root)
    shutil.copytree(PARENT, root / "releases" / PARENT.name)
    v4 = (root / "CURRENT.json").read_bytes()
    v3 = encoded(
        {
            "schema_version": "2.0",
            "state": "isolated_rollback_test",
            "release_id": PARENT.name,
            "release_path": "releases/" + PARENT.name,
            "release_sha256": pair[0].release_identity["release_sha256"],
            "index_entrypoint": "chunks.jsonl",
            "generated_reference_requires_opt_in": True,
        }
    )
    monkeypatch.setenv("HUS_RAG_ROOT", str(root))
    with TestClient(app) as cli:
        values = []
        for pointer in (v3, v4, v3):
            (root / "CURRENT.json").write_bytes(pointer)
            get_hus_answerer.cache_clear()
            values.append(
                (
                    cli.post("/hus/chat", json=payload(major, version)).json(),
                    cli.get("/hus/questions", params={"major": major, "version": version}).json(),
                )
            )
    assert values[0] == values[2] and values[0] != values[1]
    assert values[1][0]["hus_answer"]["release_id"] == pair[1].release_identity["release_id"]


def test_old_vector_contract_rejects_new_release(pair):
    from app.hus.vector_contract import verify_contract_files
    from app.hus.vector_runtime import CONTRACT_PATH

    with pytest.raises(ValueError):
        verify_contract_files(CONTRACT_PATH, pair[1])


def test_inherited_source_binary_opens_under_new_release(client, pair):
    import hashlib

    response = client.post(
        "/hus/chat",
        json={
            "question": "CME1000 có bao nhiêu tín chỉ?",
            "major": "data_science",
            "version": "QD3569-2023",
        },
    ).json()
    citation = response["hus_answer"]["citations"][0]
    assert citation["availability"] == "available"
    binary = client.get(citation["open_url"].split("#")[0])
    assert binary.status_code == 200 and binary.content.startswith(b"%PDF-")
    assert hashlib.sha256(binary.content).hexdigest() == citation["document_sha256"]
    assert (
        pair[1].citation_context["asset_release_sha256"]
        == pair[0].release_identity["release_sha256"]
    )


def test_foreign_asset_registry_is_still_rejected(pair, tmp_path):
    from app.hus.citation_assets import DEFAULT_ASSET_ROOT
    from app.hus.citations import CitationResolver
    from app.hus.data_release import digest, encoded

    registry = json.loads((DEFAULT_ASSET_ROOT / "registry.json").read_bytes())
    registry["release_sha256"] = "f" * 64
    registry.pop("registry_sha256")
    registry["registry_sha256"] = digest(encoded(registry))
    (tmp_path / "registry.json").write_bytes(encoded(registry))
    assert CitationResolver(pair[1], asset_root=tmp_path).assets.problem is not None
