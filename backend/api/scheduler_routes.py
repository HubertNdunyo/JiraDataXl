"""
Scheduler management API routes
"""
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from typing import Optional
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


class SchedulerConfig(BaseModel):
    """Scheduler configuration model"""
    enabled: bool
    interval_minutes: int = Field(ge=2, le=1440, description="Sync interval in minutes (minimum 2)")


class SchedulerStatus(BaseModel):
    """Scheduler status response"""
    enabled: bool
    interval_minutes: int
    is_running: bool
    next_run_time: Optional[str] = None


@router.get("/status", response_model=SchedulerStatus)
async def get_scheduler_status(request: Request):
    """Get current scheduler status"""
    try:
        scheduler = request.app.state.scheduler
        if not scheduler:
            raise HTTPException(status_code=500, detail="Scheduler not initialized")
        
        status = scheduler.get_status()
        next_run = status.get('next_run_time')
        
        return SchedulerStatus(
            enabled=status['enabled'],
            interval_minutes=status['interval_minutes'],
            is_running=status['is_running'],
            next_run_time=next_run.isoformat() if next_run else None
        )
    except Exception as e:
        logger.error(f"Failed to get scheduler status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/config")
async def update_scheduler_config(config: SchedulerConfig, request: Request):
    """Update scheduler configuration"""
    try:
        scheduler = request.app.state.scheduler
        if not scheduler:
            raise HTTPException(status_code=500, detail="Scheduler not initialized")
        
        # Update interval (Pydantic already validates >= 2)
        if config.interval_minutes < 2:
            raise ValueError("Interval must be at least 2 minutes to prevent API rate limiting")
        
        scheduler.update_interval(config.interval_minutes)
        
        # Enable/disable scheduler
        if config.enabled:
            scheduler.enable()
        else:
            scheduler.disable()
        
        return {"success": True, "message": "Scheduler configuration updated"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to update scheduler config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/enable")
async def enable_scheduler(request: Request):
    """Enable the scheduler"""
    try:
        scheduler = request.app.state.scheduler
        if not scheduler:
            raise HTTPException(status_code=500, detail="Scheduler not initialized")
        
        scheduler.enable()
        return {"success": True, "message": "Scheduler enabled"}
    except Exception as e:
        logger.error(f"Failed to enable scheduler: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/disable")
async def disable_scheduler(request: Request):
    """Disable the scheduler"""
    try:
        scheduler = request.app.state.scheduler
        if not scheduler:
            raise HTTPException(status_code=500, detail="Scheduler not initialized")
        
        scheduler.disable()
        return {"success": True, "message": "Scheduler disabled"}
    except Exception as e:
        logger.error(f"Failed to disable scheduler: {e}")
        raise HTTPException(status_code=500, detail=str(e))


