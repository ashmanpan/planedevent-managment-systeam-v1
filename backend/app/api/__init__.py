from fastapi import APIRouter

from app.api import auth, events, devices, approvals, users

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(events.router, prefix="/events", tags=["Events"])
api_router.include_router(devices.router, prefix="/devices", tags=["Devices"])
api_router.include_router(approvals.router, prefix="/approvals", tags=["Approvals"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
