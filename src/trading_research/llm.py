from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from trading_research.config import settings

try:
    from langchain_openai import ChatOpenAI
except ImportError:  # pragma: no cover - optional dependency at authoring time
    ChatOpenAI = None


@dataclass
class LLMOutput:
    content: str
    prompt_tokens: int = 0
    completion_tokens: int = 0


class LLMService:
    """Minimal wrapper so the rest of the app can run with or without a live LLM."""

    def __init__(self, model: str | None = None, temperature: float = 0.1):
        self.model = model or settings.default_model
        self.temperature = temperature

    def invoke(self, system_prompt: str, user_prompt: str) -> LLMOutput:
        if ChatOpenAI and settings.openai_api_key:
            client = ChatOpenAI(model=self.model, temperature=self.temperature)
            response = client.invoke(
                [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ]
            )
            usage = response.response_metadata.get("token_usage", {})
            return LLMOutput(
                content=response.content,
                prompt_tokens=int(usage.get("prompt_tokens", 0)),
                completion_tokens=int(usage.get("completion_tokens", 0)),
            )

        # Deterministic offline fallback so the project remains inspectable without keys.
        fallback = {
            "system_prompt": system_prompt[:120],
            "summary": "LLM call skipped because no provider credentials were configured.",
            "next_step": "Configure OPENAI_API_KEY to enable synthesized narrative output.",
        }
        return LLMOutput(content=json.dumps(fallback, indent=2))

