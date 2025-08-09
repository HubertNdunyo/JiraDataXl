"""
Core database functionality including connection management and base operations.
"""

import os
import time
import logging
import psycopg2
from psycopg2 import sql, DatabaseError
from contextlib import contextmanager
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# Database connection settings
DB_CONFIG = {
    'dbname': os.getenv('DB_NAME', 'jira_data_pipeline'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD'),
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432'),
    'application_name': 'jira_sync'  # For better database monitoring
}

# Constants
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds

class DatabaseError(Exception):
    """Custom exception for database errors"""
    pass

@contextmanager
def get_db_connection():
    """
    Enhanced context manager for database connections with retry logic.
    
    Yields:
        psycopg2.connection: Database connection object
        
    Raises:
        DatabaseError: If connection cannot be established after retries
    """
    conn = None
    retries = 0
    
    while retries < MAX_RETRIES:
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            conn.set_session(autocommit=False)  # Explicit transaction control
            yield conn
            return
        except psycopg2.OperationalError as e:
            retries += 1
            if retries == MAX_RETRIES:
                logger.error(f"Failed to connect to database after {MAX_RETRIES} attempts: {e}")
                raise DatabaseOperationError(f"Database connection failed: {e}")
            logger.warning(f"Database connection attempt {retries} failed, retrying in {RETRY_DELAY} seconds")
            time.sleep(RETRY_DELAY)
        except Exception as e:
            logger.error(f"Unexpected database error: {e}")
            raise DatabaseOperationError(f"Database error: {e}")
        finally:
            if conn:
                conn.close()

def execute_query(query: str, params: Optional[tuple] = None, fetch: bool = False):
    """
    Execute a database query with proper error handling.
    
    Args:
        query: SQL query to execute
        params: Query parameters (optional)
        fetch: Whether to fetch and return results
        
    Returns:
        Query results if fetch=True, else None
        
    Raises:
        DatabaseOperationError: If query execution fails
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                
                if fetch:
                    result = cursor.fetchall()
                    conn.commit()
                    return result
                    
                conn.commit()
                return None
                
    except Exception as e:
        logger.error(f"Query execution failed: {e}")
        raise DatabaseError(f"Query execution failed: {e}")

def execute_batch(query: str, params_list: list, page_size: int = 1000):
    """
    Execute a batch operation with proper error handling.
    
    Args:
        query: SQL query to execute
        params_list: List of parameter tuples
        page_size: Number of operations per batch
        
    Raises:
        DatabaseError: If batch execution fails
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                psycopg2.extras.execute_batch(
                    cursor,
                    query,
                    params_list,
                    page_size=page_size
                )
                conn.commit()
                
    except Exception as e:
        logger.error(f"Batch execution failed: {e}")
        raise DatabaseError(f"Batch execution failed: {e}")

def check_table_exists(table_name: str) -> bool:
    """
    Check if a table exists in the database.
    
    Args:
        table_name: Name of the table to check
        
    Returns:
        bool: True if table exists, False otherwise
    """
    query = """
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = %s
        )
    """
    try:
        result = execute_query(query, (table_name,), fetch=True)
        return result[0][0] if result else False
    except Exception as e:
        logger.error(f"Failed to check table existence: {e}")
        return False

def get_column_names(table_name: str) -> list:
    """
    Get column names for a table.
    
    Args:
        table_name: Name of the table
        
    Returns:
        list: List of column names
    """
    query = """
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = %s
        ORDER BY ordinal_position
    """
    try:
        result = execute_query(query, (table_name,), fetch=True)
        return [row[0] for row in result] if result else []
    except Exception as e:
        logger.error(f"Failed to get column names: {e}")
        return []