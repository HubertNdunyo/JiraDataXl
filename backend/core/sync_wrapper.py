"""
Wrapper for sync operations to avoid circular imports
"""
import sys
from pathlib import Path

# Import sync functions from copied main module
def get_sync_functions():
    """Lazy import sync functions to avoid circular imports"""
    try:
        import main_parent
        return {
            'fetch_all_issues': main_parent.fetch_all_issues,
            'stop_sync': main_parent.stop_sync,
            'is_sync_stopped': main_parent.is_sync_stopped,
            'get_app': main_parent.get_app
        }
    except ImportError as e:
        print(f"Warning: Could not import main_parent module: {e}")
        raise ImportError(f"Could not import main_parent module: {e}") from e