import pytest

from app.hus.urls import CrawlError, canonicalize_url, is_private_host, is_spider_trap


def test_canonicalize_url_basic():
    url = "HTTP://MIM.HUS.VNU.EDU.VN/vi/dao-tao/?utm_source=fb&gclid=123&page=1#"
    clean = canonicalize_url(url)
    assert clean == "https://mim.hus.vnu.edu.vn/vi/dao-tao?page=1"


def test_canonicalize_url_errors():
    with pytest.raises(CrawlError):
        canonicalize_url("ftp://example.com")
    with pytest.raises(CrawlError):
        canonicalize_url("https://example.com:8080/path")


def test_is_private_host():
    assert is_private_host("localhost")
    assert is_private_host("test.localhost")
    assert is_private_host("127.0.0.1")
    assert is_private_host("192.168.1.1")
    assert is_private_host("10.0.0.1")
    assert not is_private_host("mim.hus.vnu.edu.vn")
    assert not is_private_host("hus.vnu.edu.vn")


def test_is_spider_trap():
    # Traps: calendar, search, query filters, repetitive path
    assert is_spider_trap("https://mim.hus.vnu.edu.vn/vi/calendar?month=10&year=2026")
    assert is_spider_trap("https://hus.vnu.edu.vn/index.php?task=search&q=abc")
    assert is_spider_trap("https://mim.hus.vnu.edu.vn/vi/news/page/page/page")
    assert not is_spider_trap("https://mim.hus.vnu.edu.vn/vi/dao-tao/chuong-trinh-dao-tao")
    assert not is_spider_trap("https://hus.vnu.edu.vn/dao-tao/dai-hoc/quy-che")
