"""
Sync operation API routes
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks, Request
from typing import Dict
import logging

from ..models.schemas import (
    SyncResponse,
    SyncStartRequest,
    SyncProgress,
    SyncHistoryFilter,
    SyncHistoryResponse,
    SyncStatistics,
    SyncStatus
)
from ..core.db.db_sync_history import (
    get_sync_history, 
    get_sync_run_details,
    get_project_sync_details,
    get_performance_metrics
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/start", response_model=SyncResponse)
async def start_sync(
    sync_request: SyncStartRequest,
    background_tasks: BackgroundTasks,
    request: Request
):
    """Start a new sync operation"""
    try:
        sync_manager = request.app.state.sync_manager
        if not sync_manager:
            raise HTTPException(status_code=500, detail="Sync manager not initialized")
        
        # Check if sync is already running
        if sync_manager.is_running and not sync_request.force:
            return SyncResponse(
                success=False,
                message="Sync is already running. Use force=true to override."
            )
        
        # Start sync in background
        sync_id = sync_manager.start_sync(background_tasks)
        
        return SyncResponse(
            success=True,
            message="Sync started successfully",
            sync_id=sync_id
        )
    except Exception as e:
        logger.error(f"Failed to start sync: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stop", response_model=SyncResponse)
async def stop_sync(request: Request):
    """Stop the current sync operation"""
    try:
        sync_manager = request.app.state.sync_manager
        if not sync_manager:
            raise HTTPException(status_code=500, detail="Sync manager not initialized")
        sync_manager.stop_sync()
        return SyncResponse(
            success=True,
            message="Sync stop requested"
        )
    except Exception as e:
        logger.error(f"Failed to stop sync: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/progress", response_model=SyncProgress)
async def get_sync_progress(request: Request):
    """Get current sync progress"""
    try:
        sync_manager = request.app.state.sync_manager
        if not sync_manager:
            raise HTTPException(status_code=500, detail="Sync manager not initialized")
        progress = sync_manager.get_progress()
        return progress
    except Exception as e:
        logger.error(f"Failed to get sync progress: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history", response_model=SyncHistoryResponse)
async def get_sync_history_endpoint(
    start_date: str = None,
    end_date: str = None,
    status: SyncStatus = None,
    limit: int = 20,
    offset: int = 0
):
    """Get sync operation history"""
    try:
        from datetime import datetime
        
        # Parse dates if provided
        start_dt = datetime.fromisoformat(start_date) if start_date else None
        end_dt = datetime.fromisoformat(end_date) if end_date else None
        
        # Get history from database
        result = get_sync_history(
            limit=limit,
            offset=offset,
            status=status.value if status else None,
            start_date=start_dt,
            end_date=end_dt
        )
        
        # Convert to response model
        items = []
        for sync_run in result['items']:
            items.append(SyncStatistics(
                sync_id=sync_run['sync_id'],
                started_at=sync_run['started_at'],
                completed_at=sync_run['completed_at'],
                duration_seconds=sync_run['duration_seconds'],
                total_projects=sync_run['total_projects'],
                successful_projects=sync_run['successful_projects'],
                failed_projects=sync_run['failed_projects'],
                total_issues=sync_run['total_issues'],
                issues_per_second=sync_run['total_issues'] / sync_run['duration_seconds'] 
                    if sync_run['duration_seconds'] and sync_run['duration_seconds'] > 0 else None,
                status=SyncStatus(sync_run['status']),
                error_message=sync_run['error_message']
            ))
        
        return SyncHistoryResponse(
            total=result['total'],
            items=items,
            has_more=result['has_more']
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {e}")
    except Exception as e:
        logger.error(f"Failed to get sync history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/summary")
async def get_sync_stats_summary():
    """Get aggregated sync statistics summary"""
    try:
        from datetime import datetime, timedelta
        
        # Get last 7 days of sync history
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        result = get_sync_history(
            limit=1000,  # Increased to handle more syncs
            offset=0,
            start_date=start_date,
            end_date=end_date
        )
        
        # Calculate summary statistics
        total_syncs = result['total']
        successful_syncs = sum(1 for sync in result['items'] if sync['status'] == 'completed')
        failed_syncs = sum(1 for sync in result['items'] if sync['status'] == 'failed')
        total_issues = sum(sync['total_issues'] for sync in result['items'])
        total_duration = sum(sync['duration_seconds'] or 0 for sync in result['items'])
        
        avg_duration = total_duration / total_syncs if total_syncs > 0 else 0
        success_rate = (successful_syncs / total_syncs * 100) if total_syncs > 0 else 0
        
        return {
            "period": "last_7_days",
            "total_syncs": total_syncs,
            "successful_syncs": successful_syncs,
            "failed_syncs": failed_syncs,
            "success_rate": round(success_rate, 2),
            "total_issues_processed": total_issues,
            "average_duration_seconds": round(avg_duration, 2),
            "last_sync": result['items'][0] if result['items'] else None
        }
    except Exception as e:
        logger.error(f"Failed to get stats summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/{sync_id}", response_model=SyncStatistics)
async def get_sync_stats(sync_id: str, request: Request):
    """Get statistics for a specific sync operation"""
    try:
        sync_manager = request.app.state.sync_manager
        if not sync_manager:
            raise HTTPException(status_code=500, detail="Sync manager not initialized")
        
        # First check in-memory stats
        stats = sync_manager.get_sync_stats(sync_id)
        if stats:
            return stats
        
        # If not in memory, check database
        sync_run = get_sync_run_details(sync_id)
        if not sync_run:
            raise HTTPException(status_code=404, detail="Sync operation not found")
        
        # Convert to SyncStatistics model
        return SyncStatistics(
            sync_id=sync_run['sync_id'],
            started_at=sync_run['started_at'],
            completed_at=sync_run['completed_at'],
            duration_seconds=sync_run['duration_seconds'],
            total_projects=sync_run['total_projects'],
            successful_projects=sync_run['successful_projects'],
            failed_projects=sync_run['failed_projects'],
            total_issues=sync_run['total_issues'],
            issues_per_second=sync_run['total_issues'] / sync_run['duration_seconds'] 
                if sync_run['duration_seconds'] and sync_run['duration_seconds'] > 0 else None,
            status=SyncStatus(sync_run['status']),
            error_message=sync_run['error_message']
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get sync stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/{sync_id}/projects")
async def get_sync_project_details(sync_id: str):
    """Get detailed project-level statistics for a sync operation"""
    try:
        projects = get_project_sync_details(sync_id)
        if not projects:
            # Check if sync exists
            sync_run = get_sync_run_details(sync_id)
            if not sync_run:
                raise HTTPException(status_code=404, detail="Sync operation not found")
        
        return {
            "sync_id": sync_id,
            "projects": projects,
            "total": len(projects)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get project details: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/{sync_id}/metrics")
async def get_sync_performance_metrics(sync_id: str):
    """Get performance metrics for a sync operation"""
    try:
        metrics = get_performance_metrics(sync_id)
        
        # Group metrics by name for easier consumption
        grouped_metrics = {}
        for metric in metrics:
            name = metric['metric_name']
            if name not in grouped_metrics:
                grouped_metrics[name] = []
            grouped_metrics[name].append({
                'value': metric['metric_value'],
                'unit': metric['metric_unit'],
                'recorded_at': metric['recorded_at']
            })
        
        return {
            "sync_id": sync_id,
            "metrics": grouped_metrics,
            "total_metrics": len(metrics)
        }
    except Exception as e:
        logger.error(f"Failed to get performance metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))