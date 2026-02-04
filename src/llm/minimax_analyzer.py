"""MiniMax analyzer implementation."""

import os

from openai import OpenAI

from ..config import Config
from .base import BaseAnalyzer


class MiniMaxAnalyzer(BaseAnalyzer):
    """Paper analyzer using MiniMax API (OpenAI-compatible)."""

    def __init__(self, config: Config):
        super().__init__(config)

        api_key = config.llm.api_key
        if not api_key:
            raise ValueError(
                f"API key not found. Set {config.llm.api_key_env} environment variable."
            )

        # MiniMax uses OpenAI-compatible API
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.minimax.chat/v1",
        )

    def _call_llm(self, prompt: str) -> str:
        """Call MiniMax API."""
        response = self.client.chat.completions.create(
            model=self.config.llm.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1024,
        )

        return response.choices[0].message.content
