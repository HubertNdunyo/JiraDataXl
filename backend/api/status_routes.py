"""
System status API routes
"""
from fastapi import APIRouter, HTTPException, Request
import logging
import psutil
from datetime import datetime
import sys
from pathlib import Path

# Add parent directory to import existing logic
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from models.schemas import SystemStatus, SyncStatus
from core.sync_manager import SyncManager
from core.database import check_db_connection

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize sync manager lazily
_sync_manager = None

def get_sync_manager():
    global _sync_manager
    if _sync_manager is None:
        from core.sync_manager import SyncManager
        _sync_manager = SyncManager()
    return _sync_manager


@router.get("/system", response_model=SystemStatus)
async def get_system_status(request: Request):
    """Get overall system status"""
    try:
        # Check database connection
        db_connected = check_db_connection()
        
        # Check JIRA connections
        jira_status = {
            "instance_1": True,  # TODO: Implement actual JIRA connection check
            "instance_2": True   # TODO: Implement actual JIRA connection check
        }
        
        # Get sync status
        sync_manager = get_sync_manager()
        sync_status = sync_manager.get_status()
        sync_progress = sync_manager.get_progress() if sync_status == SyncStatus.RUNNING else None
        last_sync = sync_manager.get_last_sync_stats()
        
        # Get next sync time from scheduler if available
        next_sync_time = None
        if hasattr(request.app.state, 'scheduler') and request.app.state.scheduler:
            next_sync_time = request.app.state.scheduler.get_next_run_time()
        
        # Determine overall health
        if not db_connected:
            health = "degraded"
        elif not all(jira_status.values()):
            health = "degraded"
        elif sync_status == SyncStatus.FAILED:
            health = "warning"
        else:
            health = "healthy"
        
        return SystemStatus(
            sync_status=sync_status,
            sync_progress=sync_progress,
            last_sync=last_sync,
            next_sync_time=next_sync_time,
            database_connected=db_connected,
            jira_instances_connected=jira_status,
            system_health=health
        )
    except Exception as e:
        logger.error(f"Failed to get system status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics")
async def get_system_metrics():
    """Get system performance metrics"""
    try:
        # Get CPU and memory usage
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Get process info
        process = psutil.Process()
        process_memory = process.memory_info()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "system": {
                "cpu_percent": cpu_percent,
                "memory": {
                    "total": memory.total,
                    "available": memory.available,
                    "percent": memory.percent
                },
                "disk": {
                    "total": disk.total,
                    "used": disk.used,
                    "free": disk.free,
                    "percent": disk.percent
                }
            },
            "process": {
                "memory_rss": process_memory.rss,
                "memory_vms": process_memory.vms,
                "cpu_percent": process.cpu_percent()
            }
        }
    except Exception as e:
        logger.error(f"Failed to get system metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))