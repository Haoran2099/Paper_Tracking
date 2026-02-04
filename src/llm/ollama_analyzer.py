"""Ollama (local) analyzer implementation."""

import os

import httpx

from ..config import Config
from .base import BaseAnalyzer


class OllamaAnalyzer(BaseAnalyzer):
    """Paper analyzer using Ollama local models."""

    def __init__(self, config: Config):
        super().__init__(config)

        self.host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        self.model = config.llm.model

    def _call_llm(self, prompt: str) -> str:
        """Call Ollama API."""
        response = httpx.post(
            f"{self.host}/api/generate",
            json={
                "model": self.model,
                "prompt": prompt,
                "stream": False,
            },
            timeout=120.0,  # Local models can be slow
        )

        response.raise_for_status()
        return response.json()["response"]
