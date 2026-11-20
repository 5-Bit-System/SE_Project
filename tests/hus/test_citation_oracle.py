"""Prove the independent acceptance oracle rejects plausible citation regressions."""

from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from app.hus.answering import HUSAnswerer
from app.hus.demo import app
from app.hus.retrieval import _body
from app.schemas.hus import HUSQuestion
from tools.verify_hus_e2e import EvidenceOracle


@pytest.fixture(scope="module")
def oracle(historical_v3_root):
    # This oracle's binary registry and full-text F3 checks are sealed to v3.
    return EvidenceOracle(package=historical_v3_root)


@pytest.fixture(scope="module")
def answerer(historical_v3_data):
    return HUSAnswerer(historical_v3_data)


@pytest.fixture(scope="module")
def answers(answerer):
    requests = {
        "f1": HUSQuestion(question="Mục tiêu đào tạo", major="mathematics", dataset="f1", field="objectives",
                          version="2008", program_variant="advanced"),
        "f2": HUSQuestion(question="Tiên quyết MAT3325?", major="mathematics", version="QD3565-2023"),
        "f3": HUSQuestion(question="Nội dung MAT3533?", major="data_science", version="QD3569-2023",
                          allow_generated_reference=True),
    }
    return {key: answerer.answer(request).model_dump() for key, request in requests.items()}


def _check(oracle, answer):
    oracle.check(answer, answer["major"], dataset=answer["dataset"], version=answer["version"],
                 code={"f1": None, "f2": "MAT3325", "f3": "MAT3533"}[answer["dataset"]])


@pytest.mark.parametrize("dataset", ["f1", "f2", "f3"])
def test_oracle_accepts_real_current_answers(oracle, answers, dataset):
    _check(oracle, answers[dataset])


@pytest.mark.parametrize("page_span", [[1], [6], [7], [5, 6, 7], [6, 7, 8], []])
def test_oracle_rejects_wrong_or_incomplete_f1_physical_span(oracle, answers, page_span):
    answer = deepcopy(answers["f1"])
    citation = answer["citations"][0]
    assert citation["pdf_pages"] == [6, 7]
    citation.update(pdf_pages=page_span, pdf_page=page_span[0] if page_span else None)
    citation["open_url"] = f"/hus/sources/{citation['document_sha256']}"
    if page_span:
        citation["open_url"] += f"?page={page_span[0]}#page={page_span[0]}"
    # URL/hash/range remain valid: the quote ownership check must be what rejects it.
    with pytest.raises(AssertionError, match="F1 PDF pages must locate the quote"):
        _check(oracle, answer)


def test_oracle_checks_all_f1_quote_pages_without_calling_product_page_resolver(oracle, answerer, monkeypatch):
    observed = []
    for major, _ in answerer.data.program_scopes().values():
        for chunk in answerer.data.chunks("f1", major=major):
            observed.append(answerer.citation_resolver.chunk(chunk, _body(chunk), 1).model_dump())

    def forbidden(*args, **kwargs):
        raise AssertionError("Oracle may not use the page resolver it is testing")

    monkeypatch.setattr("app.hus.citations.CitationResolver._quote_pages", forbidden)
    for citation in observed:
        if citation["evidence_kind"] == "pdf":
            assert oracle.expected_f1_pages(citation["source_id"], citation["quote"]) == citation["pdf_pages"]


@pytest.mark.parametrize("mutation", ["json_open_url", "json_source_url", "wrong_page", "wrong_hash",
                                      "dropped_source", "duplicated_source"])
