"""
Core JIRA API client functionality with rate limiting and error handling.
"""

import logging
import time
import requests
from requests.auth import HTTPBasicAuth
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from typing import Dict, Any, Optional, List
from datetime import datetime
from ..config.performance_config import get_performance_config

# Configure logging
logger = logging.getLogger(__name__)

# Default constants (can be overridden by performance config)
MAX_RETRIES = 3
BACKOFF_FACTOR = 0.5
TIMEOUT = 60  # Increased from 30
RATE_LIMIT_PAUSE = 0.5  # seconds between requests
BATCH_SIZE = 100 # Reduced from 200

class JiraClientError(Exception):
    """Base exception for JIRA client errors"""
    pass

class JiraRateLimitError(JiraClientError):
    """Exception for rate limiting issues"""
    pass

class JiraAuthenticationError(JiraClientError):
    """Exception for authentication issues"""
    pass

class JiraApiError(JiraClientError):
    """Exception for API-related issues"""
    pass

class JiraClient:
    """
    JIRA API client with built-in rate limiting and error handling.
    """
    
    def __init__(
        self,
        url: str,
        username: str,
        password: str,
        rate_limit_pause: float = RATE_LIMIT_PAUSE,
        timeout: int = TIMEOUT
    ):
        """
        Initialize JIRA client.
        
        Args:
            url: JIRA instance URL
            username: JIRA username
            password: JIRA password/token
            rate_limit_pause: Pause between requests
            timeout: Request timeout in seconds
        """
        self.base_url = url.rstrip('/')
        self.auth = HTTPBasicAuth(username, password)
        
        # Load performance configuration
        self.perf_config = get_performance_config()
        self.rate_limit_pause = self.perf_config.get('rate_limit_pause', rate_limit_pause)
        self.timeout = timeout
        self.connection_pool_size = self.perf_config.get('connection_pool_size', 20)
        self.connection_pool_block = self.perf_config.get('connection_pool_block', False)
        
        self.session = self._create_session()
        self.last_request_time = 0

    def _create_session(self) -> requests.Session:
        """Create a requests session with retry logic and optimized connection pool."""
        session = requests.Session()
        
        retry_strategy = Retry(
            total=MAX_RETRIES,
            backoff_factor=BACKOFF_FACTOR,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        
        # Create adapter with configurable connection pool size
        # Use values from performance config, with sensible defaults
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=self.connection_pool_size,  # Number of connection pools to cache
            pool_maxsize=self.connection_pool_size,      # Maximum number of connections to save in the pool
            pool_block=self.connection_pool_block        # Whether to block when pool is exhausted
        )
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        session.auth = self.auth
        
        return session

    def _wait_for_rate_limit(self):
        """Implement rate limiting."""
        now = time.time()
        time_since_last_request = now - self.last_request_time
        
        if time_since_last_request < self.rate_limit_pause:
            time.sleep(self.rate_limit_pause - time_since_last_request)
        
        self.last_request_time = time.time()

    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        data: Optional[Dict] = None,
        headers: Optional[Dict] = None
    ) -> Dict:
        """
        Make a request to the JIRA API with rate limiting and error handling.
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            params: Query parameters
            data: Request body
            headers: Request headers
            
        Returns:
            Dict containing response data
            
        Raises:
            JiraClientError: If request fails
        """
        self._wait_for_rate_limit()
        
        default_headers = {
            "Accept": "application/json",
            "User-Agent": "JiraSync/2.0"
        }
        
        if headers:
            default_headers.update(headers)
            
        url = f"{self.base_url}/rest/api/2/{endpoint.lstrip('/')}"
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                json=data,
                headers=default_headers,
                timeout=self.timeout
            )
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.HTTPError as e:
            if response.status_code == 429:
                retry_after = int(response.headers.get('Retry-After', 60))
                raise JiraRateLimitError(
                    f"Rate limit exceeded. Retry after {retry_after} seconds"
                )
            elif response.status_code == 401:
                raise JiraAuthenticationError("Authentication failed")
            else:
                raise JiraApiError(f"HTTP error occurred: {e}")
                
        except requests.exceptions.RequestException as e:
            raise JiraClientError(f"Request failed: {e}")

    def get_projects(self) -> List[Dict[str, Any]]:
        """
        Get all accessible projects.
        
        Returns:
            List of project dictionaries
        """
        return self._make_request('GET', 'project')

    def search_issues(
        self,
        jql: str,
        fields: List[str],
        start_at: int = 0,
        max_results: int = BATCH_SIZE,
        expand: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Search for issues using JQL.
        
        Args:
            jql: JQL query string
            fields: List of fields to retrieve
            start_at: Starting index
            max_results: Maximum results to return
            expand: Fields to expand
            
        Returns:
            Dict containing search results
        """
        params = {
            'jql': jql,
            'fields': ','.join(fields),
            'startAt': start_at,
            'maxResults': max_results
        }
        
        if expand:
            params['expand'] = ','.join(expand)
            
        return self._make_request('GET', 'search', params=params)

    def get_issue(
        self,
        issue_key: str,
        fields: Optional[List[str]] = None,
        expand: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Get a single issue by key.
        
        Args:
            issue_key: JIRA issue key
            fields: List of fields to retrieve
            expand: Fields to expand
            
        Returns:
            Dict containing issue data
        """
        params = {}
        
        if fields:
            params['fields'] = ','.join(fields)
        if expand:
            params['expand'] = ','.join(expand)
            
        return self._make_request('GET', f'issue/{issue_key}', params=params)

    def get_issue_changelog(self, issue_key: str) -> List[Dict[str, Any]]:
        """
        Get the changelog for an issue.
        
        Args:
            issue_key: JIRA issue key
            
        Returns:
            List of changelog entries
        """
        return self._make_request(
            'GET',
            f'issue/{issue_key}/changelog'
        ).get('values', [])

    def get_field_metadata(self) -> List[Dict[str, Any]]:
        """
        Get metadata about available fields.
        
        Returns:
            List of field metadata dictionaries
        """
        return self._make_request('GET', 'field')
    
    def get_fields(self) -> List[Dict[str, Any]]:
        """
        Alias for get_field_metadata for compatibility.
        
        Returns:
            List of field metadata dictionaries
        """
        return self.get_field_metadata()