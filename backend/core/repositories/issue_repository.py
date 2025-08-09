"""
Repository layer for issue-related database operations.
Separates data persistence from business logic.
"""

import logging
from typing import List, Dict, Any, Optional

from ..db.db_issues import batch_insert_issues
from ..db.db_audit import log_operation

logger = logging.getLogger(__name__)


class IssueRepository:
    """
    Repository for handling issue-related database operations.
    Provides a clean interface between business logic and data persistence.
    """
    
    def __init__(self):
        """Initialize the issue repository."""
        pass
    
    def batch_insert(self, issues: List[Dict[str, Any]]) -> int:
        """
        Insert multiple issues into the database.
        
        Args:
            issues: List of issue dictionaries to insert
            
        Returns:
            Number of issues successfully inserted
            
        Raises:
            DatabaseOperationError: If insertion fails
        """
        try:
            return batch_insert_issues(issues)
        except Exception as e:
            logger.error(f"Failed to batch insert issues: {e}")
            raise
    
    def log_update(
        self, 
        project_name: str, 
        status: str, 
        issues_count: int = 0, 
        error_message: Optional[str] = None
    ) -> None:
        """
        Log an update operation to the audit table.
        
        Args:
            project_name: Name of the project being updated
            status: Status of the update operation
            issues_count: Number of issues processed
            error_message: Optional error message if operation failed
        """
        try:
            log_operation('UPDATE', project_name, status, issues_count, error_message)
        except Exception as e:
            logger.error(f"Failed to log update operation: {e}")
            # Don't raise - logging failures shouldn't stop processing
    
    def log_sync_operation(
        self,
        operation_type: str,
        entity: str,
        status: str,
        count: int = 0,
        details: Optional[str] = None
    ) -> None:
        """
        Log a sync operation to the audit table.
        
        Args:
            operation_type: Type of operation (e.g., 'SYNC', 'UPDATE', 'DELETE')
            entity: Entity being operated on (e.g., project name, issue key)
            status: Status of the operation
            count: Number of entities affected
            details: Additional details about the operation
        """
        try:
            log_operation(operation_type, entity, status, count, details)
        except Exception as e:
            logger.error(f"Failed to log {operation_type} operation: {e}")
            # Don't raise - logging failures shouldn't stop processing
    
    def get_existing_issues(self, project_key: str) -> List[str]:
        """
        Get list of existing issue keys for a project.
        
        Args:
            project_key: The project key to query
            
        Returns:
            List of issue keys currently in the database
        """
        # This could be implemented if needed for incremental syncs
        # For now, returning empty list as batch_insert handles duplicates
        return []
    
    def update_issue(self, issue_key: str, data: Dict[str, Any]) -> bool:
        """
        Update a single issue in the database.
        
        Args:
            issue_key: The issue key to update
            data: Dictionary of fields to update
            
        Returns:
            True if update was successful, False otherwise
        """
        # This could be implemented if needed for single issue updates
        # For now, batch_insert with ON CONFLICT handles updates
        try:
            return batch_insert_issues([data]) == 1
        except Exception as e:
            logger.error(f"Failed to update issue {issue_key}: {e}")
            return False