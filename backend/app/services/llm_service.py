import json
from typing import Any, Dict, Protocol

import httpx

from app.config import Settings, get_settings


class StructuredLLM(Protocol):
    async def generate_structured(
        self, *, system_prompt: str, user_prompt: str, schema: Dict[str, Any]
    ) -> Dict[str, Any]: ...


class OllamaStructuredLLM:
    def __init__(self, settings: Settings) -> None:
        self.base_url = settings.ollama_base_url.rstrip("/")
        self.model = settings.llm_model
        self.timeout = settings.llm_timeout_seconds

    async def generate_structured(
        self, *, system_prompt: str, user_prompt: str, schema: Dict[str, Any]
    ) -> Dict[str, Any]:
        payload = {
            "model": self.model,
            "stream": False,
            "format": schema,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "options": {"temperature": 0.2},
        }
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(f"{self.base_url}/api/chat", json=payload)
            response.raise_for_status()
        data = response.json()
        content = data.get("message", {}).get("content", "")
        if not content:
            raise ValueError("Ollama returned no structured content")
        return json.loads(content)


class DisabledStructuredLLM:
    async def generate_structured(
        self, *, system_prompt: str, user_prompt: str, schema: Dict[str, Any]
    ) -> Dict[str, Any]:
        raise RuntimeError("LLM provider is disabled")


def create_llm(settings: Settings = None) -> StructuredLLM:
    configured = settings or get_settings()
    if configured.llm_provider.lower() == "ollama":
        return OllamaStructuredLLM(configured)
    return DisabledStructuredLLM()
