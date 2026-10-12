"""Technical SEO diagnostic checks registry."""

from seo_doctor.checks.broken_links import check_broken_links
from seo_doctor.checks.canonical import check_canonical_tags
from seo_doctor.checks.headings import check_headings
from seo_doctor.checks.images import check_images
from seo_doctor.checks.indexability import check_indexability
from seo_doctor.checks.metadata import check_metadata
from seo_doctor.checks.orphan_pages import check_orphan_pages
from seo_doctor.checks.redirects import check_redirects
from seo_doctor.checks.robots import check_robots_directives
from seo_doctor.checks.sitemap import check_sitemap_urls

__all__ = [
    "check_broken_links",
    "check_canonical_tags",
    "check_headings",
    "check_images",
    "check_indexability",
    "check_metadata",
    "check_orphan_pages",
    "check_redirects",
    "check_robots_directives",
    "check_sitemap_urls",
]
