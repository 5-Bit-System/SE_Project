"""Scope boundaries and source-presence claims, independent of live HUS/network."""

import hashlib
from pathlib import Path

import pytest

from app.hus.models import HUSDocument
from app.hus.scope_audit import (
    audit, catalog_inventory, classify, evidence_lines, syllabus_courses, table_courses,
    validate_experimental,
)


def document(content: str, title: str = "Ngành Toán Tin", url: str = "http://mim.hus.vnu.edu.vn/vi/toantin"):
    return HUSDocument(url=url, title=title, content=content,
                       content_hash=hashlib.sha256(content.encode()).hexdigest(),
                       fetched_at="2026-10-28T10:00:00Z", publisher="MIM", document_type="curriculum")


def test_undergraduate_article_not_changed_by_further_study_or_linked_versions():
    content = ("Chương trình đào tạo ngành Toán Tin trình độ đại học.\n"
               "Mục tiêu đào tạo: toán và tin.\nVị trí việc làm: lập trình.\n"
               "Có thể học tiếp ở bậc Thạc sĩ, Tiến sĩ.\n"
               "- [Khung chương trình 2023](https://mim.hus.vnu.edu.vn/2023.pdf)\n")
    row = classify(document(content))
    assert row["education_level_proposed"] == "undergraduate"
    assert row["program_version_proposed"] == "unknown"
    assert row["groups"] == ["F1"]
    assert row["admission_cohort"] == "unknown"
    for values in row["evidence"].values():
        for e in values:
            assert content[e["start"]:e["end"]] == e["quote"]


def test_scientific_advances_are_not_advanced_program_variant():
    doc = document("Chương trình đào tạo trình độ đại học ngành Khoa học dữ liệu.\n"
                   "Mục tiêu: ứng dụng các thành tựu khoa học tiên tiến.\n",
                   title="Khoa học Dữ liệu", url="https://mim.hus.vnu.edu.vn/vi/khoa-hoc-du-lieu")
    assert classify(doc)["program_variant_proposed"] == "unknown"


@pytest.mark.parametrize("degree,level", [("THẠC SĨ", "master"), ("TIẾN SĨ", "doctoral")])
def test_graduate_curriculum_is_excluded_despite_F2_words(degree, level):
    row = classify(document(f"CHƯƠNG TRÌNH ĐÀO TẠO TRÌNH ĐỘ {degree}\n"
                            "NGÀNH: TOÁN TIN\nSố tín chỉ\n"
                            "| 1 | MAT6001 | Toán | 3 |\n"))
    assert row["education_level_proposed"] == level
    assert row["disposition"] == "exclude"
    assert row["groups"] == []


def test_lab_news_and_unrelated_unit_not_accepted_from_major_title():
    for content in ("Trưởng đơn vị: X\nCác hướng nghiên cứu: khai phá dữ liệu",
                    "Tin tức\n- [Mục tiêu đào tạo đại học](https://mim.hus.vnu.edu.vn/vi/toantin)"):
        assert classify(document(content))["disposition"] == "exclude"
    assert classify(document("Bậc đại học\n", title="Địa lý, Quản lý đất đai và GISc",
                             url="https://hus.vnu.edu.vn/dao-tao/bac-dai-hoc/dia-ly"))["disposition"] == "exclude"


def test_mixed_degree_document_is_quarantined_without_slicing_gate():
    row = classify(document("Chương trình đào tạo trình độ đại học ngành Toán Tin.\n"
                            "Mục tiêu đào tạo.\nChương trình đào tạo trình độ thạc sĩ.\n"))
    assert row["disposition"] in {"exclude", "quarantine"}


def test_unknown_degree_and_scan_never_become_undergraduate_from_filename():
    row = classify(document("<!-- Page 1 -->", title="ToanTin_2022_daihoc.pdf"))
    assert row["education_level_proposed"] == "unknown"
    assert row["program_version_proposed"] == "unknown"
    assert row["groups"] == []


def test_F2_preserves_source_row_and_does_not_call_empty_prerequisite_none():
    doc = document("TRÌNH ĐỘ ĐẠI HỌC\nNGÀNH: TOÁN TIN\nHà Nội, 2015\n"
                   "| TT | Mã học phần | Tên học phần | Số tín chỉ | Tiên quyết |\n"
                   "| 1 | MAT1001 | Giải tích | 3 |  |\n")
    row = classify(doc)
    assert "F2" in row["groups"]
    assert row["program_version_proposed"] == "2015"
    course = table_courses(doc)[0]
    assert course["prerequisite_interpretation"] == "unknown"
    assert doc.content[course["start"]:course["end"]] == course["row_raw"]
    assert not course["relation_types_verified"]


def test_F3_field_presence_bound_to_each_course_not_document_wide():
    doc = document("1. Mã học phần: MAT1001\n7. Mục tiêu học phần\nMục tiêu A\n"
                   "10. Tóm tắt nội dung học phần\nNội dung A\n"
                   "1. Mã học phần: MAT1002\n8. Phương pháp kiểm tra, đánh giá\nBài tập\n")
    one, two = syllabus_courses(doc)
    assert one["fields"]["content"]
    assert not one["fields"]["assessment"]
    assert not two["fields"]["content"]
    assert two["fields"]["assessment"]
    assert not one["answer_eligible"] and one["program_applicability"] == "unknown"
    for row in (one, two):
        for values in row["fields"].values():
            for e in values:
                assert doc.content[e["start"]:e["end"]] == e["quote"]


