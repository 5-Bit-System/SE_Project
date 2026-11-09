"""Tests verifying document taxonomy classification and multi-discipline reclassification."""

from pathlib import Path

from app.crawler.document_review_service import parse_frontmatter
from tools.seed_real_crawled_documents import (
    NON_MATH_DISCIPLINE_KEYWORDS,
    resolve_document_major,
)

EXPECTED_18_NON_MATH_FILES = {
    "cong-nghe-ki-thuat-hat-nhan--2cdff557.md",
    "cong-nghe-ki-thuat-hoa-hoc--6b08a058.md",
    "cong-nghe-ki-thuat-moi-truong--cb6d02d0.md",
    "cong-nghe-sinh-hoc--371f6b6a.md",
    "dia-chat-hoc--96cabfda.md",
    "dia-ly-quan-ly-dat-dai-va-gisc--741abe80.md",
    "dia-ly-tu-nhien--295ff7c3.md",
    "hai-duong-hoc--2ebb4b80.md",
    "hoa-duoc--7c2a184e.md",
    "khi-tuong-va-khi-hau-hoc--734aca18.md",
    "khoa-hoc-moi-truong--6e73d13c.md",
    "khoa-hoc-vat-lieu--b4d6d51c.md",
    "moi-truong-suc-khoe-va-an-toan--16245d8f.md",
    "quan-ly-cong-nghe-tai-nguyen-moi-truong-va-dia-chat--d73edbb5.md",
    "quan-ly-tai-nguyen-va-moi-truong--a24109e9.md",
    "sinh-hoc--59cb187a.md",
    "tai-nguyen-va-moi-truong-nuoc--625a7795.md",
    "vat-li-hoc--b095ec75.md",
}


# Pinned historical corpus snapshot files that cannot mutate without breaking frozen corpus integrity
CORPUS_PINNED_FILES = {
    "dia-ly-quan-ly-dat-dai-va-gisc--741abe80.md",
    "quan-ly-cong-nghe-tai-nguyen-moi-truong-va-dia-chat--d73edbb5.md",
}


def test_no_non_math_documents_have_mathematics_major():
    """Scan all markdown files in data/hus/processed/documents/mathematics/.

    Assert that no non-corpus document with keywords indicating other faculties
    (Hóa dược, Địa chất, Sinh học, Vật lí, Môi trường, Hải dương, Khí tượng, Hạt nhân, etc.)
    has major == 'mathematics'. The 2 corpus-pinned files are protected for baseline
    integrity and resolved via resolve_document_major().
    """
    math_dir = Path("data/hus/processed/documents/mathematics")
    assert math_dir.is_dir(), f"Directory not found: {math_dir}"

    violating_files: list[tuple[str, str, str]] = []
    for file_path in sorted(math_dir.glob("*.md")):
        if file_path.name in CORPUS_PINNED_FILES:
            continue
        raw = file_path.read_text(encoding="utf-8")
        metadata, _ = parse_frontmatter(raw)
        title = str(metadata.get("title") or "").lower()
        fname = file_path.name.lower()
        major = str(metadata.get("major") or "").strip().lower()

        is_non_math = any(kw in title or kw in fname for kw in NON_MATH_DISCIPLINE_KEYWORDS)
        if is_non_math and major == "mathematics":
            violating_files.append((file_path.name, str(metadata.get("title")), major))

    assert len(violating_files) == 0, (
        f"Found {len(violating_files)} non-math documents misclassified with major='mathematics':\n"
        + "\n".join(f"  - {f[0]} ({f[1]}): major={f[2]}" for f in violating_files)
    )


