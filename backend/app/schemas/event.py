from datetime import date, time, datetime
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.event import EventStatus
from app.schemas.device import DeviceResponse
from app.schemas.user import UserResponse


class EventCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    scheduled_date: date
    start_time: time
    end_time: time
    config_changes: Optional[str] = None
    mop_content: Optional[str] = None


class EventUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    scheduled_date: Optional[date] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    config_changes: Optional[str] = None
    mop_content: Optional[str] = None


class EventStatusUpdate(BaseModel):
    reason: Optional[str] = None


class ApprovalInfo(BaseModel):
    id: UUID
    approval_level: int
    status: str
    approver_id: Optional[UUID]
    comments: Optional[str]
    approved_at: Optional[datetime]

    class Config:
        from_attributes = True


class EventResponse(BaseModel):
    id: UUID
    title: str
    description: Optional[str]
    scheduled_date: date
    start_time: time
    end_time: time
    config_changes: Optional[str]
    mop_content: Optional[str]
    mop_file_path: Optional[str]
    status: EventStatus
    created_by: UUID
    created_at: datetime
    updated_at: datetime
    creator: Optional[UserResponse] = None
    devices: List[DeviceResponse] = []
    approvals: List[ApprovalInfo] = []

    class Config:
        from_attributes = True


class EventListResponse(BaseModel):
    items: List[EventResponse]
    total: int
    page: int
    limit: int
    pages: int


class EventHistoryResponse(BaseModel):
    id: UUID
    event_id: UUID
    previous_status: Optional[str]
    new_status: str
    changed_by: UUID
    change_reason: Optional[str]
    changed_at: datetime

    class Config:
        from_attributes = True


class StatsResponse(BaseModel):
    """Dashboard statistics response."""
    total_events: int
    draft: int
    pending_approval: int  # submitted + approved_l1
    in_progress: int
    completed: int
    rejected: int
    reverted: int
    postponed: int
    deferred: int
