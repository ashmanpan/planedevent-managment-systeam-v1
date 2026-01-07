import os
import aiofiles
from datetime import date
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.config import settings
from app.models.event import EventStatus
from app.models.user import User
from app.schemas.event import (
    EventCreate,
    EventUpdate,
    EventResponse,
    EventListResponse,
    EventStatusUpdate,
    EventHistoryResponse,
)
from app.schemas.device import DeviceCreate, DeviceResponse, DeviceBulkCreate
from app.services.event_service import EventService
from app.services.device_service import DeviceService
from app.utils.csv_parser import parse_device_csv

router = APIRouter()


@router.post("", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
def create_event(
    event_data: EventCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new planned event."""
    event_service = EventService(db)
    event = event_service.create_event(event_data, current_user.id)
    return event


@router.get("", response_model=EventListResponse)
def list_events(
    status: Optional[EventStatus] = Query(None, description="Filter by status"),
    start_date: Optional[date] = Query(None, description="Filter events from this date"),
    end_date: Optional[date] = Query(None, description="Filter events until this date"),
    created_by: Optional[UUID] = Query(None, description="Filter by creator user ID"),
    device_id: Optional[str] = Query(None, description="Filter by device ID"),
    device_name: Optional[str] = Query(None, description="Filter by device name (partial match)"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all planned events with optional filters."""
    event_service = EventService(db)
    events, total = event_service.get_events(
        status=status,
        start_date=start_date,
        end_date=end_date,
        created_by=created_by,
        device_id=device_id,
        device_name=device_name,
        page=page,
        limit=limit,
    )

    pages = (total + limit - 1) // limit

    return EventListResponse(
        items=events,
        total=total,
        page=page,
        limit=limit,
        pages=pages,
    )


@router.get("/{event_id}", response_model=EventResponse)
def get_event(
    event_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific planned event by ID."""
    event_service = EventService(db)
    event = event_service.get_event(event_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found",
        )
    return event


@router.put("/{event_id}", response_model=EventResponse)
def update_event(
    event_id: UUID,
    event_data: EventUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a planned event (only in draft status)."""
    event_service = EventService(db)
    event = event_service.get_event(event_id)

    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found",
        )

    if event.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own events",
        )

    try:
        updated_event = event_service.update_event(event_id, event_data, current_user.id)
        return updated_event
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_event(
    event_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a planned event (only in draft status)."""
    event_service = EventService(db)
    event = event_service.get_event(event_id)

    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found",
        )

    if event.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own events",
        )

    try:
        event_service.delete_event(event_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/{event_id}/submit", response_model=EventResponse)
def submit_event(
    event_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Submit event for approval."""
    event_service = EventService(db)
    event = event_service.get_event(event_id)

    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found",
        )

    if event.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only submit your own events",
        )

    try:
        updated_event = event_service.submit_for_approval(event_id, current_user.id)
        return updated_event
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/{event_id}/start", response_model=EventResponse)
def start_event(
    event_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Mark event as in progress."""
    event_service = EventService(db)

    try:
        event = event_service.change_status(
            event_id, EventStatus.IN_PROGRESS, current_user.id, "Event execution started"
        )
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


@router.post("/{event_id}/complete", response_model=EventResponse)
def complete_event(
    event_id: UUID,
    status_update: EventStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Mark event as completed."""
    event_service = EventService(db)

    try:
        event = event_service.change_status(
            event_id, EventStatus.COMPLETED, current_user.id, status_update.reason
        )
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


@router.post("/{event_id}/revert", response_model=EventResponse)
def revert_event(
    event_id: UUID,
    status_update: EventStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Mark event as reverted (rolled back)."""
    event_service = EventService(db)

    try:
        event = event_service.change_status(
            event_id, EventStatus.REVERTED, current_user.id, status_update.reason
        )
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


@router.post("/{event_id}/postpone", response_model=EventResponse)
def postpone_event(
    event_id: UUID,
    status_update: EventStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Postpone the event."""
    event_service = EventService(db)

    try:
        event = event_service.change_status(
            event_id, EventStatus.POSTPONED, current_user.id, status_update.reason
        )
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


@router.post("/{event_id}/defer", response_model=EventResponse)
def defer_event(
    event_id: UUID,
    status_update: EventStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Defer the event indefinitely."""
    event_service = EventService(db)

    try:
        event = event_service.change_status(
            event_id, EventStatus.DEFERRED, current_user.id, status_update.reason
        )
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


@router.get("/{event_id}/history", response_model=list[EventHistoryResponse])
def get_event_history(
    event_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get status change history for an event."""
    event_service = EventService(db)

    event = event_service.get_event(event_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found",
        )

    return event_service.get_history(event_id)


# Device management for events
@router.post("/{event_id}/devices", response_model=DeviceResponse, status_code=status.HTTP_201_CREATED)
def add_device_to_event(
    event_id: UUID,
    device_data: DeviceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Add a device to an event."""
    device_service = DeviceService(db)

    try:
        device = device_service.add_device_to_event(event_id, device_data)
        return device
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/{event_id}/devices/bulk", response_model=list[DeviceResponse], status_code=status.HTTP_201_CREATED)
def add_devices_bulk(
    event_id: UUID,
    devices_data: DeviceBulkCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Add multiple devices to an event."""
    device_service = DeviceService(db)

    try:
        devices = device_service.add_devices_bulk(event_id, devices_data.devices)
        return devices
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/{event_id}/devices/csv", response_model=list[DeviceResponse], status_code=status.HTTP_201_CREATED)
async def upload_devices_csv(
    event_id: UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Upload devices from CSV file."""
    if not file.filename.endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only CSV files are allowed",
        )

    content = await file.read()
    devices_data = parse_device_csv(content)

    if not devices_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid devices found in CSV",
        )

    device_service = DeviceService(db)

    try:
        devices = device_service.add_devices_bulk(event_id, devices_data)
        return devices
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.delete("/{event_id}/devices/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_device_from_event(
    event_id: UUID,
    device_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Remove a device from an event."""
    device_service = DeviceService(db)

    try:
        success = device_service.remove_device(event_id, device_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Device not found in event",
            )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# MOP file upload
@router.post("/{event_id}/mop/upload", response_model=EventResponse)
async def upload_mop(
    event_id: UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Upload MOP (Method of Procedure) document."""
    event_service = EventService(db)

    event = event_service.get_event(event_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found",
        )

    if event.status != EventStatus.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only upload MOP for events in draft status",
        )

    # Validate file size
    content = await file.read()
    if len(content) > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum size is {settings.MAX_UPLOAD_SIZE / 1024 / 1024}MB",
        )

    # Save file
    file_ext = os.path.splitext(file.filename)[1]
    file_name = f"{event_id}_mop{file_ext}"
    file_path = os.path.join(settings.UPLOAD_DIR, file_name)

    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

    async with aiofiles.open(file_path, "wb") as f:
        await f.write(content)

    # Update event with file path
    event = event_service.update_mop_file(event_id, file_path)
    return event


@router.get("/{event_id}/mop/download")
async def download_mop(
    event_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Download MOP document."""
    from fastapi.responses import FileResponse

    event_service = EventService(db)

    event = event_service.get_event(event_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found",
        )

    if not event.mop_file_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No MOP file uploaded for this event",
        )

    if not os.path.exists(event.mop_file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="MOP file not found on server",
        )

    return FileResponse(
        event.mop_file_path,
        filename=f"MOP_{event.title}{os.path.splitext(event.mop_file_path)[1]}",
    )
