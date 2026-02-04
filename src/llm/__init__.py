"""LLM analyzers for paper analysis."""

from .base import BaseAnalyzer
from .claude_analyzer import ClaudeAnalyzer
from .openai_analyzer import OpenAIAnalyzer
from .ollama_analyzer import OllamaAnalyzer


def get_analyzer(config) -> BaseAnalyzer:
    """Get the appropriate analyzer based on configuration."""
    provider = config.llm.provider

    if provider == "claude":
        return ClaudeAnalyzer(config)
    elif provider == "openai":
        return OpenAIAnalyzer(config)
    elif provider == "ollama":
        return OllamaAnalyzer(config)
    else:
        raise ValueError(f"Unknown LLM provider: {provider}")


__all__ = [
    "BaseAnalyzer",
    "ClaudeAnalyzer",
    "OpenAIAnalyzer",
    "OllamaAnalyzer",
    "get_analyzer",
]
