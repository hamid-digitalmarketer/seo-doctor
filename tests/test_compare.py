"""Unit tests for crawl comparison between runs."""

from seo_doctor.compare import compare_crawls
from seo_doctor.models import (
    CrawlReport,
    CrawlSummary,
    IssueCategory,
    SEOIssue,
    Severity,
)


def test_compare_crawls():
    iss_a = SEOIssue(
        url="https://example.com/a",
        issue_type="missing_title",
        category=IssueCategory.METADATA,
        severity=Severity.CRITICAL,
        evidence="Title missing",
        suggested_fix="Add title",
    )
    iss_b = SEOIssue(
        url="https://example.com/b",
        issue_type="broken_internal_link",
        category=IssueCategory.LINKS,
        severity=Severity.CRITICAL,
        evidence="Returns 404",
        suggested_fix="Fix link",
    )
    iss_c = SEOIssue(
        url="https://example.com/c",
        issue_type="missing_h1",
        category=IssueCategory.HEADINGS,
        severity=Severity.HIGH,
        evidence="No H1 tag",
        suggested_fix="Add H1",
    )

    report_1 = CrawlReport(
        summary=CrawlSummary(
            crawl_id="run-1",
            start_url="https://example.com",
            timestamp="2026-01-01T12:00:00Z",
            duration_seconds=1.0,
            total_pages_crawled=10,
            total_issues_found=2,
            health_score=70,
        ),
        issues=[iss_a, iss_b],
    )

    report_2 = CrawlReport(
        summary=CrawlSummary(
            crawl_id="run-2",
            start_url="https://example.com",
            timestamp="2026-02-01T12:00:00Z",
            duration_seconds=1.0,
            total_pages_crawled=12,
            total_issues_found=2,
            health_score=85,
        ),
        issues=[iss_b, iss_c],
    )

    result = compare_crawls(report_1, report_2)

    assert result.health_score_delta == 15
    assert result.total_issues_delta == 0
    assert result.pages_crawled_delta == 2

    # Fixed: iss_a was in run-1, fixed in run-2
    assert len(result.issues_fixed) == 1
    assert result.issues_fixed[0].issue_type == "missing_title"

    # Introduced: iss_c was not in run-1, introduced in run-2
    assert len(result.issues_introduced) == 1
    assert result.issues_introduced[0].issue_type == "missing_h1"

    # Still open: iss_b was in both
    assert len(result.issues_still_open) == 1
    assert result.issues_still_open[0].issue_type == "broken_internal_link"
