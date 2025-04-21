import os
import time
import logging
import psutil
from datetime import datetime
from prometheus_client import Counter, Gauge, start_http_server

# Configure logging
logger = logging.getLogger(__name__)

# Define metrics
ISSUES_PROCESSED = Counter('jira_issues_v2_processed_total', 'Total number of issues processed')
SYNC_ERRORS = Counter('jira_sync_errors_total', 'Total number of sync errors', ['error_type'])
SYNC_DURATION = Gauge('jira_sync_duration_seconds', 'Time taken for sync operation')
BATCH_SIZE = Gauge('jira_sync_batch_size', 'Current batch size for processing')
DB_SIZE = Gauge('jira_database_size_bytes', 'Database size in bytes')
MEMORY_USAGE = Gauge('jira_memory_usage_bytes', 'Memory usage in bytes')

from core.config.logging_config import setup_logging

def monitor_database_size():
    """Monitor database size using system commands."""
    try:
        # This is a placeholder - in production you'd want to query the database
        # for its actual size using database-specific commands
        logger.info("Database size monitoring placeholder")
        size = 0  # Set to actual size in production
        DB_SIZE.set(size)
        return {"size_bytes": size}
    except Exception as e:
        logger.error(f"Error monitoring database size: {e}")
        return {"size_bytes": 0, "error": str(e)}

def monitor_memory_usage():
    """Monitor memory usage of the current process."""
    try:
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()
        memory_usage = memory_info.rss  # Resident Set Size
        MEMORY_USAGE.set(memory_usage)
        return {
            "rss_bytes": memory_usage,
            "percent": process.memory_percent()
        }
    except Exception as e:
        logger.error(f"Error monitoring memory usage: {e}")
        return {"rss_bytes": 0, "percent": 0, "error": str(e)}

def log_performance_metrics(start_time: datetime, total_issues: int, successful_projects: int):
    """Log performance metrics for the sync operation."""
    try:
        duration = (datetime.now() - start_time).total_seconds()
        SYNC_DURATION.set(duration)
        ISSUES_PROCESSED.inc(total_issues)
        
        rate = total_issues / duration if duration > 0 else 0
        logger.info(f"Sync completed - Duration: {duration:.2f}s, Issues: {total_issues}, Projects: {successful_projects}, Rate: {rate:.2f} issues/s")
    except Exception as e:
        logger.error(f"Error logging performance metrics: {e}")

def start_metrics_server(port: int = 8000):
    """Start the Prometheus metrics server."""
    try:
        start_http_server(port)
        logger.info(f"Metrics server started on port {port}")
    except Exception as e:
        logger.error(f"Failed to start metrics server: {e}")
        raise
