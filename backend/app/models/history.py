import uuid
from datetime import datetime

from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class EventHistory(Base):
    __tablename__ = "event_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id = Column(UUID(as_uuid=True), ForeignKey("planned_events.id", ondelete="CASCADE"), nullable=False)
    previous_status = Column(String(50), nullable=True)
    new_status = Column(String(50), nullable=False)
    changed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    change_reason = Column(Text, nullable=True)
    changed_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    event = relationship("PlannedEvent", back_populates="history")
    changed_by_user = relationship("User", back_populates="history_changes")
