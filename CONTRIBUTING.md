# Contributing to SEO-Doctor

Thank you for contributing to **SEO-Doctor**! We welcome bug reports, feature enhancements, documentation improvements, and new technical SEO audit checks.

---

## 1. Development Environment Setup

1. Fork and clone the repository:
   ```bash
   git clone https://github.com/hamid-digitalmarketer/seo-doctor.git
   cd seo-doctor
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install editable dependencies and dev tools:
   ```bash
   pip install -e .
   pip install pytest ruff mypy
   ```

---

## 2. Quality Assurance Checks

Before submitting a pull request, verify all linting, type checks, and tests pass:

```bash
# 1. Run unit and integration tests
pytest

# 2. Check code style and formatting
ruff check .

# 3. Verify static type hints
mypy src
```

---

## 3. Adding New SEO Checks

All diagnostic checks reside in `src/seo_doctor/checks/`. When introducing a new check:
1. Create a descriptive module (e.g. `src/seo_doctor/checks/hreflang.py`).
2. Accept `pages: List[CrawledPage]` and return `List[SEOIssue]`.
3. Assign appropriate `Severity` (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`) and `IssueCategory`.
4. Include clear `evidence` and actionable `suggested_fix` guidance.
5. Add unit tests in `tests/test_checks.py` using mock HTML fixtures (never depend on live websites).
6. Register the check in `src/seo_doctor/checks/__init__.py` and `src/seo_doctor/crawler.py`.

---

## 4. Pull Request Guidelines

- Use conventional commits (`feat: ...`, `fix: ...`, `docs: ...`, `test: ...`).
- Target the `main` branch.
- Complete the Pull Request template checklist.
