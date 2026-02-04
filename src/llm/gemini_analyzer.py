"""Google Gemini analyzer implementation."""

import google.generativeai as genai

from ..config import Config
from .base import BaseAnalyzer


class GeminiAnalyzer(BaseAnalyzer):
    """Paper analyzer using Google Gemini API."""

    def __init__(self, config: Config):
        super().__init__(config)

        api_key = config.llm.api_key
        if not api_key:
            raise ValueError(
                f"API key not found. Set {config.llm.api_key_env} environment variable."
            )

        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(config.llm.model)

    def _call_llm(self, prompt: str) -> str:
        """Call Gemini API."""
        response = self.model.generate_content(prompt)
        return response.text
