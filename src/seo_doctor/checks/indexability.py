"""Check page indexability status, HTTP response codes, and content depth."""

from __future__ import annotations

from typing import List

from seo_doctor.models import CrawledPage, IssueCategory, SEOIssue, Severity


def check_indexability(pages: List[CrawledPage]) -> List[SEOIssue]:
    """Audit HTTP status codes, server errors, and content depth across all crawled pages."""
    issues: List[SEOIssue] = []

    for page in pages:
        # 1. 4xx Client Errors
        if 400 <= page.status_code < 500:
            issues.append(
                SEOIssue(
                    url=page.url,
                    issue_type="client_error_4xx",
                    category=IssueCategory.INDEXABILITY,
                    severity=Severity.CRITICAL,
                    evidence=f"Server returned HTTP {page.status_code} client error.",
                    suggested_fix="Fix dead link, restore missing resource, or implement 301 redirect to relevant active page.",
                    blocks_indexing=True,
                    blocks_ranking=True,
                )
            )

        # 2. 5xx Server Errors
        elif page.status_code >= 500:
            issues.append(
                SEOIssue(
                    url=page.url,
                    issue_type="server_error_5xx",
                    category=IssueCategory.INDEXABILITY,
                    severity=Severity.CRITICAL,
                    evidence=f"Server returned HTTP {page.status_code} internal error.",
                    suggested_fix="Investigate backend web server logs, database timeouts, or runtime exceptions.",
                    blocks_indexing=True,
                    blocks_ranking=True,
                )
            )

        # 3. Connection Errors / Timeouts
        elif page.error_message:
            issues.append(
                SEOIssue(
                    url=page.url,
                    issue_type="page_fetch_failed",
                    category=IssueCategory.INDEXABILITY,
                    severity=Severity.CRITICAL,
                    evidence=f"Crawl fetch failed with error: {page.error_message}",
                    suggested_fix="Check domain DNS records, SSL/TLS certificate validity, and firewall rate-limiting.",
                    blocks_indexing=True,
                    blocks_ranking=True,
                )
            )

        # 4. Thin content check on indexable pages
        if page.status_code == 200 and not page.is_redirect:
            if page.word_count < 100:
                issues.append(
                    SEOIssue(
                        url=page.url,
                        issue_type="thin_content",
                        category=IssueCategory.INDEXABILITY,
                        severity=Severity.LOW,
                        evidence=f"Page body contains only {page.word_count} words.",
                        suggested_fix="Enrich page with comprehensive, helpful content answering user search intent.",
                        blocks_indexing=False,
                        blocks_ranking=False,
                    )
                )

    return issues
