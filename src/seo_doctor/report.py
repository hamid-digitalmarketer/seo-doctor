"""Report generation in HTML, CSV, and JSON formats."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict

from jinja2 import Environment, FileSystemLoader

from seo_doctor.models import CrawlReport


def get_template_env() -> Environment:
    """Initialize Jinja2 template environment."""
    template_dir = Path(__file__).parent / "templates"
    return Environment(loader=FileSystemLoader(str(template_dir)), autoescape=True)


def export_json(report: CrawlReport, output_path: Path) -> Path:
    """Export audit report as structured machine-readable JSON."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report.model_dump_json(indent=2))
    return output_path


def export_csv(report: CrawlReport, output_path: Path) -> Path:
    """Export detected technical SEO issues to CSV."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "id",
        "url",
        "issue_type",
        "category",
        "severity",
        "evidence",
        "suggested_fix",
        "blocks_indexing",
        "blocks_ranking",
    ]

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for issue in report.issues:
            writer.writerow(
                {
                    "id": issue.id,
                    "url": issue.url,
                    "issue_type": issue.issue_type,
                    "category": (
                        issue.category.value
                        if hasattr(issue.category, "value")
                        else str(issue.category)
                    ),
                    "severity": (
                        issue.severity.value
                        if hasattr(issue.severity, "value")
                        else str(issue.severity)
                    ),
                    "evidence": issue.evidence,
                    "suggested_fix": issue.suggested_fix,
                    "blocks_indexing": issue.blocks_indexing,
                    "blocks_ranking": issue.blocks_ranking,
                }
            )
    return output_path


def export_html(report: CrawlReport, output_path: Path) -> Path:
    """Render and export interactive HTML dashboard report."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    env = get_template_env()
    template = env.get_template("report.html")

    html_content = template.render(report=report)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    return output_path


def generate_all_reports(report: CrawlReport, output_dir: Path) -> Dict[str, Path]:
    """Generate HTML, CSV, and JSON reports in the target directory."""
    output_dir.mkdir(parents=True, exist_ok=True)
    base_name = report.summary.crawl_id

    json_path = output_dir / f"{base_name}.json"
    csv_path = output_dir / f"{base_name}.csv"
    html_path = output_dir / f"{base_name}.html"

    export_json(report, json_path)
    export_csv(report, csv_path)
    export_html(report, html_path)

    return {
        "json": json_path,
        "csv": csv_path,
        "html": html_path,
    }
