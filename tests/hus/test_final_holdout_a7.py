"""Automated test suite verifying prospective final holdout suite A7.

Ensures HUS RAG achieves Recall@5 >= 90%, zero false positives on missing evidence,
100% citation integrity across all 4 majors in data/hus/evaluation/p11_holdout_v1.
"""

from tools import run_final_holdout_a7


def test_prospective_holdout_a7_metrics(monkeypatch, tmp_path):
    monkeypatch.setattr(run_final_holdout_a7, "OUT_REPORT", tmp_path / "report.json")
    monkeypatch.setattr(run_final_holdout_a7, "OUT_DOC", tmp_path / "report.md")
    report = run_final_holdout_a7.run_a7_evaluation()

    metrics = report["metrics"]
    criteria = report["acceptance_criteria"]

    # 1. Total questions and major distribution
    assert report["total_questions"] == 48
    assert criteria["all_4_majors_covered"] is True
    assert set(report["by_major"].keys()) == {
        "computer_science",
        "data_science",
        "mathematics",
        "mathematics_informatics",
    }
    for major, count in report["by_major"].items():
        assert count == 12, f"Expected 12 questions for {major}, got {count}"

    # 2. Retrieval metrics
    assert metrics["recall_at_5"] >= 0.90, f"Expected Recall@5 >= 0.90, got {metrics['recall_at_5']}"
    assert metrics["mrr"] >= 0.85, f"Expected MRR >= 0.85, got {metrics['mrr']}"

    # 3. Safety criteria: zero false positives on missing evidence or out-of-scope questions
    assert metrics["false_positives"] == 0, f"Expected 0 false positives, got {metrics['false_positives']}"
    assert criteria["zero_false_positives_on_missing_evidence"] is True

    # 4. Citation integrity
    assert metrics["citation_integrity"] == 1.0, f"Expected 100% citation integrity, got {metrics['citation_integrity']}"
    assert criteria["citation_integrity_100"] is True

    # 5. Status accuracy
    assert metrics["status_accuracy"] >= 0.90, f"Expected status accuracy >= 90%, got {metrics['status_accuracy']}"
