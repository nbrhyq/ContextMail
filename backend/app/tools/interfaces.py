from __future__ import annotations

from pathlib import Path
from typing import List, Protocol

from app.models.domain import ApprovalStatus, EmailDraft, Evidence


class DocumentReader(Protocol):
    async def read(self, path: Path) -> str: ...


class WebSearchTool(Protocol):
    async def search(self, query: str, *, preferred_domains: List[str] | None = None) -> List[Evidence]: ...


class RetrievalTool(Protocol):
    async def retrieve(self, query: str, evidence: List[Evidence]) -> List[Evidence]: ...


class EmailTool(Protocol):
    async def send(self, draft: EmailDraft, approval: ApprovalStatus) -> str: ...
