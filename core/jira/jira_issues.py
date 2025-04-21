"""
JIRA issue fetching and processing functionality.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from .jira_client import JiraClient, JiraClientError
from .field_processor import FieldProcessor
from ..db import log_update, constants, get_project_mapping
from ..db.constants import ISSUE_COLUMNS

# Configure logging
logger = logging.getLogger(__name__)

class IssueProcessingError(Exception):
    """Exception for issue processing errors"""
    pass

class IssueFetcher:
    """
    Handles fetching and processing of JIRA issues.
    """
    
    def __init__(
        self,
        client: JiraClient,
        batch_size: int = 200,
        lookback_days: int = 60,
        field_config_path: Optional[str] = None
    ):
        """
        Initialize issue fetcher.
        
        Args:
            client: Configured JIRA client
            batch_size: Number of issues to fetch per request
            lookback_days: Days of history to fetch
            field_config_path: Path to field mapping configuration file
        """
        self.client = client
        self.batch_size = batch_size
        self.lookback_days = lookback_days
        
        # Initialize field processor with config and load fields
        self.field_processor = FieldProcessor(field_config_path)
        self.fields = ['summary', 'status', 'project']  # Always include basic fields
        
        # Add configured fields
        for group in self.field_processor.config.get('field_groups', {}).values():
            for field_config in group.get('fields', {}).values():
                for instance_config in field_config.values():
                    if isinstance(instance_config, dict) and 'field_id' in instance_config:
                        field_id = instance_config['field_id']
                        if isinstance(field_id, list):
                            self.fields.extend(field_id)
                        else:
                            self.fields.append(field_id)
        
        # Remove duplicates while preserving order
        self.fields = list(dict.fromkeys(self.fields))

    def build_jql_query(self, project_key: str) -> str:
        """
        Build JQL query for fetching issues.
        
        Args:
            project_key: Project to fetch issues from
            
        Returns:
            JQL query string
        """
        date_limit = (datetime.now() - timedelta(days=self.lookback_days)
                    ).strftime('%Y-%m-%d')
        
        return (
            f"project = {project_key} AND "
            f"created >= {date_limit} "
            "ORDER BY updated DESC"
        )

    def fetch_project_issues(
        self,
        project_key: str,
        instance_type: str
    ) -> List[Tuple]:
        """
        Fetch all issues for a project.
        
        Args:
            project_key: Project to fetch issues from
            instance_type: Type of JIRA instance
            
        Returns:
            List of processed issue tuples
            
        Raises:
            IssueProcessingError: If fetching or processing fails
        """
        issues_data = []
        start_at = 0
        total_issues = 0
        fetch_start_time = datetime.now()

        try:
            while True:
                # Search for issues
                response = self.client.search_issues(
                    jql=self.build_jql_query(project_key),
                    fields=self.fields,
                    start_at=start_at,
                    max_results=self.batch_size,
                    expand=['changelog']
                )
                
                # Get total on first request
                if start_at == 0:
                    total_issues = response.get('total', 0)
                    if total_issues == 0:
                        logger.info(f"No issues found for project {project_key}")
                        return []

                batch_issues = response.get('issues', [])
                
                # Process issues in current batch
                for issue in batch_issues:
                    processed_issue = self.process_issue(
                        issue,
                        project_key,
                        instance_type
                    )
                    if processed_issue:
                        issues_data.append(processed_issue)

                # Update progress
                start_at += self.batch_size
                
                # Log progress every 500 issues
                if len(issues_data) % 500 == 0:
                    logger.info(
                        f"Processed {len(issues_data)} out of {total_issues} "
                        f"issues from project {project_key}"
                    )

                if start_at >= total_issues:
                    break

            # Log final metrics
            total_duration = (datetime.now() - fetch_start_time).total_seconds()
            if issues_data:
                processing_rate = len(issues_data) / total_duration
                logger.info(
                    f"Completed fetching {len(issues_data)} issues for project "
                    f"{project_key} in {total_duration:.2f}s "
                    f"({processing_rate:.2f} issues/s)"
                )

            return issues_data

        except JiraClientError as e:
            error_msg = f"Failed to fetch issues for project {project_key}: {e}"
            logger.error(error_msg)
            log_update(project_key, "Failed", error_message=error_msg)
            raise IssueProcessingError(error_msg)
            
        except Exception as e:
            error_msg = f"Unexpected error processing project {project_key}: {e}"
            logger.exception(error_msg)
            log_update(project_key, "Failed", error_message=error_msg)
            raise IssueProcessingError(error_msg)

    def process_issue(
        self,
        issue: Dict[str, Any],
        project_key: str,
        instance_type: str
    ) -> Optional[Tuple]:
        """
        Process individual JIRA issue.
        
        Args:
            issue: Raw issue data from JIRA
            project_key: Project key
            instance_type: Type of JIRA instance
            
        Returns:
            Tuple of processed issue data or None if processing fails
        """
        try:
            fields = issue['fields']
            issue_key = issue.get('key')
            
            # Basic fields
            summary = self.field_processor.extract_field_value(fields, 'summary')
            status = self.field_processor.extract_field_value(fields, 'status.name')
            
            # Order and photos fields
            order_number = self.field_processor.extract_field_value(fields, 'customfield_10501')
            raw_photos = None
            for field_id in ['customfield_12602', 'customfield_12581']:
                raw_photos = self.field_processor.extract_field_value(fields, field_id)
                if raw_photos is not None:
                    break
            
            # Link fields
            dropbox_raw = self.field_processor.extract_field_value(fields, 'customfield_10713')
            dropbox_edited = self.field_processor.extract_field_value(fields, 'customfield_10714')
            
            # Delivery and editing fields
            same_day = self.field_processor.extract_field_value(fields, 'customfield_12661')
            if isinstance(same_day, dict):
                same_day = same_day.get('value')
            
            escalated = self.field_processor.extract_field_value(fields, 'customfield_11712')
            revision_notes = self.field_processor.extract_field_value(fields, 'customfield_10716')
            
            # Team field
            editing_team = None
            for field_id in ['customfield_12648', 'customfield_12644']:
                editing_team = self.field_processor.extract_field_value(fields, field_id)
                if editing_team is not None:
                    break
            
            # Service field
            service = (
                self.field_processor.extract_field_value(fields, 'customfield_11104') or
                self.field_processor.extract_field_value(fields, 'customfield_11700')
            )
            
            # Client fields
            client_name = self.field_processor.extract_field_value(fields, 'customfield_10600')
            client_email = self.field_processor.extract_field_value(fields, 'customfield_10601')
                    
            comments = self.field_processor.extract_field_value(fields, 'customfield_10612')
            editor_notes = self.field_processor.extract_field_value(fields, 'customfield_11601')
            
            # Combined instruction fields
            access_instructions = []
            for field_id in ['customfield_10700', 'customfield_12594', 'customfield_12611']:
                value = self.field_processor.extract_field_value(fields, field_id)
                if value:
                    access_instructions.append(str(value))
            access_instructions = ' '.join(access_instructions) if access_instructions else None
            
            special_instructions = []
            for field_id in ['customfield_11100', 'customfield_12595', 'customfield_12612']:
                value = self.field_processor.extract_field_value(fields, field_id)
                if value:
                    special_instructions.append(str(value))
            special_instructions = ' '.join(special_instructions) if special_instructions else None
            
            # Process transitions
            transitions = self.process_transitions(issue.get('changelog', {}))
            
            # Build record tuple matching ISSUE_COLUMNS order exactly
            record = (
                issue_key,                    # issue_key
                summary,                      # summary
                status,                       # status
                order_number,                 # ndpu_order_number
                raw_photos,                   # ndpu_raw_photos
                dropbox_raw,                  # dropbox_raw_link
                dropbox_edited,               # dropbox_edited_link
                self.field_processor.sanitize_value(same_day, 'boolean'),      # same_day_delivery
                self.field_processor.sanitize_value(escalated, 'boolean'),     # escalated_editing
                revision_notes,               # edited_media_revision_notes
                editing_team,                 # ndpu_editing_team
                transitions.get('scheduled'),  # scheduled
                transitions.get('acknowledged'), # acknowledged
                transitions.get('at_listing'), # at_listing
                transitions.get('shoot_complete'), # shoot_complete
                transitions.get('uploaded'),   # uploaded
                transitions.get('edit_start'), # edit_start
                transitions.get('final_review'), # final_review
                transitions.get('closed'),     # closed
                service,                      # ndpu_service
                project_key,                  # project_name
                datetime.now(),               # last_updated
                self._get_location_name(project_key, fields),  # location_name - use mapping or fallback to project name
                client_name,                  # ndpu_client_name
                client_email,                 # ndpu_client_email
                comments,                     # ndpu_comments
                editor_notes,                 # ndpu_editor_notes
                access_instructions,          # ndpu_access_instructions
                special_instructions          # ndpu_special_instructions
            )
            
            # Validate record structure
            if len(record) != len(ISSUE_COLUMNS):
                logger.debug(
                    f"Record structure for {issue_key}: "
                    f"Expected {len(ISSUE_COLUMNS)} columns, got {len(record)}"
                )
                return None
            
            return record
            
        except Exception as e:
            issue_key = issue.get('key', 'unknown')
            logger.debug(
                f"Failed to process {issue_key}: {str(e)}. "
                "This is expected if record structure changed."
            )
            return None

    @staticmethod
    def process_transitions(changelog: Dict[str, Any]) -> Dict[str, Optional[datetime]]:
        """
        Process issue transitions from changelog.
        
        Args:
            changelog: Issue changelog data
            
        Returns:
            Dict mapping transition names to timestamps
        """
        transitions = {
            "scheduled": None,
            "acknowledged": None,
            "at_listing": None,
            "shoot_complete": None,
            "uploaded": None,
            "edit_start": None,
            "final_review": None,
            "escalated_editing": None,
            "closed": None
        }
        
        # Status mapping
        STATUS_MAPPING = {
            'scheduled': {
                'scheduled', 'Scheduled'
            },
            'acknowledged': {
                'acknowledged', 'ack', 'acknowledged by agent',
                'acknowledged', 'ACKNOWLEDGED'
            },
            'at_listing': {
                'at listing', 'listing', 'at_listing', 'At Listing'
            },
            'shoot_complete': {
                'shoot complete', 'shooting complete',
                'shoot_complete', 'Shoot Complete'
            },
            'uploaded': {
                'uploaded', 'upload complete',
                'upload_complete', 'Uploaded'
            },
            'edit_start': {
                'edit start', 'editing started',
                'edit_start', 'Edit'
            },
            'final_review': {
                'final review', 'final_review',
                'pending review', 'Final Review',
                'Managing Partner Ready'
            },
            'escalated_editing': {
                'escalated editing', 'Escalated Editing'
            },
            'closed': {
                'closed', 'complete', 'completed',
                'done', 'Closed'
            }
        }
        
        try:
            if not changelog:
                return transitions

            for history in changelog.get('histories', []):
                created = history.get('created')
                if not created:
                    continue
                    
                # Handle various timezone formats
                created = created.replace('Z', '+00:00')
                if '+' in created and ':' not in created[-5:]:
                    # Convert +HHMM to +HH:MM
                    parts = created.rsplit('+', 1)
                    if len(parts) == 2:
                        tz = parts[1]
                        if len(tz) == 4:  # HHMM format
                            created = f"{parts[0]}+{tz[:2]}:{tz[2:]}"
                elif '-' in created and ':' not in created[-5:]:
                    # Convert -HHMM to -HH:MM
                    parts = created.rsplit('-', 1)
                    if len(parts) == 2:
                        tz = parts[1]
                        if len(tz) == 4:  # HHMM format
                            created = f"{parts[0]}-{tz[:2]}:{tz[2:]}"
                try:
                    created_date = datetime.fromisoformat(created)
                except ValueError as e:
                    logger.debug(f"Invalid timestamp format: {created}")
                    continue
                
                for item in history.get('items', []):
                    if item.get('field') == 'status':
                        to_status = item.get('toString', '').strip()
                        
                        # Check against mapped statuses
                        for transition_key, valid_statuses in STATUS_MAPPING.items():
                            if to_status.lower() in {s.lower() for s in valid_statuses}:
                                if (transitions[transition_key] is None or
                                    created_date > transitions[transition_key]):
                                    transitions[transition_key] = created_date
                                break

        except Exception as e:
            # Only log unique timestamp format errors once
            if "Invalid isoformat string" in str(e):
                error_msg = str(e).split(": ")[1] if ": " in str(e) else str(e)
                logger.debug(f"Skipping invalid timestamp: {error_msg}")
            else:
                logger.error(f"Error processing transitions: {e}")
            
        return transitions

    def _get_location_name(self, project_key: str, fields: Dict[str, Any]) -> str:
        """
        Get location name from JIRA project name.
        
        Args:
            project_key: Project key
            fields: JIRA issue fields
            
        Returns:
            Location name string
        """
        try:
            # First try to get the project name directly from JIRA
            project_name = fields.get('project', {}).get('name')
            if project_name:
                return project_name
                
            # If no project name in JIRA, try to get from project_mappings_v2 table
            project_mapping = get_project_mapping(project_key)
            if project_mapping and project_mapping.get('location_name'):
                return project_mapping['location_name']
                
            # Last resort: use project key
            return project_key
            
        except Exception as e:
            logger.debug(f"Error getting location name for {project_key}: {e}")
            # Fall back to project key
            return project_key
    
    @staticmethod
    def _format_error_summary(errors):
        """Format error summary to avoid duplicate messages."""
        if not errors:
            return ""
        
        error_counts = {}
        for error in errors:
            error_counts[error] = error_counts.get(error, 0) + 1
            
        summary = []
        for error, count in error_counts.items():
            if count > 1:
                summary.append(f"{error} (x{count})")
            else:
                summary.append(error)
                
        return "\n".join(summary)