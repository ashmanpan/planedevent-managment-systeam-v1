from typing import Optional, List
import httpx

from app.config import settings
from app.schemas.device import ExternalDevice


class ExternalDeviceAPI:
    """Client for fetching devices from external inventory API."""

    def __init__(self):
        self.base_url = settings.EXTERNAL_DEVICE_API_URL
        self.api_key = settings.EXTERNAL_DEVICE_API_KEY

    @property
    def is_configured(self) -> bool:
        return bool(self.base_url)

    async def get_devices(
        self,
        search: Optional[str] = None,
        device_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[ExternalDevice]:
        """Fetch devices from external API."""
        if not self.is_configured:
            # Return mock data if external API is not configured
            return self._get_mock_devices(search, device_type, limit, offset)

        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        params = {"limit": limit, "offset": offset}
        if search:
            params["search"] = search
        if device_type:
            params["type"] = device_type

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/devices",
                    headers=headers,
                    params=params,
                    timeout=30.0,
                )
                response.raise_for_status()
                data = response.json()

                devices = []
                for item in data.get("devices", []):
                    devices.append(
                        ExternalDevice(
                            id=item.get("id"),
                            name=item.get("name"),
                            ip=item.get("ip"),
                            type=item.get("type"),
                            location=item.get("location"),
                        )
                    )
                return devices
            except httpx.HTTPError as e:
                # Log error and return empty list
                print(f"Error fetching devices from external API: {e}")
                return []

    def _get_mock_devices(
        self,
        search: Optional[str] = None,
        device_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[ExternalDevice]:
        """Return mock devices for testing when external API is not configured."""
        mock_devices = [
            ExternalDevice(id="dev-001", name="router-core-01", ip="10.0.0.1", type="router", location="DC1"),
            ExternalDevice(id="dev-002", name="router-core-02", ip="10.0.0.2", type="router", location="DC1"),
            ExternalDevice(id="dev-003", name="switch-dist-01", ip="10.0.1.1", type="switch", location="DC1"),
            ExternalDevice(id="dev-004", name="switch-dist-02", ip="10.0.1.2", type="switch", location="DC1"),
            ExternalDevice(id="dev-005", name="firewall-edge-01", ip="10.0.2.1", type="firewall", location="DC1"),
            ExternalDevice(id="dev-006", name="router-branch-01", ip="10.1.0.1", type="router", location="Branch1"),
            ExternalDevice(id="dev-007", name="switch-access-01", ip="10.1.1.1", type="switch", location="Branch1"),
            ExternalDevice(id="dev-008", name="router-branch-02", ip="10.2.0.1", type="router", location="Branch2"),
            ExternalDevice(id="dev-009", name="loadbalancer-01", ip="10.0.3.1", type="loadbalancer", location="DC1"),
            ExternalDevice(id="dev-010", name="wap-office-01", ip="10.0.4.1", type="wireless", location="Office"),
        ]

        # Apply filters
        filtered = mock_devices
        if search:
            search_lower = search.lower()
            filtered = [
                d for d in filtered
                if search_lower in d.name.lower() or search_lower in (d.ip or "") or search_lower in d.id.lower()
            ]
        if device_type:
            filtered = [d for d in filtered if d.type == device_type]

        # Apply pagination
        return filtered[offset : offset + limit]


# Singleton instance
external_device_api = ExternalDeviceAPI()
