import csv
import io
from typing import List

from app.schemas.device import DeviceCreate


def parse_device_csv(file_content: bytes) -> List[DeviceCreate]:
    """
    Parse CSV file content and return list of DeviceCreate objects.

    Expected CSV format:
    device_id,device_name,device_ip,device_type,device_location
    dev-001,router-core-01,10.0.0.1,router,DC1
    """
    devices = []

    # Decode bytes to string
    content = file_content.decode("utf-8")

    # Create a CSV reader
    reader = csv.DictReader(io.StringIO(content))

    # Expected columns (with fallback names)
    id_columns = ["device_id", "id", "device-id", "deviceid"]
    name_columns = ["device_name", "name", "device-name", "devicename", "hostname"]
    ip_columns = ["device_ip", "ip", "ip_address", "ipaddress", "device-ip"]
    type_columns = ["device_type", "type", "device-type", "devicetype"]
    location_columns = ["device_location", "location", "device-location", "site"]

    def get_value(row: dict, columns: List[str]) -> str:
        """Get value from row using multiple possible column names."""
        for col in columns:
            if col in row and row[col]:
                return row[col].strip()
            # Try case-insensitive match
            for key in row.keys():
                if key.lower() == col.lower() and row[key]:
                    return row[key].strip()
        return None

    for row in reader:
        device_id = get_value(row, id_columns)

        if not device_id:
            continue  # Skip rows without device ID

        device = DeviceCreate(
            device_id=device_id,
            device_name=get_value(row, name_columns),
            device_ip=get_value(row, ip_columns),
            device_type=get_value(row, type_columns),
            device_location=get_value(row, location_columns),
        )
        devices.append(device)

    return devices
