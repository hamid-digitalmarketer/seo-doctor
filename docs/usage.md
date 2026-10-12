# SEO-Doctor Usage Guide & Workflow Recipes

This guide covers complete workflows, CLI commands, and integration patterns for **SEO-Doctor**.

---

## 1. Quick Installation

### Standard Installation
```bash
git clone https://github.com/hamid-digitalmarketer/seo-doctor.git
cd seo-doctor
pip install -e .
```

### Verify Installation
```bash
seo-doctor version
```

---

## 2. CLI Command Reference

### A. The `crawl` Command
Crawls internal URLs, discovers sitemaps, analyzes robots directives, and generates HTML/CSV/JSON reports.

```bash
seo-doctor crawl <URL> [OPTIONS]
```

**Common Examples:**
```bash
# Basic audit up to 50 pages
seo-doctor crawl https://example.com --max-pages 50

# Fast audit targeting an XML sitemap
seo-doctor crawl https://example.com --sitemap https://example.com/sitemap.xml --max-pages 200

# Polite crawl for sensitive staging servers
seo-doctor crawl https://example.com --delay 0.5 --timeout 15.0 --output-dir ./reports

# Deep crawl traversing up to 10 link hops
seo-doctor crawl https://example.com --max-depth 10 --max-pages 1000
```

**Options & Flags:**
- `URL` *(required)*: Starting URL (e.g. `https://example.com`).
- `--max-pages`, `-m` *(default: 100)*: Cap total pages crawled.
- `--max-depth`, `-d` *(default: 5)*: Maximum link depth traversal.
- `--sitemap`, `-s` *(default: None)*: Explicit XML sitemap URL.
- `--delay` *(default: 0.05)*: Rate-limiting sleep delay between requests in seconds.
- `--timeout`, `-t` *(default: 10.0)*: Request timeout in seconds.
- `--output-dir`, `-o` *(default: ./reports)*: Target directory for generated reports.
- `--user-agent` *(default: SEO-Doctor-Bot/0.1.0)*: Custom User-Agent header string.
- `--check-external / --no-check-external` *(default: True)*: Perform shallow HTTP HEAD/GET status verification on external links.
- `--save-db / --no-save-db` *(default: True)*: Persist crawl results into local SQLite database.

---

### B. The `compare` Command
Compares two JSON audit reports to determine issues fixed, issues introduced, and health score deltas.

```bash
seo-doctor compare reports/crawl-20260101.json reports/crawl-20260201.json
```

**Output Breakdown:**
- **Score Delta**: Change in overall technical health score (+15, -5).
- **Issues Fixed (Green)**: Critical/High errors resolved since previous run.
- **Issues Introduced (Red)**: New broken links or canonical mismatches introduced.
- **Issues Still Open (Yellow)**: Persistent problems requiring ongoing attention.

---

### C. The `serve` Command
Launches a local web viewer powered by FastAPI to browse and review generated HTML reports in your web browser.

```bash
seo-doctor serve --port 8000
```
Open [http://127.0.0.1:8000](http://127.0.0.1:8000) in your browser to inspect reports.

---

## 3. Auditing Local Staging Sites

You can audit local static websites or pre-production previews directly:

```bash
# Terminal 1: Serve local site folder
cd examples/sample-site
python -m http.server 8000

# Terminal 2: Crawl local server
seo-doctor crawl http://127.0.0.1:8000/index.html --sitemap http://127.0.0.1:8000/sitemap.xml
```

---

## 4. Continuous Integration (CI/CD) Workflow

To catch broken links and SEO regressions before merging pull requests, add this step to `.github/workflows/seo-audit.yml`:

```yaml
name: Technical SEO Audit
on: [pull_request]

jobs:
  seo-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install -e .
      - name: Build and Serve Staging Site
        run: |
          python -m http.server 8000 --directory examples/sample-site &
          sleep 3
      - name: Run SEO-Doctor Audit
        run: |
          seo-doctor crawl http://127.0.0.1:8000/index.html --output-dir ./reports
```
