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
    IssueFetcher,
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
    'IssueFetcher',
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

def create_issue_fetcher(
    client: JiraClient,
    **kwargs
) -> IssueFetcher:
    """
    Create a configured issue fetcher.
    
    Args:
        client: JIRA client instance
        **kwargs: Additional fetcher configuration
        
    Returns:
        Configured IssueFetcher instance
    """
    return IssueFetcher(client, **kwargs)

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