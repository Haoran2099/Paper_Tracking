"""Base class for LLM analyzers."""

import json
import re
from abc import ABC, abstractmethod

from ..config import Config
from ..models import AnalysisResult, AnalyzedPaper, RawPaper


class BaseAnalyzer(ABC):
    """Abstract base class for paper analyzers."""

    def __init__(self, config: Config):
        self.config = config
        self._output_categories = [d.output_category for d in config.domains]
        self._domain_descriptions = {
            d.output_category: f"{d.name} (keywords: {', '.join(d.keywords)})"
            for d in config.domains
        }

    @property
    def provider_name(self) -> str:
        """Get the provider name."""
        return self.config.llm.provider

    @property
    def model_name(self) -> str:
        """Get the model name."""
        return self.config.llm.model

    def _build_prompt(self, title: str, abstract: str) -> str:
        """Build the analysis prompt."""
        categories_desc = "\n".join(
            f"  - {cat}: {desc}" for cat, desc in self._domain_descriptions.items()
        )

        return f"""请分析以下学术论文，并以 JSON 格式返回分析结果。

论文标题: {title}

论文摘要: {abstract}

请返回以下格式的 JSON（不要包含 markdown 代码块标记）:
{{
  "summary": "一句话中文总结（30字以内）",
  "key_contributions": ["贡献点1", "贡献点2", "贡献点3"],
  "methodology": "简要描述论文的方法论（50字以内）",
  "tags": ["标签1", "标签2", "标签3"],
  "category": "从以下类别中选择最相关的一个",
  "relevance_score": 1-10的整数,
  "relevance_reason": "评分原因（30字以内）"
}}

可选类别:
{categories_desc}

评分标准:
- 9-10: 核心相关，直接研究该领域的关键问题
- 7-8: 高度相关，涉及该领域的重要方面
- 5-6: 中等相关，有一定参考价值
- 3-4: 边缘相关，仅涉及部分概念
- 1-2: 基本无关

请直接返回 JSON，不要有任何额外文字。"""

    def _parse_response(self, response: str) -> AnalysisResult:
        """Parse LLM response to AnalysisResult."""
        # Remove markdown code block if present
        response = response.strip()
        if response.startswith("```"):
            # Remove opening ```json or ```
            response = re.sub(r"^```\w*\n?", "", response)
            # Remove closing ```
            response = re.sub(r"\n?```$", "", response)

        try:
            data = json.loads(response)
        except json.JSONDecodeError as e:
            # Try to extract JSON from the response
            json_match = re.search(r"\{[\s\S]*\}", response)
            if json_match:
                data = json.loads(json_match.group())
            else:
                raise ValueError(f"Failed to parse JSON response: {e}")

        # Validate category
        if data.get("category") not in self._output_categories:
            # Default to first category if invalid
            data["category"] = self._output_categories[0] if self._output_categories else "other"

        # Ensure relevance_score is int
        data["relevance_score"] = int(data.get("relevance_score", 5))

        return AnalysisResult.model_validate(data)

    @abstractmethod
    def _call_llm(self, prompt: str) -> str:
        """Call the LLM API and return the response text."""
        pass

    def analyze_paper(self, paper: RawPaper) -> AnalysisResult:
        """Analyze a single paper."""
        prompt = self._build_prompt(paper.title, paper.abstract)
        response = self._call_llm(prompt)
        return self._parse_response(response)

    def analyze_and_convert(self, paper: RawPaper) -> AnalyzedPaper:
        """Analyze paper and convert to AnalyzedPaper model."""
        analysis = self.analyze_paper(paper)
        return AnalyzedPaper.from_raw_and_analysis(
            raw=paper,
            analysis=analysis,
            llm_provider=self.provider_name,
            llm_model=self.model_name,
        )

    def analyze_batch(
        self,
        papers: list[RawPaper],
        min_score: int | None = None,
        progress_callback=None,
    ) -> list[AnalyzedPaper]:
        """Analyze multiple papers with optional filtering."""
        if min_score is None:
            min_score = self.config.fetch.min_relevance_score

        results = []
        for i, paper in enumerate(papers):
            try:
                if progress_callback:
                    progress_callback(i + 1, len(papers), paper.title)

                analyzed = self.analyze_and_convert(paper)

                if analyzed.relevance_score >= min_score:
                    results.append(analyzed)
                    print(f"  ✓ [{analyzed.relevance_score}/10] {paper.title[:60]}...")
                else:
                    print(f"  ○ [{analyzed.relevance_score}/10] Skipped: {paper.title[:50]}...")

            except Exception as e:
                print(f"  ✗ Error analyzing {paper.arxiv_id}: {e}")
                continue

        return results
