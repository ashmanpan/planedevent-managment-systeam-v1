import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class EventDevice(Base):
    __tablename__ = "event_devices"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id = Column(UUID(as_uuid=True), ForeignKey("planned_events.id", ondelete="CASCADE"), nullable=False)
    device_id = Column(String(100), nullable=False, index=True)
    device_name = Column(String(200), nullable=True)
    device_ip = Column(String(45), nullable=True)
    device_type = Column(String(50), nullable=True)
    device_location = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    event = relationship("PlannedEvent", back_populates="devices")
