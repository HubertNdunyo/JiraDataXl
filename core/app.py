"""
Main application class that coordinates all components.
"""

import os
import logging
from typing import Dict, List, Optional
from datetime import datetime
from dotenv import load_dotenv

from .db import initialize_database
from .jira import create_jira_client
from .sync import (
    create_sync_manager,
    create_status_manager,
    SyncStatistics
)

# Configure logging
logger = logging.getLogger(__name__)

class Application:
    """
    Main application class that coordinates database, JIRA, and sync operations.
    """
    
    def __init__(
        self,
        config_dir: str = 'config',
        max_workers: int = 8,
        project_timeout: int = 300
    ):
        """
        Initialize application.
        
        Args:
            config_dir: Directory containing configuration files
            max_workers: Maximum number of concurrent workers
            project_timeout: Timeout per project in seconds
        """
        self.config_dir = config_dir
        self.max_workers = max_workers
        self.project_timeout = project_timeout
        
        # Load environment variables
        load_dotenv()
        
        # Validate environment
        self._check_environment()
        
        # Initialize components
        self._initialize_components()

    def _check_environment(self):
        """Verify all required environment variables are set."""
        required_vars = [
            'DB_NAME', 'DB_USER', 'DB_PASSWORD', 'DB_HOST', 'DB_PORT',
            'JIRA_USERNAME_1', 'JIRA_PASSWORD_1',
            'JIRA_USERNAME_2', 'JIRA_PASSWORD_2'
        ]
        
        missing = [var for var in required_vars if not os.getenv(var)]
        
        if missing:
            raise EnvironmentError(
                f"Missing required environment variables: {', '.join(missing)}"
            )

    def _initialize_components(self):
        """Initialize all application components."""
        # Initialize database
        initialize_database()
        
        # Configure JIRA instances
        self.jira_instances = [
            {
                "url": "https://betteredits.atlassian.net",
                "username": os.getenv('JIRA_USERNAME_1'),
                "password": os.getenv('JIRA_PASSWORD_1'),
                "instance_type": "instance_1"
            },
            {
                "url": "https://betteredits2.atlassian.net",
                "username": os.getenv('JIRA_USERNAME_2'),
                "password": os.getenv('JIRA_PASSWORD_2'),
                "instance_type": "instance_2"
            }
        ]
        
        # Create managers
        self.sync_manager = create_sync_manager(
            jira_instances=self.jira_instances,
            max_workers=self.max_workers,
            project_timeout=self.project_timeout,
            field_config_path=os.path.join(
                self.config_dir,
                'field_mappings.json'
            )
        )
        
        self.status_manager = create_status_manager()

    def run_sync(self) -> SyncStatistics:
        """
        Run the sync process.
        
        Returns:
            SyncStatistics object with sync results
        """
        logger.info("Starting sync process")
        start_time = datetime.now()
        
        try:
            # Run sync
            stats = self.sync_manager.sync_all_projects()
            
            # Log completion
            duration = (datetime.now() - start_time).total_seconds()
            status = "stopped by user" if self.is_sync_stopped() else "completed"
            logger.info(f"Sync {status} in {duration:.2f}s")
            logger.info(stats.generate_report())
            
            return stats
            
        except Exception as e:
            logger.exception("Sync process failed")
            if not self.is_sync_stopped():
                self.stop_sync()  # Ensure cleanup on error
            raise

    def stop_sync(self):
        """Stop the current sync process gracefully."""
        logger.info("Stopping sync process...")
        self.sync_manager.stop_sync()

    def is_sync_stopped(self) -> bool:
        """Check if sync process has been stopped."""
        return self.sync_manager.is_stopped()

    def get_jira_client(
        self,
        instance_type: str
    ) -> Optional[Dict]:
        """
        Get configuration for a JIRA instance.
        
        Args:
            instance_type: Type of JIRA instance
            
        Returns:
            Dict containing instance configuration or None if not found
        """
        for instance in self.jira_instances:
            if instance['instance_type'] == instance_type:
                return create_jira_client(
                    url=instance['url'],
                    username=instance['username'],
                    password=instance['password']
                )
        return None

    @property
    def is_ready(self) -> bool:
        """Check if application is ready to run."""
        try:
            self._check_environment()
            return True
        except Exception:
            return False

def create_app(
    config_dir: str = 'config',
    max_workers: int = 8,
    project_timeout: int = 300
) -> Application:
    """
    Create and initialize application instance.
    
    Args:
        config_dir: Directory containing configuration files
        max_workers: Maximum number of concurrent workers
        project_timeout: Timeout per project in seconds
        
    Returns:
        Configured Application instance
    """
    return Application(
        config_dir=config_dir,
        max_workers=max_workers,
        project_timeout=project_timeout
    )