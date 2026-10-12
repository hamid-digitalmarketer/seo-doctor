"""Check page metadata: title and meta description presence, lengths, and duplicates."""

from __future__ import annotations

from collections import defaultdict
from typing import Dict, List

from seo_doctor.models import CrawledPage, IssueCategory, SEOIssue, Severity


def check_metadata(pages: List[CrawledPage]) -> List[SEOIssue]:
    """Audit title tags and meta descriptions for missing elements, length anomalies, and duplicates."""
    issues: List[SEOIssue] = []

    # Filter to successful HTML pages
    valid_pages = [p for p in pages if p.status_code == 200 and not p.is_redirect]

    title_map: Dict[str, List[str]] = defaultdict(list)
    desc_map: Dict[str, List[str]] = defaultdict(list)

    for page in valid_pages:
        title = page.title.strip() if page.title else ""
        desc = page.meta_description.strip() if page.meta_description else ""

        # --- Title Checks ---
        if not title:
            issues.append(
                SEOIssue(
                    url=page.url,
                    issue_type="missing_title",
                    category=IssueCategory.METADATA,
                    severity=Severity.CRITICAL,
                    evidence="Page has no <title> tag or the title element is blank.",
                    suggested_fix="Add a unique, descriptive <title> tag between 30 and 60 characters incorporating primary page keywords.",
                    blocks_indexing=False,
                    blocks_ranking=True,
                )
            )
        else:
            title_len = len(title)
            if title_len < 30:
                issues.append(
                    SEOIssue(
                        url=page.url,
                        issue_type="title_too_short",
                        category=IssueCategory.METADATA,
                        severity=Severity.LOW,
                        evidence=f"Title length is {title_len} characters ('{title}'), below the recommended 30 character minimum.",
                        suggested_fix="Expand title to provide better context for search engine users and click-through rates.",
                        blocks_indexing=False,
                        blocks_ranking=False,
                    )
                )
            elif title_len > 60:
                issues.append(
                    SEOIssue(
                        url=page.url,
                        issue_type="title_too_long",
                        category=IssueCategory.METADATA,
                        severity=Severity.LOW,
                        evidence=f"Title length is {title_len} characters ('{title[:60]}...'), exceeding the 60 character SERP display limit.",
                        suggested_fix="Shorten title to under 60 characters to prevent truncation in Google search results.",
                        blocks_indexing=False,
                        blocks_ranking=False,
                    )
                )
            title_map[title.lower()].append(page.url)

        # --- Meta Description Checks ---
        if not desc:
            issues.append(
                SEOIssue(
                    url=page.url,
                    issue_type="missing_meta_description",
                    category=IssueCategory.METADATA,
                    severity=Severity.MEDIUM,
                    evidence="Page lacks a meta description tag.",
                    suggested_fix="Add a concise, compelling meta description between 50 and 160 characters to improve organic CTR.",
                    blocks_indexing=False,
                    blocks_ranking=False,
                )
            )
        else:
            desc_len = len(desc)
            if desc_len < 50:
                issues.append(
                    SEOIssue(
                        url=page.url,
                        issue_type="meta_description_too_short",
                        category=IssueCategory.METADATA,
                        severity=Severity.LOW,
                        evidence=f"Meta description is only {desc_len} characters, below optimal 50-character threshold.",
                        suggested_fix="Provide a more descriptive summary of the page content.",
                        blocks_indexing=False,
                        blocks_ranking=False,
                    )
                )
            elif desc_len > 160:
                issues.append(
                    SEOIssue(
                        url=page.url,
                        issue_type="meta_description_too_long",
                        category=IssueCategory.METADATA,
                        severity=Severity.LOW,
                        evidence=f"Meta description is {desc_len} characters, which may be truncated in search snippets.",
                        suggested_fix="Trim meta description to under 160 characters.",
                        blocks_indexing=False,
                        blocks_ranking=False,
                    )
                )
            desc_map[desc.lower()].append(page.url)

    # --- Duplicate Title Detection ---
    for raw_title_lower, urls in title_map.items():
        if len(urls) > 1:
            for url in urls:
                other_urls = [u for u in urls if u != url]
                issues.append(
                    SEOIssue(
                        url=url,
                        issue_type="duplicate_title",
                        category=IssueCategory.METADATA,
                        severity=Severity.HIGH,
                        evidence=f"Shares exact title with {len(other_urls)} other page(s) (e.g. {other_urls[0]}).",
                        suggested_fix="Craft a unique title tag reflecting this specific URL's distinct value proposition.",
                        blocks_indexing=False,
                        blocks_ranking=True,
                    )
                )

    # --- Duplicate Meta Description Detection ---
    for raw_desc_lower, urls in desc_map.items():
        if len(urls) > 1:
            for url in urls:
                other_urls = [u for u in urls if u != url]
                issues.append(
                    SEOIssue(
                        url=url,
                        issue_type="duplicate_meta_description",
                        category=IssueCategory.METADATA,
                        severity=Severity.MEDIUM,
                        evidence=f"Shares identical meta description with {len(other_urls)} other page(s) (e.g. {other_urls[0]}).",
                        suggested_fix="Write unique meta description tailored specifically to this page's topic.",
                        blocks_indexing=False,
                        blocks_ranking=False,
                    )
                )

    return issues
