from app.graph.state import WorkflowState
from typing import Optional

from app.models.domain import EmailDraft, Intent, TraceEvent
from app.services.llm_service import StructuredLLM


class WriterAgent:
    def __init__(self, llm: Optional[StructuredLLM] = None) -> None:
        self.llm = llm

    async def run(self, state: WorkflowState) -> WorkflowState:
        recipient_name = state.recipient.name if state.recipient and state.recipient.name else "there"
        recipient_address = state.recipient.email if state.recipient and state.recipient.email else ""
        verified = [item for item in state.evidence if item.verified]
        snippets = [item.content.replace("\n", " ")[:220] for item in verified[:2]]
        context_line = f" Based on the materials provided, {snippets[0]}." if snippets else ""

        subjects = {
            Intent.JOB_APPLICATION: "Application inquiry",
            Intent.PHD_OUTREACH: "Prospective PhD research inquiry",
            Intent.SCHOOL_AFFAIRS: "Course matter inquiry",
            Intent.OTHER: "A quick note",
            Intent.UNCERTAIN: "Message",
        }
        body = (
            f"Dear {recipient_name},\n\n"
            f"I’m writing regarding the following goal: {state.goal}.{context_line}\n\n"
            "I would appreciate the opportunity to discuss this further. Please let me know if any additional information would be helpful.\n\n"
            "Kind regards"
        )
        fallback = EmailDraft(
            recipient=recipient_address,
            subject=subjects[state.intent],
            body=body,
            attachments=[document.filename for document in state.uploaded_documents],
            evidence_ids=[item.id for item in verified],
        )
        state.draft = fallback
        if self.llm:
            try:
                result = await self.llm.generate_structured(
                    system_prompt=(
                        "You are ContextMail's email writer. Write a concise, natural, personalized email. "
                        "Use only facts present in VERIFIED EVIDENCE. Do not invent achievements, publications, "
                        "relationships, or recipient details. Return only the requested JSON object."
                    ),
                    user_prompt=(
                        f"GOAL:\n{state.goal}\n\nRECIPIENT:\n{state.recipient.model_dump_json() if state.recipient else '{}'}"
                        f"\n\nVERIFIED EVIDENCE:\n{[{'id': item.id, 'content': item.content} for item in verified]}"
                        f"\n\nATTACHMENTS:\n{fallback.attachments}"
                    ),
                    schema=EmailDraft.model_json_schema(),
                )
                generated = EmailDraft.model_validate(result)
                generated.recipient = generated.recipient or recipient_address
                generated.attachments = fallback.attachments
                generated.evidence_ids = [item.id for item in verified]
                state.draft = generated
            except Exception as exc:
                state.errors.append(f"Ollama writer fallback used: {exc}")
        state.llm_call_count += 1
        state.execution_trace.append(TraceEvent(
            actor="writer_agent", action="draft", status="COMPLETED",
            summary=f"Drafted email using {len(verified)} verified evidence item(s)",
        ))
        return state
