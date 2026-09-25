from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app.models.domain import (
    ApprovalStatus,
    EmailDraft,
    Evidence,
    Intent,
    PlanStep,
    Recipient,
    ReviewResult,
    RiskLevel,
    TraceEvent,
    UploadedDocument,
)


class WorkflowState(BaseModel):
    user_request: str
    intent: Intent = Intent.UNCERTAIN
    goal: str = ""
    recipient: Optional[Recipient] = None
    uploaded_documents: List[UploadedDocument] = Field(default_factory=list)
    available_context: List[str] = Field(default_factory=list)
    missing_context: List[str] = Field(default_factory=list)
    execution_plan: List[PlanStep] = Field(default_factory=list)
    selected_agents: List[str] = Field(default_factory=list)
    tool_results: Dict[str, Any] = Field(default_factory=dict)
    evidence: List[Evidence] = Field(default_factory=list)
    draft: Optional[EmailDraft] = None
    review_result: Optional[ReviewResult] = None
    risk_level: RiskLevel = RiskLevel.LOW
    approval_status: ApprovalStatus = ApprovalStatus.NOT_REQUESTED
    next_action: str = "EXECUTE"
    workflow_status: str = "CREATED"
    iteration_count: int = Field(default=0, ge=0)
    max_iterations: int = Field(default=3, ge=1, le=10)
    llm_call_count: int = Field(default=0, ge=0)
    execution_trace: List[TraceEvent] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)

    @property
    def can_replan(self) -> bool:
        return self.iteration_count < self.max_iterations
