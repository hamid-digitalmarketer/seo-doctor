"""Check canonical link tags: missing, multiple, broken targets, and redirect targets."""

from __future__ import annotations

from typing import Dict, List
from urllib.parse import urlparse

from seo_doctor.models import CrawledPage, IssueCategory, SEOIssue, Severity


def check_canonical_tags(
    pages: List[CrawledPage],
    page_by_url: Dict[str, CrawledPage],
) -> List[SEOIssue]:
    """Audit canonical link elements for missing tags, duplicates, and invalid destinations."""
    issues: List[SEOIssue] = []

    for page in pages:
        if page.status_code != 200 or page.is_redirect:
            continue

        c_tags = page.canonical_tags

        # 1. Missing canonical tag
        if not c_tags:
            issues.append(
                SEOIssue(
                    url=page.url,
                    issue_type="missing_canonical",
                    category=IssueCategory.CANONICAL,
                    severity=Severity.MEDIUM,
                    evidence="Page has no <link rel='canonical'> tag declared.",
                    suggested_fix=f"Add a self-referential canonical tag <link rel='canonical' href='{page.url}'> to prevent duplicate URL parameters from diluting ranking signals.",
                    blocks_indexing=False,
                    blocks_ranking=False,
                )
            )
            continue

        # 2. Multiple canonical tags
        if len(c_tags) > 1:
            issues.append(
                SEOIssue(
                    url=page.url,
                    issue_type="multiple_canonical_tags",
                    category=IssueCategory.CANONICAL,
                    severity=Severity.CRITICAL,
                    evidence=f"Page declares {len(c_tags)} conflicting canonical tags: {', '.join(c_tags)}.",
                    suggested_fix="Ensure only one authoritative <link rel='canonical'> tag is present in the <head>.",
                    blocks_indexing=True,
                    blocks_ranking=True,
                )
            )
            continue

        # 3. Canonical target validity
        canonical_target = c_tags[0].strip()
        target_page = page_by_url.get(canonical_target)

        if target_page:
            # Canonical points to broken page (4xx / 5xx)
            if target_page.status_code >= 400 or target_page.error_message:
                issues.append(
                    SEOIssue(
                        url=page.url,
                        issue_type="canonical_points_to_broken_url",
                        category=IssueCategory.CANONICAL,
                        severity=Severity.CRITICAL,
                        evidence=f"Canonical tag points to '{canonical_target}', which returns HTTP {target_page.status_code}.",
                        suggested_fix="Update canonical destination to a live, indexable HTTP 200 URL.",
                        blocks_indexing=True,
                        blocks_ranking=True,
                    )
                )
            # Canonical points to a redirect (3xx)
            elif target_page.is_redirect or target_page.status_code in (301, 302, 307, 308):
                issues.append(
                    SEOIssue(
                        url=page.url,
                        issue_type="canonical_points_to_redirect",
                        category=IssueCategory.CANONICAL,
                        severity=Severity.HIGH,
                        evidence=f"Canonical tag points to '{canonical_target}', which redirects (HTTP {target_page.status_code}).",
                        suggested_fix=f"Update canonical URL to point directly to the final destination '{target_page.final_url or canonical_target}'.",
                        blocks_indexing=False,
                        blocks_ranking=True,
                    )
                )

        # 4. Cross-domain canonical check
        page_domain = urlparse(page.url).netloc
        canonical_domain = urlparse(canonical_target).netloc
        if canonical_domain and page_domain != canonical_domain:
            issues.append(
                SEOIssue(
                    url=page.url,
                    issue_type="canonical_cross_domain_conflict",
                    category=IssueCategory.CANONICAL,
                    severity=Severity.HIGH,
                    evidence=f"Canonical points to external domain '{canonical_domain}' instead of current domain '{page_domain}'.",
                    suggested_fix="Verify if cross-domain canonicalization is intentional (e.g. syndicated content); otherwise, point to current domain.",
                    blocks_indexing=True,
                    blocks_ranking=True,
                )
            )

    return issues
