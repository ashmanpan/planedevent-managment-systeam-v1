from datetime import datetime
from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session, joinedload

from app.models.approval import Approval, ApprovalStatus
from app.models.event import PlannedEvent, EventStatus
from app.models.user import User, UserRole
from app.services.event_service import EventService


class ApprovalService:
    def __init__(self, db: Session):
        self.db = db
        self.event_service = EventService(db)

    def get_pending_approvals(self, user: User) -> List[Approval]:
        """Get pending approvals for a user based on their role."""
        query = self.db.query(Approval).options(
            joinedload(Approval.event).joinedload(PlannedEvent.creator)
        ).filter(Approval.status == ApprovalStatus.PENDING)

        if user.role == UserRole.APPROVER_L1:
            query = query.filter(Approval.approval_level == 1)
        elif user.role == UserRole.APPROVER_L2:
            query = query.filter(Approval.approval_level == 2)
        elif user.role == UserRole.ADMIN:
            pass  # Admin can see all pending approvals
        else:
            return []  # Regular users cannot approve

        return query.all()

    def approve_event(
        self,
        event_id: UUID,
        approver: User,
        comments: Optional[str] = None,
    ) -> Optional[PlannedEvent]:
        """Approve an event at the current approval level."""
        event = self.db.query(PlannedEvent).filter(PlannedEvent.id == event_id).first()
        if not event:
            return None

        # Determine required approval level based on event status
        if event.status == EventStatus.SUBMITTED:
            required_level = 1
            next_status = EventStatus.APPROVED_L1
        elif event.status == EventStatus.APPROVED_L1:
            required_level = 2
            next_status = EventStatus.APPROVED_L2
        else:
            raise ValueError(f"Event cannot be approved in status: {event.status.value}")

        # Check user has permission for this approval level
        if not self._can_approve(approver, required_level):
            raise ValueError(f"User does not have permission for level {required_level} approval")

        # Find pending approval
        approval = (
            self.db.query(Approval)
            .filter(
                Approval.event_id == event_id,
                Approval.approval_level == required_level,
                Approval.status == ApprovalStatus.PENDING,
            )
            .first()
        )

        if not approval:
            raise ValueError("No pending approval found for this event")

        # Update approval record
        approval.approver_id = approver.id
        approval.status = ApprovalStatus.APPROVED
        approval.comments = comments
        approval.approved_at = datetime.utcnow()

        # Update event status
        event = self.event_service.change_status(
            event_id,
            next_status,
            approver.id,
            f"Approved by {approver.username}" + (f": {comments}" if comments else ""),
        )

        # If approved at L1, create L2 approval request
        if required_level == 1:
            l2_approval = Approval(
                event_id=event_id,
                approval_level=2,
                status=ApprovalStatus.PENDING,
            )
            self.db.add(l2_approval)

        self.db.commit()
        return event

    def reject_event(
        self,
        event_id: UUID,
        approver: User,
        comments: Optional[str] = None,
    ) -> Optional[PlannedEvent]:
        """Reject an event and return it to draft status."""
        event = self.db.query(PlannedEvent).filter(PlannedEvent.id == event_id).first()
        if not event:
            return None

        # Determine required approval level based on event status
        if event.status == EventStatus.SUBMITTED:
            required_level = 1
        elif event.status == EventStatus.APPROVED_L1:
            required_level = 2
        else:
            raise ValueError(f"Event cannot be rejected in status: {event.status.value}")

        # Check user has permission
        if not self._can_approve(approver, required_level):
            raise ValueError(f"User does not have permission for level {required_level} approval")

        # Find pending approval
        approval = (
            self.db.query(Approval)
            .filter(
                Approval.event_id == event_id,
                Approval.approval_level == required_level,
                Approval.status == ApprovalStatus.PENDING,
            )
            .first()
        )

        if not approval:
            raise ValueError("No pending approval found for this event")

        # Update approval record
        approval.approver_id = approver.id
        approval.status = ApprovalStatus.REJECTED
        approval.comments = comments
        approval.approved_at = datetime.utcnow()

        # Update event status to rejected (which can transition back to draft)
        event = self.event_service.change_status(
            event_id,
            EventStatus.REJECTED,
            approver.id,
            f"Rejected by {approver.username}" + (f": {comments}" if comments else ""),
        )

        self.db.commit()
        return event

    def _can_approve(self, user: User, level: int) -> bool:
        """Check if user can approve at given level."""
        if user.role == UserRole.ADMIN:
            return True
        if level == 1 and user.role in [UserRole.APPROVER_L1, UserRole.APPROVER_L2]:
            return True
        if level == 2 and user.role == UserRole.APPROVER_L2:
            return True
        return False