def test_oracle_rejects_f2_json_substitution_and_lost_source_occurrences(oracle, answers, mutation):
    answer = deepcopy(answers["f2"])
    citation = answer["citations"][0]
    if mutation == "json_open_url":
        citation["open_url"] = oracle.f2_url
    elif mutation == "json_source_url":
        citation["source_url"] = oracle.f2_url
    elif mutation == "wrong_page":
        citation.update(pdf_page=1, pdf_pages=[1])
        citation["open_url"] = f"/hus/sources/{citation['document_sha256']}?page=1#page=1"
    elif mutation == "wrong_hash":
        other = next(sha for sha, entry in oracle.asset_registry["assets"].items()
                     if entry["file_type"] == "pdf" and entry["page_count"] >= citation["pdf_page"]
                     and sha != citation["document_sha256"])
        citation["document_sha256"] = other
        citation["open_url"] = f"/hus/sources/{other}?page={citation['pdf_page']}#page={citation['pdf_page']}"
    elif mutation == "dropped_source":
        answer["citations"].pop()
    else:
        answer["citations"][1] = deepcopy(citation)
        answer["citations"][1]["citation_id"] = "2"
    with pytest.raises(AssertionError):
        _check(oracle, answer)


@pytest.mark.parametrize("updates", [
    {"open_url": "https://example.test/syllabus.pdf"},
    {"source_url": "https://example.test/syllabus.pdf"},
    {"document_sha256": "a" * 64},
    {"pdf_page": 1, "pdf_pages": [1]},
    {"display_label": "Tài liệu chính thức"},
    {"content_origin": "crawled_source_quote"},
    {"review_status": "verified"},
])
def test_oracle_rejects_ai_document_links_and_review_upgrades(oracle, answers, updates):
    answer = deepcopy(answers["f3"])
    answer["citations"][0].update(updates)
    with pytest.raises(AssertionError):
        _check(oracle, answer)


@pytest.mark.parametrize("location", ["reply", "warnings"])
def test_oracle_rejects_hidden_ai_warning(oracle, answers, location):
    answer = deepcopy(answers["f3"])
    if location == "warnings":
        answer["warnings"] = []
    else:
        answer["reply"] = answer["reply"].replace(answer["warnings"][0], "")
    with pytest.raises(AssertionError):
        _check(oracle, answer)


@pytest.mark.parametrize("endpoint", ["/hus/chat"])
def test_real_api_preserves_same_pdf_distinct_pages_and_opens_the_binary(answerer, oracle, monkeypatch, endpoint):
    monkeypatch.setattr("app.hus.demo.get_hus_answerer", lambda: answerer)
    payload = ({"question": "Tiên quyết MAT3325?", "major": "mathematics", "version": "QD3565-2023"}
               if endpoint == "/hus/chat" else {"message": "Tiên quyết MAT3325?", "program_id": "toan_hoc_7460101_2022"})
    client = TestClient(app)
    response = client.post(endpoint, json=payload)
    assert response.status_code == 200
    answer = response.json()["hus_answer"]
    _check(oracle, answer)
    citations = answer["citations"]
    assert len(citations) == 2 and {c["pdf_page"] for c in citations} == {12, 13}
    assert len({c["document_sha256"] for c in citations}) == 1
    assert len({c["open_url"] for c in citations}) == 2
    for citation in citations:
        binary = client.get(citation["open_url"].split("#")[0], headers={"Range": "bytes=0-4"})
        assert binary.status_code == 206 and binary.content == b"%PDF-"
        assert binary.headers["content-type"] == "application/pdf"


@pytest.mark.parametrize("endpoint", ["/hus/chat"])
def test_real_api_ai_citation_has_null_links_without_hiding_evidence(answerer, oracle, monkeypatch, endpoint):
    monkeypatch.setattr("app.hus.demo.get_hus_answerer", lambda: answerer)
    payload = ({"question": "Nội dung MAT3533?", "major": "data_science", "version": "QD3569-2023"}
               if endpoint == "/hus/chat" else {"message": "Nội dung MAT3533?", "program_id": "khdl_7460108_2022"})
    response = TestClient(app).post(endpoint, json={**payload, "allow_generated_reference": True})
    assert response.status_code == 200
    answer = response.json()["hus_answer"]
    _check(oracle, answer)
    assert answer["citations"]
    assert all(c["display_label"] == "kiến thức AI" and c["open_url"] is None for c in answer["citations"])
