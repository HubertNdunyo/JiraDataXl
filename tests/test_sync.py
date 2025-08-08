#!/usr/bin/env python3
"""Test sync with a single project"""

import os
import sys
from dotenv import load_dotenv

# Add project root to path
project_root = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, project_root)

from core.app import Application
from core.config.logging_config import setup_logging

def main():
    """Run a test sync"""
    # Load environment and setup logging
    load_dotenv()
    setup_logging('test_sync.log')
    
    # Create application instance
    app = Application(
        config_dir='config',
        max_workers=1,  # Use single worker for testing
        project_timeout=300
    )
    
    print("Starting test sync...")
    print("This will sync data from both Jira instances")
    print("Projects will be automatically discovered")
    print("-" * 50)
    
    try:
        # Run the sync
        stats = app.run_sync()
        print("\nSync completed!")
        print(stats.generate_report())
        
    except KeyboardInterrupt:
        print("\nSync interrupted by user")
        app.stop_sync()
    except Exception as e:
        print(f"\nError during sync: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()