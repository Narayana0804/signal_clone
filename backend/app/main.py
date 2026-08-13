"""FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db
from app.middleware import OriginProtectionMiddleware
from app.routers import (
    auth_router,
    contacts_router,
    conversations_router,
    health_router,
    users_router,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO if settings.is_production else logging.DEBUG,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan — startup and shutdown events."""
    # Startup
    logger.info("Starting Signal Clone backend...")
    logger.info("Environment: %s", settings.environment)

    # Ensure data directory exists for SQLite
    db_path = settings.database_path
    db_dir = Path(db_path).parent
    db_dir.mkdir(parents=True, exist_ok=True)
    logger.info("Database path: %s", db_path)

    # Initialize database (WAL mode, foreign keys)
    await init_db()
    logger.info("Database initialized")

    logger.info("Signal Clone backend started successfully")

    yield

    # Shutdown
    logger.info("Shutting down Signal Clone backend...")


app = FastAPI(
    title="Signal Clone API",
    description="A Signal-like messaging platform API",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# CSRF / Origin Protection Middleware
app.add_middleware(OriginProtectionMiddleware)

# Routers
app.include_router(health_router)
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(contacts_router)
app.include_router(conversations_router)
