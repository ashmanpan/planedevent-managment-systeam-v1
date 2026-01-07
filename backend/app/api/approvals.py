from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, require_approver
from app.models.user import User
from app.schemas.approval import ApprovalAction, ApprovalResponse, PendingApprovalResponse
from app.schemas.event import EventResponse
from app.services.approval_service import ApprovalService

router = APIRouter()


@router.get("/pending", response_model=List[PendingApprovalResponse])
def get_pending_approvals(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_approver),
):
    """Get pending approvals for the current user based on their role."""
    approval_service = ApprovalService(db)
    approvals = approval_service.get_pending_approvals(current_user)

    result = []
    for approval in approvals:
        result.append(
            PendingApprovalResponse(
                id=approval.id,
                event_id=approval.event_id,
                event_title=approval.event.title,
                event_scheduled_date=str(approval.event.scheduled_date),
                approval_level=approval.approval_level,
                status=approval.status,
                created_at=approval.created_at,
                creator_name=approval.event.creator.full_name or approval.event.creator.username,
            )
        )

    return result


@router.post("/{event_id}/approve", response_model=EventResponse)
def approve_event(
    event_id: UUID,
    action: ApprovalAction,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_approver),
):
    """Approve a planned event."""
    approval_service = ApprovalService(db)

    try:
        event = approval_service.approve_event(event_id, current_user, action.comments)
        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event not found",
            )
        return event
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/{event_id}/reject", response_model=EventResponse)
def reject_event(
    event_id: UUID,
    action: ApprovalAction,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_approver),
):
    """Reject a planned event."""
    approval_service = ApprovalService(db)

    try:
        event = approval_service.reject_event(event_id, current_user, action.comments)
        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event not found",
            )
        return event
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
