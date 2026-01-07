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
