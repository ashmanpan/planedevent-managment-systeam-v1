from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import api_router
from app.database import engine, Base

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Planned Event Management System",
    description="""
    A system for managing network planned events with 2-stage approval workflow.

    ## Features
    - Create and manage planned events with scheduling
    - Device management from external inventory API
    - CSV upload for bulk device import
    - MOP (Method of Procedure) document upload
    - 2-stage approval workflow
    - Complete event lifecycle management
    - RESTful API for external integrations
    """,
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api/v1")


@app.get("/")
def root():
    return {
        "message": "Planned Event Management System API",
        "version": "1.0.0",
        "docs": "/api/docs",
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}
