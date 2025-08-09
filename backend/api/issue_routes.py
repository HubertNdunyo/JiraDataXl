"""
JIRA issue API routes
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
import logging
import sys
from pathlib import Path

# Add parent directory to import existing logic
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from models.schemas import JiraIssue, IssueSearchRequest
from core.issue_manager import IssueManager
from core.cache import cache_result

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize issue manager lazily
_issue_manager = None

def get_issue_manager():
    global _issue_manager
    if _issue_manager is None:
        _issue_manager = IssueManager()
    return _issue_manager


@router.get("/{issue_key}", response_model=JiraIssue)
async def get_issue(issue_key: str):
    """Get details for a specific JIRA issue"""
    try:
        # Validate issue key format
        if not issue_key or len(issue_key) < 3:
            raise HTTPException(status_code=400, detail="Invalid issue key format")
        
        issue_manager = get_issue_manager()
        issue = issue_manager.get_issue(issue_key)
        if not issue:
            raise HTTPException(status_code=404, detail=f"Issue {issue_key} not found")
        
        return issue
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get issue {issue_key}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search", response_model=List[JiraIssue])
async def search_issues(
    request: IssueSearchRequest,
    limit: int = Query(default=10, ge=1, le=100)
):
    """Search for JIRA issues"""
    try:
        issue_manager = get_issue_manager()
        issues = issue_manager.search_issues(request.issue_key, limit)
        return issues
    except Exception as e:
        logger.error(f"Failed to search issues: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/project/{project_key}/issues", response_model=List[JiraIssue])
async def get_project_issues(
    project_key: str,
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0)
):
    """Get all issues for a specific project"""
    try:
        issue_manager = get_issue_manager()
        issues = issue_manager.get_project_issues(project_key, limit, offset)
        return issues
    except Exception as e:
        logger.error(f"Failed to get project issues: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recent", response_model=List[JiraIssue])
async def get_recent_issues(
    limit: int = Query(default=10, ge=1, le=50)
):
    """Get recently updated issues"""
    try:
        issue_manager = get_issue_manager()
        issues = issue_manager.get_recent_issues(limit)
        return issues
    except Exception as e:
        logger.error(f"Failed to get recent issues: {e}")
        raise HTTPException(status_code=500, detail=str(e))