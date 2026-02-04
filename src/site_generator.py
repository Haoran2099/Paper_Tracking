"""Static site generator for paper tracking."""

import json
import shutil
from datetime import datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from .config import Config
from .models import AnalyzedPaper, DailyPapers


class SiteGenerator:
    """Generates static website from analyzed papers."""

    def __init__(self, config: Config, output_dir: str | Path = "docs"):
        self.config = config
        self.project_root = Path(__file__).parent.parent
        self.output_dir = Path(output_dir)
        self.data_dir = self.project_root / "data" / "papers"
        self.templates_dir = self.project_root / "templates"
        self.static_dir = self.project_root / "static"

        # Setup Jinja2
        self.env = Environment(
            loader=FileSystemLoader(self.templates_dir),
            autoescape=True,
        )

        # Add custom filters
        self.env.filters["format_date"] = self._format_date
        self.env.filters["truncate_text"] = self._truncate_text

    def _format_date(self, dt: datetime | str, fmt: str = "%Y-%m-%d") -> str:
        """Format datetime for templates."""
        if isinstance(dt, str):
            dt = datetime.fromisoformat(dt.replace("Z", "+00:00"))
        return dt.strftime(fmt)

    def _truncate_text(self, text: str, length: int = 200) -> str:
        """Truncate text with ellipsis."""
        if len(text) <= length:
            return text
        return text[:length].rsplit(" ", 1)[0] + "..."

    def _load_all_papers(self) -> list[DailyPapers]:
        """Load all paper data from JSON files."""
        papers_list = []

        if not self.data_dir.exists():
            return papers_list

        for json_file in sorted(self.data_dir.glob("*.json"), reverse=True):
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    daily = DailyPapers.model_validate(data)
                    papers_list.append(daily)
            except Exception as e:
                print(f"Warning: Failed to load {json_file}: {e}")

        return papers_list

    def _get_all_papers_flat(self, daily_list: list[DailyPapers]) -> list[AnalyzedPaper]:
        """Get all papers as a flat list, sorted by date."""
        all_papers = []
        for daily in daily_list:
            all_papers.extend(daily.papers)

        # Sort by published date, newest first
        all_papers.sort(key=lambda p: p.published, reverse=True)
        return all_papers

    def _group_by_category(
        self, papers: list[AnalyzedPaper]
    ) -> dict[str, list[AnalyzedPaper]]:
        """Group papers by assigned category."""
        grouped: dict[str, list[AnalyzedPaper]] = {}
        for paper in papers:
            cat = paper.assigned_category
            if cat not in grouped:
                grouped[cat] = []
            grouped[cat].append(paper)
        return grouped

    def _generate_search_index(self, papers: list[AnalyzedPaper]) -> list[dict]:
        """Generate search index for client-side search."""
        index = []
        for paper in papers:
            index.append({
                "id": paper.arxiv_id,
                "title": paper.title,
                "summary": paper.summary,
                "authors": ", ".join(paper.authors[:3]),
                "tags": paper.tags,
                "category": paper.assigned_category,
                "score": paper.relevance_score,
                "date": paper.published.strftime("%Y-%m-%d"),
            })
        return index

    def _copy_static_files(self):
        """Copy static files to output directory."""
        output_static = self.output_dir / "static"

        if output_static.exists():
            shutil.rmtree(output_static)

        if self.static_dir.exists():
            shutil.copytree(self.static_dir, output_static)

    def generate(self):
        """Generate the complete static site."""
        print("Generating static site...")

        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Load all papers
        daily_list = self._load_all_papers()
        all_papers = self._get_all_papers_flat(daily_list)
        papers_by_category = self._group_by_category(all_papers)

        # Get available dates
        available_dates = [d.date for d in daily_list]

        # Context for all templates
        base_context = {
            "site": self.config.site,
            "categories": self.config.get_output_categories(),
            "category_names": {
                d.output_category: d.name for d in self.config.domains
            },
            "available_dates": available_dates,
            "generated_at": datetime.now(),
        }

        # Generate index page
        self._generate_index(all_papers, papers_by_category, base_context)

        # Generate category pages
        for category in self.config.get_output_categories():
            self._generate_category_page(
                category, papers_by_category.get(category, []), base_context
            )

        # Generate paper detail pages
        for paper in all_papers:
            self._generate_paper_page(paper, base_context)

        # Generate search index
        search_index = self._generate_search_index(all_papers)
        with open(self.output_dir / "search_index.json", "w", encoding="utf-8") as f:
            json.dump(search_index, f, ensure_ascii=False)

        # Copy static files
        self._copy_static_files()

        print(f"Site generated at {self.output_dir}")
        print(f"  - {len(all_papers)} papers total")
        print(f"  - {len(papers_by_category)} categories")

    def _generate_index(
        self,
        all_papers: list[AnalyzedPaper],
        papers_by_category: dict[str, list[AnalyzedPaper]],
        base_context: dict,
    ):
        """Generate the index page."""
        template = self.env.get_template("index.html")

        # Get recent and high-relevance papers
        recent_papers = all_papers[:20]
        high_relevance = [p for p in all_papers if p.relevance_score >= 8][:10]

        context = {
            **base_context,
            "recent_papers": recent_papers,
            "high_relevance_papers": high_relevance,
            "papers_by_category": papers_by_category,
            "total_papers": len(all_papers),
        }

        html = template.render(**context)
        with open(self.output_dir / "index.html", "w", encoding="utf-8") as f:
            f.write(html)

    def _generate_category_page(
        self,
        category: str,
        papers: list[AnalyzedPaper],
        base_context: dict,
    ):
        """Generate a category page."""
        template = self.env.get_template("paper_list.html")

        domain = self.config.get_domain_by_output_category(category)
        category_name = domain.name if domain else category

        context = {
            **base_context,
            "current_category": category,
            "category_name": category_name,
            "papers": papers,
        }

        html = template.render(**context)

        # Create category directory
        cat_dir = self.output_dir / "category" / category
        cat_dir.mkdir(parents=True, exist_ok=True)

        with open(cat_dir / "index.html", "w", encoding="utf-8") as f:
            f.write(html)

    def _generate_paper_page(
        self,
        paper: AnalyzedPaper,
        base_context: dict,
    ):
        """Generate a paper detail page."""
        template = self.env.get_template("paper_detail.html")

        context = {
            **base_context,
            "paper": paper,
        }

        html = template.render(**context)

        # Create paper directory using short ID
        paper_dir = self.output_dir / "paper" / paper.short_id
        paper_dir.mkdir(parents=True, exist_ok=True)

        with open(paper_dir / "index.html", "w", encoding="utf-8") as f:
            f.write(html)


def save_daily_papers(papers: list[AnalyzedPaper], date: str | None = None):
    """Save analyzed papers to a daily JSON file."""
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")

    project_root = Path(__file__).parent.parent
    data_dir = project_root / "data" / "papers"
    data_dir.mkdir(parents=True, exist_ok=True)

    file_path = data_dir / f"{date}.json"

    # Load existing if present
    if file_path.exists():
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            daily = DailyPapers.model_validate(data)
    else:
        daily = DailyPapers(date=date)

    # Add new papers (deduplicating)
    added = 0
    for paper in papers:
        if daily.add_paper(paper):
            added += 1

    # Save
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(daily.model_dump(mode="json"), f, ensure_ascii=False, indent=2, default=str)

    print(f"Saved {added} new papers to {file_path}")
    return file_path
