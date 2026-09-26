from __future__ import annotations

from pathlib import Path
from typing import List
from uuid import uuid4

from app.models.domain import ApprovalStatus, EmailDraft, Evidence


class MockDocumentReader:
    async def read(self, path: Path) -> str:
        return f"Mock extracted content from {path.name}"


class MockWebSearch:
    async def search(self, query: str, *, preferred_domains: List[str] | None = None) -> List[Evidence]:
        return []


class InMemoryRetrieval:
    async def retrieve(self, query: str, evidence: List[Evidence]) -> List[Evidence]:
        terms = set(query.lower().split())
        return [item for item in evidence if terms.intersection(item.content.lower().split())]


class MockEmailTool:
    async def send(self, draft: EmailDraft, approval: ApprovalStatus) -> str:
        if approval != ApprovalStatus.APPROVED:
            raise PermissionError("Explicit user approval is required before email action")
        return f"mock_email_{uuid4().hex[:12]}"
