"""RAG/basic chat must stay independent of academic recommendation execution."""

import json
from pathlib import Path
import subprocess
import sys

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize("question,fragment", [
    ("Xin chào!", "Chào"), ("Cảm ơn bạn", "giúp"), ("Tạm biệt", "Hẹn"),
    ("Bạn có thể làm gì?", "học phần"), ("hello", "Chào"),
])
def test_basic_chat_has_no_academic_claims_or_fake_citations(question, fragment):
    from app.hus.chat import chat
    from app.schemas.hus import HUSQuestion
    from app.services.hus_service import get_hus_answerer

    result = chat(HUSQuestion(question=question, major="data_science"), get_hus_answerer())
    assert result.mode == "basic_chat" and fragment in result.reply
    assert result.hus_answer is None
    assert set(result.model_dump()) == {"mode", "reply", "hus_answer"}


@pytest.mark.parametrize("question", [
    "Kỳ tới nên học môn gì?", "Xếp thời khóa biểu cho tôi", "Thầy nào dễ tính?",
    "Gợi ý môn nào dễ qua", "Nên học MAT3533 vì thi cuối kỳ 20% đúng không?",
])
def test_out_of_scope_prompts_never_generate_recommendations(question):
    from app.hus.chat import chat
    from app.schemas.hus import HUSQuestion
    from app.services.hus_service import get_hus_answerer

    result = chat(HUSQuestion(question=question, major="data_science", version="QD3569-2023"), get_hus_answerer())
    assert result.mode == "hus_rag" and result.hus_answer.status == "no_information"
    assert not result.hus_answer.facts and not result.hus_answer.citations


@pytest.mark.parametrize("question,dataset,generated", [
    ("Giới thiệu ngành", "f1", False),
    ("Xin chào, MAT3533 có bao nhiêu tín chỉ?", "f2", False),
    ("Nội dung MAT3533?", "f3", True),
])
def test_rag_keeps_real_sources_and_f1_edition_separate(question, dataset, generated):
    from app.hus.chat import chat
    from app.schemas.hus import HUSQuestion
    from app.services.hus_service import get_hus_answerer

    answerer = get_hus_answerer()
    result = chat(HUSQuestion(question=question, major="data_science", version="QD3569-2023",
                              allow_generated_reference=generated), answerer)
    answer = result.hus_answer
    assert result.mode == "hus_rag" and result.reply == answer.reply
    assert answer.status == "answered" and answer.dataset == dataset and answer.citations
    assert answer.release_sha256 == answerer.data.release_identity["release_sha256"]
    if dataset == "f2":
        assert answer.facts["value"] == 3
    if dataset == "f3":
        assert all(c.display_label == "kiến thức AI" and c.open_url is None for c in answer.citations)


def test_f3_still_requires_opt_in_and_foreign_major_does_not_leak():
    from app.hus.chat import chat
    from app.schemas.hus import HUSQuestion
    from app.services.hus_service import get_hus_answerer

    answerer = get_hus_answerer()
    result = chat(HUSQuestion(question="Nội dung MAT3533?", major="data_science", version="QD3569-2023"), answerer)
    assert result.hus_answer.status == "needs_clarification" and not result.hus_answer.citations
    result = chat(HUSQuestion(question="Tín chỉ MAT3533 của ngành Toán tin?", major="data_science", version="QD3569-2023"), answerer)
    assert result.hus_answer.status == "no_information" and not result.hus_answer.facts


def test_explicit_f1_source_edition_is_not_replaced_with_current_edition():
    from app.hus.chat import chat
    from app.schemas.hus import HUSQuestion
    from app.services.hus_service import get_hus_answerer

    result = chat(HUSQuestion(question="Giới thiệu ngành", major="data_science", version="2010"), get_hus_answerer())
    assert result.hus_answer.status == "no_information" and not result.hus_answer.citations


def test_standalone_app_import_and_chat_do_not_reach_recommendation_or_auth():
    script = '''
import importlib.abc, json, sys
class RejectProductStack(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        banned = ('app.advisor','app.api','app.recommendation','app.rules','app.catalog',
                  'app.profiles','app.auth','app.integrations','app.services.advisor_service')
        if any(fullname == p or fullname.startswith(p + '.') for p in banned):
            raise AssertionError('RAG imported product stack: ' + fullname)
sys.meta_path.insert(0, RejectProductStack())
from fastapi.testclient import TestClient
from app.hus.demo import app
with TestClient(app) as client:
    config = client.get('/hus/config')
    assert config.status_code == 200 and len(config.json()['majors']) == 4
    for message in ['Xin chào', 'Kỳ tới nên học môn gì?', 'Giới thiệu ngành', 'Tín chỉ MAT3533?']:
        result = client.post('/hus/chat', json={'question':message,'major':'data_science','version':'QD3569-2023'})
        assert result.status_code == 200, result.text
        assert 'suggested_courses' not in result.json()
print('isolated-rag-ok')
'''
    result = subprocess.run([sys.executable, "-X", "utf8", "-c", script], cwd=ROOT,
                            capture_output=True, text=True, encoding="utf-8", timeout=60)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "isolated-rag-ok" in result.stdout


def test_demo_api_rejects_ranking_inputs_and_binds_source_binary_hash():
    import hashlib

    from app.hus.demo import app

    client = TestClient(app)
    payload = {"question": "Tín chỉ MAT3533?", "major": "data_science", "version": "QD3569-2023"}
    assert client.post("/hus/chat", json={**payload, "ranking_weights": {}}).status_code == 422
    response = client.post("/hus/chat", json=payload)
    assert response.status_code == 200
    citation = response.json()["hus_answer"]["citations"][0]
    binary = client.get(citation["open_url"])
    assert binary.status_code == 200 and binary.content.startswith(b"%PDF-")
    assert hashlib.sha256(binary.content).hexdigest() == citation["document_sha256"]
    assert client.get("/hus/sources/invalid").status_code == 404
    assert client.get("/me/recommendations").status_code == 404


def test_demo_corrupt_data_is_a_service_error_without_private_paths(monkeypatch):
    from app.hus import demo
    from app.hus.rag_loader import RAGDataError

    def corrupt():
        raise RAGDataError("private local path")

    monkeypatch.setattr(demo, "get_hus_answerer", corrupt)
    response = TestClient(demo.app).post("/hus/chat", json={"question": "Giới thiệu ngành", "major": "data_science"})
    assert response.status_code == 503 and "private local path" not in response.text
