from datetime import date
from typing import Optional, List, Tuple
from uuid import UUID

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session, joinedload

from app.models.event import PlannedEvent, EventStatus, STATUS_TRANSITIONS
from app.models.history import EventHistory
from app.models.approval import Approval, ApprovalStatus
from app.schemas.event import EventCreate, EventUpdate


class EventService:
    def __init__(self, db: Session):
        self.db = db

    def create_event(self, event_data: EventCreate, user_id: UUID) -> PlannedEvent:
        event = PlannedEvent(
            title=event_data.title,
            description=event_data.description,
            scheduled_date=event_data.scheduled_date,
            start_time=event_data.start_time,
            end_time=event_data.end_time,
            config_changes=event_data.config_changes,
            mop_content=event_data.mop_content,
            created_by=user_id,
            status=EventStatus.DRAFT,
        )
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)

        # Create initial history entry
        self._add_history(event.id, None, EventStatus.DRAFT.value, user_id, "Event created")

        return event

    def get_event(self, event_id: UUID) -> Optional[PlannedEvent]:
        return (
            self.db.query(PlannedEvent)
            .options(
                joinedload(PlannedEvent.creator),
                joinedload(PlannedEvent.devices),
                joinedload(PlannedEvent.approvals),
            )
            .filter(PlannedEvent.id == event_id)
            .first()
        )

    def get_events(
        self,
        status: Optional[EventStatus] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        created_by: Optional[UUID] = None,
        device_id: Optional[str] = None,
        device_name: Optional[str] = None,
        page: int = 1,
        limit: int = 20,
    ) -> Tuple[List[PlannedEvent], int]:
        query = self.db.query(PlannedEvent).options(
            joinedload(PlannedEvent.creator),
            joinedload(PlannedEvent.devices),
            joinedload(PlannedEvent.approvals),
        )

        # Apply filters
        if status:
            query = query.filter(PlannedEvent.status == status)
        if start_date:
            query = query.filter(PlannedEvent.scheduled_date >= start_date)
        if end_date:
            query = query.filter(PlannedEvent.scheduled_date <= end_date)
        if created_by:
            query = query.filter(PlannedEvent.created_by == created_by)
        if device_id or device_name:
            from app.models.device import EventDevice

            device_query = self.db.query(EventDevice.event_id)
            if device_id:
                device_query = device_query.filter(EventDevice.device_id == device_id)
            if device_name:
                device_query = device_query.filter(EventDevice.device_name.ilike(f"%{device_name}%"))
            event_ids = [r[0] for r in device_query.distinct().all()]
            query = query.filter(PlannedEvent.id.in_(event_ids))

        # Get total count
        total = query.count()

        # Apply pagination
        offset = (page - 1) * limit
        events = query.order_by(PlannedEvent.scheduled_date.desc()).offset(offset).limit(limit).all()

        return events, total

    def update_event(self, event_id: UUID, event_data: EventUpdate, user_id: UUID) -> Optional[PlannedEvent]:
        event = self.db.query(PlannedEvent).filter(PlannedEvent.id == event_id).first()
        if not event:
            return None

        # Only allow updates in draft status
        if event.status != EventStatus.DRAFT:
            raise ValueError("Can only update events in draft status")

        for field, value in event_data.model_dump(exclude_unset=True).items():
            setattr(event, field, value)

        self.db.commit()
        self.db.refresh(event)
        return event

    def delete_event(self, event_id: UUID) -> bool:
        event = self.db.query(PlannedEvent).filter(PlannedEvent.id == event_id).first()
        if not event:
            return False

        if event.status != EventStatus.DRAFT:
            raise ValueError("Can only delete events in draft status")

        self.db.delete(event)
        self.db.commit()
        return True

    def change_status(
        self,
        event_id: UUID,
        new_status: EventStatus,
        user_id: UUID,
        reason: Optional[str] = None,
    ) -> Optional[PlannedEvent]:
        event = self.db.query(PlannedEvent).filter(PlannedEvent.id == event_id).first()
        if not event:
            return None

        # Validate transition
        allowed_transitions = STATUS_TRANSITIONS.get(event.status, [])
        if new_status not in allowed_transitions:
            raise ValueError(
                f"Invalid status transition from {event.status.value} to {new_status.value}"
            )

        old_status = event.status.value
        event.status = new_status

        # Add history entry
        self._add_history(event_id, old_status, new_status.value, user_id, reason)

        self.db.commit()
        self.db.refresh(event)
        return event

    def submit_for_approval(self, event_id: UUID, user_id: UUID) -> Optional[PlannedEvent]:
        event = self.change_status(event_id, EventStatus.SUBMITTED, user_id, "Submitted for approval")
        if event:
            # Create Level 1 approval request
            approval = Approval(
                event_id=event_id,
                approval_level=1,
                status=ApprovalStatus.PENDING,
            )
            self.db.add(approval)
            self.db.commit()
        return event

    def get_history(self, event_id: UUID) -> List[EventHistory]:
        return (
            self.db.query(EventHistory)
            .filter(EventHistory.event_id == event_id)
            .order_by(EventHistory.changed_at.desc())
            .all()
        )

    def update_mop_file(self, event_id: UUID, file_path: str) -> Optional[PlannedEvent]:
        event = self.db.query(PlannedEvent).filter(PlannedEvent.id == event_id).first()
        if event:
            event.mop_file_path = file_path
            self.db.commit()
            self.db.refresh(event)
        return event

    def _add_history(
        self,
        event_id: UUID,
        previous_status: Optional[str],
        new_status: str,
        user_id: UUID,
        reason: Optional[str] = None,
    ):
        history = EventHistory(
            event_id=event_id,
            previous_status=previous_status,
            new_status=new_status,
            changed_by=user_id,
            change_reason=reason,
        )
        self.db.add(history)
