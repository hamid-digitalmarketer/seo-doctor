"""Check internal link graph for orphan page candidates."""

from __future__ import annotations

from collections import defaultdict
from typing import Dict, List, Set

from seo_doctor.models import CrawledPage, IssueCategory, SEOIssue, Severity


def check_orphan_pages(
    pages: List[CrawledPage],
    sitemap_urls: List[str],
    start_url: str,
) -> tuple[List[SEOIssue], List[str]]:
    """Identify URLs present in sitemaps or crawled sets that have zero inbound internal links."""
    issues: List[SEOIssue] = []
    inbound_counts: Dict[str, int] = defaultdict(int)

    # Count inbound internal links across all crawled pages
    for page in pages:
        for target in set(page.internal_links):
            inbound_counts[target] += 1

    # Candidate set: all sitemap URLs plus crawled pages
    all_known_urls: Set[str] = set(sitemap_urls) | {p.url for p in pages}
    orphan_candidates: List[str] = []

    for url in sorted(all_known_urls):
        # Exclude homepage / start_url from orphan flag
        if url.rstrip("/") == start_url.rstrip("/"):
            continue

        if inbound_counts[url] == 0:
            orphan_candidates.append(url)
            issues.append(
                SEOIssue(
                    url=url,
                    issue_type="orphan_page_candidate",
                    category=IssueCategory.STRUCTURE,
                    severity=Severity.HIGH,
                    evidence="Page has 0 inbound internal links from other pages on the website.",
                    suggested_fix="Integrate this page into site navigation, category pages, or relevant contextual blog links to distribute PageRank.",
                    blocks_indexing=False,
                    blocks_ranking=True,
                )
            )

    return issues, orphan_candidates
