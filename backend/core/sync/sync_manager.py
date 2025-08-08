"""
Sync process management and coordination.
"""

import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from ..jira import (
    JiraClient,
    IssueFetcher,
    FieldProcessor,
    JiraClientError,
    IssueProcessingError
)
from ..db import (
    get_all_project_mappings,
    batch_insert_issues,
    log_update,
    log_operation
)

# Configure logging
logger = logging.getLogger(__name__)

class SyncError(Exception):
    """Exception for sync-related errors"""
    pass

class SyncStatistics:
    """Class to track sync statistics"""
    
    def __init__(self):
        """Initialize statistics tracking."""
        self.successful_projects = 0
        self.empty_projects = 0
        self.failed_projects = 0
        self.skipped_projects = 0
        self.total_issues = 0
        self.processing_times: Dict[str, float] = {}
        self.errors: Dict[str, str] = {}
        self.project_issues: Dict[str, int] = {}  # Track issues per project
        self.project_instances: Dict[str, str] = {}  # Track which instance each project belongs to

    def add_project_result(
        self,
        project_key: str,
        status: str,
        duration: float,
        issues_count: int = 0,
        error: Optional[str] = None
    ):
        """Record project sync result."""
        self.processing_times[project_key] = duration
        
        if status == "Success":
            self.successful_projects += 1
            self.total_issues += issues_count
            self.project_issues[project_key] = issues_count
        elif status == "Empty":
            self.empty_projects += 1
            self.project_issues[project_key] = 0
        elif status == "Failed":
            self.failed_projects += 1
            self.project_issues[project_key] = 0
            if error:
                self.errors[project_key] = error

    def generate_report(self) -> str:
        """Generate a detailed sync report."""
        avg_time = (
            sum(self.processing_times.values()) / len(self.processing_times)
            if self.processing_times else 0
        )
        
        return f"""
Sync Summary:
-------------
Successful projects: {self.successful_projects}
Empty projects: {self.empty_projects}
Failed projects: {self.failed_projects}
Skipped projects: {self.skipped_projects}
Total issues processed: {self.total_issues}
Average processing time: {avg_time:.2f}s

Project Details:
---------------
{self._format_project_details()}

Errors:
-------
{self._format_errors()}
"""

    def _format_project_details(self) -> str:
        """Format project processing details."""
        details = []
        for project, duration in sorted(
            self.processing_times.items(),
            key=lambda x: x[1],
            reverse=True
        ):
            details.append(f"{project}: {duration:.2f}s")
        return "\n".join(details)

    def _format_errors(self) -> str:
        """Format error details."""
        if not self.errors:
            return "No errors reported"
        return "\n".join(
            f"{project}: {error}"
            for project, error in self.errors.items()
        )

