"""
Issue management and tracking functionality.
"""

import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from psycopg2.extras import execute_batch
from .db_core import get_db_connection, execute_query, DatabaseOperationError
from .constants import ISSUE_COLUMNS

# Configure logging
logger = logging.getLogger(__name__)

# Constants
BATCH_SIZE = 1000

# Global counters
total_issues_processed = 0

class IssueError(Exception):
    """Custom exception for issue operations"""
    pass

def create_issues_table():
    """Create the issues table if it doesn't exist."""
    try:
        execute_query("""
            CREATE TABLE IF NOT EXISTS jira_issues_v2 (
                issue_key VARCHAR(255) PRIMARY KEY,
                summary TEXT,
                status VARCHAR(255),
                ndpu_order_number VARCHAR(255),
                ndpu_raw_photos INTEGER,
                dropbox_raw_link TEXT,
                dropbox_edited_link TEXT,
                same_day_delivery BOOLEAN,
                escalated_editing BOOLEAN,
                edited_media_revision_notes TEXT,
                ndpu_editing_team VARCHAR(255),
                scheduled TIMESTAMP,
                acknowledged TIMESTAMP,
                at_listing TIMESTAMP,
                shoot_complete TIMESTAMP,
                uploaded TIMESTAMP,
                edit_start TIMESTAMP,
                final_review TIMESTAMP,
                closed TIMESTAMP,
                ndpu_service VARCHAR(255),
                project_name TEXT,
                location_name TEXT,
                ndpu_client_name TEXT,
                ndpu_client_email TEXT,
                ndpu_listing_address TEXT, -- Added column definition
                ndpu_comments TEXT,
                ndpu_editor_notes TEXT,
                ndpu_access_instructions TEXT,
                ndpu_special_instructions TEXT,
                last_updated TIMESTAMP DEFAULT now()
            );

            CREATE INDEX IF NOT EXISTS idx_jira_issues_v2_location_name 
            ON jira_issues_v2(location_name);

            CREATE INDEX IF NOT EXISTS idx_jira_issues_v2_project 
            ON jira_issues_v2(project_name);

            CREATE INDEX IF NOT EXISTS idx_jira_issues_v2_status 
            ON jira_issues_v2(status);

            CREATE INDEX IF NOT EXISTS idx_jira_issues_v2_last_updated 
            ON jira_issues_v2(last_updated);
        """)
        
        logger.info("Issues table created successfully")
        
    except DatabaseError as e:
        logger.error(f"Failed to create issues table: {e}")
        raise IssueError(f"Table creation failed: {e}")

