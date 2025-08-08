"""
Database operations for sync history management.
"""
import uuid
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from contextlib import contextmanager

from .db_core import get_db_connection, DatabaseError

logger = logging.getLogger(__name__)


def create_sync_run(
    sync_type: str = 'manual',
    initiated_by: str = 'system'
) -> str:
    """
    Create a new sync run record.
    
    Args:
        sync_type: Type of sync (manual, scheduled, forced)
        initiated_by: User or system that initiated the sync
        
    Returns:
        sync_id: UUID of the created sync run
    """
    sync_id = str(uuid.uuid4())
    
    query = """
    INSERT INTO jira_sync.sync_runs (
        sync_id, started_at, status, sync_type, initiated_by
    ) VALUES (%s, %s, %s, %s, %s)
    """
    
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    query,
                    (sync_id, datetime.now(), 'running', sync_type, initiated_by)
                )
                conn.commit()
                logger.info(f"Created sync run {sync_id}")
                return sync_id
    except Exception as e:
        logger.error(f"Failed to create sync run: {e}")
        raise DatabaseError(f"Failed to create sync run: {e}")


def update_sync_run(
    sync_id: str,
    status: Optional[str] = None,
    total_projects: Optional[int] = None,
    successful_projects: Optional[int] = None,
    failed_projects: Optional[int] = None,
    empty_projects: Optional[int] = None,
    total_issues: Optional[int] = None,
    error_message: Optional[str] = None,
    completed: bool = False
) -> bool:
    """
    Update an existing sync run record.
    
    Args:
        sync_id: UUID of the sync run
        Various optional statistics to update
        completed: Whether the sync has completed
        
    Returns:
        bool: True if updated successfully
    """
    # Build dynamic update query
    updates = []
    params = []
    
    if status is not None:
        updates.append("status = %s")
        params.append(status)
    
    if total_projects is not None:
        updates.append("total_projects = %s")
        params.append(total_projects)
    
    if successful_projects is not None:
        updates.append("successful_projects = %s")
        params.append(successful_projects)
    
    if failed_projects is not None:
        updates.append("failed_projects = %s")
        params.append(failed_projects)
    
    if empty_projects is not None:
        updates.append("empty_projects = %s")
        params.append(empty_projects)
    
    if total_issues is not None:
        updates.append("total_issues = %s")
        params.append(total_issues)
    
    if error_message is not None:
        updates.append("error_message = %s")
        params.append(error_message[:1000])  # Truncate long error messages
    
    if completed:
        updates.append("completed_at = %s")
        params.append(datetime.now())
        updates.append("duration_seconds = EXTRACT(EPOCH FROM (%s - started_at))")
        params.append(datetime.now())
    
    if not updates:
        return True  # Nothing to update
    
    # Add sync_id to params
    params.append(sync_id)
    
    query = f"""
    UPDATE jira_sync.sync_runs 
    SET {', '.join(updates)}
    WHERE sync_id = %s
    """
    
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                conn.commit()
                return cursor.rowcount > 0
    except Exception as e:
        logger.error(f"Failed to update sync run {sync_id}: {e}")
        return False


def get_sync_history(
    limit: int = 20,
    offset: int = 0,
    status: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> Dict[str, Any]:
    """
    Get sync run history with pagination and filtering.
    
    Args:
        limit: Number of records to return
        offset: Number of records to skip
        status: Filter by status
        start_date: Filter by start date
        end_date: Filter by end date
        
    Returns:
        Dict containing total count and list of sync runs
    """
    # Build WHERE clause
    conditions = []
    params = []
    
    if status:
        conditions.append("status = %s")
        params.append(status)
    
    if start_date:
        conditions.append("started_at >= %s")
        params.append(start_date)
    
    if end_date:
        conditions.append("started_at <= %s")
        params.append(end_date)
    
    where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
    
    # Count query
    count_query = f"""
    SELECT COUNT(*) FROM jira_sync.sync_runs {where_clause}
    """
    
    # Data query
    data_query = f"""
    SELECT 
        sync_id,
        started_at,
        completed_at,
        duration_seconds,
        status,
        sync_type,
        total_projects,
        successful_projects,
        failed_projects,
        empty_projects,
        total_issues,
        error_message,
        initiated_by
    FROM jira_sync.sync_runs 
    {where_clause}
    ORDER BY started_at DESC
    LIMIT %s OFFSET %s
    """
    
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                # Get total count
                cursor.execute(count_query, params)
                total_count = cursor.fetchone()[0]
                
                # Get data
                cursor.execute(data_query, params + [limit, offset])
                columns = [desc[0] for desc in cursor.description]
                rows = cursor.fetchall()
                
                # Convert to list of dicts
                sync_runs = []
                for row in rows:
                    sync_run = dict(zip(columns, row))
                    sync_runs.append(sync_run)
                
                return {
                    'total': total_count,
                    'items': sync_runs,
                    'has_more': offset + limit < total_count
                }
                
    except Exception as e:
        logger.error(f"Failed to get sync history: {e}")
        raise DatabaseError(f"Failed to get sync history: {e}")


def get_sync_run_details(sync_id: str) -> Optional[Dict[str, Any]]:
    """
    Get detailed information for a specific sync run.
    
    Args:
        sync_id: UUID of the sync run
        
    Returns:
        Dict with sync run details or None if not found
    """
    query = """
    SELECT 
        sync_id,
        started_at,
        completed_at,
        duration_seconds,
        status,
        sync_type,
        total_projects,
        successful_projects,
        failed_projects,
        empty_projects,
        total_issues,
        error_message,
        initiated_by,
        created_at
    FROM jira_sync.sync_runs 
    WHERE sync_id = %s
    """
    
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (sync_id,))
                row = cursor.fetchone()
                
                if not row:
                    return None
                
                columns = [desc[0] for desc in cursor.description]
                return dict(zip(columns, row))
                
    except Exception as e:
        logger.error(f"Failed to get sync run details: {e}")
        raise DatabaseError(f"Failed to get sync run details: {e}")


