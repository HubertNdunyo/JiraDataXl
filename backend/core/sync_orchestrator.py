"""
Sync orchestrator that manages sync operations and state for the API layer.
"""
import uuid
import logging
from datetime import datetime
from typing import Optional, Dict
from fastapi import BackgroundTasks

from .sync_wrapper import get_sync_functions
from .db.db_sync_history import (
    create_sync_run,
    update_sync_run,
    get_latest_sync_run,
    record_performance_metric
)
from .cache import get_cache
from models.schemas import SyncProgress, SyncStatistics, SyncStatus

logger = logging.getLogger(__name__)


class SyncOrchestrator:
    """Orchestrates sync operations and manages state for API layer"""
    
    def __init__(self):
        self.current_sync_id: Optional[str] = None
        self.sync_start_time: Optional[datetime] = None
        self.sync_stats: Dict[str, SyncStatistics] = {}
        self._is_running = False
        self.sync_functions = get_sync_functions()
        
    @property
    def is_running(self) -> bool:
        """Check if sync is currently running"""
        return self._is_running and not self.sync_functions['is_sync_stopped']()
    
    def start_sync(self, background_tasks: BackgroundTasks, sync_type: str = 'manual', initiated_by: str = 'api') -> str:
        """Start a new sync operation"""
        if self.is_running:
            self.stop_sync()
        
        # Create sync run in database
        sync_id = create_sync_run(sync_type=sync_type, triggered_by=initiated_by)
        self.current_sync_id = sync_id
        self.sync_start_time = datetime.now()
        self._is_running = True
        
        # Add sync task to background
        background_tasks.add_task(self._run_sync, sync_id)
        
        logger.info(f"Started sync operation {sync_id}")
        return sync_id
    
    def _run_sync(self, sync_id: str):
        """Run the actual sync operation"""
        try:
            # Get the app instance to access statistics
            app = self.sync_functions['get_app']()
            
            # Reload performance configuration for this sync
            from core.config.performance_config import get_performance_config
            perf_config = get_performance_config()
            
            # Update the app's sync manager with new configuration
            if hasattr(app, 'sync_manager') and app.sync_manager:
                app.sync_manager.max_workers = perf_config['max_workers']
                app.sync_manager.project_timeout = perf_config['project_timeout']
                app.sync_manager.performance_config = perf_config
                logger.info(f"Sync using dynamic config: max_workers={perf_config['max_workers']}, "
                           f"project_timeout={perf_config['project_timeout']}s, "
                           f"batch_size={perf_config['batch_size']}, "
                           f"lookback_days={perf_config['lookback_days']}")
            
            # Run the existing sync logic
            success = self.sync_functions['fetch_all_issues']()
            
            # Get statistics from the app's last sync
            stats = None
            try:
                # The app should have sync stats after running
                if hasattr(app, 'sync_manager') and app.sync_manager:
                    stats = app.sync_manager.stats
            except Exception as e:
                logger.warning(f"Could not get sync stats from app: {e}")
            
            if success and stats:
                # Invalidate Redis cache after successful sync
                cache = get_cache()
                cache.invalidate_sync_cache()
                logger.info("Redis cache invalidated after successful sync")
                
                # Update database with actual statistics
                update_sync_run(
                    sync_id=sync_id,
                    status='completed',
                    total_issues=stats.total_issues,
                    issues_created=stats.total_created,
                    issues_updated=stats.total_updated,
                    issues_failed=0,
                    completed=True
                )
                
                # Record project-level details
                from core.db.db_sync_history import create_project_sync_record, update_project_sync_record
                
                # Process each project's results
                for project_key, duration in stats.processing_times.items():
                    try:
                        # Determine project status based on errors
                        project_status = 'failed' if project_key in stats.errors else 'completed'
                        error_msg = stats.errors.get(project_key, None)
                        
                        # Get the instance type for this project
                        instance_type = stats.project_instances.get(project_key, 'instance_1')
                        
                        # Create project sync record
                        project_id = create_project_sync_record(
                            sync_id=sync_id,
                            project_key=project_key,
                            instance=instance_type
                        )
                        
                        if project_id:
                            # Update with details
                            issues_count = stats.project_issues.get(project_key, 0)
                            created = stats.project_created.get(project_key, 0)
                            updated = stats.project_updated.get(project_key, 0)
                            update_project_sync_record(
                                project_sync_id=project_id,
                                status=project_status,
                                issues_processed=issues_count,
                                issues_created=created,
                                issues_updated=updated,
                                issues_failed=0,
                                error_message=error_msg,
                                completed=True
                            )
                            logger.debug(f"Recorded project sync details for {project_key}")
                    except Exception as e:
                        logger.error(f"Failed to record project details for {project_key}: {e}")
                
                # Record performance metrics
                record_performance_metric(
                    sync_id=sync_id,
                    metric_name='avg_project_time',
                    metric_value=sum(stats.processing_times.values()) / len(stats.processing_times) if stats.processing_times else 0,
                    metric_unit='seconds'
                )
                
                # Record additional performance metrics
                if stats.processing_times:
                    # Record min/max project times
                    record_performance_metric(
                        sync_id=sync_id,
                        metric_name='min_project_time',
                        metric_value=min(stats.processing_times.values()),
                        metric_unit='seconds'
                    )
                    record_performance_metric(
                        sync_id=sync_id,
                        metric_name='max_project_time',
                        metric_value=max(stats.processing_times.values()),
                        metric_unit='seconds'
                    )
                
                # Update in-memory stats
                end_time = datetime.now()
                duration = (end_time - self.sync_start_time).total_seconds()
                self.sync_stats[sync_id] = SyncStatistics(
                    sync_id=sync_id,
                    started_at=self.sync_start_time,
                    completed_at=end_time,
                    duration_seconds=duration,
                    total_projects=stats.successful_projects + stats.failed_projects + stats.empty_projects,
                    successful_projects=stats.successful_projects,
                    failed_projects=stats.failed_projects,
                    total_issues=stats.total_issues,
                    issues_created=stats.total_created,
                    issues_updated=stats.total_updated,
                    issues_failed=0,
                    issues_per_second=stats.total_issues/duration if duration > 0 else None,
                    status=SyncStatus.STOPPED,
                    error_message=None
                )
            elif success:
                # No stats available, use basic success
                update_sync_run(
                    sync_id=sync_id,
                    status='completed',
                    completed=True
                )
            else:
                # Update database with failure
                update_sync_run(
                    sync_id=sync_id,
                    status='failed',
                    error_message="Sync failed",
                    completed=True
                )
                
        except Exception as e:
            logger.error(f"Sync operation {sync_id} failed: {e}")
            
            # Update database with error
            update_sync_run(
                sync_id=sync_id,
                status='failed',
                error_message=str(e)[:1000],
                completed=True
            )
            
            # Update in-memory stats
            self.sync_stats[sync_id] = SyncStatistics(
                sync_id=sync_id,
                started_at=self.sync_start_time,
                completed_at=datetime.now(),
                duration_seconds=(datetime.now() - self.sync_start_time).total_seconds(),
                total_projects=0,
                successful_projects=0,
                failed_projects=0,
                total_issues=0,
                issues_created=0,
                issues_updated=0,
                issues_failed=0,
                issues_per_second=None,
                status=SyncStatus.FAILED,
                error_message=str(e)
            )
        finally:
            self._is_running = False
            self.current_sync_id = None
    
    def stop_sync(self):
        """Stop the current sync operation"""
        self.sync_functions['stop_sync']()
        self._is_running = False
        
        # Update database if we have a current sync
        if self.current_sync_id:
            update_sync_run(
                sync_id=self.current_sync_id,
                status='stopped',
                completed=True
            )
        
        logger.info("Sync operation stopped")
    
    def get_progress(self) -> SyncProgress:
        """Get current sync progress"""
        if not self.is_running:
            return SyncProgress(status=SyncStatus.IDLE)
        app = self.sync_functions['get_app']()
        if hasattr(app, 'sync_manager') and app.sync_manager:
            progress_data = app.sync_manager.get_progress()
            return SyncProgress(
                status=SyncStatus.RUNNING,
                current_project=progress_data['current_project'],
                total_projects=progress_data['total_projects'],
                current_issues=progress_data['current_issues'],
                total_issues=progress_data['total_issues'],
                progress_percentage=progress_data['progress_percentage'],
                started_at=progress_data['started_at'],
                updated_at=progress_data['updated_at']
            )
        return SyncProgress(status=SyncStatus.RUNNING, started_at=self.sync_start_time, updated_at=datetime.now())
    
    def get_status(self) -> SyncStatus:
        """Get current sync status"""
        if self.is_running:
            return SyncStatus.RUNNING
        elif self.sync_functions['is_sync_stopped']():
            return SyncStatus.STOPPED
        else:
            return SyncStatus.IDLE
    
    def get_sync_stats(self, sync_id: str) -> Optional[SyncStatistics]:
        """Get statistics for a specific sync operation"""
        return self.sync_stats.get(sync_id)
    
    def get_last_sync_stats(self) -> Optional[SyncStatistics]:
        """Get statistics for the last sync operation"""
        if not self.sync_stats:
            return None
        # Get the most recent sync
        return sorted(
            self.sync_stats.values(),
            key=lambda x: x.started_at,
            reverse=True
        )[0]
    
    def get_next_sync_time(self) -> Optional[datetime]:
        """Get the next scheduled sync time"""
        try:
            from main import scheduler as main_scheduler
            if main_scheduler:
                return main_scheduler.get_next_run_time()
        except Exception:
            pass
        return None
