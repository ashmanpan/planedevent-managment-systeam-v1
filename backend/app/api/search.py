"""
Enhanced Search and Query API for Planned Events.

Provides detailed endpoints for external systems to query events with full details
including MOP, devices, approvals, and history.
"""

from datetime import date, time, datetime
from typing import Optional, List
from uuid import UUID
from enum import Enum

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.services.event_service import EventService
from app.services.search_service import SearchService

router = APIRouter()


# Response Models for detailed queries
class DeviceDetail(BaseModel):
    device_id: str
    device_name: Optional[str]
    device_ip: Optional[str]
    device_type: Optional[str]
    device_location: Optional[str]

    class Config:
        from_attributes = True


class ApprovalDetail(BaseModel):
    approval_level: int
    status: str
    approver_username: Optional[str]
    approver_name: Optional[str]
    comments: Optional[str]
    approved_at: Optional[datetime]

    class Config:
        from_attributes = True


class HistoryDetail(BaseModel):
    previous_status: Optional[str]
    new_status: str
    changed_by_username: str
    changed_by_name: Optional[str]
    change_reason: Optional[str]
    changed_at: datetime

    class Config:
        from_attributes = True


class CreatorDetail(BaseModel):
    id: UUID
    username: str
    full_name: Optional[str]
    email: str

    class Config:
        from_attributes = True


class EventFullDetail(BaseModel):
    """Full event details including MOP, devices, approvals, and history."""
    id: UUID
    title: str
    description: Optional[str]
    scheduled_date: date
    start_time: time
    end_time: time
    scheduled_datetime_start: datetime
    scheduled_datetime_end: datetime
    config_changes: Optional[str]
    mop_content: Optional[str]
    mop_file_available: bool
    status: str
    creator: CreatorDetail
    devices: List[DeviceDetail]
    device_count: int
    approvals: List[ApprovalDetail]
    history: List[HistoryDetail]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class EventSummary(BaseModel):
    """Summary view of an event for listing."""
    id: UUID
    title: str
    description: Optional[str]
    scheduled_date: date
    start_time: time
    end_time: time
    status: str
    creator_username: str
    creator_name: Optional[str]
    device_count: int
    device_names: List[str]
    has_mop: bool
    created_at: datetime

    class Config:
        from_attributes = True


class SortOrder(str, Enum):
    ASC = "asc"
    DESC = "desc"


class SortField(str, Enum):
    DATE = "date"
    CREATED = "created"
    UPDATED = "updated"
    TITLE = "title"
    STATUS = "status"


class SearchResponse(BaseModel):
    items: List[EventSummary]
    total: int
    page: int
    limit: int
    pages: int
    filters_applied: dict


class DetailedSearchResponse(BaseModel):
    items: List[EventFullDetail]
    total: int
    page: int
    limit: int
    pages: int
    filters_applied: dict


# ============================================================================
# SEARCH ENDPOINTS
# ============================================================================

