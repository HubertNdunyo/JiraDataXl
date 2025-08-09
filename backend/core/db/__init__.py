"""
Database module initialization and interface.

This module provides a clean interface to the database functionality,
abstracting away the implementation details into separate modules.
"""

from .db_core import (
    DatabaseOperationError,
    get_db_connection,
    execute_query,
    execute_batch,
    check_table_exists,
    get_column_names
)

# Alias for backward compatibility
DatabaseError = DatabaseOperationError

from .db_projects import (
    ProjectMappingError,
    create_project_tables,
    get_project_mapping,
    add_project_mapping,
    update_project_mapping,
    get_all_project_mappings,
    get_project_stats
)

from .db_issues import (
    IssueError,
    create_issues_table,
    batch_insert_issues,
    get_issue_by_key,
    get_project_issues,
    get_issues_since
)

from .db_audit import (
    AuditError,
    create_audit_tables,
    log_update,
    log_operation,
    get_project_update_history,
    get_entity_history,
    cleanup_old_logs
)

__all__ = [
    # Exceptions
    'DatabaseError',
    'ProjectMappingError',
    'IssueError',
    'AuditError',
    
    # Core database operations
    'get_db_connection',
    'execute_query',
    'execute_batch',
    'check_table_exists',
    'get_column_names',
    
    # Project operations
    'create_project_tables',
    'get_project_mapping',
    'add_project_mapping',
    'update_project_mapping',
    'get_all_project_mappings',
    'get_project_stats',
    
    # Issue operations
    'create_issues_table',
    'batch_insert_issues',
    'get_issue_by_key',
    'get_project_issues',
    'get_issues_since',
    
    # Audit operations
    'create_audit_tables',
    'log_update',
    'log_operation',
    'get_project_update_history',
    'get_entity_history',
    'cleanup_old_logs'
]

def initialize_database():
    """
    Initialize all database tables and required structures.
    
    This function should be called when the application starts
    to ensure all necessary database objects exist.
    """
    create_project_tables()
    create_issues_table()
    create_audit_tables()