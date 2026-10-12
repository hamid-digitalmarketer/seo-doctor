"""Unit tests for report generation in JSON, CSV, and HTML."""

import json
from pathlib import Path

from seo_doctor.models import (
    CrawledPage,
    CrawlReport,
    CrawlSummary,
    IssueCategory,
    SEOIssue,
    Severity,
)
from seo_doctor.report import (
    export_csv,
    export_html,
    export_json,
    generate_all_reports,
)


def _create_mock_report() -> CrawlReport:
    summary = CrawlSummary(
        crawl_id="test-run-12345",
        start_url="https://example.com",
        timestamp="2026-01-01T12:00:00Z",
        duration_seconds=1.25,
        total_pages_crawled=2,
        status_200_count=2,
        total_issues_found=1,
        critical_issues=1,
        health_score=85,
    )
    pages = [
        CrawledPage(url="https://example.com", status_code=200, title="Home", word_count=250),
        CrawledPage(url="https://example.com/dead", status_code=404),
    ]
    issues = [
        SEOIssue(
            url="https://example.com",
            issue_type="broken_internal_link",
            category=IssueCategory.LINKS,
            severity=Severity.CRITICAL,
            evidence="Links to 404 page",
            suggested_fix="Fix link",
            blocks_indexing=False,
            blocks_ranking=True,
        )
    ]
    return CrawlReport(summary=summary, pages=pages, issues=issues)


def test_export_json(tmp_path: Path):
    report = _create_mock_report()
    json_path = tmp_path / "report.json"
    export_json(report, json_path)

    assert json_path.exists()
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["summary"]["crawl_id"] == "test-run-12345"
    assert len(data["issues"]) == 1


def test_export_csv(tmp_path: Path):
    report = _create_mock_report()
    csv_path = tmp_path / "report.csv"
    export_csv(report, csv_path)

    assert csv_path.exists()
    content = csv_path.read_text(encoding="utf-8")
    assert "broken_internal_link" in content
    assert "critical" in content


def test_export_html(tmp_path: Path):
    report = _create_mock_report()
    html_path = tmp_path / "report.html"
    export_html(report, html_path)

    assert html_path.exists()
    content = html_path.read_text(encoding="utf-8")
    assert "SEO-Doctor" in content
    assert "test-run-12345" in content
    assert "85" in content


def test_generate_all_reports(tmp_path: Path):
    report = _create_mock_report()
    paths = generate_all_reports(report, tmp_path)

    assert paths["json"].exists()
    assert paths["csv"].exists()
    assert paths["html"].exists()
