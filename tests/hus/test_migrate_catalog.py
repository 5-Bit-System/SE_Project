"""Tests for tools/migrate_catalog_majors.py."""

from __future__ import annotations

import json
from pathlib import Path

from tools.migrate_catalog_majors import main, migrate_catalog


def test_migrate_catalog_success(tmp_path: Path) -> None:
    catalog_path = tmp_path / "catalog.json"
    data = {
        "version": "1.0",
        "document_count": 3,
        "documents": {
            "doc1": {
                "source_url": "https://mim.hus.vnu.edu.vn/vi/khoa-hoc-du-lieu",
                "title": "Khoa học Dữ liệu",
                "content_markdown": "Chương trình KHDL",
            },
            "doc2": {
                "source_url": "https://mim.hus.vnu.edu.vn/vi/khmt-tt",
                "title": "Ngành Khoa học máy tính và thông tin",
                "content_markdown": "Đào tạo KHMT",
            },
            "doc3": {
                "source_url": "https://mim.hus.vnu.edu.vn/vi/gioi-thieu",
                "title": "Giới thiệu Khoa Toán - Cơ - Tin học",
                "content_markdown": "Thông tin chung về khoa",
            },
        },
    }
    catalog_path.write_text(json.dumps(data), encoding="utf-8")

    total, stats = migrate_catalog(catalog_path, dry_run=False)
    assert total == 3
    assert stats["data_science"] == 1
    assert stats["computer_science"] == 1
    assert stats["general"] == 1

    # Verify written file has major field
    updated = json.loads(catalog_path.read_text(encoding="utf-8"))
    assert updated["documents"]["doc1"]["major"] == "data_science"
    assert updated["documents"]["doc2"]["major"] == "computer_science"
    assert updated["documents"]["doc3"]["major"] == "general"


def test_migrate_catalog_dry_run(tmp_path: Path) -> None:
    catalog_path = tmp_path / "catalog.json"
    data = {
        "version": "1.0",
        "document_count": 1,
        "documents": {
            "doc1": {
                "source_url": "https://mim.hus.vnu.edu.vn/vi/toantin",
                "title": "Ngành Toán - Tin",
                "content_markdown": "Nội dung Toán Tin",
            },
        },
    }
    catalog_path.write_text(json.dumps(data), encoding="utf-8")

    total, stats = migrate_catalog(catalog_path, dry_run=True)
    assert total == 1
    assert stats["mathematics_informatics"] == 1

    # Verify file was not modified in dry-run mode
    on_disk = json.loads(catalog_path.read_text(encoding="utf-8"))
    assert "major" not in on_disk["documents"]["doc1"]


def test_migrate_catalog_cli_main(tmp_path: Path, capsys) -> None:
    catalog_path = tmp_path / "catalog.json"
    data = {
        "version": "1.0",
        "document_count": 1,
        "documents": {
            "doc1": {
                "source_url": "https://mim.hus.vnu.edu.vn/vi/news",
                "title": "Tuyển sinh Cử nhân tài năng Toán",
                "content_markdown": "Lớp CNTN Toán",
            },
        },
    }
    catalog_path.write_text(json.dumps(data), encoding="utf-8")

    code = main(["--catalog", str(catalog_path)])
    assert code == 0

    out = capsys.readouterr().out
    assert "HUS Catalog Major Migration Summary:" in out
    assert "mathematics" in out
    assert "[SUCCESS]" in out


def test_migrate_catalog_missing_file(capsys) -> None:
    code = main(["--catalog", "non_existent_catalog_file.json"])
    assert code != 0
    err = capsys.readouterr().err
    assert "Migration failed" in err