@router.get("/by-time-window", response_model=DetailedSearchResponse)
def search_by_time_window(
    start_date: date = Query(..., description="Start date of time window"),
    end_date: date = Query(..., description="End date of time window"),
    start_time: Optional[time] = Query(None, description="Start time filter (optional)"),
    end_time: Optional[time] = Query(None, description="End time filter (optional)"),
    status: Optional[str] = Query(None, description="Filter by status"),
    include_mop: bool = Query(True, description="Include MOP content in response"),
    sort_order: SortOrder = Query(SortOrder.ASC, description="Sort order"),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Search planned events within a specific time window.

    Returns full event details including MOP, sorted by scheduled date/time.

    Example:
    - GET /api/v1/search/by-time-window?start_date=2024-01-01&end_date=2024-01-31
    - GET /api/v1/search/by-time-window?start_date=2024-01-15&end_date=2024-01-15&start_time=00:00&end_time=06:00
    """
    search_service = SearchService(db)

    events, total = search_service.search_by_time_window(
        start_date=start_date,
        end_date=end_date,
        start_time=start_time,
        end_time=end_time,
        status=status,
        sort_order=sort_order.value,
        page=page,
        limit=limit,
    )

    items = [_build_full_detail(e, include_mop) for e in events]
    pages = (total + limit - 1) // limit if limit > 0 else 0

    return DetailedSearchResponse(
        items=items,
        total=total,
        page=page,
        limit=limit,
        pages=pages,
        filters_applied={
            "start_date": str(start_date),
            "end_date": str(end_date),
            "start_time": str(start_time) if start_time else None,
            "end_time": str(end_time) if end_time else None,
            "status": status,
        }
    )


@router.get("/by-device", response_model=DetailedSearchResponse)
def search_by_device(
    device_id: Optional[str] = Query(None, description="Exact device ID"),
    device_name: Optional[str] = Query(None, description="Device name (partial match)"),
    device_ip: Optional[str] = Query(None, description="Device IP address"),
    device_type: Optional[str] = Query(None, description="Device type"),
    status: Optional[str] = Query(None, description="Filter by event status"),
    start_date: Optional[date] = Query(None, description="Filter from date"),
    end_date: Optional[date] = Query(None, description="Filter to date"),
    include_mop: bool = Query(True, description="Include MOP content"),
    sort_by: SortField = Query(SortField.DATE, description="Sort field"),
    sort_order: SortOrder = Query(SortOrder.DESC, description="Sort order"),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Search planned events by affected device(s).

    Find all events that affect a specific device or devices matching criteria.

    Examples:
    - GET /api/v1/search/by-device?device_id=router-001
    - GET /api/v1/search/by-device?device_name=core-router
    - GET /api/v1/search/by-device?device_type=router&device_ip=10.0.0
    """
    if not any([device_id, device_name, device_ip, device_type]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one device filter is required (device_id, device_name, device_ip, or device_type)"
        )

    search_service = SearchService(db)

    events, total = search_service.search_by_device(
        device_id=device_id,
        device_name=device_name,
        device_ip=device_ip,
        device_type=device_type,
        status=status,
        start_date=start_date,
        end_date=end_date,
        sort_by=sort_by.value,
        sort_order=sort_order.value,
        page=page,
        limit=limit,
    )

    items = [_build_full_detail(e, include_mop) for e in events]
    pages = (total + limit - 1) // limit if limit > 0 else 0

    return DetailedSearchResponse(
        items=items,
        total=total,
        page=page,
        limit=limit,
        pages=pages,
        filters_applied={
            "device_id": device_id,
            "device_name": device_name,
            "device_ip": device_ip,
            "device_type": device_type,
            "status": status,
        }
    )


@router.get("/by-creator", response_model=DetailedSearchResponse)
def search_by_creator(
    creator_id: Optional[UUID] = Query(None, description="Creator user ID"),
    creator_username: Optional[str] = Query(None, description="Creator username"),
    status: Optional[str] = Query(None, description="Filter by event status"),
    start_date: Optional[date] = Query(None, description="Filter from date"),
    end_date: Optional[date] = Query(None, description="Filter to date"),
    include_mop: bool = Query(True, description="Include MOP content"),
    sort_by: SortField = Query(SortField.DATE, description="Sort field"),
    sort_order: SortOrder = Query(SortOrder.DESC, description="Sort order"),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Search planned events by creator/user.

    Find all events created by a specific user.

    Examples:
    - GET /api/v1/search/by-creator?creator_username=john
    - GET /api/v1/search/by-creator?creator_id=uuid-here
    """
    if not creator_id and not creator_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either creator_id or creator_username is required"
        )

    search_service = SearchService(db)

    events, total = search_service.search_by_creator(
        creator_id=creator_id,
        creator_username=creator_username,
        status=status,
        start_date=start_date,
        end_date=end_date,
        sort_by=sort_by.value,
        sort_order=sort_order.value,
        page=page,
        limit=limit,
    )

    items = [_build_full_detail(e, include_mop) for e in events]
    pages = (total + limit - 1) // limit if limit > 0 else 0

    return DetailedSearchResponse(
        items=items,
        total=total,
        page=page,
        limit=limit,
        pages=pages,
        filters_applied={
            "creator_id": str(creator_id) if creator_id else None,
            "creator_username": creator_username,
            "status": status,
        }
    )


@router.get("/by-status", response_model=DetailedSearchResponse)
def search_by_status(
    status: str = Query(..., description="Event status to filter"),
    start_date: Optional[date] = Query(None, description="Filter from date"),
    end_date: Optional[date] = Query(None, description="Filter to date"),
    include_mop: bool = Query(True, description="Include MOP content"),
    sort_by: SortField = Query(SortField.DATE, description="Sort field"),
    sort_order: SortOrder = Query(SortOrder.ASC, description="Sort order"),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Search planned events by status.

    Valid statuses: draft, submitted, approved_l1, approved_l2, in_progress,
    completed, rejected, reverted, postponed, deferred

    Examples:
    - GET /api/v1/search/by-status?status=approved_l2
    - GET /api/v1/search/by-status?status=in_progress&start_date=2024-01-01
    """
    search_service = SearchService(db)

    events, total = search_service.search_by_status(
        status=status,
        start_date=start_date,
        end_date=end_date,
        sort_by=sort_by.value,
        sort_order=sort_order.value,
        page=page,
        limit=limit,
    )

    items = [_build_full_detail(e, include_mop) for e in events]
    pages = (total + limit - 1) // limit if limit > 0 else 0

    return DetailedSearchResponse(
        items=items,
        total=total,
        page=page,
        limit=limit,
        pages=pages,
        filters_applied={
            "status": status,
            "start_date": str(start_date) if start_date else None,
            "end_date": str(end_date) if end_date else None,
        }
    )


@router.get("/upcoming", response_model=DetailedSearchResponse)
def get_upcoming_events(
    days: int = Query(7, ge=1, le=90, description="Number of days to look ahead"),
    status: Optional[str] = Query(None, description="Filter by status"),
    include_mop: bool = Query(True, description="Include MOP content"),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get upcoming planned events within the next N days.

    Sorted by scheduled date/time ascending.

    Examples:
    - GET /api/v1/search/upcoming?days=7
    - GET /api/v1/search/upcoming?days=30&status=approved_l2
    """
    from datetime import timedelta

    today = date.today()
    end_date = today + timedelta(days=days)

    search_service = SearchService(db)

    events, total = search_service.search_by_time_window(
        start_date=today,
        end_date=end_date,
        status=status,
        sort_order="asc",
        page=page,
        limit=limit,
    )

    items = [_build_full_detail(e, include_mop) for e in events]
    pages = (total + limit - 1) // limit if limit > 0 else 0

    return DetailedSearchResponse(
        items=items,
        total=total,
        page=page,
        limit=limit,
        pages=pages,
        filters_applied={
            "days_ahead": days,
            "from_date": str(today),
            "to_date": str(end_date),
            "status": status,
        }
    )


@router.get("/today", response_model=DetailedSearchResponse)
def get_todays_events(
    status: Optional[str] = Query(None, description="Filter by status"),
    include_mop: bool = Query(True, description="Include MOP content"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get all planned events scheduled for today.

    Sorted by start time ascending.
    """
    today = date.today()

    search_service = SearchService(db)

    events, total = search_service.search_by_time_window(
        start_date=today,
        end_date=today,
        status=status,
        sort_order="asc",
        page=1,
        limit=100,
    )

    items = [_build_full_detail(e, include_mop) for e in events]

    return DetailedSearchResponse(
        items=items,
        total=total,
        page=1,
        limit=100,
        pages=1,
        filters_applied={
            "date": str(today),
            "status": status,
        }
    )


@router.get("/advanced", response_model=DetailedSearchResponse)
def advanced_search(
    # Time filters
    start_date: Optional[date] = Query(None, description="Filter from date"),
    end_date: Optional[date] = Query(None, description="Filter to date"),
    start_time: Optional[time] = Query(None, description="Filter from time"),
    end_time: Optional[time] = Query(None, description="Filter to time"),
    # Status filter
    status: Optional[str] = Query(None, description="Filter by status"),
    statuses: Optional[str] = Query(None, description="Comma-separated list of statuses"),
    # Device filters
    device_id: Optional[str] = Query(None, description="Filter by device ID"),
    device_name: Optional[str] = Query(None, description="Filter by device name (partial)"),
    device_ip: Optional[str] = Query(None, description="Filter by device IP (partial)"),
    device_type: Optional[str] = Query(None, description="Filter by device type"),
    # Creator filters
    creator_id: Optional[UUID] = Query(None, description="Filter by creator ID"),
    creator_username: Optional[str] = Query(None, description="Filter by creator username"),
    # Text search
    title_contains: Optional[str] = Query(None, description="Title contains text"),
    description_contains: Optional[str] = Query(None, description="Description contains text"),
    mop_contains: Optional[str] = Query(None, description="MOP content contains text"),
    # Output options
    include_mop: bool = Query(True, description="Include MOP content"),
    sort_by: SortField = Query(SortField.DATE, description="Sort field"),
    sort_order: SortOrder = Query(SortOrder.DESC, description="Sort order"),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Advanced search with multiple filters combined.

    All filters are optional and can be combined.

    Examples:
    - GET /api/v1/search/advanced?device_name=router&status=approved_l2&start_date=2024-01-01
    - GET /api/v1/search/advanced?statuses=in_progress,approved_l2&creator_username=admin
    - GET /api/v1/search/advanced?mop_contains=backup&device_type=router
    """
    search_service = SearchService(db)

    # Parse comma-separated statuses
    status_list = None
    if statuses:
        status_list = [s.strip() for s in statuses.split(",")]
    elif status:
        status_list = [status]

    events, total = search_service.advanced_search(
        start_date=start_date,
        end_date=end_date,
        start_time=start_time,
        end_time=end_time,
        statuses=status_list,
        device_id=device_id,
        device_name=device_name,
        device_ip=device_ip,
        device_type=device_type,
        creator_id=creator_id,
        creator_username=creator_username,
        title_contains=title_contains,
        description_contains=description_contains,
        mop_contains=mop_contains,
        sort_by=sort_by.value,
        sort_order=sort_order.value,
        page=page,
        limit=limit,
    )

    items = [_build_full_detail(e, include_mop) for e in events]
    pages = (total + limit - 1) // limit if limit > 0 else 0

    return DetailedSearchResponse(
        items=items,
        total=total,
        page=page,
        limit=limit,
        pages=pages,
        filters_applied={
            "start_date": str(start_date) if start_date else None,
            "end_date": str(end_date) if end_date else None,
            "statuses": status_list,
            "device_id": device_id,
            "device_name": device_name,
            "creator_username": creator_username,
            "title_contains": title_contains,
        }
    )


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _build_full_detail(event, include_mop: bool = True) -> EventFullDetail:
    """Build full event detail response."""
    from datetime import datetime as dt

    # Build scheduled datetime
    scheduled_start = dt.combine(event.scheduled_date, event.start_time)
    scheduled_end = dt.combine(event.scheduled_date, event.end_time)

    # Build creator detail
    creator = CreatorDetail(
        id=event.creator.id,
        username=event.creator.username,
        full_name=event.creator.full_name,
        email=event.creator.email,
    )

    # Build device details
    devices = [
        DeviceDetail(
            device_id=d.device_id,
            device_name=d.device_name,
            device_ip=d.device_ip,
            device_type=d.device_type,
            device_location=d.device_location,
        )
        for d in event.devices
    ]

    # Build approval details
    approvals = []
    for a in event.approvals:
        approvals.append(ApprovalDetail(
            approval_level=a.approval_level,
            status=a.status.value if hasattr(a.status, 'value') else a.status,
            approver_username=a.approver.username if a.approver else None,
            approver_name=a.approver.full_name if a.approver else None,
            comments=a.comments,
            approved_at=a.approved_at,
        ))

    # Build history details
    history = []
    for h in event.history:
        history.append(HistoryDetail(
            previous_status=h.previous_status,
            new_status=h.new_status,
            changed_by_username=h.changed_by_user.username,
            changed_by_name=h.changed_by_user.full_name,
            change_reason=h.change_reason,
            changed_at=h.changed_at,
        ))

    return EventFullDetail(
        id=event.id,
        title=event.title,
        description=event.description,
        scheduled_date=event.scheduled_date,
        start_time=event.start_time,
        end_time=event.end_time,
        scheduled_datetime_start=scheduled_start,
        scheduled_datetime_end=scheduled_end,
        config_changes=event.config_changes,
        mop_content=event.mop_content if include_mop else None,
        mop_file_available=bool(event.mop_file_path),
        status=event.status.value if hasattr(event.status, 'value') else event.status,
        creator=creator,
        devices=devices,
        device_count=len(devices),
        approvals=approvals,
        history=history,
        created_at=event.created_at,
        updated_at=event.updated_at,
    )