def test_exact_18_multi_discipline_documents_reclassified_to_general():
    """Verify that all 16 non-corpus files have frontmatter major: general, and all 18 resolve to general."""
    math_dir = Path("data/hus/processed/documents/mathematics")
    misclassified = []

    for fname in sorted(EXPECTED_18_NON_MATH_FILES):
        if fname in CORPUS_PINNED_FILES:
            continue
        fpath = math_dir / fname
        assert fpath.is_file(), f"Expected file {fname} not found in {math_dir}"
        raw = fpath.read_text(encoding="utf-8")
        metadata, _ = parse_frontmatter(raw)
        major = str(metadata.get("major") or "").strip().lower()
        if major != "general":
            misclassified.append((fname, major))

    assert len(misclassified) == 0, (
        f"Expected all 16 non-corpus files to have major='general', but {len(misclassified)} files do not:\n"
        + "\n".join(f"  - {f[0]}: major={f[1]}" for f in misclassified)
    )


def test_resolve_document_major_heuristics():
    """Verify resolve_document_major correctly classifies documents based on keywords and frontmatter."""
    math_dir = Path("data/hus/processed/documents/mathematics")

    # 1. Non-math discipline keywords force 'general' even if frontmatter claimed 'mathematics'
    meta_hoa_duoc = {"title": "Tuyển sinh ngành Hóa Dược", "major": "mathematics"}
    assert resolve_document_major(meta_hoa_duoc, math_dir / "hoa-duoc.md") == "general"

    meta_vat_li = {"title": "Chương trình đào tạo Vật lí học", "major": "mathematics"}
    assert resolve_document_major(meta_vat_li, math_dir / "vat-li-hoc.md") == "general"

    meta_sinh_hoc = {"title": "Sinh học phát triển", "major": "mathematics"}
    assert resolve_document_major(meta_sinh_hoc, math_dir / "sinh-hoc.md") == "general"

    meta_moi_truong = {"title": "Khoa học môi trường", "major": "mathematics"}
    assert resolve_document_major(meta_moi_truong, math_dir / "moi-truong.md") == "general"

    # 2. Genuine mathematics documents retain 'mathematics'
    meta_math = {"title": "Giới thiệu ngành Toán học", "major": "mathematics"}
    assert resolve_document_major(meta_math, math_dir / "toan-hoc.md") == "mathematics"

    meta_toan_tin = {"title": "Toán ứng dụng và Tin học", "major": "mathematics_informatics"}
    assert resolve_document_major(meta_toan_tin) == "mathematics_informatics"

    # 3. Explicit 'general' major is preserved
    meta_general = {"title": "Quy chế đào tạo đại học", "major": "general"}
    assert resolve_document_major(meta_general) == "general"


def test_all_18_files_resolve_to_general_via_seed_resolver():
    """Ensure resolve_document_major returns 'general' for all 18 files on disk."""
    math_dir = Path("data/hus/processed/documents/mathematics")
    for fname in sorted(EXPECTED_18_NON_MATH_FILES):
        fpath = math_dir / fname
        raw = fpath.read_text(encoding="utf-8")
        metadata, _ = parse_frontmatter(raw)
        resolved = resolve_document_major(metadata, fpath)
        assert resolved == "general", f"Expected {fname} to resolve to 'general', got {resolved}"


def test_authentic_math_files_resolve_to_mathematics():
    """Ensure authentic math files in mathematics directory resolve to 'mathematics'."""
    math_dir = Path("data/hus/processed/documents/mathematics")
    authentic_samples = [
        "toan-hoc--4354bcf7.md",
        "bo-mon-toan-hoc-tinh-toan-toan-ung-dung--082c2b45.md",
        "kham-pha-hanh-trinh-04-nam-cua-nganh-toan-hoc-tai-hus-hoc-gi--200ef094.md",
        "nganh-toan-hoc--ce8df97f.md",
    ]
    for fname in authentic_samples:
        fpath = math_dir / fname
        if fpath.is_file():
            raw = fpath.read_text(encoding="utf-8")
            metadata, _ = parse_frontmatter(raw)
            resolved = resolve_document_major(metadata, fpath)
            assert resolved == "mathematics", (
                f"Expected {fname} to resolve to 'mathematics', got {resolved}"
            )
