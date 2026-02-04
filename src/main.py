"""CLI entry point for paper tracking system."""

import sys
from datetime import datetime
from pathlib import Path

import click
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from .config import load_config
from .arxiv_fetcher import ArxivFetcher
from .llm import get_analyzer
from .site_generator import SiteGenerator, save_daily_papers


@click.group()
@click.option("--config", "-c", default=None, help="Path to config.json")
@click.pass_context
def cli(ctx, config):
    """arXiv Paper Tracking System - Fetch, analyze, and display research papers."""
    ctx.ensure_object(dict)
    ctx.obj["config_path"] = config


@cli.command()
@click.option("--days", "-d", default=None, type=int, help="Number of days to look back")
@click.option("--dry-run", is_flag=True, help="Fetch papers without analyzing")
@click.pass_context
def fetch_and_analyze(ctx, days, dry_run):
    """Fetch papers from arXiv and analyze with LLM."""
    config = load_config(ctx.obj.get("config_path"))

    if days is not None:
        config.fetch.days_back = days

    print(f"Configuration loaded: {len(config.domains)} domains")
    print(f"LLM Provider: {config.llm.provider} / {config.llm.model}")
    print(f"Looking back {config.fetch.days_back} day(s)")
    print("=" * 60)

    # Fetch papers
    fetcher = ArxivFetcher(config)
    raw_papers = fetcher.fetch_recent(config.fetch.days_back)

    print(f"\nFetched {len(raw_papers)} papers total")

    if not raw_papers:
        print("No papers found. Exiting.")
        return

    if dry_run:
        print("\n[Dry run] Skipping analysis. Papers fetched:")
        for paper in raw_papers[:10]:
            print(f"  - {paper.title[:70]}...")
        if len(raw_papers) > 10:
            print(f"  ... and {len(raw_papers) - 10} more")
        return

    # Analyze papers
    print("\nAnalyzing papers with LLM...")
    print("-" * 60)

    try:
        analyzer = get_analyzer(config)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)

    analyzed_papers = analyzer.analyze_batch(
        raw_papers,
        min_score=config.fetch.min_relevance_score,
    )

    print("-" * 60)
    print(f"\n{len(analyzed_papers)} papers passed relevance filter (>= {config.fetch.min_relevance_score})")

    # Save results
    today = datetime.now().strftime("%Y-%m-%d")
    save_daily_papers(analyzed_papers, today)


@cli.command()
@click.option("--output", "-o", default="docs", help="Output directory for generated site")
@click.pass_context
def generate_site(ctx, output):
    """Generate static website from analyzed papers."""
    config = load_config(ctx.obj.get("config_path"))

    generator = SiteGenerator(config, output_dir=output)
    generator.generate()


@cli.command()
@click.pass_context
def run(ctx):
    """Run complete pipeline: fetch, analyze, and generate site."""
    ctx.invoke(fetch_and_analyze)
    ctx.invoke(generate_site)


@cli.command()
@click.pass_context
def show_config(ctx):
    """Display current configuration."""
    config = load_config(ctx.obj.get("config_path"))

    print("Current Configuration")
    print("=" * 60)
    print(f"\nSite:")
    print(f"  Title: {config.site.title}")
    print(f"  Description: {config.site.description}")
    print(f"  Base URL: {config.site.base_url or '(none)'}")

    print(f"\nLLM:")
    print(f"  Provider: {config.llm.provider}")
    print(f"  Model: {config.llm.model}")
    print(f"  API Key Env: {config.llm.api_key_env}")
    print(f"  API Key Set: {'Yes' if config.llm.api_key else 'No'}")

    print(f"\nFetch:")
    print(f"  Days back: {config.fetch.days_back}")
    print(f"  Max papers per domain: {config.fetch.max_papers_per_domain}")
    print(f"  Min relevance score: {config.fetch.min_relevance_score}")

    print(f"\nDomains ({len(config.domains)}):")
    for domain in config.domains:
        print(f"\n  {domain.name} ({domain.output_category}):")
        print(f"    Categories: {', '.join(domain.categories)}")
        print(f"    Keywords: {', '.join(domain.keywords)}")


@cli.command()
@click.option("--port", "-p", default=8000, type=int, help="Port to serve on")
@click.option("--output", "-o", default="docs", help="Directory to serve")
def serve(port, output):
    """Start local development server."""
    import http.server
    import socketserver
    import os

    output_path = Path(output)
    if not output_path.exists():
        print(f"Error: Output directory '{output}' does not exist.")
        print("Run 'generate-site' first to create the site.")
        sys.exit(1)

    os.chdir(output_path)

    Handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", port), Handler) as httpd:
        print(f"Serving site at http://localhost:{port}")
        print("Press Ctrl+C to stop")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped")


def main():
    """Main entry point."""
    cli(obj={})


if __name__ == "__main__":
    main()
