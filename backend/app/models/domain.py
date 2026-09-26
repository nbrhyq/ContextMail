from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class Intent(str, Enum):
    JOB_APPLICATION = "JOB_APPLICATION"
    PHD_OUTREACH = "PHD_OUTREACH"
    SCHOOL_AFFAIRS = "SCHOOL_AFFAIRS"
    OTHER = "OTHER"
    UNCERTAIN = "UNCERTAIN"


class Complexity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class NextAction(str, Enum):
    EXECUTE = "EXECUTE"
    ASK_USER = "ASK_USER"
    REQUIRE_APPROVAL = "REQUIRE_APPROVAL"
    STOP = "STOP"


class ApprovalStatus(str, Enum):
    NOT_REQUESTED = "NOT_REQUESTED"
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class RunStatus(str, Enum):
    CREATED = "CREATED"
    RUNNING = "RUNNING"
    NEEDS_INPUT = "NEEDS_INPUT"
    READY_FOR_APPROVAL = "READY_FOR_APPROVAL"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    SENT = "SENT"
    FAILED = "FAILED"


class EvidenceSourceType(str, Enum):
    USER_DOCUMENT = "USER_DOCUMENT"
    WEB = "WEB"
    USER_INPUT = "USER_INPUT"
    EMAIL_HISTORY = "EMAIL_HISTORY"
    SYSTEM = "SYSTEM"


class UploadedDocument(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    filename: str
    media_type: Optional[str] = None
    size_bytes: Optional[int] = Field(default=None, ge=0)
    local_path: Optional[str] = Field(default=None, exclude=True)


class Recipient(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    organization: Optional[str] = None


class Evidence(BaseModel):
    evidence_id: str = Field(default_factory=lambda: f"evidence_{uuid4().hex[:12]}")
    claim: str
    content: str
    source_name: str
    source_url: Optional[str] = None
    source_type: EvidenceSourceType
    relevance: str
    verified: bool = False
    retrieved_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    filename: Optional[str] = None
    document_location: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @property
    def id(self) -> str:
        """Compatibility accessor for existing state and portfolio demo code."""
        return self.evidence_id

    @property
    def source(self) -> str:
        return self.source_name


class PlanStep(BaseModel):
    id: str
    agent: str
    action: str
    tools: List[str] = Field(default_factory=list)
    depends_on: List[str] = Field(default_factory=list)


class PlannerDecision(BaseModel):
    intent: Intent
    confidence: float = Field(ge=0, le=1)
    goal: str
    complexity: Complexity
    risk_level: RiskLevel
    required_context: List[str] = Field(default_factory=list)
    available_context: List[str] = Field(default_factory=list)
    missing_context: List[str] = Field(default_factory=list)
    agents_required: List[str] = Field(default_factory=list)
    tools_required: List[str] = Field(default_factory=list)
    execution_plan: List[PlanStep] = Field(default_factory=list)
    next_action: NextAction


class EmailDraft(BaseModel):
    recipient: str = ""
    subject: str
    body: str
    attachments: List[str] = Field(default_factory=list)
    evidence_ids: List[str] = Field(default_factory=list)


class ReviewDecision(str, Enum):
    PASS = "PASS"
    REVISE = "REVISE"
    NEED_MORE_EVIDENCE = "NEED_MORE_EVIDENCE"
    NEED_USER_INFORMATION = "NEED_USER_INFORMATION"


class ReviewResult(BaseModel):
    factuality: str
    personalization: str
    tone: str
    unsupported_claims: List[str] = Field(default_factory=list)
    missing_information: List[str] = Field(default_factory=list)
    decision: ReviewDecision
    revision_instructions: List[str] = Field(default_factory=list)


class TraceEvent(BaseModel):
    actor: str
    action: str
    status: str
    summary: str
    tool: Optional[str] = None
    latency_ms: Optional[int] = Field(default=None, ge=0)
    token_usage: Optional[int] = Field(default=None, ge=0)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
