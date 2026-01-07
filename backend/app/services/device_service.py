from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.device import EventDevice
from app.models.event import PlannedEvent, EventStatus
from app.schemas.device import DeviceCreate


class DeviceService:
    def __init__(self, db: Session):
        self.db = db

    def add_device_to_event(self, event_id: UUID, device_data: DeviceCreate) -> EventDevice:
        # Verify event exists and is in draft status
        event = self.db.query(PlannedEvent).filter(PlannedEvent.id == event_id).first()
        if not event:
            raise ValueError("Event not found")
        if event.status != EventStatus.DRAFT:
            raise ValueError("Can only add devices to events in draft status")

        device = EventDevice(
            event_id=event_id,
            device_id=device_data.device_id,
            device_name=device_data.device_name,
            device_ip=device_data.device_ip,
            device_type=device_data.device_type,
            device_location=device_data.device_location,
        )
        self.db.add(device)
        self.db.commit()
        self.db.refresh(device)
        return device

    def add_devices_bulk(self, event_id: UUID, devices: List[DeviceCreate]) -> List[EventDevice]:
        # Verify event exists and is in draft status
        event = self.db.query(PlannedEvent).filter(PlannedEvent.id == event_id).first()
        if not event:
            raise ValueError("Event not found")
        if event.status != EventStatus.DRAFT:
            raise ValueError("Can only add devices to events in draft status")

        created_devices = []
        for device_data in devices:
            device = EventDevice(
                event_id=event_id,
                device_id=device_data.device_id,
                device_name=device_data.device_name,
                device_ip=device_data.device_ip,
                device_type=device_data.device_type,
                device_location=device_data.device_location,
            )
            self.db.add(device)
            created_devices.append(device)

        self.db.commit()
        for device in created_devices:
            self.db.refresh(device)

        return created_devices

    def get_devices_for_event(self, event_id: UUID) -> List[EventDevice]:
        return self.db.query(EventDevice).filter(EventDevice.event_id == event_id).all()

    def remove_device(self, event_id: UUID, device_id: str) -> bool:
        # Verify event exists and is in draft status
        event = self.db.query(PlannedEvent).filter(PlannedEvent.id == event_id).first()
        if not event:
            raise ValueError("Event not found")
        if event.status != EventStatus.DRAFT:
            raise ValueError("Can only remove devices from events in draft status")

        device = (
            self.db.query(EventDevice)
            .filter(EventDevice.event_id == event_id, EventDevice.device_id == device_id)
            .first()
        )
        if not device:
            return False

        self.db.delete(device)
        self.db.commit()
        return True

    def clear_devices(self, event_id: UUID) -> int:
        """Remove all devices from an event. Returns count of deleted devices."""
        event = self.db.query(PlannedEvent).filter(PlannedEvent.id == event_id).first()
        if not event:
            raise ValueError("Event not found")
        if event.status != EventStatus.DRAFT:
            raise ValueError("Can only clear devices from events in draft status")

        count = self.db.query(EventDevice).filter(EventDevice.event_id == event_id).delete()
        self.db.commit()
        return count
