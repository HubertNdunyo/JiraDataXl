"""
Centralized logging configuration.
"""

import os
import logging
from datetime import datetime

def setup_logging(log_name: str = None):
    """
    Configure logging settings with consistent format across the application.
    
    Args:
        log_name: Optional name for the log file. If not provided, uses timestamp.
    """
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    # Set log filename
    if not log_name:
        log_name = f"sync_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(f"logs/{log_name}")
        ]
    )