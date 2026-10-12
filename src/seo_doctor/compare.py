"""Compare two crawl runs to track technical SEO improvements and regressions."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Set

from seo_doctor.models import ComparisonResult, CrawlReport, SEOIssue


def load_report_from_file(file_path: Path) -> CrawlReport:
    """Load and parse CrawlReport from a JSON file."""
    if not file_path.exists():
        raise FileNotFoundError(f"Report file not found: {file_path}")
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return CrawlReport.model_validate(data)


def compare_crawls(
    baseline_report: CrawlReport,
    comparison_report: CrawlReport,
) -> ComparisonResult:
    """Compare baseline audit with newer comparison audit."""
    base_issues_by_key: Dict[str, SEOIssue] = {
        f"{i.url}|{i.issue_type}": i for i in baseline_report.issues
    }
    comp_issues_by_key: Dict[str, SEOIssue] = {
        f"{i.url}|{i.issue_type}": i for i in comparison_report.issues
    }

    base_keys: Set[str] = set(base_issues_by_key.keys())
    comp_keys: Set[str] = set(comp_issues_by_key.keys())

    fixed_keys = base_keys - comp_keys
    introduced_keys = comp_keys - base_keys
    still_open_keys = base_keys & comp_keys

    issues_fixed: List[SEOIssue] = [base_issues_by_key[k] for k in sorted(fixed_keys)]
    issues_introduced: List[SEOIssue] = [comp_issues_by_key[k] for k in sorted(introduced_keys)]
    issues_still_open: List[SEOIssue] = [comp_issues_by_key[k] for k in sorted(still_open_keys)]

    health_delta = comparison_report.summary.health_score - baseline_report.summary.health_score
    issues_delta = (
        comparison_report.summary.total_issues_found - baseline_report.summary.total_issues_found
    )
    pages_delta = (
        comparison_report.summary.total_pages_crawled - baseline_report.summary.total_pages_crawled
    )

    return ComparisonResult(
        baseline_crawl_id=baseline_report.summary.crawl_id,
        comparison_crawl_id=comparison_report.summary.crawl_id,
        baseline_timestamp=baseline_report.summary.timestamp,
        comparison_timestamp=comparison_report.summary.timestamp,
        health_score_delta=health_delta,
        total_issues_delta=issues_delta,
        pages_crawled_delta=pages_delta,
        issues_fixed=issues_fixed,
        issues_introduced=issues_introduced,
        issues_still_open=issues_still_open,
    )
