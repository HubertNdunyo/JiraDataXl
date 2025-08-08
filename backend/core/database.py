"""
Database utilities for the FastAPI backend
"""
import logging
import psycopg2
import os
from typing import Optional

logger = logging.getLogger(__name__)


def get_db_config():
    """Get database configuration from environment"""
    return {
        'dbname': os.getenv('DB_NAME'),
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD'),
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': os.getenv('DB_PORT', '5432')
    }


def init_db():
    """Initialize database connection"""
    try:
        config = get_db_config()
        conn = psycopg2.connect(**config)
        conn.close()
        logger.info("Database connection initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        return False


def check_db_connection() -> bool:
    """Check if database is accessible"""
    try:
        config = get_db_config()
        conn = psycopg2.connect(**config)
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.close()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Database connection check failed: {e}")
        return False