"""
Issue manager that interfaces with the existing JIRA and database logic
"""
import logging
from typing import List, Optional
from datetime import datetime

from core.db.db_issues import get_issue_by_key, get_project_issues as db_get_project_issues, get_issues_since
from core.cache import cache_result
from models.schemas import JiraIssue, JiraField

logger = logging.getLogger(__name__)


class IssueManager:
    """Manages JIRA issue operations"""
    
    @cache_result("issues", ttl=110)
    def get_issue(self, issue_key: str) -> Optional[JiraIssue]:
        """Get a single issue by key"""
        try:
            # Get issue from database
            issue_data = get_issue_by_key(issue_key)
            if not issue_data:
                return None
            
            # Convert to schema
            return self._convert_to_schema(issue_data)
        except Exception as e:
            logger.error(f"Failed to get issue {issue_key}: {e}")
            raise
    
    @cache_result("search", ttl=110)
    def search_issues(self, query: str, limit: int = 10) -> List[JiraIssue]:
        """Search for issues by key pattern"""
        try:
            # Use get_project_issues if query looks like a project key
            if '-' not in query and query.isupper():
                results = db_get_project_issues(query, limit=limit)
            else:
                # Get specific issue if full key provided
                issue = get_issue_by_key(query)
                results = [issue] if issue else []
            
            return [self._convert_to_schema(issue) for issue in results if issue]
        except Exception as e:
            logger.error(f"Failed to search issues: {e}")
            raise
    
    @cache_result("project", ttl=110)
    def get_project_issues(self, project_key: str, limit: int = 50, offset: int = 0) -> List[JiraIssue]:
        """Get all issues for a project"""
        try:
            results = db_get_project_issues(project_key, limit=limit, offset=offset)
            return [self._convert_to_schema(issue) for issue in results if issue]
        except Exception as e:
            logger.error(f"Failed to get project issues: {e}")
            raise
    
    @cache_result("recent", ttl=110)
    def get_recent_issues(self, limit: int = 10) -> List[JiraIssue]:
        """Get recently updated issues"""
        try:
            # Get issues from the last 7 days
            from datetime import timedelta
            since = datetime.now() - timedelta(days=7)
            results = get_issues_since(since, limit=limit)
            return [self._convert_to_schema(issue) for issue in results if issue]
        except Exception as e:
            logger.error(f"Failed to get recent issues: {e}")
            raise
    
    def _convert_to_schema(self, issue_data: dict) -> JiraIssue:
        """Convert database issue to API schema"""
        # Extract fields
        fields = []
        
        # Add custom fields
        for key, value in issue_data.items():
            if key.startswith('customfield_') or key in ['ndis_plan_managementype', 'listing_agent_name']:
                fields.append(JiraField(
                    field_id=key,
                    field_name=key.replace('_', ' ').title(),
                    field_type='string',
                    value=value,
                    instance=issue_data.get('instance', 'instance_1')
                ))
        
        # Determine JIRA instance URL
        instance = issue_data.get('instance', 'instance_1')
        base_url = "https://betteredits.atlassian.net" if instance == 'instance_1' else "https://betteredits2.atlassian.net"
        
        return JiraIssue(
            issue_key=issue_data['issue_key'],
            summary=issue_data.get('summary', ''),
            status=issue_data.get('status', 'Unknown'),
            issue_type=issue_data.get('issue_type', 'Task'),
            created=issue_data.get('created', datetime.now()),
            updated=issue_data.get('updated', datetime.now()),
            project_key=issue_data.get('project_key', issue_data['issue_key'].split('-')[0]),
            instance=instance,
            fields=fields,
            url=f"{base_url}/browse/{issue_data['issue_key']}"
        )