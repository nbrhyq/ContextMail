from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, Field

from app.graph.state import WorkflowState
from app.models.domain import RunStatus


class RunRecord(BaseModel):
    id: str = Field(default_factory=lambda: f"run_{uuid4().hex[:12]}")
    status: RunStatus = RunStatus.CREATED
    state: WorkflowState
    mock_message_id: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
