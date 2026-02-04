"""Data models for paper tracking system."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class RawPaper(BaseModel):
    """Raw paper data from arXiv API."""

    arxiv_id: str = Field(description="arXiv paper ID (e.g., '2401.12345')")
    title: str = Field(description="Paper title")
    abstract: str = Field(description="Paper abstract")
    authors: list[str] = Field(description="List of author names")
    categories: list[str] = Field(description="arXiv categories (e.g., ['cs.CL', 'cs.AI'])")
    primary_category: str = Field(description="Primary arXiv category")
    published: datetime = Field(description="Publication date")
    updated: datetime = Field(description="Last update date")
    pdf_url: str = Field(description="URL to PDF")
    abs_url: str = Field(description="URL to abstract page")

    @property
    def short_id(self) -> str:
        """Get short ID without version (e.g., '2401.12345' from '2401.12345v1')."""
        return self.arxiv_id.split("v")[0]


class AnalysisResult(BaseModel):
    """LLM analysis result for a paper."""

    summary: str = Field(description="One-sentence Chinese summary")
    key_contributions: list[str] = Field(description="Main contributions (2-4 points)")
    methodology: str = Field(description="Brief methodology description")
    tags: list[str] = Field(description="Technical tags (e.g., ['Transformer', 'RAG', 'Memory'])")
    category: str = Field(description="Assigned category from config")
    relevance_score: int = Field(ge=1, le=10, description="Relevance score 1-10")
    relevance_reason: str = Field(description="Why this score was given")


class AnalyzedPaper(BaseModel):
    """Fully analyzed paper with both raw data and analysis."""

    # Raw data
    arxiv_id: str
    title: str
    abstract: str
    authors: list[str]
    categories: list[str]
    primary_category: str
    published: datetime
    updated: datetime
    pdf_url: str
    abs_url: str

    # Analysis results
    summary: str
    key_contributions: list[str]
    methodology: str
    tags: list[str]
    assigned_category: str
    relevance_score: int
    relevance_reason: str

    # Metadata
    analyzed_at: datetime = Field(default_factory=datetime.now)
    llm_provider: str = Field(description="LLM provider used for analysis")
    llm_model: str = Field(description="LLM model used for analysis")

    @classmethod
    def from_raw_and_analysis(
        cls,
        raw: RawPaper,
        analysis: AnalysisResult,
        llm_provider: str,
        llm_model: str,
    ) -> "AnalyzedPaper":
        """Create AnalyzedPaper from raw paper and analysis result."""
        return cls(
            arxiv_id=raw.arxiv_id,
            title=raw.title,
            abstract=raw.abstract,
            authors=raw.authors,
            categories=raw.categories,
            primary_category=raw.primary_category,
            published=raw.published,
            updated=raw.updated,
            pdf_url=raw.pdf_url,
            abs_url=raw.abs_url,
            summary=analysis.summary,
            key_contributions=analysis.key_contributions,
            methodology=analysis.methodology,
            tags=analysis.tags,
            assigned_category=analysis.category,
            relevance_score=analysis.relevance_score,
            relevance_reason=analysis.relevance_reason,
            llm_provider=llm_provider,
            llm_model=llm_model,
        )

    @property
    def short_id(self) -> str:
        """Get short ID without version."""
        return self.arxiv_id.split("v")[0]


class DailyPapers(BaseModel):
    """Collection of papers for a single day."""

    date: str = Field(description="Date in YYYY-MM-DD format")
    papers: list[AnalyzedPaper] = Field(default_factory=list)
    fetch_time: datetime = Field(default_factory=datetime.now)

    def add_paper(self, paper: AnalyzedPaper) -> bool:
        """Add paper if not duplicate. Returns True if added."""
        existing_ids = {p.arxiv_id for p in self.papers}
        if paper.arxiv_id not in existing_ids:
            self.papers.append(paper)
            return True
        return False

    def get_by_category(self, category: str) -> list[AnalyzedPaper]:
        """Get papers by assigned category."""
        return [p for p in self.papers if p.assigned_category == category]

    def get_high_relevance(self, min_score: int = 7) -> list[AnalyzedPaper]:
        """Get papers with high relevance scores."""
        return [p for p in self.papers if p.relevance_score >= min_score]
