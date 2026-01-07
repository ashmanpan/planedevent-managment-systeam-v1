from datetime import datetime
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field


class DeviceCreate(BaseModel):
    device_id: str = Field(..., min_length=1, max_length=100)
    device_name: Optional[str] = Field(None, max_length=200)
    device_ip: Optional[str] = Field(None, max_length=45)
    device_type: Optional[str] = Field(None, max_length=50)
    device_location: Optional[str] = Field(None, max_length=100)


class DeviceResponse(BaseModel):
    id: UUID
    event_id: UUID
    device_id: str
    device_name: Optional[str]
    device_ip: Optional[str]
    device_type: Optional[str]
    device_location: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class DeviceBulkCreate(BaseModel):
    devices: List[DeviceCreate]


class ExternalDevice(BaseModel):
    id: str
    name: str
    ip: Optional[str] = None
    type: Optional[str] = None
    location: Optional[str] = None


class ExternalDeviceListResponse(BaseModel):
    devices: List[ExternalDevice]
    total: int
