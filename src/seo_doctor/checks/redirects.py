"""Check for redirect chains, redirect loops, and temporary redirects."""

from __future__ import annotations

from typing import List

from seo_doctor.models import CrawledPage, IssueCategory, SEOIssue, Severity


def check_redirects(pages: List[CrawledPage]) -> List[SEOIssue]:
    """Analyze redirect histories across all crawled URLs."""
    issues: List[SEOIssue] = []

    for page in pages:
        history = page.redirect_history
        if not history:
            continue

        hop_urls = [h.get("url", "") for h in history if h.get("url")]
        hop_statuses = [str(h.get("status_code", "")) for h in history]

        # 1. Redirect Loops
        seen = set()
        has_loop = False
        loop_url = ""
        for u in hop_urls:
            if u in seen:
                has_loop = True
                loop_url = u
                break
            seen.add(u)

        if has_loop or (page.final_url and page.final_url in hop_urls[:-1]):
            issues.append(
                SEOIssue(
                    url=page.url,
                    issue_type="redirect_loop",
                    category=IssueCategory.REDIRECTS,
                    severity=Severity.CRITICAL,
                    evidence=f"Redirect loop detected: sequence revisits '{loop_url or page.final_url}'.",
                    suggested_fix="Break circular redirection. Point initial URL directly to final destination without loops.",
                    blocks_indexing=True,
                    blocks_ranking=True,
                )
            )
            continue  # Loop takes precedence over chain warning

        # 2. Redirect Chains (2 or more hops)
        if len(history) >= 2:
            chain_str = " -> ".join([f"{u} ({s})" for u, s in zip(hop_urls, hop_statuses)])
            chain_str += f" -> {page.final_url}"
            issues.append(
                SEOIssue(
                    url=page.url,
                    issue_type="redirect_chain",
                    category=IssueCategory.REDIRECTS,
                    severity=Severity.HIGH,
                    evidence=f"Redirect chain of {len(history)} hops detected: {chain_str}",
                    suggested_fix=f"Update links and server configuration to redirect directly to '{page.final_url}' in a single 301 hop.",
                    blocks_indexing=False,
                    blocks_ranking=True,
                )
            )

        # 3. Temporary Redirect (302, 307) on internal URLs
        first_hop_status = history[0].get("status_code", 0) if history else 0
        if first_hop_status in (302, 307):
            issues.append(
                SEOIssue(
                    url=page.url,
                    issue_type="temporary_redirect_used",
                    category=IssueCategory.REDIRECTS,
                    severity=Severity.LOW,
                    evidence=f"URL uses temporary HTTP {first_hop_status} redirect instead of permanent 301.",
                    suggested_fix="If this is a permanent site restructuring, use HTTP 301 to pass full link equity.",
                    blocks_indexing=False,
                    blocks_ranking=False,
                )
            )

    return issues
