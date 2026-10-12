"""Check sitemap status and validate sitemap URL health."""

from __future__ import annotations

from typing import Dict, List

from seo_doctor.models import CrawledPage, IssueCategory, SEOIssue, Severity


def check_sitemap_urls(
    start_url: str,
    sitemap_found: bool,
    sitemap_urls: List[str],
    page_by_url: Dict[str, CrawledPage],
) -> List[SEOIssue]:
    """Audit sitemap discovery and verify that sitemap URLs are live, canonical, and indexable."""
    issues: List[SEOIssue] = []

    # 1. Missing sitemap.xml
    if not sitemap_found:
        issues.append(
            SEOIssue(
                url=start_url,
                issue_type="missing_sitemap",
                category=IssueCategory.SITEMAP,
                severity=Severity.HIGH,
                evidence="Could not locate a valid XML sitemap at /sitemap.xml or specified location.",
                suggested_fix="Create and submit a standard XML sitemap (sitemap.xml) and declare its location in robots.txt.",
                blocks_indexing=False,
                blocks_ranking=True,
            )
        )
        return issues

    # 2. Audit each URL listed in sitemap
    for s_url in set(sitemap_urls):
        page = page_by_url.get(s_url)
        if not page:
            continue

        # Broken URL in sitemap
        if page.status_code >= 400 or page.error_message:
            issues.append(
                SEOIssue(
                    url=s_url,
                    issue_type="sitemap_broken_url",
                    category=IssueCategory.SITEMAP,
                    severity=Severity.CRITICAL,
                    evidence=f"URL listed in XML sitemap returned HTTP {page.status_code} (Dead/Unreachable).",
                    suggested_fix=f"Remove '{s_url}' from sitemap.xml or restore page to HTTP 200.",
                    blocks_indexing=True,
                    blocks_ranking=True,
                )
            )

        # Redirect in sitemap
        elif page.is_redirect or page.status_code in (301, 302, 307, 308):
            issues.append(
                SEOIssue(
                    url=s_url,
                    issue_type="sitemap_redirect_url",
                    category=IssueCategory.SITEMAP,
                    severity=Severity.HIGH,
                    evidence=f"URL listed in XML sitemap redirects (HTTP {page.status_code}) to '{page.final_url}'.",
                    suggested_fix=f"Update sitemap.xml to list destination '{page.final_url}' directly.",
                    blocks_indexing=False,
                    blocks_ranking=False,
                )
            )

        # Noindex in sitemap
        all_directives = [d.lower() for d in page.meta_robots]
        if page.x_robots_tag:
            all_directives.append(page.x_robots_tag.lower())
        if any("noindex" in d for d in all_directives):
            issues.append(
                SEOIssue(
                    url=s_url,
                    issue_type="sitemap_noindex_url",
                    category=IssueCategory.SITEMAP,
                    severity=Severity.CRITICAL,
                    evidence=f"URL listed in XML sitemap has a 'noindex' directive ({', '.join(all_directives)}).",
                    suggested_fix="Remove noindexed URLs from sitemap.xml. Sitemaps should exclusively contain indexable URLs.",
                    blocks_indexing=True,
                    blocks_ranking=False,
                )
            )

    return issues
