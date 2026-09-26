from __future__ import annotations

from typing import Optional

from app.models.domain import EmailDraft
from app.services.llm_service import StructuredLLM


class SingleLLMBaseline:
    """Fair one-call baseline: request + available materials -> email draft."""

    def __init__(self, llm: Optional[StructuredLLM]) -> None:
        self.llm = llm

    async def generate(self, user_request: str, available_materials: list[str]) -> EmailDraft:
        if self.llm:
            result = await self.llm.generate_structured(
                system_prompt=(
                    "You are a capable professional email assistant. Produce a concise, natural email that "
                    "fulfils the request. Use only facts in the request and available materials. If critical "
                    "information is missing, say so conservatively rather than inventing it. Return JSON only."
                ),
                user_prompt=f"USER REQUEST:\n{user_request}\n\nAVAILABLE MATERIALS:\n{available_materials}",
                schema=EmailDraft.model_json_schema(),
            )
            return EmailDraft.model_validate(result)
        return EmailDraft(
            subject="Regarding your request",
            body=(
                "Hello,\n\nI am writing regarding the request described above. "
                "I would appreciate your guidance on the next step.\n\nKind regards"
            ),
        )
