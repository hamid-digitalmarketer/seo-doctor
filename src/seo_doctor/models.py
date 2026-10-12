"""Core data models for SEO-Doctor."""

from __future__ import annotations

import hashlib
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class Severity(str, Enum):
    """Severity levels for technical SEO issues."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class IssueCategory(str, Enum):
    """Categorization of technical SEO audits."""
    INDEXABILITY = "indexability"
    LINKS = "links"
    REDIRECTS = "redirects"
    METADATA = "metadata"
    HEADINGS = "headings"
    CANONICAL = "canonical"
    ROBOTS = "robots"
    IMAGES = "images"
    SITEMAP = "sitemap"
    STRUCTURE = "structure"


class SEOIssue(BaseModel):
    """Represents a discrete technical SEO issue detected on a page."""
    id: str = ""
    url: str
    issue_type: str
    category: IssueCategory
    severity: Severity
    evidence: str
    suggested_fix: str
    blocks_indexing: bool = False
    blocks_ranking: bool = False

    def model_post_init(self, __context: Any) -> None:
        if not self.id:
            raw_key = f"{self.url}|{self.issue_type}|{self.evidence}"
            self.id = hashlib.sha256(raw_key.encode("utf-8")).hexdigest()[:12]


class CrawledPage(BaseModel):
    """Comprehensive telemetry and SEO attributes extracted from a crawled URL."""
    url: str
    status_code: int = 0
    content_type: str = "text/html"
    load_time_ms: float = 0.0
    title: Optional[str] = None
    meta_description: Optional[str] = None
    canonical_url: Optional[str] = None
    canonical_tags: List[str] = Field(default_factory=list)
    h1_tags: List[str] = Field(default_factory=list)
    headings: List[Dict[str, str]] = Field(default_factory=list)
    meta_robots: List[str] = Field(default_factory=list)
    x_robots_tag: Optional[str] = None
    internal_links: List[str] = Field(default_factory=list)
    external_links: List[str] = Field(default_factory=list)
    images: List[Dict[str, Any]] = Field(default_factory=list)
    redirect_history: List[Dict[str, Any]] = Field(default_factory=list)
    is_redirect: bool = False
    final_url: Optional[str] = None
    word_count: int = 0
    html_size_bytes: int = 0
    error_message: Optional[str] = None


class CrawlSummary(BaseModel):
    """High-level metrics and health summary for an audit run."""
    crawl_id: str
    start_url: str
    timestamp: str
    duration_seconds: float
    total_pages_crawled: int
    status_200_count: int = 0
    status_3xx_count: int = 0
    status_4xx_count: int = 0
    status_5xx_count: int = 0
    total_issues_found: int = 0
    critical_issues: int = 0
    high_issues: int = 0
    medium_issues: int = 0
    low_issues: int = 0
    health_score: int = 100


class CrawlReport(BaseModel):
    """Complete technical audit report for persistence and export."""
    summary: CrawlSummary
    pages: List[CrawledPage] = Field(default_factory=list)
    issues: List[SEOIssue] = Field(default_factory=list)
    orphan_candidates: List[str] = Field(default_factory=list)
    sitemap_urls: List[str] = Field(default_factory=list)


class ComparisonResult(BaseModel):
    """Comparison between two crawl reports showing fixes and regressions."""
    baseline_crawl_id: str
    comparison_crawl_id: str
    baseline_timestamp: str
    comparison_timestamp: str
    health_score_delta: int
    total_issues_delta: int
    pages_crawled_delta: int
    issues_fixed: List[SEOIssue] = Field(default_factory=list)
    issues_introduced: List[SEOIssue] = Field(default_factory=list)
    issues_still_open: List[SEOIssue] = Field(default_factory=list)