def get_latest_sync_run() -> Optional[Dict[str, Any]]:
    """
    Get the most recent sync run.
    
    Returns:
        Dict with sync run details or None if no syncs exist
    """
    query = """
    SELECT 
        sync_id,
        started_at,
        completed_at,
        duration_seconds,
        status,
        sync_type,
        total_projects,
        successful_projects,
        failed_projects,
        empty_projects,
        total_issues,
        error_message,
        initiated_by
    FROM jira_sync.sync_runs 
    ORDER BY started_at DESC
    LIMIT 1
    """
    
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                row = cursor.fetchone()
                
                if not row:
                    return None
                
                columns = [desc[0] for desc in cursor.description]
                return dict(zip(columns, row))
                
    except Exception as e:
        logger.error(f"Failed to get latest sync run: {e}")
        return None


def cleanup_old_sync_runs(days_to_keep: int = 30) -> int:
    """
    Clean up old sync runs to prevent database bloat.
    
    Args:
        days_to_keep: Number of days of history to keep
        
    Returns:
        Number of records deleted
    """
    query = """
    DELETE FROM jira_sync.sync_runs 
    WHERE started_at < NOW() - INTERVAL '%s days'
    """
    
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (days_to_keep,))
                deleted_count = cursor.rowcount
                conn.commit()
                
                if deleted_count > 0:
                    logger.info(f"Cleaned up {deleted_count} old sync runs")
                
                return deleted_count
                
    except Exception as e:
        logger.error(f"Failed to cleanup old sync runs: {e}")
        return 0


# Project-level tracking functions

def get_sync_run_id(sync_id: str) -> Optional[int]:
    """
    Get the internal database ID for a sync run.
    
    Args:
        sync_id: UUID of the sync run
        
    Returns:
        Internal database ID or None if not found
    """
    query = "SELECT id FROM jira_sync.sync_runs WHERE sync_id = %s"
    
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (sync_id,))
                result = cursor.fetchone()
                return result[0] if result else None
    except Exception as e:
        logger.error(f"Failed to get sync run ID: {e}")
        return None


def create_project_sync_record(
    sync_id: str,
    project_key: str,
    instance: str
) -> Optional[int]:
    """
    Create a project sync record.
    
    Args:
        sync_id: UUID of the parent sync run
        project_key: JIRA project key
        instance: Which JIRA instance (instance_1 or instance_2)
        
    Returns:
        ID of created record or None if failed
    """
    # Get sync_run_id first
    sync_run_id = get_sync_run_id(sync_id)
    if not sync_run_id:
        logger.error(f"Sync run {sync_id} not found")
        return None
    
    query = """
    INSERT INTO jira_sync.sync_project_details (
        sync_run_id, project_key, instance, started_at, status
    ) VALUES (%s, %s, %s, %s, %s)
    RETURNING id
    """
    
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    query,
                    (sync_run_id, project_key, instance, datetime.now(), 'running')
                )
                conn.commit()
                result = cursor.fetchone()
                return result[0] if result else None
    except Exception as e:
        logger.error(f"Failed to create project sync record: {e}")
        return None


