"""
System status API routes
"""
from fastapi import APIRouter, HTTPException, Request
import logging
import psutil
from datetime import datetime
import os
import asyncio
from typing import Dict

from models.schemas import SystemStatus, SyncStatus
from core.database import check_db_connection
from core.jira import JiraClient

router = APIRouter()
logger = logging.getLogger(__name__)


async def check_jira_connections(jira_instances=None) -> Dict[str, bool]:
    """Check JIRA instance connectivity by calling /myself endpoint
    
    Args:
        jira_instances: Optional list of JIRA instance configurations.
                       If not provided, will fall back to environment variables.
    """
    results = {}
    
    if jira_instances:
        # Use dynamic instances from application
        for instance in jira_instances:
            instance_type = instance.get('instance_type', instance.get('type', 'unknown'))
            url = instance.get('url')
            username = instance.get('username')
            password = instance.get('password')
            enabled = instance.get('enabled', True)
            
            if not enabled:
                results[instance_type] = False
                continue
                
            if url and username and password:
                try:
                    client = JiraClient(url, username, password)
                    # Call lightweight endpoint
                    response = await asyncio.to_thread(client._make_request, 'GET', '/myself')
                    results[instance_type] = bool(response)
                except Exception as e:
                    logger.warning(f"JIRA {instance_type} health check failed: {e}")
                    results[instance_type] = False
            else:
                results[instance_type] = False
    else:
        # Fall back to legacy environment variables
        url_1 = os.getenv('JIRA_URL_1')
        username_1 = os.getenv('JIRA_USERNAME_1')
        password_1 = os.getenv('JIRA_PASSWORD_1')
        
        if url_1 and username_1 and password_1:
            try:
                client_1 = JiraClient(url_1, username_1, password_1)
                response = await asyncio.to_thread(client_1._make_request, 'GET', '/myself')
                results['instance_1'] = bool(response)
            except Exception as e:
                logger.warning(f"JIRA instance_1 health check failed: {e}")
                results['instance_1'] = False
        else:
            results['instance_1'] = False
        
        url_2 = os.getenv('JIRA_URL_2')
        username_2 = os.getenv('JIRA_USERNAME_2')
        password_2 = os.getenv('JIRA_PASSWORD_2')
        
        if url_2 and username_2 and password_2:
            try:
                client_2 = JiraClient(url_2, username_2, password_2)
                response = await asyncio.to_thread(client_2._make_request, 'GET', '/myself')
                results['instance_2'] = bool(response)
            except Exception as e:
                logger.warning(f"JIRA instance_2 health check failed: {e}")
                results['instance_2'] = False
        else:
            results['instance_2'] = False
    
    return results


@router.get("/system", response_model=SystemStatus)
async def get_system_status(request: Request):
    """Get overall system status"""
    try:
        # Check database connection
        db_connected = check_db_connection()
        
        # Check JIRA connections
        jira_instances = getattr(request.app.state, 'jira_instances', None)
        jira_status = await check_jira_connections(jira_instances)
        
        # Get sync status
        sync_manager = request.app.state.sync_manager
        if not sync_manager:
            raise HTTPException(status_code=500, detail="Sync manager not initialized")
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