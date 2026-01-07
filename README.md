# Planned Event Management System (PEMS)

A containerized system for managing network planned events with a 2-stage approval workflow, device management via external API, and comprehensive REST API for external integrations.

## Features

- **Event Management**: Create, update, and manage planned events with scheduling
- **Device Management**: Select devices from external inventory API, CSV upload, or manual entry
- **2-Stage Approval**: Level 1 and Level 2 approval workflow
- **MOP Documents**: Upload and manage Method of Procedure documents
- **Complete Lifecycle**: Draft → Submitted → Approved L1 → Approved L2 → In Progress → Completed/Reverted
- **REST API**: Comprehensive API for external system integration
- **Role-Based Access**: User, Approver L1, Approver L2, Admin roles

## Tech Stack

- **Backend**: Python FastAPI
- **Database**: PostgreSQL
- **Frontend**: HTML, CSS, JavaScript (vanilla)
- **Authentication**: JWT
- **Containerization**: Docker & Docker Compose

## Quick Start

### Prerequisites

- Docker and Docker Compose installed
- Git

### Setup

1. Clone the repository:
```bash
git clone https://github.com/ashmanpan/planedevent-managment-systeam-v1.git
cd planedevent-managment-systeam-v1
```

2. Copy environment file:
```bash
cp .env.example .env
```

3. Start the containers:
```bash
docker-compose up -d
```

4. Access the application:
- Frontend: http://localhost
- API Docs: http://localhost:8000/api/docs
- API ReDoc: http://localhost:8000/api/redoc

### Default Users (from seed data)

| Username | Password | Role |
|----------|----------|------|
| admin | password123 | Admin |
| approver1 | password123 | Approver L1 |
| approver2 | password123 | Approver L2 |
| user1 | password123 | User |

## API Documentation

The API documentation is auto-generated and available at:
- Swagger UI: `/api/docs`
- ReDoc: `/api/redoc`
- OpenAPI JSON: `/api/openapi.json`

### Key API Endpoints

#### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login and get JWT token
- `GET /api/v1/auth/me` - Get current user info

#### Events
- `GET /api/v1/events` - List events (with filters)
- `POST /api/v1/events` - Create event
- `GET /api/v1/events/{id}` - Get event details
- `PUT /api/v1/events/{id}` - Update event
- `DELETE /api/v1/events/{id}` - Delete event
- `POST /api/v1/events/{id}/submit` - Submit for approval
- `POST /api/v1/events/{id}/start` - Start execution
- `POST /api/v1/events/{id}/complete` - Mark completed

#### Query Parameters for Events
- `status` - Filter by status (draft, submitted, approved_l1, etc.)
- `start_date` / `end_date` - Filter by date range
- `created_by` - Filter by user ID
- `device_id` - Filter by device ID
- `device_name` - Filter by device name (partial match)
- `page` / `limit` - Pagination

#### Devices
- `GET /api/v1/devices` - List devices from external API
- `GET /api/v1/devices/search?q=query` - Search devices
- `POST /api/v1/events/{id}/devices` - Add device to event
- `POST /api/v1/events/{id}/devices/csv` - Upload devices via CSV

#### Approvals
- `GET /api/v1/approvals/pending` - Get pending approvals
- `POST /api/v1/approvals/{event_id}/approve` - Approve event
- `POST /api/v1/approvals/{event_id}/reject` - Reject event

### Search & Query API (for External Systems)

These endpoints return **full event details with MOP content**, devices, approvals, and history.

#### Search by Time Window
```
GET /api/v1/search/by-time-window?start_date=2024-01-01&end_date=2024-01-31
GET /api/v1/search/by-time-window?start_date=2024-01-15&end_date=2024-01-15&start_time=00:00&end_time=06:00
```

#### Search by Device
```
GET /api/v1/search/by-device?device_id=router-001
GET /api/v1/search/by-device?device_name=core-router
GET /api/v1/search/by-device?device_type=router&device_ip=10.0.0
```

#### Search by Creator/User
```
GET /api/v1/search/by-creator?creator_username=john
GET /api/v1/search/by-creator?creator_id=uuid-here
```

