"""arXiv paper fetcher module."""

import re
import time
from datetime import datetime, timedelta
from typing import Generator

import arxiv

from .config import Config, DomainConfig
from .models import RawPaper


class ArxivFetcher:
    """Fetches papers from arXiv based on configuration."""

    def __init__(self, config: Config):
        self.config = config
        self.client = arxiv.Client(
            page_size=20,
            delay_seconds=15.0,  # Increased from 10.0 to reduce rate limit hits
            num_retries=5
        )

    def _build_query(self, domain: DomainConfig) -> str:
        """Build arXiv search query from domain configuration."""
        # Build category part: (cat:cs.CL OR cat:cs.AI)
        if domain.categories:
            cat_parts = [f"cat:{cat}" for cat in domain.categories]
            cat_query = "(" + " OR ".join(cat_parts) + ")"
        else:
            cat_query = ""

        # Build keyword part: (ti:memory OR abs:memory OR ti:agent OR abs:agent)
        if domain.keywords:
            kw_parts = []
            for kw in domain.keywords:
                # Search in both title and abstract
                kw_parts.append(f'ti:"{kw}"')
                kw_parts.append(f'abs:"{kw}"')
            kw_query = "(" + " OR ".join(kw_parts) + ")"
        else:
            kw_query = ""

        # Combine with AND
        if cat_query and kw_query:
            return f"{cat_query} AND {kw_query}"
        return cat_query or kw_query or "cat:cs.AI"

    def _result_to_paper(self, result: arxiv.Result) -> RawPaper:
        """Convert arxiv.Result to RawPaper model."""
        # Extract arXiv ID from entry_id (e.g., "http://arxiv.org/abs/2401.12345v1")
        arxiv_id = result.entry_id.split("/")[-1]

        return RawPaper(
            arxiv_id=arxiv_id,
            title=result.title.replace("\n", " ").strip(),
            abstract=result.summary.replace("\n", " ").strip(),
            authors=[author.name for author in result.authors],
            categories=result.categories,
            primary_category=result.primary_category,
            published=result.published,
            updated=result.updated,
            pdf_url=result.pdf_url,
            abs_url=result.entry_id,
        )

    def _is_within_date_range(self, paper: RawPaper, days_back: int) -> bool:
        """Check if paper is within the date range."""
        cutoff = datetime.now(paper.published.tzinfo) - timedelta(days=days_back)
        return paper.published >= cutoff

    def fetch_domain(
        self,
        domain: DomainConfig,
        days_back: int | None = None,
        max_papers: int | None = None,
    ) -> Generator[RawPaper, None, None]:
        """Fetch papers for a single domain with strong retry logic for rate limits."""
        if days_back is None:
            days_back = self.config.fetch.days_back
        if max_papers is None:
            max_papers = self.config.fetch.max_papers_per_domain

        query = self._build_query(domain)
        print(f"  Query: {query}")

        search = arxiv.Search(
            query=query,
            max_results=min(max_papers, 40),
            sort_by=arxiv.SortCriterion.SubmittedDate,
            sort_order=arxiv.SortOrder.Descending,
        )

        # Exponential backoff retry logic for 429/503 errors
        max_retries = 3
        attempt = 0

        while attempt < max_retries:
            try:
                count = 0
                seen_ids = set()

                # Try to fetch results
                for result in self.client.results(search):
                    try:
                        paper = self._result_to_paper(result)

                        if not self._is_within_date_range(paper, days_back):
                            continue

                        if paper.short_id in seen_ids:
                            continue
                        seen_ids.add(paper.short_id)

                        yield paper
                        count += 1

                        if count >= max_papers:
                            break
                    except Exception as inner_e:
                        print(f"  ⚠️ Warning: Error processing a single paper: {inner_e}")
                        continue

                # Success - exit retry loop
                return

            except Exception as e:
                error_str = str(e)
                # Check if it's a rate limit error
                if "429" in error_str or "503" in error_str:
                    attempt += 1
                    if attempt < max_retries:
                        wait_time = 60 * attempt  # 60s, 120s, 180s for attempts 1, 2, 3
                        print(f"  ⚠️ Got rate limit (429/503). Waiting {wait_time} seconds before retry ({attempt}/{max_retries})...")
                        time.sleep(wait_time)
                    else:
                        print(f"  ❌ Failed to fetch domain '{domain.name}' after {max_retries} attempts due to rate limiting.")
                        return
                else:
                    # Not a rate limit error - don't retry
                    print(f"  ❌ Error fetching from arXiv for domain '{domain.name}': {e}")
                    print("  ⚠️ Stopping fetch for this domain and continuing...")
                    return
            
    def fetch_all(
        self,
        days_back: int | None = None,
    ) -> dict[str, list[RawPaper]]:
        """Fetch papers for all configured domains."""
        if days_back is None:
            days_back = self.config.fetch.days_back

        results: dict[str, list[RawPaper]] = {}
        all_seen_ids: set[str] = set()

        for domain in self.config.domains:
            print(f"\nFetching domain: {domain.name}")
            domain_papers = []

            for paper in self.fetch_domain(domain, days_back):
                # Global deduplication across domains
                if paper.short_id not in all_seen_ids:
                    all_seen_ids.add(paper.short_id)
                    domain_papers.append(paper)

            results[domain.output_category] = domain_papers
            print(f"  Found {len(domain_papers)} papers")
            time.sleep(20)  # Increased from 5 to 20 seconds between domain fetches

        return results

    def fetch_recent(self, days_back: int = 1) -> list[RawPaper]:
        """Fetch all recent papers as a flat list (deduplicated)."""
        all_papers = self.fetch_all(days_back)

        # Flatten and deduplicate
        seen_ids = set()
        papers = []
        for domain_papers in all_papers.values():
            for paper in domain_papers:
                if paper.short_id not in seen_ids:
                    seen_ids.add(paper.short_id)
                    papers.append(paper)

        # Sort by published date, newest first
        papers.sort(key=lambda p: p.published, reverse=True)
        return papers