def test_toc_link_is_not_source_field_evidence():
    assert not evidence_lines("7. Nội dung học phần ............ 25\n"
                              "- [Nội dung học phần](https://x)\n", "noi dung hoc phan")


def test_real_scoped_artifacts_only_use_hash_bound_includes_and_reproduce():
    from app.hus.scope_audit import read_jsonl_bytes
    from app.hus.corpus import verify_artifacts

    out = Path("data/hus/qa/20261028/audit")
    expected = audit(Path("data/hus"), Path("data/hus/qa/20261028/contract/build_config.json"),
                     Path("data/curricula"), Path("data/hus/qa/20261028/experimental/f3_inferred.json"))
    verify_artifacts(out, expected)
    docs = read_jsonl_bytes(expected["answer_documents.jsonl"])
    assert len(docs) == 4
    assert all(d["review_status"] == "include" and d["review"]["usage_scope"] == "descriptive" for d in docs)
    assert {d["major"] for d in docs} == {"mathematics", "mathematics_informatics", "computer_science", "data_science"}
    classified = read_jsonl_bytes(expected["classification.jsonl"])
    assert len(classified) == 106
    assert not any(d["answer_eligible"] for d in classified if d["disposition"] != "retain_candidate")
    courses = catalog_inventory(Path("data/curricula"))
    assert len(courses) == 65 and all(c["row_matches"] for c in courses)
    assert all(c["prerequisite_answer_status"] == "unknown" for c in courses)


def test_CDR_matrix_values_are_never_read_as_credits():
    doc = document("| STT | Mã HP | CĐR Học phần | Kiến thức | Kiến thức |\n"
                   "| 1 | MAT1001 | Giải tích | 3 | 4 |\n")
    assert table_courses(doc) == []


def test_syllabus_code_suffix_and_malformed_code_are_preserved_without_repair():
    rows = syllabus_courses(document("1. Mã học phần: MAT3550E\nNội dung học phần\nA\n"
                                     "1. Mã học phần: 2502\nNội dung học phần\nB\n"))
    assert [r["code"] for r in rows] == ["MAT3550E", "2502"]
    assert rows[1]["code_status"] == "malformed_unresolved"


@pytest.mark.parametrize("mutation", ["hash", "official_assessment", "verified", "foreign_code"])
def test_generated_examples_reject_verified_official_and_stale_inputs(tmp_path, mutation):
    import json
    data = json.loads(Path("data/hus/qa/20261028/experimental/f3_inferred.json").read_text(encoding="utf-8"))
    if mutation == "hash":
        data["input_sha256_utf8_lf"] = "0" * 64
    elif mutation == "verified":
        data["verified"] = True
    elif mutation == "foreign_code":
        data["courses"][0]["code"] = "XXX0000"
    else:
        data["courses"][0][mutation] = "Thi cuối kỳ 70%"
    path = tmp_path / "inferred.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError):
        validate_experimental(path, catalog_inventory(Path("data/curricula")))


def test_targeted_fetch_fails_closed_when_robots_unreachable(tmp_path, monkeypatch):
    import httpx
    import json
    from tools.fetch_hus_gaps import fetch
    from app.hus.crawler import Robots

    original_client = httpx.Client
    def handle(request):
        assert request.url.path == "/robots.txt"
        raise httpx.ConnectError("synthetic unreachable robots", request=request)
    monkeypatch.setattr("tools.fetch_hus_gaps.httpx.Client",
                        lambda **kw: original_client(transport=httpx.MockTransport(handle), **kw))
    monkeypatch.setattr("tools.fetch_hus_gaps.Robots",
                        lambda *a, **kw: Robots(*a, **kw, sleep=lambda _: None))
    targets = tmp_path / "targets.json"
    targets.write_text(json.dumps({"targets": [{"url": "https://mim.hus.vnu.edu.vn/vi/toantin"}]}))
    report = fetch(Path("data/hus/config/qa_sources.json"), targets, tmp_path / "acquisition")
    assert report["results"][0]["status"] == "blocked"
    assert not report["results"][0]["answer_eligible"]
    assert len(report["http_attempts"]) == 2
    assert all(r["status"] is None and r["purpose"] == "robots" for r in report["http_attempts"])
    assert (tmp_path / "acquisition/raw/provenance.jsonl").is_file()


def test_F2_header_survives_page_numbers_and_never_reads_comparison_tables():
    rows = table_courses(document("| STT | Mã học phần | Học phần | Số tín chỉ |\n"
                                   "| 1 | MAT1001 | A | 3 |\n\n12\n<!-- Page 13 -->\n"
                                   "| 2 | MAT1002 | B | 4 |\n"
                                   "| STT | Mã học phần | Học phần | Số tín chỉ | Mã học phần |\n"
                                   "| 3 | MAT1003 | C | 9 | ABC1000 |\n"))
    assert [r["code"] for r in rows] == ["MAT1001", "MAT1002"]
