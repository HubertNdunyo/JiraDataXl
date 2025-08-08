import logging
from core.config.logging_config import setup_logging
from core.db.db_core import get_db_connection, execute_query

# Configure logging
setup_logging('clear_jira_data.log')
logger = logging.getLogger(__name__)

def clear_jira_issues():
    """Clear all data from the jira_issues_v2 table and its dependent tables."""
    try:
        # Get count before truncate
        count_before = execute_query("SELECT COUNT(*) FROM jira_issues_v2", fetch=True)[0][0]
        logger.info(f"Current number of records in jira_issues_v2: {count_before}")

        # Truncate the tables with CASCADE
        logger.info("Truncating jira_issues_v2 and dependent tables...")
        execute_query("TRUNCATE TABLE jira_issues_v2 CASCADE")
        logger.info("Successfully cleared all data from jira_issues_v2 and dependent tables")

        # Verify the tables are empty
        count_after = execute_query("SELECT COUNT(*) FROM jira_issues_v2", fetch=True)[0][0]
        logger.info(f"Records in jira_issues_v2 after truncate: {count_after}")

        if count_after == 0:
            logger.info("Data cleared successfully")
        else:
            logger.warning(f"Table not empty after truncate: {count_after} records remain")

    except Exception as e:
        logger.error(f"Error clearing data: {e}")
        raise

if __name__ == "__main__":
    try:
        clear_jira_issues()
    except Exception as e:
        logger.error(f"Script failed: {e}")
        exit(1)
