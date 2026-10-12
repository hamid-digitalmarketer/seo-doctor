"""SQLite storage layer for persisting and retrieving audit reports."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

from seo_doctor.models import CrawlReport


def get_default_db_path() -> Path:
    return Path("./reports/seo_doctor.sqlite")


def init_db(db_path: Path) -> None:
    """Initialize database tables if they do not exist."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS crawls (
                crawl_id TEXT PRIMARY KEY,
                start_url TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                duration_seconds REAL NOT NULL,
                total_pages_crawled INTEGER NOT NULL,
                total_issues_found INTEGER NOT NULL,
                critical_issues INTEGER NOT NULL,
                high_issues INTEGER NOT NULL,
                medium_issues INTEGER NOT NULL,
                low_issues INTEGER NOT NULL,
                health_score INTEGER NOT NULL,
                report_json TEXT NOT NULL
            )
            """
        )
        conn.commit()


def save_crawl(report: CrawlReport, db_path: Optional[Path] = None) -> None:
    """Persist a crawl report into SQLite."""
    target_db = db_path or get_default_db_path()
    init_db(target_db)

    report_json_str = report.model_dump_json()
    summary = report.summary

    with sqlite3.connect(target_db) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO crawls (
                crawl_id, start_url, timestamp, duration_seconds,
                total_pages_crawled, total_issues_found, critical_issues,
                high_issues, medium_issues, low_issues, health_score, report_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                summary.crawl_id,
                summary.start_url,
                summary.timestamp,
                summary.duration_seconds,
                summary.total_pages_crawled,
                summary.total_issues_found,
                summary.critical_issues,
                summary.high_issues,
                summary.medium_issues,
                summary.low_issues,
                summary.health_score,
                report_json_str,
            ),
        )
        conn.commit()


def get_crawl(crawl_id: str, db_path: Optional[Path] = None) -> Optional[CrawlReport]:
    """Retrieve a full crawl report by its crawl_id."""
    target_db = db_path or get_default_db_path()
    if not target_db.exists():
        return None

    with sqlite3.connect(target_db) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT report_json FROM crawls WHERE crawl_id = ?", (crawl_id,))
        row = cursor.fetchone()
        if not row:
            return None
        data = json.loads(row[0])
        return CrawlReport.model_validate(data)


def list_crawls(db_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    """List summary records of all stored crawl runs."""
    target_db = db_path or get_default_db_path()
    if not target_db.exists():
        return []

    with sqlite3.connect(target_db) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT crawl_id, start_url, timestamp, total_pages_crawled,
                   total_issues_found, health_score
            FROM crawls
            ORDER BY timestamp DESC
            """
        )
        rows = cursor.fetchall()
        return [
            {
                "crawl_id": r[0],
                "start_url": r[1],
                "timestamp": r[2],
                "total_pages_crawled": r[3],
                "total_issues_found": r[4],
                "health_score": r[5],
            }
            for r in rows
        ]
