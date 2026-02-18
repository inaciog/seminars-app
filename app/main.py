"""
Seminars App - FastAPI Application
"""

from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import create_db_and_tables
from app.routers import seminars, speakers, planning, files, external


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    create_db_and_tables()
    yield
    # Shutdown


settings = get_settings()

app = FastAPI(
    title="Seminars App",
    version="1.0.0",
    description="Seminar management system with unified authentication",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(seminars.router)
app.include_router(speakers.router)
app.include_router(planning.router)
app.include_router(files.router)
app.include_router(external.router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "Seminars App",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }
