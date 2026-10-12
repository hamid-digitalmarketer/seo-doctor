"""Configuration parameters for SEO-Doctor crawler and audit runs."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class CrawlConfig(BaseModel):
    """Runtime configuration for crawling and analysis."""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    start_url: str
    sitemap_url: Optional[str] = None
    max_pages: int = Field(default=100, ge=1, le=5000)
    max_depth: int = Field(default=5, ge=1, le=20)
    delay_seconds: float = Field(default=0.05, ge=0.0, le=10.0)
    timeout_seconds: float = Field(default=10.0, ge=1.0, le=60.0)
    user_agent: str = "SEO-Doctor-Bot/0.1.0 (+https://github.com/hamid-digitalmarketer/seo-doctor)"
    respect_robots_txt: bool = True
    check_external_links: bool = True
    output_dir: Path = Field(default_factory=lambda: Path("./reports"))
    db_path: Optional[Path] = None
    render_javascript: bool = False
