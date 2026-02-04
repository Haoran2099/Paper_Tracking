"""Claude (Anthropic) analyzer implementation."""

from anthropic import Anthropic

from ..config import Config
from .base import BaseAnalyzer


class ClaudeAnalyzer(BaseAnalyzer):
    """Paper analyzer using Claude API."""

    def __init__(self, config: Config):
        super().__init__(config)

        api_key = config.llm.api_key
        if not api_key:
            raise ValueError(
                f"API key not found. Set {config.llm.api_key_env} environment variable."
            )

        self.client = Anthropic(api_key=api_key)

    def _call_llm(self, prompt: str) -> str:
        """Call Claude API."""
        message = self.client.messages.create(
            model=self.config.llm.model,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )

        return message.content[0].text
