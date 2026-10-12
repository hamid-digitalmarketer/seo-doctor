# SEO-Doctor Limitations & Technical Boundaries

While **SEO-Doctor** is designed to provide comprehensive, production-grade technical audits for commercial and indie websites, users should understand its boundaries, technical scope, and operational guidelines.

---

## 1. Technical Scope & Architecture Boundaries

### A. Server-Side HTML vs. Client-Side JavaScript (SPAs)
- **Default Engine**: By default, SEO-Doctor operates as a high-performance HTTP crawler utilizing `requests` and `BeautifulSoup` to parse server-rendered HTML. This delivers fast, lightweight crawling with zero external browser overhead.
- **Client-Side SPAs**: Single Page Applications built with React, Vue, or Angular that rely 100% on client-side JavaScript execution to render content into an empty `<div id="root">` will appear as thin or blank pages to standard HTTP crawlers. Search engines (like Googlebot) also strongly prefer Server-Side Rendering (SSR) via Next.js, Nuxt, or Remix. If your site relies entirely on client-side hydration, ensure SSR or dynamic rendering is configured.

### B. Anti-Bot Firewalls & Cloud WAFs
- Enterprise websites protected by Cloudflare Bot Management, Akamai, AWS WAF, or Incapsula may challenge or block automated HTTP requests with HTTP 403 Forbidden or JavaScript challenge pages.
- **Mitigation**: When auditing internal or staging environments, whitelist the `SEO-Doctor-Bot` User-Agent string or run the crawl on a local preview server (`127.0.0.1`).

### C. Rate Limits & Politeness
- By default, SEO-Doctor enforces a polite rate limit delay (`--delay 0.05` seconds).
- Setting `--delay 0` against production servers can trigger HTTP 429 (Too Many Requests) or temporarily overload small web hosting environments. Always respect target server capacity.

---

## 2. Non-Goals & Ethical Guardrails

- **No Guaranteed Rankings**: SEO-Doctor diagnoses technical indexability, metadata hygiene, internal linking, and crawl barriers. Resolving technical errors creates the necessary foundation for indexation, but does not guarantee top rankings without high-quality content, domain authority, and search intent satisfaction.
- **No Private Data Harvesting**: The tool does not store credentials, personal customer information, or private ad-account data.
- **No Paywall / Authentication Bypassing**: Pages protected behind HTTP Basic Auth, login portals, or private paywalls are strictly excluded unless explicitly routed through authorized local staging proxies.
- **Respect for `robots.txt`**: SEO-Doctor respects `robots.txt` disallow rules by default (`--respect-robots-txt`), flagging internally linked disallowed pages as indexing risks rather than blindly scraping forbidden paths.

---

## 3. Scale Considerations

- **Recommended Site Size**: 1 to 10,000 URLs per run.
- For enterprise sites exceeding 100,000 URLs, consider running section-based audits using `--sitemap` or scoping subdirectories with `--max-pages` and `--max-depth`.
