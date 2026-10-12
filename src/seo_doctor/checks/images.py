"""Check image assets: missing alt text, empty alt text, and broken image sources."""

from __future__ import annotations

from typing import Dict, List

from seo_doctor.models import CrawledPage, IssueCategory, SEOIssue, Severity


def check_images(
    pages: List[CrawledPage],
    page_by_url: Dict[str, CrawledPage] | None = None,
) -> List[SEOIssue]:
    """Audit image tags across crawled pages for accessibility and SEO best practices."""
    issues: List[SEOIssue] = []
    url_map = page_by_url or {}

    for page in pages:
        if page.status_code != 200 or page.is_redirect:
            continue

        for img in page.images:
            src = img.get("src", "").strip()
            alt = img.get("alt")
            is_missing_alt = img.get("missing_alt", False)

            if not src:
                continue

            # 1. Missing alt attribute entirely
            if is_missing_alt:
                issues.append(
                    SEOIssue(
                        url=page.url,
                        issue_type="missing_image_alt",
                        category=IssueCategory.IMAGES,
                        severity=Severity.MEDIUM,
                        evidence=f"Image source '{src}' lacks an alt attribute entirely.",
                        suggested_fix=f"Add descriptive alt text to <img src='{src}'> to assist screen readers and Google Image search.",
                        blocks_indexing=False,
                        blocks_ranking=False,
                    )
                )
            # 2. Empty alt on non-decorative images
            elif alt == "":
                # Check if image looks like a content or brand asset rather than a spacer
                lower_src = src.lower()
                is_likely_content = any(k in lower_src for k in ("product", "hero", "logo", "banner", "chart", "diagram"))
                if is_likely_content:
                    issues.append(
                        SEOIssue(
                            url=page.url,
                            issue_type="empty_image_alt",
                            category=IssueCategory.IMAGES,
                            severity=Severity.LOW,
                            evidence=f"Content image '{src}' has an empty alt='' attribute.",
                            suggested_fix="If this image conveys meaningful information, supply descriptive alt text. If purely decorative, keep empty.",
                            blocks_indexing=False,
                            blocks_ranking=False,
                        )
                    )

            # 3. Broken image source (if target crawled or matched 404)
            if src in url_map and url_map[src].status_code >= 400:
                issues.append(
                    SEOIssue(
                        url=page.url,
                        issue_type="broken_image_source",
                        category=IssueCategory.IMAGES,
                        severity=Severity.HIGH,
                        evidence=f"Image src '{src}' returns HTTP {url_map[src].status_code}.",
                        suggested_fix=f"Replace or repair broken image link '{src}'.",
                        blocks_indexing=False,
                        blocks_ranking=False,
                    )
                )

    return issues
