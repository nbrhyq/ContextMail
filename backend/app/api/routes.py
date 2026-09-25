from pathlib import Path
from typing import Dict, List, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel, Field

from app.agents.planner import RuleBasedPlanner
from app.config import get_settings
from app.graph.state import WorkflowState
from app.graph.workflow import ContextMailWorkflow
from app.models.domain import (
    ApprovalStatus, EmailDraft, PlannerDecision, Recipient, RunStatus, UploadedDocument,
)
from app.models.run import RunRecord
from app.services.run_store import SQLiteRunStore
from app.tools.mock_tools import MockEmailTool


router = APIRouter()
UPLOAD_ROOT = Path("uploads")
UPLOAD_ROOT.mkdir(exist_ok=True)
_uploads: Dict[str, UploadedDocument] = {}
_store = SQLiteRunStore()
_workflow = ContextMailWorkflow()


class PlanRequest(BaseModel):
    user_request: str = Field(min_length=1)
    recipient: Optional[Recipient] = None
    documents: List[UploadedDocument] = Field(default_factory=list)


class CreateRunRequest(BaseModel):
    user_request: str = Field(min_length=1)
    recipient: Optional[Recipient] = None
    document_ids: List[str] = Field(default_factory=list)


class EditDraftRequest(BaseModel):
    subject: str = Field(min_length=1)
    body: str = Field(min_length=1)
    recipient: str = ""
    attachments: List[str] = Field(default_factory=list)


def get_planner() -> RuleBasedPlanner:
    return RuleBasedPlanner()


def require_run(run_id: str) -> RunRecord:
    record = _store.get(run_id)
    if not record:
        raise HTTPException(status_code=404, detail="Run not found")
    return record


@router.get("/health")
async def health() -> dict:
    settings = get_settings()
    return {
        "status": "ok",
        "service": "contextmail",
        "llm_provider": settings.llm_provider,
        "llm_model": settings.llm_model,
    }


@router.post("/uploads", response_model=UploadedDocument)
async def upload_document(file: UploadFile = File(...)) -> UploadedDocument:
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in {".pdf", ".docx", ".txt"}:
        raise HTTPException(status_code=415, detail="Only PDF, DOCX, and TXT files are supported")
    document_id = str(uuid4())
    safe_name = f"{document_id}{suffix}"
    target = UPLOAD_ROOT / safe_name
    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File exceeds the 10 MB limit")
    target.write_bytes(content)
    document = UploadedDocument(
        id=document_id, filename=file.filename or safe_name, media_type=file.content_type,
        size_bytes=len(content), local_path=str(target.resolve()),
    )
    _uploads[document_id] = document
    return document


@router.post("/runs/plan", response_model=PlannerDecision)
async def create_plan(payload: PlanRequest, planner: RuleBasedPlanner = Depends(get_planner)) -> PlannerDecision:
    return planner.plan(payload.user_request, payload.recipient, payload.documents)


@router.post("/runs", response_model=RunRecord)
async def create_run(payload: CreateRunRequest) -> RunRecord:
    missing_ids = [item for item in payload.document_ids if item not in _uploads]
    if missing_ids:
        raise HTTPException(status_code=400, detail=f"Unknown upload IDs: {', '.join(missing_ids)}")
    state = WorkflowState(
        user_request=payload.user_request,
        recipient=payload.recipient,
        uploaded_documents=[_uploads[item] for item in payload.document_ids],
        workflow_status="RUNNING",
    )
    record = RunRecord(status=RunStatus.RUNNING, state=state)
    try:
        record.state = await _workflow.run(state)
        if record.state.workflow_status == "READY_FOR_APPROVAL":
            record.status = RunStatus.READY_FOR_APPROVAL
        elif record.state.workflow_status == "NEEDS_INPUT":
            record.status = RunStatus.NEEDS_INPUT
        else:
            record.status = RunStatus.FAILED
    except Exception as exc:
        record.status = RunStatus.FAILED
        record.state.errors.append(str(exc))
    return _store.save(record)


@router.get("/runs/{run_id}", response_model=RunRecord)
async def get_run(run_id: str) -> RunRecord:
    return require_run(run_id)


@router.put("/runs/{run_id}/draft", response_model=RunRecord)
async def edit_draft(run_id: str, payload: EditDraftRequest) -> RunRecord:
    record = require_run(run_id)
    evidence_ids = record.state.draft.evidence_ids if record.state.draft else []
    record.state.draft = EmailDraft(**payload.model_dump(), evidence_ids=evidence_ids)
    record.state.approval_status = ApprovalStatus.PENDING
    record.status = RunStatus.READY_FOR_APPROVAL
    return _store.save(record)


@router.post("/runs/{run_id}/approve", response_model=RunRecord)
async def approve_run(run_id: str) -> RunRecord:
    record = require_run(run_id)
    if record.status != RunStatus.READY_FOR_APPROVAL or not record.state.draft:
        raise HTTPException(status_code=409, detail="Run is not ready for approval")
    record.state.approval_status = ApprovalStatus.APPROVED
    record.mock_message_id = await MockEmailTool().send(record.state.draft, record.state.approval_status)
    record.status = RunStatus.SENT
    record.state.workflow_status = "SENT"
    return _store.save(record)


@router.post("/runs/{run_id}/reject", response_model=RunRecord)
async def reject_run(run_id: str) -> RunRecord:
    record = require_run(run_id)
    record.state.approval_status = ApprovalStatus.REJECTED
    record.status = RunStatus.REJECTED
    record.state.workflow_status = "REJECTED"
    return _store.save(record)
