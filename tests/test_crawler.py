"""Unit tests for crawler engine and URL utilities."""

import requests

from seo_doctor.config import CrawlConfig
from seo_doctor.crawler import RobotsTxtParser, SEOCrawler, is_internal_url, normalize_url
from tests.fixtures.sample_pages import (
    HTML_PERFECT_PAGE,
    ROBOTS_TXT_FIXTURE,
    SITEMAP_XML_FIXTURE,
)


def test_normalize_url():
    # Trim fragments
    assert normalize_url("https://example.com/about#team") == "https://example.com/about"
    # Resolve relative URL
    assert normalize_url("/contact", "https://example.com/home") == "https://example.com/contact"
    # Drop standard ports
    assert normalize_url("http://example.com:80/page") == "http://example.com/page"
    assert normalize_url("https://example.com:443/page") == "https://example.com/page"
    # Handle redundant slashes
    assert normalize_url("https://example.com//blog///post") == "https://example.com/blog/post"


def test_is_internal_url():
    base = "example.com"
    assert is_internal_url("https://example.com/about", base) is True
    assert is_internal_url("https://www.example.com/pricing", base) is True
    assert is_internal_url("https://external.org/landing", base) is False
    assert is_internal_url("https://sub.otherdomain.com", base) is False


def test_robots_txt_parser():
    parser = RobotsTxtParser(ROBOTS_TXT_FIXTURE)
    assert parser.is_allowed("/blog/seo-tips") is True
    assert parser.is_allowed("/admin/users") is False
    assert parser.is_allowed("/checkout/cart") is False
    assert parser.sitemap_urls == ["https://example.com/sitemap.xml"]


def test_sitemap_xml_parsing():
    config = CrawlConfig(start_url="https://example.com")
    crawler = SEOCrawler(config)
    urls = crawler._parse_sitemap_xml(SITEMAP_XML_FIXTURE.encode("utf-8"))

    assert len(urls) == 3
    assert "https://example.com/page-1" in urls
    assert "https://example.com/orphan-page" in urls


def test_parse_page_structure():
    config = CrawlConfig(start_url="https://example.com")
    crawler = SEOCrawler(config)

    mock_resp = requests.Response()
    mock_resp.status_code = 200
    mock_resp._content = HTML_PERFECT_PAGE.encode("utf-8")
    mock_resp.headers["Content-Type"] = "text/html; charset=utf-8"
    mock_resp.url = "https://example.com/perfect-page"

    page = crawler.parse_page("https://example.com/perfect-page", mock_resp, 45.2)

    assert page.status_code == 200
    assert page.title == "High Quality Organic Coffee Beans Online"
    assert "ethically sourced" in (page.meta_description or "")
    assert page.canonical_url == "https://example.com/perfect-page"
    assert page.h1_tags == ["Artisanal Coffee Roasting"]
    assert "https://example.com/about" in page.internal_links
    assert any("partner-origin.org" in link for link in page.external_links)
    assert len(page.images) == 1
    assert page.images[0]["alt"] == "Artisan coffee beans roasting in cast iron drum"
    assert page.word_count > 10
