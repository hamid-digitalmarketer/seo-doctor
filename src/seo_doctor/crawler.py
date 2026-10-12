"""Production-grade asynchronous/synchronous SEO crawler and analyzer."""

from __future__ import annotations

import re
import time
import uuid
import xml.etree.ElementTree as ET
from collections import deque
from datetime import datetime
from typing import Dict, List, Set, Tuple
from urllib.parse import urljoin, urlparse, urlunparse

import requests
from bs4 import BeautifulSoup

from seo_doctor.checks import (
    check_broken_links,
    check_canonical_tags,
    check_headings,
    check_images,
    check_indexability,
    check_metadata,
    check_orphan_pages,
    check_redirects,
    check_robots_directives,
    check_sitemap_urls,
)
from seo_doctor.config import CrawlConfig
from seo_doctor.models import (
    CrawledPage,
    CrawlReport,
    CrawlSummary,
    SEOIssue,
    Severity,
)


def normalize_url(url: str, base_url: str = "") -> str:
    """Normalize and resolve URL: trim fragments, unify scheme/domain, format paths."""
    if not url:
        return ""
    if base_url:
        url = urljoin(base_url, url)

    parsed = urlparse(url)
    scheme = parsed.scheme.lower() or "http"
    netloc = parsed.netloc.lower()

    # Drop standard default ports
    if netloc.endswith(":80") and scheme == "http":
        netloc = netloc[:-3]
    elif netloc.endswith(":443") and scheme == "https":
        netloc = netloc[:-4]

    path = parsed.path or "/"
    # Clean redundant slashes
    path = re.sub(r"/+", "/", path)

    # Standardize query
    query = parsed.query

    # Reconstruct without fragment
    normalized = urlunparse((scheme, netloc, path, parsed.params, query, ""))
    return normalized


def is_internal_url(url: str, base_domain: str) -> bool:
    """Determine whether a given URL belongs to the target domain."""
    target_netloc = urlparse(url).netloc.lower()
    base_netloc = base_domain.lower()

    # Strip port if present
    target_domain = target_netloc.split(":")[0]
    base_domain_clean = base_netloc.split(":")[0]

    if target_domain == base_domain_clean:
        return True

    # Allow matching www.example.com to example.com
    target_clean = re.sub(r"^www\.", "", target_domain)
    base_clean = re.sub(r"^www\.", "", base_domain_clean)
    return target_clean == base_clean


class RobotsTxtParser:
    """Simple, robust robots.txt parser and checker."""

    def __init__(self, raw_content: str = ""):
        self.disallowed_paths: List[str] = []
        self.sitemap_urls: List[str] = []
        if raw_content:
            self._parse(raw_content)

    def _parse(self, content: str) -> None:
        lines = content.splitlines()
        current_agent_applies = False

        for line in lines:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            parts = line.split(":", 1)
            if len(parts) != 2:
                continue

            key = parts[0].strip().lower()
            val = parts[1].strip()

            if key == "user-agent":
                agent = val.lower()
                current_agent_applies = agent in ("*", "seo-doctor-bot", "googlebot")
            elif key == "disallow" and current_agent_applies:
                if val:
                    self.disallowed_paths.append(val)
            elif key == "sitemap":
                self.sitemap_urls.append(val)

    def is_allowed(self, path: str) -> bool:
        for disallow in self.disallowed_paths:
            if disallow == "/":
                return False
            if path.startswith(disallow):
                return False
        return True


