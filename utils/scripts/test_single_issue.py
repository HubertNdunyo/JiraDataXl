import os
import sys
import logging
from dotenv import load_dotenv
from pprint import pprint

# Add project root to path to allow imports from core
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

from core.config.logging_config import setup_logging
from core.jira.jira_client import JiraClient, JiraClientError
from core.jira.jira_issues import IssueFetcher
from core.db.constants import ISSUE_COLUMNS

# --- Configuration ---
ISSUE_KEY_TO_TEST = "SQHNVLY-14646"
JIRA_INSTANCE_TYPE = "instance_2" # Corresponds to field_mappings.json - TRYING INSTANCE 2
# --- End Configuration ---

def main():
    """Fetches and processes a single JIRA issue for testing."""
    load_dotenv(os.path.join(project_root, '.env'))
    setup_logging()
    logger = logging.getLogger(__name__)

    jira_url = os.getenv(f'JIRA_URL_{JIRA_INSTANCE_TYPE[-1]}')
    jira_user = os.getenv(f'JIRA_USERNAME_{JIRA_INSTANCE_TYPE[-1]}')
    jira_token = os.getenv(f'JIRA_PASSWORD_{JIRA_INSTANCE_TYPE[-1]}') # Assuming password is API token

    if not all([jira_url, jira_user, jira_token]):
        logger.error("JIRA credentials not found in .env file for instance %s", JIRA_INSTANCE_TYPE)
        sys.exit(1)

    logger.info(f"Testing issue: {ISSUE_KEY_TO_TEST} from {jira_url}")

    try:
        # 1. Initialize JIRA Client
        client = JiraClient(jira_url, jira_user, jira_token)
        logger.info("JIRA Client initialized.")

        # 2. Initialize Issue Fetcher (loads field mappings)
        # Use the correct path relative to project root
        field_config_path = os.path.join(project_root, 'config', 'field_mappings.json')
        fetcher = IssueFetcher(client=client, field_config_path=field_config_path)
        logger.info("Issue Fetcher initialized.")
        logger.info(f"Fields requested from JIRA: {fetcher.fields}")


        # 3. Fetch the specific issue
        logger.info(f"Fetching issue {ISSUE_KEY_TO_TEST}...")
        issue_data = client.get_issue(ISSUE_KEY_TO_TEST, fields=fetcher.fields, expand=['changelog'])
        logger.info("Issue data fetched successfully.")

        # Print the specific custom field from raw data
        raw_address_field_data = issue_data.get('fields', {}).get('customfield_10603', 'FIELD_NOT_FOUND')
        print("\n--- Raw Data for customfield_10603 ---")
        pprint(raw_address_field_data)
        print("-------------------------------------\n")

        # 4. Process the issue
        logger.info("Processing issue...")
        project_key = ISSUE_KEY_TO_TEST.split('-')[0]
        processed_tuple = fetcher.process_issue(issue_data, project_key, JIRA_INSTANCE_TYPE)

        if processed_tuple:
            logger.info("Issue processed successfully.")
            # Map tuple to dictionary using ISSUE_COLUMNS for readability
            processed_dict = dict(zip(ISSUE_COLUMNS, processed_tuple))

            print("\n--- Processed Issue Data ---")
            pprint(processed_dict)
            print("---------------------------\n")

            # Highlight the address field
            address_value = processed_dict.get('ndpu_listing_address')
            print(f"Value for 'ndpu_listing_address': {address_value}")

            if len(processed_tuple) != len(ISSUE_COLUMNS):
                 logger.error(f"Mismatch! Processed tuple has {len(processed_tuple)} elements, expected {len(ISSUE_COLUMNS)}.")
            else:
                 logger.info(f"Processed tuple length ({len(processed_tuple)}) matches expected column count.")

        else:
            logger.error("Failed to process the issue.")

    except JiraClientError as e:
        logger.error(f"JIRA Client Error: {e}")
    except Exception as e:
        logger.exception(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()