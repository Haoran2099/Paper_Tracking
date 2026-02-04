"""LLM analyzers for paper analysis."""

from .base import BaseAnalyzer
from .claude_analyzer import ClaudeAnalyzer
from .openai_analyzer import OpenAIAnalyzer
from .ollama_analyzer import OllamaAnalyzer
from .minimax_analyzer import MiniMaxAnalyzer
from .gemini_analyzer import GeminiAnalyzer


def get_analyzer(config) -> BaseAnalyzer:
    """Get the appropriate analyzer based on configuration."""
    provider = config.llm.provider

    if provider == "claude":
        return ClaudeAnalyzer(config)
    elif provider == "openai":
        return OpenAIAnalyzer(config)
    elif provider == "ollama":
        return OllamaAnalyzer(config)
    elif provider == "minimax":
        return MiniMaxAnalyzer(config)
    elif provider == "gemini":
        return GeminiAnalyzer(config)
    else:
        raise ValueError(f"Unknown LLM provider: {provider}")


__all__ = [
    "BaseAnalyzer",
    "ClaudeAnalyzer",
    "OpenAIAnalyzer",
    "OllamaAnalyzer",
    "MiniMaxAnalyzer",
    "get_analyzer",
]
