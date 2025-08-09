"""
Automated sync scheduler for JIRA data synchronization.
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from concurrent.futures import ThreadPoolExecutor
import threading

from .sync_manager import SyncManager
from .db.db_sync_history import get_latest_sync_run
from models.schemas import SyncStatus

logger = logging.getLogger(__name__)


class SyncScheduler:
    """Manages automated sync scheduling"""
    
    def __init__(self, sync_manager: SyncManager):
        self.sync_manager = sync_manager
        self.scheduler = AsyncIOScheduler()
        self.job_id = "jira_sync_job"
        self.is_running = False
        self.thread_pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix="sync_scheduler")
        
    def load_config(self) -> Dict:
        """Load sync configuration from database"""
        try:
            from .db.db_config import get_configuration
            config = get_configuration('sync', 'scheduler')
            if config and config.get('value'):
                return config['value']
            return {"interval_minutes": 5, "enabled": True}  # Default config
        except Exception as e:
            logger.error(f"Failed to load sync config from database: {e}")
            return {"interval_minutes": 5, "enabled": True}
    
    def save_config(self, config: Dict):
        """Save sync configuration to database"""
        try:
            from .db.db_config import save_configuration
            save_configuration(
                config_type='sync',
                config_key='scheduler',
                config_value=config,
                user='scheduler'
            )
        except Exception as e:
            logger.error(f"Failed to save sync config to database: {e}")
    
    async def run_scheduled_sync(self):
        """Execute a scheduled sync"""
        try:
            logger.info("Starting scheduled sync...")
            
            # Check if sync is already running
            if self.sync_manager.is_running:
                logger.warning("Sync already in progress, skipping scheduled run")
                return
            
            # Check last sync time to avoid too frequent syncs
            last_sync = get_latest_sync_run()
            if last_sync:
                time_since_last = datetime.now() - last_sync['started_at']
                if time_since_last < timedelta(minutes=1):
                    logger.warning("Last sync was less than 1 minute ago, skipping")
                    return
            
            # Run sync in a separate thread to avoid blocking the event loop
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                self.thread_pool, 
                self._run_sync_in_thread
            )
            
        except Exception as e:
            logger.error(f"Failed to run scheduled sync: {e}")
    
    def _run_sync_in_thread(self):
        """Run sync in a separate thread to avoid blocking the main event loop"""
        try:
            # Create a new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Create a mock background tasks object for scheduled syncs
            class MockBackgroundTasks:
                def add_task(self, func, *args, **kwargs):
                    # Run synchronously in this thread
                    func(*args, **kwargs)
            
            background_tasks = MockBackgroundTasks()
            sync_id = self.sync_manager.start_sync(
                background_tasks=background_tasks,
                sync_type='scheduled',
                initiated_by='scheduler'
            )
            logger.info(f"Scheduled sync started with ID: {sync_id} in thread: {threading.current_thread().name}")
            
        except Exception as e:
            logger.error(f"Failed to run sync in thread: {e}")
        finally:
            # Clean up the event loop
            try:
                loop.close()
            except:
                pass
    
    def start(self):
        """Start the scheduler"""
        try:
            config = self.load_config()
            
            if not config.get('enabled', True):
                logger.info("Sync scheduler is disabled in config")
                return
            
            interval_minutes = config.get('interval_minutes', 5)
            
            # Remove existing job if any
            if self.scheduler.get_job(self.job_id):
                self.scheduler.remove_job(self.job_id)
            
            # Add new job with interval trigger
            self.scheduler.add_job(
                self.run_scheduled_sync,
                trigger=IntervalTrigger(minutes=interval_minutes),
                id=self.job_id,
                name="JIRA Sync Job",
                replace_existing=True,
                max_instances=1  # Prevent overlapping runs
            )
            
            # Start the scheduler
            if not self.scheduler.running:
                self.scheduler.start()
                self.is_running = True
                logger.info(f"Sync scheduler started with {interval_minutes} minute interval")
            
        except Exception as e:
            logger.error(f"Failed to start scheduler: {e}")
    
    def stop(self):
        """Stop the scheduler"""
        try:
            if self.scheduler.running:
                self.scheduler.shutdown(wait=False)
                self.is_running = False
                logger.info("Sync scheduler stopped")
            
            # Shutdown thread pool
            self.thread_pool.shutdown(wait=True, cancel_futures=True)
            logger.info("Thread pool shut down")
        except Exception as e:
            logger.error(f"Failed to stop scheduler: {e}")
    
    def update_interval(self, interval_minutes: int):
        """Update the sync interval"""
        try:
            config = self.load_config()
            config['interval_minutes'] = interval_minutes
            self.save_config(config)
            
            # Restart scheduler with new interval
            self.stop()
            self.start()
            
            logger.info(f"Sync interval updated to {interval_minutes} minutes")
        except Exception as e:
            logger.error(f"Failed to update interval: {e}")
    
    def enable(self):
        """Enable automated syncs"""
        config = self.load_config()
        config['enabled'] = True
        self.save_config(config)
        self.start()
    
    def disable(self):
        """Disable automated syncs"""
        config = self.load_config()
        config['enabled'] = False
        self.save_config(config)
        self.stop()
    
    def get_next_run_time(self) -> Optional[datetime]:
        """Get the next scheduled sync time"""
        try:
            job = self.scheduler.get_job(self.job_id)
            if job and job.next_run_time:
                return job.next_run_time
        except Exception as e:
            logger.error(f"Failed to get next run time: {e}")
        return None
    
    def get_status(self) -> Dict:
        """Get scheduler status"""
        config = self.load_config()
        return {
            "enabled": config.get('enabled', True),
            "interval_minutes": config.get('interval_minutes', 5),
            "is_running": self.is_running and self.scheduler.running,
            "next_run_time": self.get_next_run_time()
        }