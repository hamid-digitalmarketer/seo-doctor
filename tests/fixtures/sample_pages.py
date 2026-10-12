"""Mock HTML fixtures for testing SEO-Doctor checks without live network dependencies."""

HTML_PERFECT_PAGE = """<!DOCTYPE html>
<html>
<head>
  <title>High Quality Organic Coffee Beans Online</title>
  <meta name="description" content="Shop premium single origin organic coffee beans ethically sourced and freshly roasted in small batches.">
  <link rel="canonical" href="https://example.com/perfect-page">
</head>
<body>
  <h1>Artisanal Coffee Roasting</h1>
  <h2>Small Batch Profiles</h2>
  <p>Detailed guide on roasting profiles with comprehensive extraction notes for baristas and coffee enthusiasts worldwide.</p>
  <img src="/images/coffee.jpg" alt="Artisan coffee beans roasting in cast iron drum">
  <a href="/about">About Us</a>
  <a href="https://partner-origin.org">Farms</a>
</body>
</html>
"""

HTML_MISSING_TITLE_PAGE = """<!DOCTYPE html>
<html>
<head>
  <meta name="description" content="Valid meta description for coffee beans.">
</head>
<body>
  <h1>Artisan Coffee Roasting</h1>
</body>
</html>
"""

HTML_MULTIPLE_H1_PAGE = """<!DOCTYPE html>
<html>
<head>
  <title>Roaster Profiles and Heritage Story</title>
  <meta name="description" content="Discover our multi-decade coffee roasting heritage.">
</head>
<body>
  <h1>First Primary Heading</h1>
  <h1>Second Conflicting Heading</h1>
  <h3>Skipped Heading Level</h3>
</body>
</html>
"""

HTML_CONFLICTING_CANONICAL_PAGE = """<!DOCTYPE html>
<html>
<head>
  <title>Syndicated Coffee Brewing Ratios</title>
  <meta name="description" content="How to brew the best pour over coffee with exact water to grind ratios.">
  <link rel="canonical" href="https://example.com/target-a">
  <link rel="canonical" href="https://example.com/target-b">
</head>
<body>
  <h1>Syndicated Brewing Guide</h1>
</body>
</html>
"""

HTML_NOINDEX_PAGE = """<!DOCTYPE html>
<html>
<head>
  <title>Private VIP Staging Discount Page</title>
  <meta name="robots" content="noindex, nofollow">
</head>
<body>
  <h1>Secret Discount Campaign</h1>
</body>
</html>
"""

HTML_MISSING_IMG_ALT_PAGE = """<!DOCTYPE html>
<html>
<head>
  <title>Visual Gallery of Coffee Farms</title>
  <meta name="description" content="Photographs from coffee washing stations in Yirgacheffe.">
</head>
<body>
  <h1>Farm Gallery</h1>
  <img src="/images/farm-hero.jpg">
  <img src="/images/product-beans.png" alt="">
</body>
</html>
"""

ROBOTS_TXT_FIXTURE = """User-agent: *
Disallow: /admin/
Disallow: /checkout/
Sitemap: https://example.com/sitemap.xml
"""

SITEMAP_XML_FIXTURE = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://example.com/page-1</loc>
  </url>
  <url>
    <loc>https://example.com/page-2</loc>
  </url>
  <url>
    <loc>https://example.com/orphan-page</loc>
  </url>
</urlset>
"""