#### Search by Status
```
GET /api/v1/search/by-status?status=approved_l2
GET /api/v1/search/by-status?status=in_progress&start_date=2024-01-01
```

#### Convenience Endpoints
```
GET /api/v1/search/today                    # Events scheduled for today
GET /api/v1/search/upcoming?days=7          # Events in next 7 days
GET /api/v1/search/upcoming?days=30&status=approved_l2
```

#### Advanced Search (combine multiple filters)
```
GET /api/v1/search/advanced?device_name=router&status=approved_l2&start_date=2024-01-01
GET /api/v1/search/advanced?statuses=in_progress,approved_l2&creator_username=admin
GET /api/v1/search/advanced?mop_contains=backup&device_type=router
GET /api/v1/search/advanced?title_contains=upgrade&device_ip=10.0.0
```

#### Search Response Format
All search endpoints return full event details:
```json
{
  "items": [
    {
      "id": "uuid",
      "title": "Core Router Upgrade",
      "description": "Upgrade firmware on core routers",
      "scheduled_date": "2024-01-15",
      "start_time": "02:00:00",
      "end_time": "04:00:00",
      "scheduled_datetime_start": "2024-01-15T02:00:00",
      "scheduled_datetime_end": "2024-01-15T04:00:00",
      "config_changes": "Firmware upgrade from v1.2 to v1.3",
      "mop_content": "Step 1: Backup config\nStep 2: ...",
      "mop_file_available": true,
      "status": "approved_l2",
      "creator": {
        "id": "uuid",
        "username": "john",
        "full_name": "John Doe",
        "email": "john@example.com"
      },
      "devices": [
        {"device_id": "router-001", "device_name": "core-router-01", "device_ip": "10.0.0.1", "device_type": "router"}
      ],
      "device_count": 1,
      "approvals": [
        {"approval_level": 1, "status": "approved", "approver_username": "approver1", "comments": "Looks good"}
      ],
      "history": [
        {"previous_status": "draft", "new_status": "submitted", "changed_by_username": "john", "change_reason": "Ready for review"}
      ]
    }
  ],
  "total": 10,
  "page": 1,
  "limit": 50,
  "pages": 1,
  "filters_applied": {"start_date": "2024-01-01", "status": "approved_l2"}
}
```

#### Common Query Parameters
| Parameter | Description |
|-----------|-------------|
| `include_mop` | Include MOP content (default: true) |
| `sort_by` | Sort field: date, created, updated, title, status |
| `sort_order` | asc or desc |
| `page` | Page number (default: 1) |
| `limit` | Items per page (default: 50, max: 200) |

## Event Lifecycle

```
DRAFT → SUBMITTED → APPROVED_L1 → APPROVED_L2 → IN_PROGRESS → COMPLETED
                  ↓              ↓                          ↓
              REJECTED       REJECTED                 REVERTED
                  ↓              ↓                   POSTPONED
                DRAFT          DRAFT                  DEFERRED
```

## External Device API Integration

Configure external device inventory API in `.env`:

```
EXTERNAL_DEVICE_API_URL=https://inventory.example.com/api
EXTERNAL_DEVICE_API_KEY=your-api-key
```

If not configured, the system uses mock device data for testing.

## Development

### Run without Docker

1. Start PostgreSQL database

2. Install Python dependencies:
```bash
cd backend
pip install -r requirements.txt
```

3. Set environment variables and run:
```bash
export DATABASE_URL=postgresql://user:pass@localhost:5432/pems_db
uvicorn app.main:app --reload
```

### Database Migrations

```bash
cd backend
alembic revision --autogenerate -m "description"
alembic upgrade head
```

## Project Structure

```
├── docker-compose.yml
├── .env.example
├── README.md
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── alembic.ini
│   └── app/
│       ├── main.py
│       ├── config.py
│       ├── database.py
│       ├── models/
│       ├── schemas/
│       ├── api/
│       ├── services/
│       └── utils/
├── frontend/
│   ├── Dockerfile
│   ├── nginx.conf
│   └── public/
│       ├── index.html
│       ├── css/
│       ├── js/
│       └── pages/
└── scripts/
    ├── init-db.sql
    └── seed-data.sql
```

## License

MIT
