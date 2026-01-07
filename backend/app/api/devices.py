from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.device import ExternalDevice, ExternalDeviceListResponse
from app.utils.external_api import external_device_api

router = APIRouter()


@router.get("", response_model=ExternalDeviceListResponse)
async def list_devices(
    search: Optional[str] = Query(None, description="Search by name, IP, or ID"),
    device_type: Optional[str] = Query(None, description="Filter by device type"),
    limit: int = Query(100, ge=1, le=500, description="Maximum devices to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    current_user: User = Depends(get_current_user),
):
    """
    List devices from external inventory API.

    If external API is not configured, returns mock data.
    """
    devices = await external_device_api.get_devices(
        search=search,
        device_type=device_type,
        limit=limit,
        offset=offset,
    )

    return ExternalDeviceListResponse(
        devices=devices,
        total=len(devices),
    )


@router.get("/search", response_model=ExternalDeviceListResponse)
async def search_devices(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(20, ge=1, le=100, description="Maximum devices to return"),
    current_user: User = Depends(get_current_user),
):
    """
    Search devices by name, IP, or ID.
    """
    devices = await external_device_api.get_devices(
        search=q,
        limit=limit,
    )

    return ExternalDeviceListResponse(
        devices=devices,
        total=len(devices),
    )
