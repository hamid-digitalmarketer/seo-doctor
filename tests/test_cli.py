"""Integration tests for Typer CLI commands."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from seo_doctor.cli import app
from seo_doctor.models import (
    CrawledPage,
    CrawlReport,
    CrawlSummary,
    IssueCategory,
    SEOIssue,
    Severity,
)
from seo_doctor.report import export_json

runner = CliRunner()


def test_cli_version():
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "SEO-Doctor" in result.stdout


def test_cli_compare(tmp_path: Path):
    r1 = CrawlReport(
        summary=CrawlSummary(
            crawl_id="c1",
            start_url="https://example.com",
            timestamp="2026-01-01T12:00:00Z",
            duration_seconds=1.0,
            total_pages_crawled=5,
            total_issues_found=1,
            health_score=75,
        ),
        issues=[
            SEOIssue(
                url="https://example.com",
                issue_type="missing_title",
                category=IssueCategory.METADATA,
                severity=Severity.CRITICAL,
                evidence="No title",
                suggested_fix="Add title",
            )
        ],
    )
    r2 = CrawlReport(
        summary=CrawlSummary(
            crawl_id="c2",
            start_url="https://example.com",
            timestamp="2026-02-01T12:00:00Z",
            duration_seconds=1.0,
            total_pages_crawled=5,
            total_issues_found=0,
            health_score=100,
        ),
        issues=[],
    )

    p1 = tmp_path / "run1.json"
    p2 = tmp_path / "run2.json"
    export_json(r1, p1)
    export_json(r2, p2)

    result = runner.invoke(app, ["compare", str(p1), str(p2)])
    assert result.exit_code == 0
    assert "Crawl Comparison Audit" in result.stdout
    assert "Issues Fixed" in result.stdout
    assert "missing_title" in result.stdout


@patch("seo_doctor.cli.SEOCrawler")
def test_cli_crawl(mock_crawler_cls, tmp_path: Path):
    mock_instance = MagicMock()
    mock_crawler_cls.return_value = mock_instance

    mock_report = CrawlReport(
        summary=CrawlSummary(
            crawl_id="cli-mock-run",
            start_url="https://example.com",
            timestamp="2026-01-01T12:00:00Z",
            duration_seconds=0.5,
            total_pages_crawled=3,
            status_200_count=3,
            total_issues_found=0,
            health_score=100,
        ),
        pages=[CrawledPage(url="https://example.com", status_code=200)],
        issues=[],
    )
    mock_instance.crawl.return_value = mock_report

    out_dir = tmp_path / "reports"
    result = runner.invoke(
        app,
        ["crawl", "https://example.com", "--max-pages", "5", "--output-dir", str(out_dir)],
    )

    assert result.exit_code == 0
    assert "SEO Audit Summary" in result.stdout
    assert "Reports generated successfully" in result.stdout
