import uuid
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import Column, String, Text, Date, Time, DateTime, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class EventStatus(str, PyEnum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPROVED_L1 = "approved_l1"
    APPROVED_L2 = "approved_l2"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    REVERTED = "reverted"
    POSTPONED = "postponed"
    DEFERRED = "deferred"
    REJECTED = "rejected"


# Valid status transitions
STATUS_TRANSITIONS = {
    EventStatus.DRAFT: [EventStatus.SUBMITTED],
    EventStatus.SUBMITTED: [EventStatus.APPROVED_L1, EventStatus.REJECTED],
    EventStatus.APPROVED_L1: [EventStatus.APPROVED_L2, EventStatus.REJECTED],
    EventStatus.APPROVED_L2: [EventStatus.IN_PROGRESS, EventStatus.POSTPONED, EventStatus.DEFERRED],
    EventStatus.IN_PROGRESS: [EventStatus.COMPLETED, EventStatus.REVERTED, EventStatus.POSTPONED],
    EventStatus.COMPLETED: [],
    EventStatus.REVERTED: [],
    EventStatus.POSTPONED: [EventStatus.IN_PROGRESS, EventStatus.DEFERRED, EventStatus.DRAFT],
    EventStatus.DEFERRED: [EventStatus.DRAFT],
    EventStatus.REJECTED: [EventStatus.DRAFT],
}


class PlannedEvent(Base):
    __tablename__ = "planned_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    scheduled_date = Column(Date, nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    config_changes = Column(Text, nullable=True)
    mop_content = Column(Text, nullable=True)
    mop_file_path = Column(String(255), nullable=True)
    status = Column(Enum(EventStatus), default=EventStatus.DRAFT, nullable=False, index=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    creator = relationship("User", back_populates="events")
    devices = relationship("EventDevice", back_populates="event", cascade="all, delete-orphan")
    approvals = relationship("Approval", back_populates="event", cascade="all, delete-orphan")
    history = relationship("EventHistory", back_populates="event", cascade="all, delete-orphan")
