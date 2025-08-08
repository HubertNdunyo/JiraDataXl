"""
Main entry point for the JIRA synchronization application.
"""

import sys
import logging
from datetime import datetime
from core.app import create_app
from setup_logging import setup_logging

# Global application instance
_app = None

def get_app():
    """Get or create the application instance."""
    global _app
    if _app is None:
        _app = create_app(
            config_dir='config'
            # Don't pass max_workers and project_timeout
            # Let the app load them from database
        )
    return _app

def fetch_all_issues():
    """Run a sync cycle through the core application."""
    logger = logging.getLogger(__name__)
    try:
        app = get_app()
        
        # Check if application is ready
        if not app.is_ready:
            logger.error("Application failed readiness check")
            return False
            
        # Run sync process
        stats = app.run_sync()
        return stats.failed_projects == 0
        
    except Exception as e:
        logger.exception("Unexpected error occurred during sync")
        return False

def stop_sync():
    """Stop the current sync process."""
    logger = logging.getLogger(__name__)
    try:
        app = get_app()
        app.stop_sync()
        return True
    except Exception as e:
        logger.exception("Failed to stop sync")
        return False

def is_sync_stopped():
    """Check if sync process is stopped."""
    try:
        app = get_app()
        return app.is_sync_stopped()
    except Exception:
        return False

def main():
    """Main application entry point."""
    try:
        # Setup logging
        setup_logging()
        logger = logging.getLogger(__name__)
        
        logger.info("=" * 80)
        logger.info("Starting JIRA Sync Application")
        logger.info(f"Script started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        success = fetch_all_issues()
        
        # Log completion
        logger.info("=" * 80)
        logger.info(f"Script completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Return success if no failed projects
        return 0 if success else 1
        
    except KeyboardInterrupt:
        logger.info("Script interrupted by user")
        return 130
    except Exception as e:
        logger.exception("Unexpected error occurred")
        return 1

if __name__ == "__main__":
    sys.exit(main())