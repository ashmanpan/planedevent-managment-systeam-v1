from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel

from app.models.approval import ApprovalStatus


class ApprovalCreate(BaseModel):
    approval_level: int


class ApprovalAction(BaseModel):
    comments: Optional[str] = None


class ApprovalResponse(BaseModel):
    id: UUID
    event_id: UUID
    approver_id: Optional[UUID]
    approval_level: int
    status: ApprovalStatus
    comments: Optional[str]
    approved_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class PendingApprovalResponse(BaseModel):
    id: UUID
    event_id: UUID
    event_title: str
    event_scheduled_date: str
    approval_level: int
    status: ApprovalStatus
    created_at: datetime
    creator_name: str
