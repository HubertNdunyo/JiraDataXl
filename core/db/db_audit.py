"""
Audit logging functionality for tracking database changes.
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from .db_core import execute_query, DatabaseError

# Configure logging
logger = logging.getLogger(__name__)

class AuditError(Exception):
    """Custom exception for audit operations"""
    pass

def create_audit_tables():
    """Create audit-related tables if they don't exist."""
    try:
        # Create update_log_v2 table
        execute_query("""
            CREATE TABLE IF NOT EXISTS update_log_v2 (
                id SERIAL PRIMARY KEY,
                project_key VARCHAR(255),
                last_update_time TIMESTAMP,
                status VARCHAR(50),
                duration NUMERIC,
                records_processed INTEGER,
                error_message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE INDEX IF NOT EXISTS idx_update_log_v2_project 
            ON update_log_v2(project_key);
            
            CREATE INDEX IF NOT EXISTS idx_update_log_v2_status 
            ON update_log_v2(status);
        """)

        # Create operation_log_v2 table for general operation logging
        execute_query("""
            CREATE TABLE IF NOT EXISTS operation_log_v2 (
                id SERIAL PRIMARY KEY,
                operation_type VARCHAR(50) NOT NULL,
                entity_type VARCHAR(50) NOT NULL,
                entity_id VARCHAR(255) NOT NULL,
                performed_by VARCHAR(255),
                performed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                details JSONB,
                status VARCHAR(50),
                duration NUMERIC,
                error_message TEXT
            );

            CREATE INDEX IF NOT EXISTS idx_operation_log_v2_type 
            ON operation_log_v2(operation_type, entity_type);
            
            CREATE INDEX IF NOT EXISTS idx_operation_log_v2_entity 
            ON operation_log_v2(entity_type, entity_id);
        """)
        
        logger.info("Audit tables created successfully")
        
    except DatabaseError as e:
        logger.error(f"Failed to create audit tables: {e}")
        raise AuditError(f"Table creation failed: {e}")

def log_update(
    project_key: str,
    status: str,
    duration: Optional[float] = None,
    records_processed: Optional[int] = None,
    error_message: Optional[str] = None
) -> bool:
    """
    Log a project update operation.
    
    Args:
        project_key: Project identifier
        status: Update status (Success/Failed/Empty)
        duration: Operation duration in seconds
        records_processed: Number of records processed
        error_message: Error message if operation failed
        
    Returns:
        bool: True if log was created successfully
    """
    try:
        execute_query("""
            INSERT INTO update_log_v2 
            (project_key, last_update_time, status, duration, records_processed, error_message)
            VALUES (%s, NOW(), %s, %s, %s, %s)
        """, (project_key, status, duration, records_processed, error_message))
        
        logger.info(f"Update log inserted for project {project_key} with status {status}")
        return True
        
    except DatabaseError as e:
        logger.error(f"Failed to log update for project {project_key}: {e}")
        return False

def log_operation(
    operation_type: str,
    entity_type: str,
    entity_id: str,
    performed_by: Optional[str] = None,
    details: Optional[Dict] = None,
    status: str = "Success",
    duration: Optional[float] = None,
    error_message: Optional[str] = None
) -> bool:
    """
    Log a general operation.
    
    Args:
        operation_type: Type of operation (Create/Update/Delete)
        entity_type: Type of entity (Project/Issue/Mapping)
        entity_id: Entity identifier
        performed_by: Username of performer
        details: Operation details
        status: Operation status
        duration: Operation duration in seconds
        error_message: Error message if operation failed
        
    Returns:
        bool: True if log was created successfully
    """
    try:
        execute_query("""
            INSERT INTO operation_log_v2 
            (operation_type, entity_type, entity_id, performed_by, details, 
             status, duration, error_message)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            operation_type,
            entity_type,
            entity_id,
            performed_by,
            json.dumps(details) if details else None,
            status,
            duration,
            error_message
        ))
        
        logger.info(f"Operation log created for {operation_type} on {entity_type} {entity_id}")
        return True
        
    except DatabaseError as e:
        logger.error(f"Failed to log operation: {e}")
        return False

def get_project_update_history(
    project_key: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
) -> List[Dict]:
    """
    Get update history for a project or all projects.
    
    Args:
        project_key: Project identifier (optional - if None, returns all projects)
        limit: Maximum number of records to return
        offset: Number of records to skip
        
    Returns:
        List of update log entries
    """
    try:
        if project_key:
            result = execute_query("""
                SELECT id, project_key, last_update_time, status, duration, 
                       records_processed, error_message
                FROM update_log_v2 
                WHERE project_key = %s
                ORDER BY last_update_time DESC
                LIMIT %s OFFSET %s
            """, (project_key, limit, offset), fetch=True)
        else:
            result = execute_query("""
                SELECT id, project_key, last_update_time, status, duration, 
                       records_processed, error_message
                FROM update_log_v2 
                ORDER BY last_update_time DESC
                LIMIT %s OFFSET %s
            """, (limit, offset), fetch=True)
        
        if result:
            columns = [
                'id', 'project_key', 'last_update_time', 'status', 'duration',
                'records_processed', 'error_message'
            ]
            return [dict(zip(columns, row)) for row in result]
        return []
        
    except DatabaseError as e:
        logger.error(f"Failed to get update history: {e}")
        raise AuditError(f"Failed to retrieve update history: {e}")

def get_entity_history(
    entity_type: str,
    entity_id: str,
    limit: int = 100,
    offset: int = 0
) -> List[Dict]:
    """
    Get operation history for an entity.
    
    Args:
        entity_type: Type of entity
        entity_id: Entity identifier
        limit: Maximum number of records to return
        offset: Number of records to skip
        
    Returns:
        List of operation log entries
    """
    try:
        result = execute_query("""
            SELECT operation_type, performed_by, performed_at, 
                   details, status, duration, error_message
            FROM operation_log_v2 
            WHERE entity_type = %s AND entity_id = %s
            ORDER BY performed_at DESC
            LIMIT %s OFFSET %s
        """, (entity_type, entity_id, limit, offset), fetch=True)
        
        if result:
            columns = [
                'operation_type', 'performed_by', 'performed_at',
                'details', 'status', 'duration', 'error_message'
            ]
            return [dict(zip(columns, row)) for row in result]
        return []
        
    except DatabaseError as e:
        logger.error(f"Failed to get history for {entity_type} {entity_id}: {e}")
        raise AuditError(f"Failed to retrieve entity history: {e}")

def cleanup_old_logs(days_to_keep: int = 90) -> int:
    """
    Clean up old log entries.
    
    Args:
        days_to_keep: Number of days of logs to retain
        
    Returns:
        int: Number of records deleted
    """
    try:
        # Delete old update logs
        update_result = execute_query("""
            DELETE FROM update_log_v2
            WHERE created_at < NOW() - INTERVAL '%s days'
            RETURNING id
        """, (days_to_keep,), fetch=True)
        
        # Delete old operation logs
        operation_result = execute_query("""
            DELETE FROM operation_log_v2
            WHERE performed_at < NOW() - INTERVAL '%s days'
            RETURNING id
        """, (days_to_keep,), fetch=True)
        
        total_deleted = len(update_result or []) + len(operation_result or [])
        logger.info(f"Cleaned up {total_deleted} old log entries")
        return total_deleted
        
    except DatabaseError as e:
        logger.error(f"Failed to clean up old logs: {e}")
        raise AuditError(f"Log cleanup failed: {e}")