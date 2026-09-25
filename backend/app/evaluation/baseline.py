from typing import Protocol

from app.models.domain import EmailDraft


class BaselineGenerator(Protocol):
    """Contract for Single LLM -> Email comparison runs."""

    async def generate(self, user_request: str) -> EmailDraft: ...

