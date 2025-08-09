"""
Main application class that coordinates all components.
"""

import os
import json
import logging
from typing import Dict, List, Optional
from datetime import datetime
from dotenv import load_dotenv
from pathlib import Path

from .db import initialize_database
from .jira import create_jira_client
from .sync import (
    create_sync_manager,
    create_status_manager,
    SyncStatistics
)
from .config.performance_config import get_performance_config

# Configure logging
logger = logging.getLogger(__name__)

class Application:
    """
    Main application class that coordinates database, JIRA, and sync operations.
    """
    
    def __init__(
        self,
        config_dir: str = 'config',
        max_workers: Optional[int] = None,
        project_timeout: Optional[int] = None
    ):
        """
        Initialize application.
        
        Args:
            config_dir: Directory containing configuration files
            max_workers: Maximum number of concurrent workers (overrides DB config)
            project_timeout: Timeout per project in seconds (overrides DB config)
        """
        # Load environment variables
        load_dotenv()
        
        # Validate environment
        self._check_environment()
        
        # Load performance configuration from database
        perf_config = get_performance_config()
        
        # Set configuration (use provided values or database values)
        self.config_dir = config_dir
        self.max_workers = max_workers if max_workers is not None else perf_config['max_workers']
        self.project_timeout = project_timeout if project_timeout is not None else perf_config['project_timeout']
        
        # Store full performance config for reference
        self.performance_config = perf_config
        
        logger.info(f"Using performance config: max_workers={self.max_workers}, project_timeout={self.project_timeout}s")
        
        # Initialize components
        self._initialize_components()

    def _check_environment(self):
        """Verify all required environment variables are set."""
        required_vars = [
            'DB_NAME', 'DB_USER', 'DB_PASSWORD', 'DB_HOST', 'DB_PORT'
        ]
        
        missing = [var for var in required_vars if not os.getenv(var)]
        
        if missing:
            raise EnvironmentError(
                f"Missing required environment variables: {', '.join(missing)}"
            )
        
        # Check for JIRA instances configuration
        if not os.getenv('JIRA_INSTANCES') and not self._has_legacy_jira_config():
            raise EnvironmentError(
                "JIRA instances not configured. Either set JIRA_INSTANCES environment variable "
                "or provide legacy JIRA_URL_1/2, JIRA_USERNAME_1/2, JIRA_PASSWORD_1/2 variables."
            )
    
    def _has_legacy_jira_config(self) -> bool:
        """Check if legacy JIRA configuration exists."""
        return all([
            os.getenv('JIRA_URL_1'), os.getenv('JIRA_USERNAME_1'), os.getenv('JIRA_PASSWORD_1'),
            os.getenv('JIRA_URL_2'), os.getenv('JIRA_USERNAME_2'), os.getenv('JIRA_PASSWORD_2')
        ])

    def _initialize_components(self):
        """Initialize all application components."""
        # Initialize database
        initialize_database()
        
        # Configure JIRA instances
        self.jira_instances = self._load_jira_instances()
        
        # Create managers
        self.sync_manager = create_sync_manager(
            jira_instances=self.jira_instances,
            max_workers=self.max_workers,
            project_timeout=self.project_timeout,
            field_config_path=os.path.join(
                self.config_dir,
                'field_mappings.json'
            ),
            performance_config=self.performance_config
        )
        
        self.status_manager = create_status_manager()
    
    def reload_performance_config(self):
        """Reload performance configuration from database"""
        perf_config = get_performance_config()
        
        # Update application settings
        self.max_workers = perf_config['max_workers']
        self.project_timeout = perf_config['project_timeout']
        self.performance_config = perf_config
        
        # Update sync manager if it exists
        if hasattr(self, 'sync_manager') and self.sync_manager:
            self.sync_manager.max_workers = perf_config['max_workers']
            self.sync_manager.project_timeout = perf_config['project_timeout']
            self.sync_manager.performance_config = perf_config
        
        logger.info(f"Reloaded performance config: max_workers={self.max_workers}, "
                    f"project_timeout={self.project_timeout}s")

    def run_sync(self) -> SyncStatistics:
        """
        Run the sync process.
        
        Returns:
            SyncStatistics object with sync results
        """
        # Reload configuration before each sync
        self.reload_performance_config()
        
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

    def _load_jira_instances(self) -> List[Dict]:
        """Load JIRA instances configuration from environment or config file."""
        # First, try to load from JIRA_INSTANCES environment variable
        jira_instances_env = os.getenv('JIRA_INSTANCES')
        if jira_instances_env:
            try:
                # JIRA_INSTANCES should be a JSON array of instance objects
                instances_data = json.loads(jira_instances_env)
                if isinstance(instances_data, list):
                    instances = []
                    for idx, inst in enumerate(instances_data):
                        instances.append({
                            "url": inst.get('url'),
                            "username": inst.get('username'),
                            "password": inst.get('api_token') or inst.get('password'),
                            "instance_type": inst.get('type', f'instance_{idx+1}'),
                            "name": inst.get('name', f'Instance {idx+1}'),
                            "enabled": inst.get('enabled', True)
                        })
                    logger.info(f"Loaded {len(instances)} JIRA instances from JIRA_INSTANCES environment variable")
                    return instances
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JIRA_INSTANCES JSON: {e}")
        
        # Second, try to load from config file if specified
        config_file_path = os.getenv('JIRA_CONFIG_FILE')
        if config_file_path:
            config_path = Path(config_file_path)
            if config_path.exists():
                try:
                    with open(config_path, 'r') as f:
                        config_data = json.load(f)
                        instances = []
                        for inst in config_data.get('instances', []):
                            if inst.get('enabled', True):
                                instances.append({
                                    "url": inst.get('url'),
                                    "username": inst.get('username'),
                                    "password": inst.get('api_token') or inst.get('password'),
                                    "instance_type": inst.get('id') or inst.get('type'),
                                    "name": inst.get('name', 'JIRA Instance'),
                                    "enabled": True
                                })
                        logger.info(f"Loaded {len(instances)} JIRA instances from config file: {config_file_path}")
                        return instances
                except Exception as e:
                    logger.error(f"Failed to load JIRA config file {config_file_path}: {e}")
        
        # Finally, fall back to legacy environment variables for backward compatibility
        if self._has_legacy_jira_config():
            logger.info("Using legacy JIRA configuration from environment variables")
            return [
                {
                    "url": os.getenv('JIRA_URL_1'),
                    "username": os.getenv('JIRA_USERNAME_1'),
                    "password": os.getenv('JIRA_PASSWORD_1'),
                    "instance_type": "instance_1",
                    "name": "Instance 1",
                    "enabled": True
                },
                {
                    "url": os.getenv('JIRA_URL_2'),
                    "username": os.getenv('JIRA_USERNAME_2'),
                    "password": os.getenv('JIRA_PASSWORD_2'),
                    "instance_type": "instance_2",
                    "name": "Instance 2",
                    "enabled": True
                }
            ]
        
        raise EnvironmentError(
            "No JIRA instances configured. Please set JIRA_INSTANCES environment variable, "
            "JIRA_CONFIG_FILE to point to a config file, or use legacy JIRA_URL_1/2 variables."
        )
    
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
    max_workers: Optional[int] = None,
    project_timeout: Optional[int] = None
) -> Application:
    """
    Create and initialize application instance.
    
    Args:
        config_dir: Directory containing configuration files
        max_workers: Maximum number of concurrent workers (overrides DB config)
        project_timeout: Timeout per project in seconds (overrides DB config)
        
    Returns:
        Configured Application instance
    """
    return Application(
        config_dir=config_dir,
        max_workers=max_workers,
        project_timeout=project_timeout
    )