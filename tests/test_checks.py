"""Unit tests covering all 10 specialized technical SEO checks."""

from seo_doctor.checks import (
    check_broken_links,
    check_canonical_tags,
    check_headings,
    check_images,
    check_indexability,
    check_metadata,
    check_orphan_pages,
    check_redirects,
    check_robots_directives,
    check_sitemap_urls,
)
from seo_doctor.models import CrawledPage, Severity


def test_broken_links_check():
    page_a = CrawledPage(
        url="https://example.com/page-a",
        status_code=200,
        internal_links=["https://example.com/dead-page"],
        external_links=["https://broken-external.com/404"],
    )
    dead_page = CrawledPage(
        url="https://example.com/dead-page",
        status_code=404,
    )
    pages = [page_a, dead_page]
    page_by_url = {p.url: p for p in pages}
    ext_statuses = {"https://broken-external.com/404": 404}

    issues = check_broken_links(pages, page_by_url, ext_statuses)

    types = [i.issue_type for i in issues]
    assert "broken_internal_link" in types
    assert "broken_external_link" in types
    internal_issue = next(i for i in issues if i.issue_type == "broken_internal_link")
    assert internal_issue.severity == Severity.CRITICAL
    assert internal_issue.blocks_ranking is True


def test_redirect_chains_and_loops():
    # Loop
    loop_page = CrawledPage(
        url="https://example.com/loop-start",
        status_code=200,
        redirect_history=[
            {"url": "https://example.com/loop-start", "status_code": 301},
            {"url": "https://example.com/step-b", "status_code": 301},
            {"url": "https://example.com/loop-start", "status_code": 301},
        ],
        final_url="https://example.com/loop-start",
        is_redirect=True,
    )
    # Chain
    chain_page = CrawledPage(
        url="https://example.com/chain-start",
        status_code=200,
        redirect_history=[
            {"url": "https://example.com/chain-start", "status_code": 301},
            {"url": "https://example.com/hop-1", "status_code": 301},
        ],
        final_url="https://example.com/destination",
        is_redirect=True,
    )

    issues = check_redirects([loop_page, chain_page])
    types = [i.issue_type for i in issues]

    assert "redirect_loop" in types
    assert "redirect_chain" in types


def test_metadata_missing_and_duplicates():
    p1 = CrawledPage(
        url="https://example.com/p1",
        status_code=200,
        title="Identical Duplicate Page Title for Testing",
        meta_description="Identical description used on both pages.",
    )
    p2 = CrawledPage(
        url="https://example.com/p2",
        status_code=200,
        title="Identical Duplicate Page Title for Testing",
        meta_description="Identical description used on both pages.",
    )
    p3 = CrawledPage(
        url="https://example.com/p3",
        status_code=200,
        title=None,
        meta_description=None,
    )

    issues = check_metadata([p1, p2, p3])
    types = [i.issue_type for i in issues]

    assert "missing_title" in types
    assert "missing_meta_description" in types
    assert "duplicate_title" in types
    assert "duplicate_meta_description" in types


def test_headings_missing_and_multiple():
    page_no_h1 = CrawledPage(
        url="https://example.com/no-h1",
        status_code=200,
        h1_tags=[],
    )
    page_multi_h1 = CrawledPage(
        url="https://example.com/multi-h1",
        status_code=200,
        h1_tags=["First Heading", "Second Conflicting Heading"],
        headings=[
            {"level": "h1", "text": "First Heading"},
            {"level": "h3", "text": "Skipped Level Subheading"},
        ],
    )

    issues = check_headings([page_no_h1, page_multi_h1])
    types = [i.issue_type for i in issues]

    assert "missing_h1" in types
    assert "multiple_h1" in types
    assert "heading_hierarchy_skipped_level" in types


def test_canonical_conflicts():
    p_multi = CrawledPage(
        url="https://example.com/multi-canonical",
        status_code=200,
        canonical_tags=["https://example.com/canonical-a", "https://example.com/canonical-b"],
    )
    p_broken = CrawledPage(
        url="https://example.com/broken-target",
        status_code=200,
        canonical_tags=["https://example.com/dead-canonical"],
    )
    dead_target = CrawledPage(
        url="https://example.com/dead-canonical",
        status_code=404,
    )
    page_by_url = {
        p_multi.url: p_multi,
        p_broken.url: p_broken,
        dead_target.url: dead_target,
    }

    issues = check_canonical_tags([p_multi, p_broken], page_by_url)
    types = [i.issue_type for i in issues]

    assert "multiple_canonical_tags" in types
    assert "canonical_points_to_broken_url" in types


def test_robots_directives():
    p_noindex = CrawledPage(
        url="https://example.com/private",
        status_code=200,
        meta_robots=["noindex", "nofollow"],
    )
    p_blocked = CrawledPage(
        url="https://example.com/admin/settings",
        status_code=200,
    )

    issues = check_robots_directives([p_noindex, p_blocked], {"https://example.com/admin/settings"})
    types = [i.issue_type for i in issues]

    assert "robots_noindex_directive" in types
    assert "robots_nofollow_directive" in types
    assert "blocked_by_robots_txt" in types


def test_images_check():
    page = CrawledPage(
        url="https://example.com/gallery",
        status_code=200,
        images=[
            {"src": "/images/roaster.jpg", "missing_alt": True, "alt": None},
            {"src": "/images/brand-logo.png", "missing_alt": False, "alt": ""},
        ],
    )
    issues = check_images([page])
    types = [i.issue_type for i in issues]

    assert "missing_image_alt" in types
    assert "empty_image_alt" in types


def test_sitemap_urls_check():
    dead_sitemap_page = CrawledPage(
        url="https://example.com/dead-sitemap-page",
        status_code=404,
    )
    noindex_sitemap_page = CrawledPage(
        url="https://example.com/noindex-sitemap-page",
        status_code=200,
        meta_robots=["noindex"],
    )
    page_by_url = {
        dead_sitemap_page.url: dead_sitemap_page,
        noindex_sitemap_page.url: noindex_sitemap_page,
    }
    sitemap_urls = [dead_sitemap_page.url, noindex_sitemap_page.url]

    issues = check_sitemap_urls(
        "https://example.com", True, sitemap_urls, page_by_url
    )
    types = [i.issue_type for i in issues]

    assert "sitemap_broken_url" in types
    assert "sitemap_noindex_url" in types


def test_orphan_pages_check():
    p_home = CrawledPage(
        url="https://example.com",
        status_code=200,
        internal_links=["https://example.com/about"],
    )
    p_about = CrawledPage(
        url="https://example.com/about",
        status_code=200,
        internal_links=["https://example.com"],
    )
    p_orphan = CrawledPage(
        url="https://example.com/orphan-secret",
        status_code=200,
        internal_links=[],
    )

    pages = [p_home, p_about, p_orphan]
    sitemap_urls = ["https://example.com", "https://example.com/about", "https://example.com/orphan-secret"]

    issues, orphans = check_orphan_pages(pages, sitemap_urls, "https://example.com")

    assert "https://example.com/orphan-secret" in orphans
    assert any(i.issue_type == "orphan_page_candidate" for i in issues)


def test_indexability_check():
    p_404 = CrawledPage(url="https://example.com/lost", status_code=404)
    p_500 = CrawledPage(url="https://example.com/crash", status_code=500)
    p_thin = CrawledPage(url="https://example.com/thin", status_code=200, word_count=25)

    issues = check_indexability([p_404, p_500, p_thin])
    types = [i.issue_type for i in issues]

    assert "client_error_4xx" in types
    assert "server_error_5xx" in types
    assert "thin_content" in types
