"""
Dynamic JIRA issue processing with configurable field mappings.
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from dateutil import parser

from .jira_client import JiraClient, JiraClientError
from .field_processor import FieldProcessor
from ..db.db_issues import batch_insert_issues
from ..db.db_config import get_field_mapping_config
from ..db.constants import ISSUE_COLUMNS
from ..db.db_audit import log_operation

# Configure logging
logger = logging.getLogger(__name__)

class IssueProcessingError(Exception):
    """Custom exception for issue processing errors"""
    pass

def log_update(project_name: str, status: str, issues_count: int = 0, error_message: str = None):
    """Log update to database."""
    try:
        log_operation('UPDATE', project_name, status, issues_count, error_message)
    except Exception as e:
        logger.error(f"Failed to log update: {e}")

class IssueProcessor:
    """
    Processes JIRA issues with dynamic field mapping from configuration.
    """
    
    def __init__(self, jira_client: JiraClient, instance_type: str):
        """
        Initialize issue processor.
        
        Args:
            jira_client: JIRA client instance
            instance_type: Type of JIRA instance (instance_1 or instance_2)
        """
        self.jira_client = jira_client
        self.instance_type = instance_type
        self.field_processor = FieldProcessor()
        self._load_field_mappings()
        
    def _load_field_mappings(self):
        """Load field mappings from database configuration."""
        try:
            config = get_field_mapping_config()
            if config:
                self.field_mappings = config.get('field_groups', {})
                logger.info(f"Loaded field mappings with {sum(len(g.get('fields', {})) for g in self.field_mappings.values())} fields")
            else:
                self.field_mappings = {}
                logger.warning("No field mappings found in configuration")
        except Exception as e:
            logger.error(f"Failed to load field mappings: {e}")
            self.field_mappings = {}
    
    def reload_mappings(self):
        """Reload field mappings from database."""
        self._load_field_mappings()
    
    def get_field_mapping_for_column(self, column_name: str) -> Optional[Dict]:
        """
        Get field mapping configuration for a database column.
        
        Args:
            column_name: Database column name
            
        Returns:
            Field mapping configuration or None
        """
        for group in self.field_mappings.values():
            fields = group.get('fields', {})
            if column_name in fields:
                field_config = fields[column_name]
                instance_config = field_config.get(self.instance_type, {})
                
                # Build complete mapping
                return {
                    'field_id': instance_config.get('field_id'),
                    'field_ids': instance_config.get('field_ids'),  # For combined fields
                    'type': field_config.get('type', 'string'),
                    'system_field': field_config.get('system_field', False),
                    'field_path': field_config.get('field_path'),
                    'source': field_config.get('source'),
                    'combine_method': field_config.get('combine_method', 'space')
                }
        return None
    
    def extract_field_value(self, issue_data: Dict, field_mapping: Dict) -> Any:
        """
        Extract field value based on mapping configuration.
        
        Args:
            issue_data: Complete issue data from JIRA
            field_mapping: Field mapping configuration
            
        Returns:
            Extracted and processed field value
        """
        if not field_mapping:
            return None
        
        # Handle different field sources
        source = field_mapping.get('source', 'field')
        
        if source == 'transitions':
            # Extract from issue transitions/changelog
            return self._extract_from_transitions(
                issue_data.get('changelog', {}),
                field_mapping.get('transition_name')
            )
        
        elif source == 'system':
            # Extract from system field path
            field_path = field_mapping.get('field_path', '')
            return self._extract_by_path(issue_data, field_path)
        
        elif field_mapping.get('field_ids'):
            # Combine multiple fields
            values = []
            for field_id in field_mapping['field_ids']:
                value = self._extract_custom_field(issue_data.get('fields', {}), field_id)
                if value:
                    values.append(str(value))
            
            if values:
                combine_method = field_mapping.get('combine_method', 'space')
                if combine_method == 'space':
                    return ' '.join(values)
                elif combine_method == 'comma':
                    return ', '.join(values)
                elif combine_method == 'first':
                    return values[0] if values else None
            return None
        
        elif field_mapping.get('field_id'):
            # Single custom field
            return self._extract_custom_field(
                issue_data.get('fields', {}),
                field_mapping['field_id']
            )
        
        elif field_mapping.get('field_path'):
            # System field with path
            return self._extract_by_path(issue_data, field_mapping['field_path'])
        
        return None
    
    def _extract_by_path(self, data: Dict, path: str) -> Any:
        """Extract value by dot-notation path."""
        if not path:
            return None
        
        parts = path.split('.')
        current = data
        
        for part in parts:
            if isinstance(current, dict):
                current = current.get(part)
            else:
                return None
            
            if current is None:
                return None
        
        return current
    
    def _extract_custom_field(self, fields: Dict, field_id: str) -> Any:
        """Extract custom field value."""
        if not field_id:
            return None
        
        value = fields.get(field_id)
        
        # Handle special field types
        if isinstance(value, dict):
            # Option field
            if 'value' in value:
                return value['value']
            # User field
            elif 'displayName' in value:
                return value['displayName']
            # Other complex field
            elif 'name' in value:
                return value['name']
        
        return value
    
    def _extract_from_transitions(self, changelog: Dict, transition_name: str) -> Optional[datetime]:
        """Extract timestamp from issue transitions."""
        if not changelog or not transition_name:
            return None
        
        # Map of transition names to status values
        transition_mappings = {
            'scheduled': ['scheduled', 'Scheduled'],
            'acknowledged': ['acknowledged', 'ACKNOWLEDGED', 'Acknowledged'],
            'at_listing': ['at listing', 'At Listing', 'AT LISTING'],
            'shoot_complete': ['shoot complete', 'Shoot Complete', 'SHOOT COMPLETE'],
            'uploaded': ['uploaded', 'Uploaded', 'UPLOADED'],
            'edit_start': ['edit start', 'Edit Start', 'Edit', 'EDIT'],
            'final_review': ['final review', 'Final Review', 'Managing Partner Ready'],
            'closed': ['closed', 'Closed', 'CLOSED', 'Complete', 'Done']
        }
        
        valid_statuses = transition_mappings.get(transition_name, [transition_name])
        latest_timestamp = None
        
        for history in changelog.get('histories', []):
            created = history.get('created')
            if not created:
                continue
            
            try:
                # Parse timestamp
                timestamp = parser.parse(created)
                
                # Check status changes
                for item in history.get('items', []):
                    if item.get('field') == 'status':
                        to_status = item.get('toString', '')
                        if any(status.lower() == to_status.lower() for status in valid_statuses):
                            if not latest_timestamp or timestamp > latest_timestamp:
                                latest_timestamp = timestamp
            except Exception as e:
                logger.debug(f"Failed to parse transition timestamp: {e}")
                continue
        
        return latest_timestamp
    
    def fetch_project_issues(
        self,
        project_key: str,
        start_at: int = 0,
        updated_after: Optional[datetime] = None,
        stop_check: Optional[callable] = None,
        batch_size: int = 100
    ) -> List[Tuple]:
        """
        Fetch and process issues for a project using dynamic field mappings.
        
        Args:
            project_key: JIRA project key
            start_at: Starting index for pagination
            updated_after: Fetch only issues updated after this time
            stop_check: Function to check if sync should stop
            batch_size: Number of issues per batch
            
        Returns:
            List of processed issue tuples ready for database insertion
        """
        try:
            logger.info(f"Fetching issues for project {project_key} using dynamic field mappings")
            
            # Reload mappings to get latest configuration
            self.reload_mappings()
            
            # Build JQL query
            jql = f'project = {project_key}'
            if updated_after:
                jql += f' AND updated >= "{updated_after.strftime("%Y-%m-%d %H:%M")}"'
            jql += ' ORDER BY updated DESC'
            
            issues_data = []
            total_fetched = 0
            fetch_start_time = datetime.now()
            
            while True:
                if stop_check and stop_check():
                    logger.info(f"Sync stopped by user for project {project_key}")
                    break
                
                # Fetch batch with changelog for transitions
                result = self.jira_client.search_issues(
                    jql=jql,
                    start_at=start_at + total_fetched,
                    max_results=batch_size,
                    expand=['changelog']
                )
                
                if not result or 'issues' not in result:
                    break
                
                batch_issues = result['issues']
                if not batch_issues:
                    break
                
                # Process each issue
                for issue in batch_issues:
                    try:
                        processed = self.process_issue(issue, project_key)
                        if processed:
                            issues_data.append(processed)
                    except Exception as e:
                        logger.debug(f"Failed to process issue {issue.get('key', 'unknown')}: {e}")
                        continue
                
                total_fetched += len(batch_issues)
                
                # Check if more issues available
                total_available = result.get('total', 0)
                if start_at + total_fetched >= total_available:
                    break
                
                logger.debug(f"Fetched {total_fetched}/{total_available} issues for {project_key}")
            
            # Log completion
            total_duration = (datetime.now() - fetch_start_time).total_seconds()
            if issues_data:
                processing_rate = len(issues_data) / total_duration
                logger.info(
                    f"Completed fetching {len(issues_data)} issues for project "
                    f"{project_key} in {total_duration:.2f}s "
                    f"({processing_rate:.2f} issues/s)"
                )
            
            return issues_data
            
        except Exception as e:
            error_msg = f"Failed to fetch issues for project {project_key}: {e}"
            logger.error(error_msg)
            log_update(project_key, "Failed", error_message=error_msg)
            raise IssueProcessingError(error_msg)
    
    def process_issue(
        self,
        issue: Dict[str, Any],
        project_key: str
    ) -> Optional[Tuple]:
        """
        Process individual JIRA issue using dynamic field mappings.
        
        Args:
            issue: Raw issue data from JIRA
            project_key: Project key
            
        Returns:
            Tuple of processed issue data matching ISSUE_COLUMNS order
        """
        try:
            issue_key = issue.get('key')
            
            # Build record tuple matching ISSUE_COLUMNS order
            record = []
            
            for column in ISSUE_COLUMNS:
                # Special handling for certain columns
                if column == 'issue_key':
                    record.append(issue_key)
                elif column == 'project_name':
                    record.append(project_key)
                elif column == 'last_updated':
                    # Use JIRA's updated timestamp or current time
                    updated = self._extract_by_path(issue, 'fields.updated')
                    if updated:
                        try:
                            record.append(parser.parse(updated))
                        except:
                            record.append(datetime.now())
                    else:
                        record.append(datetime.now())
                else:
                    # Get field mapping for this column
                    mapping = self.get_field_mapping_for_column(column)
                    
                    if mapping:
                        # Extract value using mapping
                        value = self.extract_field_value(issue, mapping)
                        
                        # Sanitize based on type
                        field_type = mapping.get('type', 'string')
                        sanitized = self.field_processor.sanitize_value(value, field_type, column)
                        record.append(sanitized)
                    else:
                        # No mapping found, use None
                        record.append(None)
            
            # Validate record structure
            if len(record) != len(ISSUE_COLUMNS):
                logger.error(
                    f"Record structure mismatch for {issue_key}: "
                    f"Expected {len(ISSUE_COLUMNS)} columns, got {len(record)}"
                )
                return None
            
            return tuple(record)
            
        except Exception as e:
            issue_key = issue.get('key', 'unknown')
            logger.debug(f"Failed to process {issue_key}: {e}")
            return None
    
    def store_issues(self, issues_data: List[Tuple]) -> int:
        """
        Store processed issues in database.
        
        Args:
            issues_data: List of issue tuples
            
        Returns:
            Number of issues stored
        """
        if not issues_data:
            return 0
        
        try:
            return batch_insert_issues(issues_data)
        except Exception as e:
            logger.error(f"Failed to store issues: {e}")
            raise IssueProcessingError(f"Database storage failed: {e}")