class SyncManager:
    """
    Manages the synchronization process between JIRA and local database.
    """
    
    def __init__(
        self,
        jira_instances: List[Dict[str, str]],
        max_workers: int = 8,
        project_timeout: int = 300,
        field_config_path: Optional[str] = None,
        performance_config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize sync manager.
        
        Args:
            jira_instances: List of JIRA instance configurations
            max_workers: Maximum number of concurrent workers
            project_timeout: Timeout per project in seconds
            field_config_path: Path to field configuration file
            performance_config: Full performance configuration dict
        """
        from threading import Event
        self.jira_instances = jira_instances
        self.max_workers = max_workers
        self.project_timeout = project_timeout
        self.field_processor = FieldProcessor(field_config_path)
        self.stats = SyncStatistics()
        self._stop_event = Event()
        self._total_projects = 0
        self._completed_projects = 0
        
        # Store performance config for IssueFetcher
        self.performance_config = performance_config or {}

    def stop_sync(self):
        """Signal the sync process to stop gracefully."""
        logger.info("Stop signal received - waiting for current projects to complete...")
        self._stop_event.set()

    def is_stopped(self) -> bool:
        """Check if sync has been stopped."""
        return self._stop_event.is_set()

    def _update_progress(self):
        """Update and log sync progress."""
        self._completed_projects += 1
        if self._total_projects > 0:
            progress = (self._completed_projects / self._total_projects) * 100
            # Update global tracking variables
            global current_project, total_projects
            current_project = self._completed_projects
            total_projects = self._total_projects
            logger.info(
                f"Progress: {self._completed_projects}/{self._total_projects} "
                f"projects ({progress:.1f}%)"
            )

    def sync_all_projects(self) -> SyncStatistics:
        """
        Synchronize all projects across all JIRA instances.
        
        Returns:
            SyncStatistics object with sync results
            
        Raises:
            SyncError: If sync process fails
        """
        start_time = datetime.now()
        logger.info("Starting full sync process")
        self._stop_event.clear()
        self._completed_projects = 0
        self._total_projects = 0
        # Reset statistics for new sync
        self.stats = SyncStatistics()
        futures = []
        
        try:
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # First pass - count total projects
                for instance in self.jira_instances:
                    if self.is_stopped():
                        logger.info("Sync stopped by user")
                        break
                        
                    client = JiraClient(
                        url=instance['url'],
                        username=instance['username'],
                        password=instance['password']
                    )
                    
                    try:
                        projects = self._get_active_projects(client)
                        self._total_projects += len(projects)
                    except JiraClientError as e:
                        logger.error(
                            f"Error accessing JIRA instance {instance['url']}: {e}"
                        )
                
                if self._total_projects == 0:
                    logger.warning("No projects found to sync")
                    return self.stats
                
                logger.info(f"Found {self._total_projects} projects to sync")
                
                # Second pass - process projects
                for instance in self.jira_instances:
                    if self.is_stopped():
                        break
                        
                    client = JiraClient(
                        url=instance['url'],
                        username=instance['username'],
                        password=instance['password']
                    )
                    
                    try:
                        projects = self._get_active_projects(client)
                        
                        for project in projects:
                            if self.is_stopped():
                                break
                                
                            future = executor.submit(
                                self._sync_project,
                                client,
                                project['key'],
                                instance['instance_type']
                            )
                            futures.append((future, project['key'], instance['instance_type']))
                            
                    except JiraClientError as e:
                        logger.error(
                            f"Error accessing JIRA instance {instance['url']}: {e}"
                        )
                        continue
                
                # Process results with progress tracking
                completed_futures = []
                for future, project_key, instance_type in futures:
                    if self.is_stopped():
                        # Cancel any pending futures
                        for f, _, _ in futures:
                            if f not in completed_futures:
                                f.cancel()
                        break
                    
                    try:
                        result = future.result(timeout=self.project_timeout)
                        completed_futures.append(future)
                        status, duration, count, error = result
                        self.stats.add_project_result(
                            project_key,
                            status,
                            duration,
                            count,
                            error
                        )
                        # Track which instance this project belongs to
                        self.stats.project_instances[project_key] = instance_type
                        self._update_progress()
                    except Exception as e:
                        completed_futures.append(future)
                        logger.error(
                            f"Error processing project {project_key}: {e}"
                        )
                        self.stats.add_project_result(
                            project_key,
                            "Failed",
                            self.project_timeout,
                            error=str(e)
                        )
                        # Track instance even for failed projects
                        self.stats.project_instances[project_key] = instance_type
                        self._update_progress()
            
            # Log final report
            duration = (datetime.now() - start_time).total_seconds()
            status = "stopped by user" if self.is_stopped() else "completed"
            logger.info(f"Sync {status} in {duration:.2f}s")
            logger.info(self.stats.generate_report())
            
            return self.stats
            
        except Exception as e:
            logger.exception("Critical error in sync process")
            if not self.is_stopped():
                self.stop_sync()  # Ensure cleanup on error
            raise SyncError(f"Sync process failed: {e}")

    def _get_active_projects(self, client: JiraClient) -> List[Dict[str, str]]:
        """
        Get list of active projects to sync.
        
        Args:
            client: JIRA client instance
            
        Returns:
            List of project dictionaries
            
        Raises:
            SyncError: If project fetching fails
        """
        try:
            # Get all projects from JIRA without filtering
            return client.get_projects()
            
        except Exception as e:
            logger.error(f"Failed to get active projects: {e}")
            raise SyncError(f"Project fetching failed: {e}")

    def _sync_project(
        self,
        client: JiraClient,
        project_key: str,
        instance_type: str
    ) -> tuple:
        """
        Synchronize a single project.
        
        Args:
            client: JIRA client instance
            project_key: Project to sync
            instance_type: Type of JIRA instance
            
        Returns:
            Tuple of (status, duration, count, error)
        """
        start_time = datetime.now()
        
        try:
            # Create issue fetcher with field config and performance settings
            fetcher = IssueFetcher(
                client,
                batch_size=self.performance_config.get('batch_size', 200),
                lookback_days=self.performance_config.get('lookback_days', 60),
                field_config_path=self.field_processor.config_path
            )
            
            # Fetch and process issues
            issues_data = fetcher.fetch_project_issues(
                project_key,
                instance_type
            )
            
            if not issues_data:
                duration = (datetime.now() - start_time).total_seconds()
                log_update(project_key, "Empty", duration, 0)
                return "Empty", duration, 0, None
            
            # Process issues in batches
            processed_count = batch_insert_issues(issues_data)
            duration = (datetime.now() - start_time).total_seconds()
            
            # Log success
            log_update(project_key, "Success", duration, processed_count)
            log_operation(
                'SYNC',
                'PROJECT',
                project_key,
                details={
                    'issues_processed': processed_count,
                    'duration': duration
                }
            )
            
            return "Success", duration, processed_count, None
            
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            error_message = str(e)
            logger.exception(f"Error processing project {project_key}")
            
            log_update(project_key, "Failed", duration, 0, error_message)
            log_operation(
                'SYNC',
                'PROJECT',
                project_key,
                status='Failed',
                error_message=error_message
            )
            
            return "Failed", duration, 0, error_message