def batch_insert_issues(issues_data: List[tuple], batch_size: int = BATCH_SIZE) -> int:
    """
    Insert or update issues in batches with improved error handling and performance.
    
    Args:
        issues_data: List of tuples containing issue data
        batch_size: Number of records to process in each batch
        
    Returns:
        int: Number of issues processed successfully
        
    Raises:
        IssueError: If batch processing fails
    """
    if not issues_data:
        logger.info("No issues to insert or update")
        return 0

    total_processed = 0
    start_time = datetime.now()

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                # Create parameter placeholders
                placeholders = ','.join(['%s'] * len(ISSUE_COLUMNS))
                query = f"""
                    INSERT INTO jira_issues_v2 (
                        {', '.join(ISSUE_COLUMNS)}
                    )
                    VALUES ({placeholders})
                    ON CONFLICT (issue_key) DO UPDATE SET
                        summary = EXCLUDED.summary,
                        status = EXCLUDED.status,
                        project_name = EXCLUDED.project_name,
                        ndpu_order_number = EXCLUDED.ndpu_order_number,
                        ndpu_raw_photos = EXCLUDED.ndpu_raw_photos,
                        dropbox_raw_link = EXCLUDED.dropbox_raw_link,
                        dropbox_edited_link = EXCLUDED.dropbox_edited_link,
                        same_day_delivery = EXCLUDED.same_day_delivery,
                        escalated_editing = EXCLUDED.escalated_editing,
                        edited_media_revision_notes = EXCLUDED.edited_media_revision_notes,
                        ndpu_editing_team = EXCLUDED.ndpu_editing_team,
                        acknowledged = EXCLUDED.acknowledged,
                        at_listing = EXCLUDED.at_listing,
                        shoot_complete = EXCLUDED.shoot_complete,
                        uploaded = EXCLUDED.uploaded,
                        edit_start = EXCLUDED.edit_start,
                        final_review = EXCLUDED.final_review,
                        closed = EXCLUDED.closed,
                        ndpu_service = EXCLUDED.ndpu_service,
                        location_name = EXCLUDED.location_name,
                        ndpu_client_name = EXCLUDED.ndpu_client_name,
                        ndpu_client_email = EXCLUDED.ndpu_client_email,
                        ndpu_listing_address = EXCLUDED.ndpu_listing_address,
                        ndpu_comments = EXCLUDED.ndpu_comments,
                        ndpu_editor_notes = EXCLUDED.ndpu_editor_notes,
                        scheduled = EXCLUDED.scheduled,
                        ndpu_access_instructions = EXCLUDED.ndpu_access_instructions,
                        ndpu_special_instructions = EXCLUDED.ndpu_special_instructions,
                        last_updated = EXCLUDED.last_updated
                """

                # Process in batches with validation
                for i in range(0, len(issues_data), batch_size):
                    batch = issues_data[i:i + batch_size]
                    valid_batch = []
                    
                    # Validate and convert batch records
                    skipped_records = []
                    for record in batch:
                        try:
                            if len(record) != len(ISSUE_COLUMNS):
                                skipped_records.append(record[0] if record else 'unknown')
                                continue

                            # Convert record to list for modification
                            record = list(record)

                            # Handle integer field (ndpu_raw_photos at index 4)
                            if record[4] is not None:
                                try:
                                    if isinstance(record[4], (int, float)):
                                        record[4] = int(record[4])
                                    elif isinstance(record[4], str):
                                        if record[4].lower() in ('zip', 'none', 'n/a', '-'):
                                            record[4] = None
                                        else:
                                            # Try to extract first number
                                            import re
                                            match = re.search(r'\d+', record[4])
                                            record[4] = int(match.group()) if match else None
                                except (ValueError, TypeError, AttributeError):
                                    record[4] = None

                            # Validate boolean fields
                            for i in (7, 8):  # same_day_delivery and escalated_editing
                                if record[i] is not None and not isinstance(record[i], bool):
                                    try:
                                        if isinstance(record[i], str):
                                            val = record[i].lower().strip()
                                            if val in ('yes', 'true', '1', 'y', 'on'):
                                                record[i] = True
                                            elif val in ('no', 'false', '0', 'n', 'off'):
                                                record[i] = False
                                            else:
                                                record[i] = None
                                        else:
                                            record[i] = None
                                    except (ValueError, AttributeError):
                                        record[i] = None

                            # Validate timestamp fields
                            for i in range(11, 19):
                                if record[i] is not None and not isinstance(record[i], datetime):
                                    try:
                                        from dateutil import parser
                                        record[i] = parser.parse(str(record[i]))
                                    except (ValueError, TypeError):
                                        record[i] = None

                            valid_batch.append(tuple(record))
                        except Exception as e:
                            skipped_records.append(f"error processing {record[0] if record else 'unknown'}: {e}")
                            continue
                    
                    if skipped_records:
                        sample_record = batch[0] if batch else None
                        logger.warning(
                            f"Skipped {len(skipped_records)} invalid records in batch.\n"
                            f"First few skipped: {', '.join(skipped_records[:3])}...\n"
                            f"Expected {len(ISSUE_COLUMNS)} columns: {ISSUE_COLUMNS}\n"
                            f"Got {len(sample_record) if sample_record else 0} columns in record: "
                            f"{list(enumerate(sample_record)) if sample_record else 'no sample'}"
                        )
                    
                    if not valid_batch:
                        logger.warning(f"No valid records in batch of {len(batch)}")
                        continue
                        
                    try:
                        execute_batch(cursor, query, valid_batch)
                        conn.commit()
                        total_processed += len(valid_batch)
                        logger.debug(f"Processed batch of {len(valid_batch)} issues")
                    except Exception as e:
                        conn.rollback()
                        if "column" in str(e) and "does not exist" in str(e):
                            logger.error(
                                f"Database schema mismatch: {e}\n"
                                f"Expected columns: {ISSUE_COLUMNS}\n"
                                f"Please ensure database schema matches constants.py"
                            )
                        else:
                            logger.error(f"Error processing batch: {e}")
                        # Continue with next batch instead of failing completely
                        continue

        duration = (datetime.now() - start_time).total_seconds()
        rate = total_processed / duration if duration > 0 else 0
        logger.info(f"Processed {total_processed} issues in {duration:.2f}s ({rate:.2f} issues/s)")
        
        # Update global counter
        global total_issues_processed
        total_issues_processed += total_processed
        
        return total_processed

    except Exception as e:
        logger.exception("Failed to insert issues into database")
        raise IssueError(f"Batch insert failed: {e}")

def get_issue_by_key(issue_key: str) -> Optional[Dict]:
    """
    Retrieve a single issue by its key.
    
    Args:
        issue_key: JIRA issue key
        
    Returns:
        Dict containing issue data or None if not found
    """
    try:
        result = execute_query(
            "SELECT * FROM jira_issues_v2 WHERE issue_key = %s",
            (issue_key,),
            fetch=True
        )
        
        if result:
            return dict(zip(ISSUE_COLUMNS, result[0]))
        return None
        
    except DatabaseError as e:
        logger.error(f"Error retrieving issue {issue_key}: {e}")
        raise IssueError(f"Failed to retrieve issue: {e}")

def get_project_issues(
    project_key: str,
    status: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
) -> List[Dict]:
    """
    Get issues for a specific project with optional filtering.
    
    Args:
        project_key: Project identifier
        status: Optional status filter
        limit: Maximum number of issues to return
        offset: Number of issues to skip
        
    Returns:
        List of issue dictionaries
    """
    try:
        query = "SELECT * FROM jira_issues_v2 WHERE project_name = %s"
        params = [project_key]
        
        if status:
            query += " AND status = %s"
            params.append(status)
            
        query += " ORDER BY last_updated DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])
        
        result = execute_query(query, tuple(params), fetch=True)
        
        if result:
            return [dict(zip(ISSUE_COLUMNS, row)) for row in result]
        return []
        
    except DatabaseError as e:
        logger.error(f"Error retrieving issues for project {project_key}: {e}")
        raise IssueError(f"Failed to retrieve project issues: {e}")

def get_issues_since(timestamp: datetime, limit: int = 100) -> List[Dict]:
    """
    Get issues updated since a specific timestamp.
    
    Args:
        timestamp: Get issues updated after this time
        limit: Maximum number of issues to return
        
    Returns:
        List of issue dictionaries
    """
    try:
        result = execute_query("""
            SELECT * FROM jira_issues_v2 
            WHERE last_updated > %s 
            ORDER BY last_updated DESC 
            LIMIT %s
        """, (timestamp, limit), fetch=True)
        
        if result:
            return [dict(zip(ISSUE_COLUMNS, row)) for row in result]
        return []
        
    except DatabaseError as e:
        logger.error(f"Error retrieving issues since {timestamp}: {e}")
        raise IssueError(f"Failed to retrieve recent issues: {e}")