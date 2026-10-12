"""Check for broken internal and external links."""

from __future__ import annotations

from typing import Dict, List, Optional

from seo_doctor.models import CrawledPage, IssueCategory, SEOIssue, Severity


def check_broken_links(
    pages: List[CrawledPage],
    page_by_url: Dict[str, CrawledPage],
    external_link_statuses: Optional[Dict[str, int]] = None,
) -> List[SEOIssue]:
    """Scan crawled pages for links leading to 4xx, 5xx, or network errors."""
    issues: List[SEOIssue] = []
    external_statuses = external_link_statuses or {}

    for page in pages:
        # 1. Internal broken links
        for target_url in set(page.internal_links):
            target_page = page_by_url.get(target_url)
            if target_page:
                if target_page.status_code >= 400 or target_page.error_message:
                    code_str = (
                        str(target_page.status_code)
                        if target_page.status_code > 0
                        else target_page.error_message or "Connection Error"
                    )
                    issues.append(
                        SEOIssue(
                            url=page.url,
                            issue_type="broken_internal_link",
                            category=IssueCategory.LINKS,
                            severity=Severity.CRITICAL,
                            evidence=f"Internal link '{target_url}' returned HTTP {code_str}.",
                            suggested_fix=f"Update or remove the hyperlink to '{target_url}', or restore the destination resource.",
                            blocks_indexing=False,
                            blocks_ranking=True,
                        )
                    )

        # 2. External broken links
        for ext_url in set(page.external_links):
            ext_status = external_statuses.get(ext_url)
            if ext_status and ext_status >= 400:
                issues.append(
                    SEOIssue(
                        url=page.url,
                        issue_type="broken_external_link",
                        category=IssueCategory.LINKS,
                        severity=Severity.MEDIUM,
                        evidence=f"External link '{ext_url}' returned HTTP {ext_status}.",
                        suggested_fix=f"Verify if external site moved; update or remove link to '{ext_url}'.",
                        blocks_indexing=False,
                        blocks_ranking=False,
                    )
                )

    return issues