class SEOCrawler:
    """Comprehensive SEO web crawler and diagnostics engine."""

    def __init__(self, config: CrawlConfig):
        self.config = config
        self.start_url = normalize_url(config.start_url)
        self.base_domain = urlparse(self.start_url).netloc
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": self.config.user_agent})
        self.robots_parser = RobotsTxtParser()
        self.disallowed_urls: Set[str] = set()
        self.sitemap_urls: List[str] = []
        self.sitemap_found = False

    def fetch_robots_txt(self) -> None:
        """Fetch and parse robots.txt for the target domain."""
        if not self.config.respect_robots_txt:
            return

        parsed = urlparse(self.start_url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        try:
            resp = self.session.get(robots_url, timeout=self.config.timeout_seconds)
            if resp.status_code == 200:
                self.robots_parser = RobotsTxtParser(resp.text)
                for s_url in self.robots_parser.sitemap_urls:
                    norm = normalize_url(s_url, self.start_url)
                    if norm not in self.sitemap_urls:
                        self.sitemap_urls.append(norm)
                        self.sitemap_found = True
        except Exception:
            pass

    def fetch_sitemap(self) -> None:
        """Discover and parse XML sitemaps."""
        candidates: List[str] = []
        if self.config.sitemap_url:
            candidates.append(normalize_url(self.config.sitemap_url))
        else:
            candidates.extend(self.sitemap_urls)
            parsed = urlparse(self.start_url)
            candidates.append(f"{parsed.scheme}://{parsed.netloc}/sitemap.xml")

        discovered: List[str] = []
        for s_url in candidates:
            try:
                resp = self.session.get(s_url, timeout=self.config.timeout_seconds)
                if resp.status_code == 200 and resp.text:
                    self.sitemap_found = True
                    urls = self._parse_sitemap_xml(resp.content)
                    discovered.extend(urls)
                    break
            except Exception:
                continue

        self.sitemap_urls = list(dict.fromkeys(discovered))

    def _parse_sitemap_xml(self, xml_bytes: bytes) -> List[str]:
        """Extract URLs from XML sitemap or sitemap index."""
        urls: List[str] = []
        try:
            root = ET.fromstring(xml_bytes)
            # Remove XML namespace prefixes if present
            for elem in root.iter():
                if "}" in elem.tag:
                    elem.tag = elem.tag.split("}", 1)[1]

            # Sitemap Index
            if root.tag == "sitemapindex":
                for sitemap_elem in root.findall("sitemap"):
                    loc = sitemap_elem.find("loc")
                    if loc is not None and loc.text:
                        sub_url = loc.text.strip()
                        try:
                            sub_resp = self.session.get(sub_url, timeout=self.config.timeout_seconds)
                            if sub_resp.status_code == 200:
                                urls.extend(self._parse_sitemap_xml(sub_resp.content))
                        except Exception:
                            pass
            # Standard Urlset
            elif root.tag == "urlset":
                for url_elem in root.findall("url"):
                    loc = url_elem.find("loc")
                    if loc is not None and loc.text:
                        urls.append(normalize_url(loc.text.strip(), self.start_url))
        except Exception:
            pass
        return urls

    def parse_page(self, url: str, resp: requests.Response, load_time_ms: float) -> CrawledPage:
        """Parse HTML document and extract SEO metadata, headings, links, and media."""
        content_type = resp.headers.get("Content-Type", "")
        page = CrawledPage(
            url=url,
            status_code=resp.status_code,
            content_type=content_type,
            load_time_ms=round(load_time_ms, 2),
            final_url=normalize_url(resp.url),
            is_redirect=len(resp.history) > 0,
            x_robots_tag=resp.headers.get("X-Robots-Tag"),
            html_size_bytes=len(resp.content),
        )

        # Process redirect history
        for hop in resp.history:
            page.redirect_history.append(
                {"url": normalize_url(hop.url), "status_code": hop.status_code}
            )

        # Non-HTML content check
        if "text/html" not in content_type and "application/xhtml" not in content_type:
            return page

        try:
            soup = BeautifulSoup(resp.text, "html.parser")
        except Exception as e:
            page.error_message = f"HTML Parsing error: {e}"
            return page

        # 1. Title
        title_tag = soup.find("title")
        if title_tag and title_tag.string:
            page.title = title_tag.string.strip()

        # 2. Meta Description
        meta_desc = soup.find("meta", attrs={"name": re.compile(r"^description$", re.I)})
        if meta_desc and meta_desc.get("content"):
            page.meta_description = str(meta_desc.get("content")).strip()

        # 3. Canonical Tags
        canonical_links = soup.find_all(
            "link", attrs={"rel": lambda r: bool(r is not None and "canonical" in str(r))}
        )
        for c in canonical_links:
            href_attr = c.get("href")
            if href_attr:
                href_str = str(href_attr).strip()
                page.canonical_tags.append(normalize_url(href_str, url))
        if page.canonical_tags:
            page.canonical_url = page.canonical_tags[0]

        # 4. Meta Robots
        meta_robots_tags = soup.find_all(
            "meta", attrs={"name": re.compile(r"^(robots|googlebot)$", re.I)}
        )
        for mr in meta_robots_tags:
            content = mr.get("content")
            if content:
                directives = [d.strip().lower() for d in str(content).split(",")]
                page.meta_robots.extend(directives)

        # 5. Headings (H1 - H6)
        headings = soup.find_all(re.compile(r"^h[1-6]$", re.I))
        for h in headings:
            h_text = h.get_text(strip=True)
            page.headings.append({"level": h.name.lower(), "text": h_text})
            if h.name.lower() == "h1":
                page.h1_tags.append(h_text)

        # 6. Links (Internal & External)
        for a_tag in soup.find_all("a", href=True):
            raw_href = str(a_tag["href"]).strip()
            if not raw_href or raw_href.startswith(
                ("javascript:", "mailto:", "tel:", "#", "data:")
            ):
                continue

            target_norm = normalize_url(raw_href, url)
            if not target_norm:
                continue

            if is_internal_url(target_norm, self.base_domain):
                if target_norm not in page.internal_links:
                    page.internal_links.append(target_norm)
            else:
                if target_norm not in page.external_links:
                    page.external_links.append(target_norm)

        # 7. Images
        for img_tag in soup.find_all("img"):
            src_attr = img_tag.get("src")
            if not src_attr:
                continue
            raw_src = str(src_attr).strip()
            if not raw_src:
                continue
            src_norm = normalize_url(raw_src, url)
            alt_attr = img_tag.get("alt")
            alt_str = str(alt_attr).strip() if alt_attr is not None else None
            page.images.append(
                {
                    "src": src_norm,
                    "alt": alt_str,
                    "missing_alt": alt_attr is None,
                }
            )

        # 8. Body text & Word Count
        for script_style in soup(["script", "style", "noscript"]):
            script_style.decompose()
        visible_text = soup.get_text(separator=" ", strip=True)
        words = [w for w in visible_text.split() if len(w) > 1]
        page.word_count = len(words)

        return page

    def crawl(self) -> CrawlReport:
        """Execute full site crawl and compile comprehensive audit report."""
        start_time = time.time()
        crawl_id = f"crawl-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:6]}"

        # Step 1: Discover robots.txt and sitemap.xml
        self.fetch_robots_txt()
        self.fetch_sitemap()

        # Queue management: (url, depth)
        queue: deque[Tuple[str, int]] = deque([(self.start_url, 0)])
        crawled_pages: List[CrawledPage] = []
        page_by_url: Dict[str, CrawledPage] = {}
        visited_urls: Set[str] = set()

        # Seed queue with discovered sitemap URLs
        for s_url in self.sitemap_urls:
            if s_url not in visited_urls and is_internal_url(s_url, self.base_domain):
                queue.append((s_url, 1))

        # External links to check for HTTP status
        external_urls_to_check: Set[str] = set()

        # Step 2: BFS Crawl Loop
        while queue and len(crawled_pages) < self.config.max_pages:
            current_url, depth = queue.popleft()
            if current_url in visited_urls:
                continue
            visited_urls.add(current_url)

            # Robots.txt Disallow Check
            path = urlparse(current_url).path or "/"
            if (
                self.config.respect_robots_txt
                and not self.robots_parser.is_allowed(path)
                and current_url != self.start_url
            ):
                self.disallowed_urls.add(current_url)
                # Still record crawled page stub
                c_page = CrawledPage(
                    url=current_url,
                    status_code=403,
                    error_message="Blocked by robots.txt",
                )
                crawled_pages.append(c_page)
                page_by_url[current_url] = c_page
                continue

            # Fetch page
            fetch_start = time.time()
            try:
                resp = self.session.get(
                    current_url,
                    timeout=self.config.timeout_seconds,
                    allow_redirects=True,
                )
                latency_ms = (time.time() - fetch_start) * 1000.0
                page_obj = self.parse_page(current_url, resp, latency_ms)
            except requests.RequestException as exc:
                latency_ms = (time.time() - fetch_start) * 1000.0
                page_obj = CrawledPage(
                    url=current_url,
                    status_code=0,
                    error_message=str(exc),
                    load_time_ms=round(latency_ms, 2),
                )

            crawled_pages.append(page_obj)
            page_by_url[current_url] = page_obj

            # Collect external links
            if self.config.check_external_links:
                for ext in page_obj.external_links[:10]:  # Cap to prevent external bloat
                    external_urls_to_check.add(ext)

            # Queue child internal links if within max_depth
            if depth < self.config.max_depth:
                for target_link in page_obj.internal_links:
                    if target_link not in visited_urls:
                        queue.append((target_link, depth + 1))

            if self.config.delay_seconds > 0:
                time.sleep(self.config.delay_seconds)

        # Step 3: Check external links shallow status
        external_statuses: Dict[str, int] = {}
        if self.config.check_external_links and external_urls_to_check:
            for ext_url in list(external_urls_to_check)[:30]:
                try:
                    head_resp = self.session.head(
                        ext_url, timeout=3.0, allow_redirects=True
                    )
                    external_statuses[ext_url] = head_resp.status_code
                except Exception:
                    external_statuses[ext_url] = 0

        # Step 4: Run All SEO Diagnostic Checks
        all_issues: List[SEOIssue] = []

        all_issues.extend(check_broken_links(crawled_pages, page_by_url, external_statuses))
        all_issues.extend(check_redirects(crawled_pages))
        all_issues.extend(check_metadata(crawled_pages))
        all_issues.extend(check_headings(crawled_pages))
        all_issues.extend(check_canonical_tags(crawled_pages, page_by_url))
        all_issues.extend(check_robots_directives(crawled_pages, self.disallowed_urls))
        all_issues.extend(check_images(crawled_pages, page_by_url))
        all_issues.extend(
            check_sitemap_urls(
                self.start_url, self.sitemap_found, self.sitemap_urls, page_by_url
            )
        )
        orphan_issues, orphan_candidates = check_orphan_pages(
            crawled_pages, self.sitemap_urls, self.start_url
        )
        all_issues.extend(orphan_issues)
        all_issues.extend(check_indexability(crawled_pages))

        # Deduplicate issues by issue.id
        unique_issues: List[SEOIssue] = []
        seen_issue_ids: Set[str] = set()
        for issue in all_issues:
            if issue.id not in seen_issue_ids:
                seen_issue_ids.add(issue.id)
                unique_issues.append(issue)

        # Sort issues by severity priority: CRITICAL > HIGH > MEDIUM > LOW
        severity_order = {
            Severity.CRITICAL: 0,
            Severity.HIGH: 1,
            Severity.MEDIUM: 2,
            Severity.LOW: 3,
        }
        unique_issues.sort(key=lambda x: severity_order.get(x.severity, 4))

        # Step 5: Calculate Summary Metrics and Health Score
        critical_c = sum(1 for i in unique_issues if i.severity == Severity.CRITICAL)
        high_c = sum(1 for i in unique_issues if i.severity == Severity.HIGH)
        med_c = sum(1 for i in unique_issues if i.severity == Severity.MEDIUM)
        low_c = sum(1 for i in unique_issues if i.severity == Severity.LOW)

        # Health score formula: 100 - (critical*15 + high*7 + med*2 + low*0.5)
        penalty = (critical_c * 15) + (high_c * 7) + (med_c * 2) + (low_c * 0.5)
        health_score = max(0, min(100, int(round(100.0 - penalty))))

        duration = round(time.time() - start_time, 2)
        summary = CrawlSummary(
            crawl_id=crawl_id,
            start_url=self.start_url,
            timestamp=datetime.utcnow().isoformat() + "Z",
            duration_seconds=duration,
            total_pages_crawled=len(crawled_pages),
            status_200_count=sum(1 for p in crawled_pages if p.status_code == 200),
            status_3xx_count=sum(1 for p in crawled_pages if 300 <= p.status_code < 400),
            status_4xx_count=sum(1 for p in crawled_pages if 400 <= p.status_code < 500),
            status_5xx_count=sum(1 for p in crawled_pages if p.status_code >= 500),
            total_issues_found=len(unique_issues),
            critical_issues=critical_c,
            high_issues=high_c,
            medium_issues=med_c,
            low_issues=low_c,
            health_score=health_score,
        )

        return CrawlReport(
            summary=summary,
            pages=crawled_pages,
            issues=unique_issues,
            orphan_candidates=orphan_candidates,
            sitemap_urls=self.sitemap_urls,
        )
