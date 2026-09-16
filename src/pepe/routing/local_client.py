"""Local model client. Ollama exposes an OpenAI-compatible endpoint at
http://localhost:11434/v1 by default. We hit it directly with httpx to keep
the dependency surface small.

Phase 1: this is the only inference path. Cloud escalation is stubbed out
until Phase 1.5.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import httpx


@dataclass
class ChatMessage:
    role: str
    content: str


@dataclass
class ChatRequest:
    model: str
    messages: list[ChatMessage]
    temperature: float = 0.2
    max_tokens: int | None = None
    extra: dict[str, Any] = field(default_factory=dict)


class OllamaUnavailable(RuntimeError):
    pass


class OllamaClient:
    def __init__(
        self,
        base_url: str = "http://localhost:11434/v1",
        api_key: str = "ollama",  # Ollama ignores the value but the header is required.
        timeout: float = 120.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self._client = httpx.Client(timeout=timeout)

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "OllamaClient":
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()

    def chat(self, req: ChatRequest) -> str:
        """Return the assistant content string. Raises OllamaUnavailable on HTTP errors."""
        payload: dict[str, Any] = {
            "model": req.model,
            "messages": [m.__dict__ for m in req.messages],
            "temperature": req.temperature,
        }
        if req.max_tokens is not None:
            payload["max_tokens"] = req.max_tokens
        payload.update(req.extra)
        try:
            r = self._client.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
            )
            r.raise_for_status()
        except httpx.HTTPError as e:
            raise OllamaUnavailable(str(e)) from e
        data = r.json()
        return data["choices"][0]["message"]["content"]


def is_running(base_url: str = "http://localhost:11434/v1") -> bool:
    try:
        with httpx.Client(timeout=2.0) as c:
            r = c.get(f"{base_url.rstrip('/')}/models")
            return r.status_code == 200
    except httpx.HTTPError:
        return False
