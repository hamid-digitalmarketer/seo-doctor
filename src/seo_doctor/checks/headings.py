"""Check heading structure: H1 existence, duplicates, and heading hierarchy order."""

from __future__ import annotations

from typing import List

from seo_doctor.models import CrawledPage, IssueCategory, SEOIssue, Severity


def check_headings(pages: List[CrawledPage]) -> List[SEOIssue]:
    """Audit H1 and nested heading hierarchy on all crawled pages."""
    issues: List[SEOIssue] = []

    for page in pages:
        if page.status_code != 200 or page.is_redirect:
            continue

        h1_count = len(page.h1_tags)

        # 1. Missing H1
        if h1_count == 0:
            issues.append(
                SEOIssue(
                    url=page.url,
                    issue_type="missing_h1",
                    category=IssueCategory.HEADINGS,
                    severity=Severity.HIGH,
                    evidence="Page contains zero <h1> heading tags.",
                    suggested_fix="Add a prominent <h1> tag that describes the page topic and includes target search terms.",
                    blocks_indexing=False,
                    blocks_ranking=True,
                )
            )
        # 2. Multiple H1s
        elif h1_count > 1:
            h1_snippets = " | ".join([f"'{h[:30]}...'" if len(h) > 30 else f"'{h}'" for h in page.h1_tags[:3]])
            issues.append(
                SEOIssue(
                    url=page.url,
                    issue_type="multiple_h1",
                    category=IssueCategory.HEADINGS,
                    severity=Severity.MEDIUM,
                    evidence=f"Page has {h1_count} <h1> tags: {h1_snippets}",
                    suggested_fix="Consolidate to a single <h1> heading representing the core page theme; convert secondary headings to <h2>.",
                    blocks_indexing=False,
                    blocks_ranking=False,
                )
            )

        # 3. Heading Hierarchy / Skipped Levels (e.g. H1 directly to H3 without H2)
        if page.headings:
            prev_level = 0
            for h_item in page.headings:
                lvl_str = h_item.get("level", "h1").lower()
                if len(lvl_str) == 2 and lvl_str[0] == "h" and lvl_str[1].isdigit():
                    curr_level = int(lvl_str[1])
                    if prev_level > 0 and curr_level > prev_level + 1:
                        issues.append(
                            SEOIssue(
                                url=page.url,
                                issue_type="heading_hierarchy_skipped_level",
                                category=IssueCategory.HEADINGS,
                                severity=Severity.LOW,
                                evidence=f"Heading hierarchy skips from <h{prev_level}> to <h{curr_level}> ('{h_item.get('text', '')[:40]}').",
                                suggested_fix=f"Maintain sequential heading levels (use <h{prev_level + 1}> before <h{curr_level}>) for better document accessibility and semantic indexing.",
                                blocks_indexing=False,
                                blocks_ranking=False,
                            )
                        )
                        break  # Report once per page
                    prev_level = curr_level

    return issues
