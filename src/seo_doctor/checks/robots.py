"""Check robots directives: meta robots noindex/nofollow, X-Robots-Tag, and robots.txt disallow."""

from __future__ import annotations

from typing import List, Set

from seo_doctor.models import CrawledPage, IssueCategory, SEOIssue, Severity


def check_robots_directives(
    pages: List[CrawledPage],
    disallowed_urls: Set[str] | None = None,
) -> List[SEOIssue]:
    """Audit indexation directives across meta robots, HTTP headers, and robots.txt disallow rules."""
    issues: List[SEOIssue] = []
    blocked_set = disallowed_urls or set()

    for page in pages:
        # 1. robots.txt Disallow
        if page.url in blocked_set:
            issues.append(
                SEOIssue(
                    url=page.url,
                    issue_type="blocked_by_robots_txt",
                    category=IssueCategory.ROBOTS,
                    severity=Severity.CRITICAL,
                    evidence="URL is disallowed in robots.txt but is linked from internal site pages.",
                    suggested_fix="If this page should be indexed, remove the Disallow directive in robots.txt. If private, remove internal links to it.",
                    blocks_indexing=True,
                    blocks_ranking=True,
                )
            )

        # Combine meta robots strings and x-robots-tag
        all_directives: List[str] = [d.lower() for d in page.meta_robots]
        if page.x_robots_tag:
            all_directives.append(page.x_robots_tag.lower())

        is_noindex = any("noindex" in d or "none" in d for d in all_directives)
        is_nofollow = any("nofollow" in d or "none" in d for d in all_directives)

        # 2. noindex directive
        if is_noindex:
            issues.append(
                SEOIssue(
                    url=page.url,
                    issue_type="robots_noindex_directive",
                    category=IssueCategory.ROBOTS,
                    severity=Severity.CRITICAL,
                    evidence=f"Directives detected: {', '.join(all_directives)}. Search engines will not index this page.",
                    suggested_fix="If this page is intended for organic traffic, remove 'noindex' from meta robots or X-Robots-Tag.",
                    blocks_indexing=True,
                    blocks_ranking=True,
                )
            )

        # 3. nofollow directive on internal page
        if is_nofollow:
            issues.append(
                SEOIssue(
                    url=page.url,
                    issue_type="robots_nofollow_directive",
                    category=IssueCategory.ROBOTS,
                    severity=Severity.HIGH,
                    evidence=f"Directives detected: {', '.join(all_directives)}. Internal outbound links will not pass link authority.",
                    suggested_fix="Remove 'nofollow' from internal pages to ensure crawl budget and internal PageRank flow naturally.",
                    blocks_indexing=False,
                    blocks_ranking=True,
                )
            )

    return issues
