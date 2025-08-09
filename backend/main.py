"""
FastAPI backend for JIRA Sync Dashboard MVP
"""
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
from pathlib import Path
from dotenv import load_dotenv
import logging

from api import sync_routes, issue_routes, config_routes, status_routes, admin_routes_v2, scheduler_routes
from models.schemas import HealthCheck
from core.database import init_db
from core.sync_orchestrator import SyncOrchestrator
from core.scheduler import SyncScheduler

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global instances
sync_manager = None
scheduler = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events"""
    global sync_manager, scheduler
    
    # Startup
    logger.info("Starting up FastAPI application...")
    init_db()
    
    # Initialize configuration tables
    try:
        from core.db.db_config import create_config_tables
        create_config_tables()
        logger.info("Configuration tables initialized")
    except Exception as e:
        logger.error(f"Failed to initialize config tables: {e}")
    
    # Initialize sync manager and scheduler
    try:
        sync_manager = SyncOrchestrator()
        scheduler = SyncScheduler(sync_manager)
        
        # Start scheduler if enabled
        scheduler.start()
        logger.info("Scheduler initialized and started")
        
        # Load JIRA instances configuration
        try:
            from core.app import Application
            temp_app = Application()
            jira_instances = temp_app.jira_instances
        except Exception as e:
            logger.warning(f"Could not load JIRA instances configuration: {e}")
            jira_instances = None
        
        # Make them available to routes
        app.state.sync_manager = sync_manager
        app.state.scheduler = scheduler
        app.state.jira_instances = jira_instances
    except Exception as e:
        logger.error(f"Failed to initialize scheduler: {e}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down FastAPI application...")
    if scheduler:
        scheduler.stop()
        logger.info("Scheduler stopped")


# Create FastAPI app
app = FastAPI(
    title="JIRA Sync Dashboard API",
    description="API for managing JIRA synchronization operations",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5648",
        "http://10.110.120.30:5648",
        "http://localhost:3000",  # fallback
        "*"  # Allow all origins for development
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(sync_routes.router, prefix="/api/sync", tags=["sync"])
app.include_router(issue_routes.router, prefix="/api/issues", tags=["issues"])
app.include_router(config_routes.router, prefix="/api/config", tags=["config"])
app.include_router(status_routes.router, prefix="/api/status", tags=["status"])
app.include_router(admin_routes_v2.router, prefix="/api/admin", tags=["admin"])
app.include_router(scheduler_routes.router, prefix="/api/scheduler", tags=["scheduler"])


@app.get("/", response_model=HealthCheck)
async def root():
    """Health check endpoint"""
    return HealthCheck(
        status="healthy",
        message="JIRA Sync Dashboard API is running"
    )


@app.get("/health", response_model=HealthCheck)
async def health_check():
    """Detailed health check"""
    # Check database connection
    try:
        # TODO: Add actual database health check
        return HealthCheck(
            status="healthy",
            message="All systems operational"
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unavailable")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="127.0.0.1",  # Listen only on localhost for security
        port=8987,
        reload=True
    )