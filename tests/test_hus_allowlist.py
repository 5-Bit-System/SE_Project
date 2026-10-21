import json
from pathlib import Path

import httpx
import pytest

from app.hus.allowlist import Allowlist, check_allowed
from app.hus.pipeline import HUSPipeline
from app.hus.state import CrawlStateManager
from app.hus.storage import ProcessedStorage, RawStorage
from app.hus.urls import CrawlError

CONFIG_PATH = Path("data/hus/config/sources.json")
HUS_BASE = "https://hus.vnu.edu.vn"
# Faculty-specific paths observed in HUS navigation, plus unreviewed faculty branches.
OTHER_FACULTY_PATHS = (
    "/dao-tao/bac-dai-hoc/dia-chat",
    "/dao-tao/bac-dai-hoc/dia-ly",
    "/dao-tao/bac-dai-hoc/hoa-hoc",
    "/dao-tao/bac-dai-hoc/khi-tuong-thuy-van-hai-duong-hoc",
    "/dao-tao/bac-dai-hoc/moi-truong",
    "/dao-tao/bac-dai-hoc/sinh-hoc",
    "/dao-tao/bac-dai-hoc/vat-li",
    "/dao-tao/sau-dai-hoc/hoa-hoc-va-cong-nghe",
    "/dao-tao/sau-dai-hoc/khoa-hoc-trai-dat-va-tai-nguyen-moi-truong",
    "/dao-tao/sau-dai-hoc/sinh-hoc-va-cong-nghe",
    "/dao-tao/sau-dai-hoc/vat-ly-va-cong-nghe",
    "/dao-tao/bac-dai-hoc/khoa-moi-chua-duyet",
    "/dao-tao/sau-dai-hoc/khoa-moi-chua-duyet",
)


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

    # Legacy faculty paths inside HUS remain refused even outside the narrowed allowlist.
    with pytest.raises(CrawlError):
        check_allowed("https://hus.vnu.edu.vn/dao-tao/khoa-hoa-hoc/thong-bao", al)

    # Completely outside allowlist host
    with pytest.raises(CrawlError, match="outside allowlist"):
        check_allowed("https://uet.vnu.edu.vn/dao-tao", al)

    with pytest.raises(CrawlError, match="outside allowlist"):
        check_allowed("https://hus.vnu.edu.vn/dao-tao-ngoai-pham-vi", al)
    with pytest.raises(CrawlError, match="outside allowlist"):
        check_allowed("https://hus.vnu.edu.vn/dao-tao/../tin-tuc", al)


@pytest.mark.parametrize("path", OTHER_FACULTY_PATHS)
@pytest.mark.parametrize("suffix", ["", "/thong-bao?utm_source=test"])
def test_hus_faculty_branches_are_refused(path, suffix):
    al = Allowlist.load(CONFIG_PATH)
    with pytest.raises(CrawlError):
        check_allowed(HUS_BASE + path + suffix, al)


@pytest.mark.parametrize(
    "path",
    [
        "/DAO-TAO/BAC-DAI-HOC/DIA-CHAT/",
        "/dao-tao/bac-dai-hoc/%64ia-ly",
        "/dao-tao/dai-hoc/../bac-dai-hoc/dia-chat",
        "/dao-tao/bac-dai-hoc/toan-toan-ung-dung-va-tin-hoc-khoa-khac",
        "/dao-tao/sau-dai-hoc/toan-co-tin-hoc-khoa-khac",
    ],
)
def test_hus_faculty_paths_cannot_bypass_scope_by_url_spelling(path):
    with pytest.raises(CrawlError):
        check_allowed(HUS_BASE + path, Allowlist.load(CONFIG_PATH))


@pytest.mark.parametrize(
    "path",
    [
        "/dao-tao/dai-hoc",
        "/dao-tao/dai-hoc/quy-che",
        "/dao-tao/gioi-thieu-chung",
        "/dao-tao/bac-dai-hoc/toan-toan-ung-dung-va-tin-hoc",
        "/dao-tao/bac-dai-hoc/toan-toan-ung-dung-va-tin-hoc/chuong-trinh",
        "/dao-tao/sau-dai-hoc/toan-co-tin-hoc",
        "/dao-tao/sau-dai-hoc/toan-co-tin-hoc/thong-bao",
        "/sinh-vien/quy-che",
        "/DATA/IMAGES/quy-che.pdf",
    ],
)
def test_hus_general_and_mim_paths_remain_allowed(path):
    assert check_allowed(HUS_BASE + path, Allowlist.load(CONFIG_PATH)) == HUS_BASE + path


def test_pipeline_never_fetches_or_stores_other_faculty_links(tmp_path):
    al = Allowlist.load(CONFIG_PATH)
    seed = HUS_BASE + "/dao-tao/dai-hoc"
    mim_path = "/dao-tao/bac-dai-hoc/toan-toan-ung-dung-va-tin-hoc"
    al.seeds = [seed]
    seen = []
    links = "".join(f'<a href="{path}">Faculty</a>' for path in OTHER_FACULTY_PATHS)
    links += f'<a href="{mim_path}">MIM</a>'

    def handler(request):
        url = str(request.url)
        seen.append(url)
        if request.url.path == "/robots.txt":
            return httpx.Response(200, text="User-agent: *\nAllow: /\n")
        if url == seed:
            html = f"<main><h1>General training</h1><p>Rules.</p>{links}</main>"
        elif request.url.path == mim_path:
            html = "<main><h1>MIM training</h1><p>Program details.</p></main>"
        else:
            raise AssertionError(f"Out-of-scope URL was requested: {url}")
        return httpx.Response(200, text=html, headers={"content-type": "text/html"})

    pipeline = HUSPipeline(
        al, RawStorage(tmp_path), ProcessedStorage(tmp_path),
        CrawlStateManager(tmp_path / "state/crawl_state.json"),
    )
    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        summary = pipeline.run(client=client, sleep=lambda _: None)

    expected_urls = {seed, HUS_BASE + mim_path}
    assert set(seen) == expected_urls | {HUS_BASE + "/robots.txt"}
    assert summary.new_count == 2
    assert summary.error_count == 0
    catalog = json.loads((tmp_path / "processed/catalog.json").read_text(encoding="utf-8"))
    assert {doc["source_url"] for doc in catalog["documents"].values()} == expected_urls
    state = json.loads((tmp_path / "state/crawl_state.json").read_text(encoding="utf-8"))
    assert set(state["records"]) == expected_urls


def test_redirect_to_other_faculty_is_refused_before_request(tmp_path):
    al = Allowlist.load(CONFIG_PATH)
    seed = HUS_BASE + "/dao-tao/dai-hoc"
    al.seeds = [seed]
    seen = []

    def handler(request):
        url = str(request.url)
        seen.append(url)
        if request.url.path == "/robots.txt":
            return httpx.Response(200, text="User-agent: *\nAllow: /\n")
        if url == seed:
            return httpx.Response(302, headers={"location": OTHER_FACULTY_PATHS[0]})
        raise AssertionError(f"Out-of-scope redirect was followed: {url}")

    pipeline = HUSPipeline(
        al, RawStorage(tmp_path), ProcessedStorage(tmp_path),
        CrawlStateManager(tmp_path / "state/crawl_state.json"),
    )
    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        summary = pipeline.run(client=client, sleep=lambda _: None)

    assert seen == [HUS_BASE + "/robots.txt", seed]
    assert summary.new_count == 0
    assert summary.error_count == 1
    assert "outside allowlist" in summary.failures[seed]
    catalog = json.loads((tmp_path / "processed/catalog.json").read_text(encoding="utf-8"))
    assert catalog["documents"] == {}
