"""Command-Line Interface (CLI) for SEO-Doctor."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from seo_doctor import __version__
from seo_doctor.compare import compare_crawls, load_report_from_file
from seo_doctor.config import CrawlConfig
from seo_doctor.crawler import SEOCrawler
from seo_doctor.report import generate_all_reports
from seo_doctor.storage import get_default_db_path, list_crawls, save_crawl

app = typer.Typer(
    name="seo-doctor",
    help="Free open-source technical SEO auditor and crawler for automated site diagnostics.",
    add_completion=False,
)
console = Console()


@app.command()
def crawl(
    url: str = typer.Argument(..., help="Target website starting URL (e.g. https://example.com)"),
    max_pages: int = typer.Option(100, "--max-pages", "-m", help="Maximum number of pages to crawl"),
    max_depth: int = typer.Option(5, "--max-depth", "-d", help="Maximum link traversal depth"),
    sitemap: Optional[str] = typer.Option(None, "--sitemap", "-s", help="Custom XML sitemap URL"),
    delay: float = typer.Option(0.05, "--delay", help="Politeness rate limit delay in seconds"),
    timeout: float = typer.Option(10.0, "--timeout", "-t", help="HTTP request timeout in seconds"),
    output_dir: Path = typer.Option(Path("./reports"), "--output-dir", "-o", help="Report output directory"),
    user_agent: str = typer.Option(
        "SEO-Doctor-Bot/0.1.0 (+https://github.com/hamid-digitalmarketer/seo-doctor)",
        "--user-agent",
        help="Custom User-Agent header",
    ),
    check_external: bool = typer.Option(True, "--check-external/--no-check-external", help="Check status of external links"),
    save_to_db: bool = typer.Option(True, "--save-db/--no-save-db", help="Persist report to SQLite database"),
) -> None:
    """Crawl a website, detect technical SEO issues, and generate HTML/CSV/JSON reports."""
    console.print(
        Panel.fit(
            f"[bold green][+] SEO-Doctor Crawler[/bold green] v{__version__}\n"
            f"[dim]Auditing target:[/dim] [cyan]{url}[/cyan]\n"
            f"[dim]Max pages:[/dim] {max_pages} | [dim]Max depth:[/dim] {max_depth} | [dim]Rate limit delay:[/dim] {delay}s",
            border_style="green",
        )
    )

    config = CrawlConfig(
        start_url=url,
        sitemap_url=sitemap,
        max_pages=max_pages,
        max_depth=max_depth,
        delay_seconds=delay,
        timeout_seconds=timeout,
        output_dir=output_dir,
        user_agent=user_agent,
        check_external_links=check_external,
    )

    with console.status("[bold green]Crawling website and executing SEO diagnostic checks...[/bold green]"):
        crawler = SEOCrawler(config)
        report = crawler.crawl()

    # Persist reports
    paths = generate_all_reports(report, output_dir)
    if save_to_db:
        save_crawl(report)

    # Display Results in Terminal
    summary = report.summary
    score_color = "green" if summary.health_score >= 85 else ("yellow" if summary.health_score >= 65 else "red")

    table = Table(title=f"SEO Audit Summary — {url}", border_style="dim")
    table.add_column("Metric", style="bold")
    table.add_column("Value", style="cyan")

    table.add_row("Health Score", f"[{score_color}]{summary.health_score} / 100[/{score_color}]")
    table.add_row("Pages Crawled", str(summary.total_pages_crawled))
    table.add_row("HTTP 200 OK", f"[green]{summary.status_200_count}[/green]")
    table.add_row("HTTP 3xx Redirects", f"[cyan]{summary.status_3xx_count}[/cyan]")
    table.add_row("HTTP 4xx/5xx Errors", f"[red]{summary.status_4xx_count + summary.status_5xx_count}[/red]")
    table.add_row("Total Issues Found", f"[yellow]{summary.total_issues_found}[/yellow]")
    table.add_row("Critical Issues", f"[red]{summary.critical_issues}[/red]")
    table.add_row("High Priority Issues", f"[orange3]{summary.high_issues}[/orange3]")
    table.add_row("Medium Priority Issues", f"[yellow]{summary.medium_issues}[/yellow]")
    table.add_row("Low Priority Issues", f"[dim]{summary.low_issues}[/dim]")
    table.add_row("Crawl Duration", f"{summary.duration_seconds} seconds")

    console.print(table)

    # Show top 5 priority issues in terminal
    if report.issues:
        console.print("\n[bold][!] Top Priority Fixes Needed:[/bold]")
        issue_table = Table(border_style="dim")
        issue_table.add_column("Severity", style="bold")
        issue_table.add_column("Issue Type")
        issue_table.add_column("URL", max_width=40, overflow="fold")
        issue_table.add_column("Suggested Fix", max_width=50, overflow="fold")

        for iss in report.issues[:5]:
            sev_color = "red" if iss.severity == "critical" else ("yellow" if iss.severity == "high" else "cyan")
            issue_table.add_row(
                f"[{sev_color}]{iss.severity.upper()}[/{sev_color}]",
                iss.issue_type.replace("_", " ").title(),
                iss.url,
                iss.suggested_fix,
            )
        console.print(issue_table)

    console.print("\n[bold green][OK] Reports generated successfully:[/bold green]")
    console.print(f"  * HTML Dashboard: [cyan]{paths['html']}[/cyan]")
    console.print(f"  * CSV Export:     [cyan]{paths['csv']}[/cyan]")
    console.print(f"  * JSON Report:    [cyan]{paths['json']}[/cyan]\n")


@app.command()
def compare(
    baseline: Path = typer.Argument(..., help="Path to baseline crawl JSON report (e.g. reports/run1.json)"),
    comparison: Path = typer.Argument(..., help="Path to newer comparison crawl JSON report (e.g. reports/run2.json)"),
) -> None:
    """Compare two crawl runs to verify which SEO issues were fixed or introduced."""
    try:
        base_rep = load_report_from_file(baseline)
        comp_rep = load_report_from_file(comparison)
    except Exception as e:
        console.print(f"[bold red]Error loading report files:[/bold red] {e}")
        raise typer.Exit(code=1)

    result = compare_crawls(base_rep, comp_rep)

    console.print(
        Panel.fit(
            f"[bold cyan][?] Crawl Comparison Audit[/bold cyan]\n"
            f"[dim]Baseline:[/dim]   {base_rep.summary.start_url} ({base_rep.summary.timestamp[:19]})\n"
            f"[dim]Comparison:[/dim] {comp_rep.summary.start_url} ({comp_rep.summary.timestamp[:19]})",
            border_style="cyan",
        )
    )

    diff_table = Table(title="Score & Issue Delta", border_style="dim")
    diff_table.add_column("Metric")
    diff_table.add_column("Baseline")
    diff_table.add_column("Comparison")
    diff_table.add_column("Delta")

    score_delta_str = (
        f"[green]+{result.health_score_delta}[/green]"
        if result.health_score_delta > 0
        else (f"[red]{result.health_score_delta}[/red]" if result.health_score_delta < 0 else "0")
    )
    diff_table.add_row(
        "Health Score",
        str(base_rep.summary.health_score),
        str(comp_rep.summary.health_score),
        score_delta_str,
    )

    issues_delta_str = (
        f"[green]{result.total_issues_delta}[/green]"
        if result.total_issues_delta < 0
        else (f"[red]+{result.total_issues_delta}[/red]" if result.total_issues_delta > 0 else "0")
    )
    diff_table.add_row(
        "Total Issues",
        str(base_rep.summary.total_issues_found),
        str(comp_rep.summary.total_issues_found),
        issues_delta_str,
    )

    diff_table.add_row(
        "Pages Crawled",
        str(base_rep.summary.total_pages_crawled),
        str(comp_rep.summary.total_pages_crawled),
        f"{result.pages_crawled_delta:+d}",
    )

    console.print(diff_table)

    # Issues Fixed (Green)
    if result.issues_fixed:
        console.print(f"\n[bold green][+] Issues Fixed ({len(result.issues_fixed)}):[/bold green]")
        for iss in result.issues_fixed[:5]:
            console.print(f"  [green]+[/green] [dim]{iss.url}[/dim] - [bold]{iss.issue_type}[/bold]")
        if len(result.issues_fixed) > 5:
            console.print(f"  [dim]... and {len(result.issues_fixed) - 5} more fixed issues.[/dim]")

    # Issues Introduced (Red)
    if result.issues_introduced:
        console.print(f"\n[bold red][!] Issues Introduced ({len(result.issues_introduced)}):[/bold red]")
        for iss in result.issues_introduced[:5]:
            console.print(f"  [red]-[/red] [dim]{iss.url}[/dim] - [bold]{iss.issue_type}[/bold]: {iss.evidence}")
        if len(result.issues_introduced) > 5:
            console.print(f"  [dim]... and {len(result.issues_introduced) - 5} more introduced issues.[/dim]")

    # Issues Still Open (Yellow)
    if result.issues_still_open:
        console.print(f"\n[bold yellow][*] Issues Still Open ({len(result.issues_still_open)}):[/bold yellow]")
        for iss in result.issues_still_open[:3]:
            console.print(f"  [yellow]*[/yellow] [dim]{iss.url}[/dim] - {iss.issue_type}")


@app.command()
def serve(
    host: str = typer.Option("127.0.0.1", "--host", "-h", help="Host address to bind to"),
    port: int = typer.Option(8000, "--port", "-p", help="Port to listen on"),
    reports_dir: Path = typer.Option(Path("./reports"), "--reports-dir", help="Directory where reports are stored"),
) -> None:
    """Launch local FastAPI web server to browse and inspect generated SEO audit reports."""
    server_app = FastAPI(
        title="SEO-Doctor Web Viewer",
        description="Local web dashboard to view and inspect technical SEO audit reports.",
        version=__version__,
    )

    @server_app.get("/", response_class=HTMLResponse)
    def index() -> str:
        crawls = list_crawls(get_default_db_path())
        html_files = sorted(reports_dir.glob("*.html"), key=lambda p: p.stat().st_mtime, reverse=True)

        links_html = "".join(
            f'<li class="p-4 bg-slate-800 rounded-lg hover:bg-slate-700 transition flex justify-between items-center"><a class="text-emerald-400 font-mono text-sm hover:underline" href="/report/{h.stem}">{h.name}</a><span class="text-xs text-slate-400 font-mono">{round(h.stat().st_size / 1024, 1)} KB</span></li>'
            for h in html_files
        )

        crawls_info = f'<p class="text-xs text-slate-400 mt-2">Stored Crawls in DB: {len(crawls)}</p>'

        return f"""
        <!DOCTYPE html>
        <html>
        <head>
          <title>SEO-Doctor Local Reports</title>
          <script src="https://cdn.tailwindcss.com"></script>
        </head>
        <body class="bg-slate-950 text-slate-100 min-h-screen p-8">
          <div class="max-w-4xl mx-auto space-y-6">
            <div class="flex items-center gap-3">
              <span class="text-3xl">🩺</span>
              <div>
                <h1 class="text-2xl font-bold">SEO-Doctor Local Dashboard</h1>
                <p class="text-xs text-slate-400">Available technical audit reports in {reports_dir.resolve()}</p>
              </div>
            </div>
            <div class="bg-slate-900 border border-slate-800 rounded-xl p-6">
              <h2 class="text-sm font-semibold uppercase tracking-wider text-slate-400 mb-4">Saved HTML Reports ({len(html_files)})</h2>
              {crawls_info}
              <ul class="space-y-2 mt-4">
                {links_html or '<li class="text-sm text-slate-500">No HTML reports generated yet. Run: seo-doctor crawl &lt;url&gt;</li>'}
              </ul>
            </div>
          </div>
        </body>
        </html>
        """

    @server_app.get("/report/{report_id}", response_class=HTMLResponse)
    def view_report(report_id: str) -> str:
        target_html = reports_dir / f"{report_id}.html"
        if not target_html.exists():
            raise HTTPException(status_code=404, detail="Report not found")
        return target_html.read_text(encoding="utf-8")

    console.print(f"[bold green]🚀 SEO-Doctor Web Viewer launching at http://{host}:{port}[/bold green]")
    uvicorn.run(server_app, host=host, port=port)


@app.command()
def version() -> None:
    """Show SEO-Doctor version information."""
    console.print(f"SEO-Doctor [bold green]v{__version__}[/bold green]")


if __name__ == "__main__":
    app()
