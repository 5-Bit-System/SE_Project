import json
from pathlib import Path
import pytest

from app.hus.allowlist import Allowlist, check_allowed
from app.hus.urls import CrawlError

CONFIG_PATH = Path("data/hus/config/sources.json")


def test_allowlist_loaded_from_sources_json():
    assert CONFIG_PATH.exists()
    al = Allowlist.load(CONFIG_PATH)
    assert len(al.sources) == 3
    assert "mim.hus.vnu.edu.vn" in al.rules
    assert "chem.hus.vnu.edu.vn" in al.excluded_hosts


def test_allowlist_rejects_invalid_source_config(tmp_path):
    path = tmp_path / "sources.json"
    path.write_text(
        json.dumps(
            {
                "sources": [
                    {
                        "host": "https://mim.hus.vnu.edu.vn",
                        "path_prefixes": ["/vi/"],
                        "seeds": ["https://mim.hus.vnu.edu.vn/vi/dao-tao"],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError):
        Allowlist.load(path)

    with pytest.raises(ValueError):
        Allowlist([], delay_seconds=-1)
    with pytest.raises(ValueError):
        Allowlist([], max_pages=0)
    with pytest.raises(ValueError):
        Allowlist([], retry_attempts=0)


def test_allowed_urls():
    al = Allowlist.load(CONFIG_PATH)
    # Valid MIM
    assert check_allowed("https://mim.hus.vnu.edu.vn/vi/dao-tao", al)
    # Valid HUS general
    assert check_allowed("https://hus.vnu.edu.vn/dao-tao/dai-hoc/quy-che", al)
    # Valid Tuyensinh
    assert check_allowed("https://tuyensinh.hus.vnu.edu.vn/dai-hoc/thong-tin", al)


def test_refused_other_faculties_and_excluded_paths():
    al = Allowlist.load(CONFIG_PATH)
    # Explicitly excluded host (Khoa Hóa, Khoa Lý)
    with pytest.raises(CrawlError, match="excluded faculty host"):
        check_allowed("https://chem.hus.vnu.edu.vn/dao-tao", al)
    with pytest.raises(CrawlError, match="excluded faculty host"):
        check_allowed("https://phys.hus.vnu.edu.vn/thong-bao", al)

    # Excluded path inside HUS
    with pytest.raises(CrawlError, match="excluded path prefix"):
        check_allowed("https://hus.vnu.edu.vn/dao-tao/khoa-hoa-hoc/thong-bao", al)

    # Completely outside allowlist host
    with pytest.raises(CrawlError, match="outside allowlist"):
        check_allowed("https://uet.vnu.edu.vn/dao-tao", al)

    with pytest.raises(CrawlError, match="outside allowlist"):
        check_allowed("https://hus.vnu.edu.vn/dao-tao-ngoai-pham-vi", al)
    with pytest.raises(CrawlError, match="outside allowlist"):
        check_allowed("https://hus.vnu.edu.vn/dao-tao/../tin-tuc", al)