def update_project_sync_record(
    project_sync_id: int,
    status: Optional[str] = None,
    issues_processed: Optional[int] = None,
    issues_created: Optional[int] = None,
    issues_updated: Optional[int] = None,
    issues_failed: Optional[int] = None,
    error_message: Optional[str] = None,
    completed: bool = False
) -> bool:
    """
    Update a project sync record.
    
    Args:
        project_sync_id: ID of the project sync record
        Various optional statistics to update
        completed: Whether the project sync has completed
        
    Returns:
        bool: True if updated successfully
    """
    # Build dynamic update query
    updates = []
    params = []
    
    if status is not None:
        updates.append("status = %s")
        params.append(status)
    
    if issues_processed is not None:
        updates.append("issues_processed = %s")
        params.append(issues_processed)
    
    if issues_created is not None:
        updates.append("issues_created = %s")
        params.append(issues_created)
    
    if issues_updated is not None:
        updates.append("issues_updated = %s")
        params.append(issues_updated)
    
    if issues_failed is not None:
        updates.append("issues_failed = %s")
        params.append(issues_failed)
    
    if error_message is not None:
        updates.append("error_message = %s")
        params.append(error_message[:1000])
    
    if completed:
        updates.append("completed_at = %s")
        params.append(datetime.now())
        updates.append("duration_seconds = EXTRACT(EPOCH FROM (%s - started_at))")
        params.append(datetime.now())
    
    if not updates:
        return True
    
    params.append(project_sync_id)
    
    query = f"""
    UPDATE jira_sync.sync_project_details 
    SET {', '.join(updates)}
    WHERE id = %s
    """
    
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                conn.commit()
                return cursor.rowcount > 0
    except Exception as e:
        logger.error(f"Failed to update project sync record: {e}")
        return False


def get_project_sync_details(sync_id: str) -> List[Dict[str, Any]]:
    """
    Get project-level sync details for a sync run.
    
    Args:
        sync_id: UUID of the sync run
        
    Returns:
        List of project sync details
    """
    query = """
    SELECT 
        pd.project_key,
        pd.instance,
        pd.started_at,
        pd.completed_at,
        pd.duration_seconds,
        pd.status,
        pd.issues_processed,
        pd.issues_created,
        pd.issues_updated,
        pd.issues_failed,
        pd.error_message,
        pd.retry_count
    FROM jira_sync.sync_project_details pd
    JOIN jira_sync.sync_runs sr ON pd.sync_run_id = sr.id
    WHERE sr.sync_id = %s
    ORDER BY pd.started_at
    """
    
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (sync_id,))
                columns = [desc[0] for desc in cursor.description]
                rows = cursor.fetchall()
                
                return [dict(zip(columns, row)) for row in rows]
    except Exception as e:
        logger.error(f"Failed to get project sync details: {e}")
        return []


# Performance metrics functions

def record_performance_metric(
    sync_id: str,
    metric_name: str,
    metric_value: float,
    metric_unit: Optional[str] = None
) -> bool:
    """
    Record a performance metric for a sync run.
    
    Args:
        sync_id: UUID of the sync run
        metric_name: Name of the metric (e.g., 'api_response_time', 'db_write_speed')
        metric_value: Numeric value of the metric
        metric_unit: Optional unit (e.g., 'ms', 'issues/sec')
        
    Returns:
        bool: True if recorded successfully
    """
    sync_run_id = get_sync_run_id(sync_id)
    if not sync_run_id:
        return False
    
    query = """
    INSERT INTO jira_sync.sync_performance_metrics (
        sync_run_id, metric_name, metric_value, metric_unit
    ) VALUES (%s, %s, %s, %s)
    """
    
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (sync_run_id, metric_name, metric_value, metric_unit))
                conn.commit()
                return True
    except Exception as e:
        logger.error(f"Failed to record performance metric: {e}")
        return False


def get_performance_metrics(sync_id: str) -> List[Dict[str, Any]]:
    """
    Get all performance metrics for a sync run.
    
    Args:
        sync_id: UUID of the sync run
        
    Returns:
        List of performance metrics
    """
    query = """
    SELECT 
        metric_name,
        metric_value,
        metric_unit,
        recorded_at
    FROM jira_sync.sync_performance_metrics pm
    JOIN jira_sync.sync_runs sr ON pm.sync_run_id = sr.id
    WHERE sr.sync_id = %s
    ORDER BY pm.recorded_at
    """
    
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (sync_id,))
                columns = [desc[0] for desc in cursor.description]
                rows = cursor.fetchall()
                
                return [dict(zip(columns, row)) for row in rows]
    except Exception as e:
        logger.error(f"Failed to get performance metrics: {e}")
        return []