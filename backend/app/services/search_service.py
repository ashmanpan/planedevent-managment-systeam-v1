"""
Search Service for advanced event queries.
"""

from datetime import date, time
from typing import Optional, List, Tuple
from uuid import UUID

from sqlalchemy import and_, or_, func
from sqlalchemy.orm import Session, joinedload

from app.models.event import PlannedEvent, EventStatus
from app.models.device import EventDevice
from app.models.user import User
from app.models.approval import Approval
from app.models.history import EventHistory


class SearchService:
    def __init__(self, db: Session):
        self.db = db

    def _base_query(self):
        """Create base query with all relationships loaded."""
        return self.db.query(PlannedEvent).options(
            joinedload(PlannedEvent.creator),
            joinedload(PlannedEvent.devices),
            joinedload(PlannedEvent.approvals).joinedload(Approval.approver),
            joinedload(PlannedEvent.history).joinedload(EventHistory.changed_by_user),
        )

    def _apply_sorting(self, query, sort_by: str, sort_order: str):
        """Apply sorting to query."""
        order_func = func.asc if sort_order == "asc" else func.desc

        if sort_by == "date":
            query = query.order_by(
                order_func(PlannedEvent.scheduled_date),
                order_func(PlannedEvent.start_time)
            )
        elif sort_by == "created":
            query = query.order_by(order_func(PlannedEvent.created_at))
        elif sort_by == "updated":
            query = query.order_by(order_func(PlannedEvent.updated_at))
        elif sort_by == "title":
            query = query.order_by(order_func(PlannedEvent.title))
        elif sort_by == "status":
            query = query.order_by(order_func(PlannedEvent.status))
        else:
            query = query.order_by(order_func(PlannedEvent.scheduled_date))

        return query

    def _paginate(self, query, page: int, limit: int) -> Tuple[list, int]:
        """Apply pagination and return results with total count."""
        # Get total count before pagination
        total = query.count()

        # Apply pagination
        offset = (page - 1) * limit
        results = query.offset(offset).limit(limit).all()

        return results, total

    def search_by_time_window(
        self,
        start_date: date,
        end_date: date,
        start_time: Optional[time] = None,
        end_time: Optional[time] = None,
        status: Optional[str] = None,
        sort_order: str = "asc",
        page: int = 1,
        limit: int = 50,
    ) -> Tuple[List[PlannedEvent], int]:
        """Search events within a time window."""
        query = self._base_query()

        # Date range filter
        query = query.filter(
            and_(
                PlannedEvent.scheduled_date >= start_date,
                PlannedEvent.scheduled_date <= end_date,
            )
        )

        # Time filter (optional)
        if start_time:
            query = query.filter(PlannedEvent.start_time >= start_time)
        if end_time:
            query = query.filter(PlannedEvent.end_time <= end_time)

        # Status filter
        if status:
            query = query.filter(PlannedEvent.status == status)

        # Sort by date and time
        query = self._apply_sorting(query, "date", sort_order)

        return self._paginate(query, page, limit)

    def search_by_device(
        self,
        device_id: Optional[str] = None,
        device_name: Optional[str] = None,
        device_ip: Optional[str] = None,
        device_type: Optional[str] = None,
        status: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        sort_by: str = "date",
        sort_order: str = "desc",
        page: int = 1,
        limit: int = 50,
    ) -> Tuple[List[PlannedEvent], int]:
        """Search events by device criteria."""
        # First, find matching event IDs based on device criteria
        device_query = self.db.query(EventDevice.event_id).distinct()

        if device_id:
            device_query = device_query.filter(EventDevice.device_id == device_id)
        if device_name:
            device_query = device_query.filter(
                EventDevice.device_name.ilike(f"%{device_name}%")
            )
        if device_ip:
            device_query = device_query.filter(
                EventDevice.device_ip.ilike(f"%{device_ip}%")
            )
        if device_type:
            device_query = device_query.filter(EventDevice.device_type == device_type)

        event_ids = [r[0] for r in device_query.all()]

        if not event_ids:
            return [], 0

        # Now query events
        query = self._base_query().filter(PlannedEvent.id.in_(event_ids))

        # Apply additional filters
        if status:
            query = query.filter(PlannedEvent.status == status)
        if start_date:
            query = query.filter(PlannedEvent.scheduled_date >= start_date)
        if end_date:
            query = query.filter(PlannedEvent.scheduled_date <= end_date)

        query = self._apply_sorting(query, sort_by, sort_order)

        return self._paginate(query, page, limit)

    def search_by_creator(
        self,
        creator_id: Optional[UUID] = None,
        creator_username: Optional[str] = None,
        status: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        sort_by: str = "date",
        sort_order: str = "desc",
        page: int = 1,
        limit: int = 50,
    ) -> Tuple[List[PlannedEvent], int]:
        """Search events by creator."""
        query = self._base_query()

        # Find user ID if username provided
        if creator_username and not creator_id:
            user = self.db.query(User).filter(
                User.username.ilike(f"%{creator_username}%")
            ).first()
            if user:
                creator_id = user.id
            else:
                return [], 0

        if creator_id:
            query = query.filter(PlannedEvent.created_by == creator_id)

        # Apply additional filters
        if status:
            query = query.filter(PlannedEvent.status == status)
        if start_date:
            query = query.filter(PlannedEvent.scheduled_date >= start_date)
        if end_date:
            query = query.filter(PlannedEvent.scheduled_date <= end_date)

        query = self._apply_sorting(query, sort_by, sort_order)

        return self._paginate(query, page, limit)

    def search_by_status(
        self,
        status: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        sort_by: str = "date",
        sort_order: str = "asc",
        page: int = 1,
        limit: int = 50,
    ) -> Tuple[List[PlannedEvent], int]:
        """Search events by status."""
        query = self._base_query().filter(PlannedEvent.status == status)

        if start_date:
            query = query.filter(PlannedEvent.scheduled_date >= start_date)
        if end_date:
            query = query.filter(PlannedEvent.scheduled_date <= end_date)

        query = self._apply_sorting(query, sort_by, sort_order)

        return self._paginate(query, page, limit)

    def advanced_search(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        start_time: Optional[time] = None,
        end_time: Optional[time] = None,
        statuses: Optional[List[str]] = None,
        device_id: Optional[str] = None,
        device_name: Optional[str] = None,
        device_ip: Optional[str] = None,
        device_type: Optional[str] = None,
        creator_id: Optional[UUID] = None,
        creator_username: Optional[str] = None,
        title_contains: Optional[str] = None,
        description_contains: Optional[str] = None,
        mop_contains: Optional[str] = None,
        sort_by: str = "date",
        sort_order: str = "desc",
        page: int = 1,
        limit: int = 50,
    ) -> Tuple[List[PlannedEvent], int]:
        """Advanced search with multiple filters combined."""
        query = self._base_query()

        # Date/time filters
        if start_date:
            query = query.filter(PlannedEvent.scheduled_date >= start_date)
        if end_date:
            query = query.filter(PlannedEvent.scheduled_date <= end_date)
        if start_time:
            query = query.filter(PlannedEvent.start_time >= start_time)
        if end_time:
            query = query.filter(PlannedEvent.end_time <= end_time)

        # Status filters
        if statuses:
            query = query.filter(PlannedEvent.status.in_(statuses))

        # Device filters - find event IDs first
        if any([device_id, device_name, device_ip, device_type]):
            device_query = self.db.query(EventDevice.event_id).distinct()

            if device_id:
                device_query = device_query.filter(EventDevice.device_id == device_id)
            if device_name:
                device_query = device_query.filter(
                    EventDevice.device_name.ilike(f"%{device_name}%")
                )
            if device_ip:
                device_query = device_query.filter(
                    EventDevice.device_ip.ilike(f"%{device_ip}%")
                )
            if device_type:
                device_query = device_query.filter(EventDevice.device_type == device_type)

            event_ids = [r[0] for r in device_query.all()]
            if not event_ids:
                return [], 0
            query = query.filter(PlannedEvent.id.in_(event_ids))

        # Creator filters
        if creator_id:
            query = query.filter(PlannedEvent.created_by == creator_id)
        elif creator_username:
            user = self.db.query(User).filter(
                User.username.ilike(f"%{creator_username}%")
            ).first()
            if user:
                query = query.filter(PlannedEvent.created_by == user.id)
            else:
                return [], 0

        # Text search filters
        if title_contains:
            query = query.filter(PlannedEvent.title.ilike(f"%{title_contains}%"))
        if description_contains:
            query = query.filter(PlannedEvent.description.ilike(f"%{description_contains}%"))
        if mop_contains:
            query = query.filter(PlannedEvent.mop_content.ilike(f"%{mop_contains}%"))

        # Apply sorting
        query = self._apply_sorting(query, sort_by, sort_order)

        return self._paginate(query, page, limit)

    def get_events_affecting_device(
        self,
        device_id: str,
        include_completed: bool = False,
    ) -> List[PlannedEvent]:
        """Get all events affecting a specific device."""
        device_query = self.db.query(EventDevice.event_id).filter(
            EventDevice.device_id == device_id
        )
        event_ids = [r[0] for r in device_query.all()]

        if not event_ids:
            return []

        query = self._base_query().filter(PlannedEvent.id.in_(event_ids))

        if not include_completed:
            query = query.filter(
                PlannedEvent.status.notin_([
                    EventStatus.COMPLETED,
                    EventStatus.REVERTED,
                ])
            )

        return query.order_by(PlannedEvent.scheduled_date, PlannedEvent.start_time).all()
