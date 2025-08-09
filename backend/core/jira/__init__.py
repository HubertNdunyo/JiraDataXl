"""
JIRA module initialization and interface.

This module provides a clean interface to the JIRA functionality,
abstracting away the implementation details into separate modules.
"""

from .jira_client import (
    JiraClient,
    JiraClientError,
    JiraRateLimitError,
    JiraAuthenticationError,
    JiraApiError
)

from .jira_issues import (
    IssueProcessor,
    IssueProcessingError
)

from .field_processor import (
    FieldProcessor,
    FieldProcessingError
)

__all__ = [
    # Client classes and exceptions
    'JiraClient',
    'JiraClientError',
    'JiraRateLimitError',
    'JiraAuthenticationError',
    'JiraApiError',
    
    # Issue handling
    'IssueProcessor',
    'IssueProcessingError',
    
    # Field processing
    'FieldProcessor',
    'FieldProcessingError'
]

def create_jira_client(
    url: str,
    username: str,
    password: str,
    **kwargs
) -> JiraClient:
    """
    Create a configured JIRA client.
    
    Args:
        url: JIRA instance URL
        username: JIRA username
        password: JIRA password/token
        **kwargs: Additional client configuration
        
    Returns:
        Configured JiraClient instance
    """
    return JiraClient(url, username, password, **kwargs)

def create_issue_processor(
    client: JiraClient,
    instance_type: str,
    **kwargs
) -> IssueProcessor:
    """
    Create a configured issue processor.
    
    Args:
        client: JIRA client instance
        instance_type: Type of JIRA instance (instance_1 or instance_2)
        **kwargs: Additional processor configuration
        
    Returns:
        Configured IssueProcessor instance
    """
    return IssueProcessor(client, instance_type, **kwargs)

def create_field_processor(
    config_path: str = None
) -> FieldProcessor:
    """
    Create a configured field processor.
    
    Args:
        config_path: Path to field configuration file
        
    Returns:
        Configured FieldProcessor instance
    """
    return FieldProcessor(config_path)