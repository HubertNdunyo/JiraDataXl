#!/usr/bin/env python3
import logging
from core.config.logging_config import setup_logging
from core.db.db_core import get_db_connection, execute_query

# Configure logging
setup_logging('setup.log')
logger = logging.getLogger(__name__)

def create_tables(cursor):
    """Create database tables"""
    logger.info("Creating tables...")
    
    # Raw Jira data table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS jira_raw_data (
            id BIGSERIAL PRIMARY KEY,
            raw_data JSONB NOT NULL,
            sync_timestamp TIMESTAMP NOT NULL
        )
    """)
    
    # Create indexes for jira_raw_data
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_jira_raw_data_sync_time 
        ON jira_raw_data(sync_timestamp)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_jira_raw_data_issue_key 
        ON jira_raw_data((raw_data->>'key'))
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_jira_raw_data_project_key 
        ON jira_raw_data((raw_data->'fields'->>'project'))
    """)
    
    # Sync log table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sync_log (
            id BIGSERIAL PRIMARY KEY,
            start_time TIMESTAMP NOT NULL,
            end_time TIMESTAMP,
            status VARCHAR(50),
            issues_processed INTEGER DEFAULT 0,
            total_size_bytes BIGINT DEFAULT 0,
            error_details TEXT
        )
    """)
    
    # Create indexes for sync_log
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_sync_log_start_time 
        ON sync_log(start_time)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_sync_log_status 
        ON sync_log(status)
    """)

def verify_tables(cursor):
    """Verify tables were created correctly"""
    logger.info("Verifying tables...")
    
    # Check tables exist
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        AND table_name IN ('jira_raw_data', 'sync_log');
    """)
    tables = cursor.fetchall()
    if len(tables) != 2:
        raise Exception("Not all tables were created")
    
    # Check indexes exist
    cursor.execute("""
        SELECT tablename, indexname 
        FROM pg_indexes 
        WHERE schemaname = 'public'
        AND tablename IN ('jira_raw_data', 'sync_log')
        ORDER BY tablename, indexname;
    """)
    indexes = cursor.fetchall()
    logger.info("Found indexes:")
    for table, index in indexes:
        logger.info(f"  {table}: {index}")
    
    expected_count = 7  # 2 PK indexes + 5 custom indexes
    if len(indexes) != expected_count:
        raise Exception(f"Expected {expected_count} indexes, found {len(indexes)}")

def verify_permissions(cursor):
    """Verify database permissions"""
    logger.info("Verifying permissions...")
    
    cursor.execute("""
        SELECT has_table_privilege(current_user, 'jira_raw_data', 'INSERT');
        SELECT has_table_privilege(current_user, 'sync_log', 'INSERT');
    """)
    if not all(cursor.fetchall()):
        raise Exception("Missing required permissions")

def main():
    """Initialize the database"""
    try:
        logger.info("Connecting to database...")
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                # Create tables
                create_tables(cursor)
                
                # Verify setup
                verify_tables(cursor)
                verify_permissions(cursor)
                
                # Commit changes
                conn.commit()
                logger.info("Database setup completed successfully")
                
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        raise

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Setup failed: {e}")
        exit(1)
