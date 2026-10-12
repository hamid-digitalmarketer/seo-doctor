"""SEO-Doctor: Open-source Technical SEO Auditor and Crawler."""

__version__ = "0.1.0"
__author__ = "Muhammad Hamid"

from seo_doctor.config import CrawlConfig
from seo_doctor.crawler import SEOCrawler
from seo_doctor.models import CrawlReport, SEOIssue, Severity

__all__ = [
    "CrawlConfig",
    "SEOCrawler",
    "CrawlReport",
    "SEOIssue",
    "Severity",
]
