from pathlib import Path
from typing import List

from app.graph.state import WorkflowState
from app.models.domain import Evidence, EvidenceSourceType, TraceEvent
from app.tools.document_reader import LocalDocumentReader


class ContextAgent:
    def __init__(self, reader: LocalDocumentReader) -> None:
        self.reader = reader

    async def run(self, state: WorkflowState) -> WorkflowState:
        collected: List[Evidence] = []
        for document in state.uploaded_documents:
            if not document.local_path:
                continue
            try:
                content = (await self.reader.read(Path(document.local_path))).strip()
                if content:
                    collected.append(Evidence(
                        claim=f"User-provided information from {document.filename}",
                        source_type=EvidenceSourceType.USER_DOCUMENT,
                        source_name=document.filename,
                        content=content[:12000],
                        relevance=f"Uploaded material relevant to: {state.goal}",
                        verified=True,
                        filename=document.filename,
                        document_location="full document (page/section unavailable from extractor)",
                    ))
                state.execution_trace.append(TraceEvent(
                    actor="context_agent", action="read_document", status="COMPLETED",
                    summary=f"Read {document.filename}", tool=f"{Path(document.filename).suffix[1:]}_reader",
                ))
            except Exception as exc:
                state.errors.append(f"Could not read {document.filename}: {exc}")
                state.execution_trace.append(TraceEvent(
                    actor="context_agent", action="read_document", status="FAILED",
                    summary=f"Could not read {document.filename}",
                ))
        state.evidence.extend(collected)
        return state
