"""
Sync module initialization and interface.

This module provides a clean interface to the synchronization functionality,
abstracting away the implementation details into separate modules.
"""

from .sync_worker import (
    SyncWorker,
    SyncStatistics,
    SyncError
)

from .status_manager import (
    StatusManager,
    StatusError
)

__all__ = [
    # Sync management
    'SyncWorker',
    'SyncStatistics',
    'SyncError',
    
    # Status management
    'StatusManager',
    'StatusError'
]

def create_sync_manager(
    jira_instances: list,
    max_workers: int = 8,
    project_timeout: int = 300,
    field_config_path: str = None,
    performance_config: dict = None
) -> SyncWorker:
    """
    Create a configured sync manager.
    
    Args:
        jira_instances: List of JIRA instance configurations
        max_workers: Maximum number of concurrent workers
        project_timeout: Timeout per project in seconds
        field_config_path: Path to field configuration file
        performance_config: Full performance configuration dict
        
    Returns:
        Configured SyncWorker instance
    """
    return SyncWorker(
        jira_instances=jira_instances,
        max_workers=max_workers,
        project_timeout=project_timeout,
        field_config_path=field_config_path,
        performance_config=performance_config
    )

def create_status_manager() -> StatusManager:
    """
    Create a configured status manager.
    
    Returns:
        Configured StatusManager instance
    """
    return StatusManager()

def initialize_sync():
    """
    Initialize sync system.
    
    This function should be called when the application starts
    to ensure all necessary sync components are initialized.
    """
    # Future initialization logic can be added here
    pass