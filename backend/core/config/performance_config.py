"""
Performance configuration management for sync operations.
Provides centralized access to performance settings with defaults.
"""
from typing import Dict, Any
from core.db.db_config import get_configuration
import logging

logger = logging.getLogger(__name__)

# Default performance settings
DEFAULT_PERFORMANCE_CONFIG = {
    'max_workers': 8,
    'project_timeout': 300,  # seconds
    'batch_size': 200,
    'lookback_days': 60,
    'max_retries': 3,
    'backoff_factor': 0.5,
    'rate_limit_pause': 1.0,  # seconds
    'connection_pool_size': 20,  # HTTP connection pool size
    'connection_pool_block': False  # Whether to block when pool is exhausted
}


def get_performance_config() -> Dict[str, Any]:
    """
    Get performance configuration from database with defaults.
    
    Returns:
        Dict containing performance settings
    """
    try:
        # Try to get from database
        config = get_configuration('performance', 'settings')
        
        if config and isinstance(config.get('value'), dict):
            # Merge with defaults to ensure all keys exist
            performance_config = DEFAULT_PERFORMANCE_CONFIG.copy()
            performance_config.update(config['value'])
            logger.info(f"Loaded performance config from database: {performance_config}")
            return performance_config
        else:
            # Return defaults if not configured
            logger.info("No performance configuration found in database, using defaults")
            return DEFAULT_PERFORMANCE_CONFIG.copy()
            
    except Exception as e:
        logger.warning(f"Error loading performance config from database, using defaults: {e}")
        return DEFAULT_PERFORMANCE_CONFIG.copy()


def get_performance_setting(setting_name: str, default=None):
    """
    Get a specific performance setting.
    
    Args:
        setting_name: Name of the setting to retrieve
        default: Default value if setting not found
        
    Returns:
        The setting value or default
    """
    config = get_performance_config()
    return config.get(setting_name, default if default is not None else DEFAULT_PERFORMANCE_CONFIG.get(setting_name))