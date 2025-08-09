"""
INUA Test Routes - Simple interface for testing JIRA card creation and transitions
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import os
from datetime import datetime
import requests
from requests.auth import HTTPBasicAuth
from pathlib import Path
import logging

# These modules are not available in the backend folder
# TODO: Move these modules to backend or comment out this route
# from jira_issue_manager import JiraIssueManager
# from change_issue_status import change_issue_status
# from inua_workflow_helper import update_issue_field

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/admin/inua-test", tags=["inua-test"])

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Pydantic models
class CreateIssueRequest(BaseModel):
    summary: str
    
class TransitionRequest(BaseModel):
    issue_key: str
    target_status: str
    comment: Optional[str] = None
    field_updates: Optional[Dict[str, Any]] = None

class IssueResponse(BaseModel):
    key: str
    summary: str
    status: str
    status_category: str
    created: str
    url: str
    transitions: List[Dict[str, Any]]

class TransitionResponse(BaseModel):
    success: bool
    message: str
    new_status: Optional[str] = None

# Helper functions
def get_jira_auth():
    """Get JIRA authentication"""
    email = os.getenv('JIRA_CREATE_EMAIL', '').strip('"')
    token = os.getenv('JIRA_CREATE_TOKEN', '').strip('"')
    return HTTPBasicAuth(email, token)

def get_issue_details(issue_key: str) -> Dict[str, Any]:
    """Get issue details from JIRA"""
    auth = get_jira_auth()
    base_url = "https://betteredits2.atlassian.net"
    
    # Get issue details
    url = f"{base_url}/rest/api/2/issue/{issue_key}"
    response = requests.get(url, auth=auth)
    
    if response.status_code != 200:
        raise HTTPException(status_code=404, detail=f"Issue {issue_key} not found")
    
    issue_data = response.json()
    
    # Get available transitions
    trans_url = f"{base_url}/rest/api/2/issue/{issue_key}/transitions"
    trans_response = requests.get(trans_url, auth=auth)
    
    transitions = []
    if trans_response.status_code == 200:
        trans_data = trans_response.json()
        transitions = [
            {
                "id": t["id"],
                "name": t["name"],
                "to": t["to"]["name"]
            }
            for t in trans_data.get("transitions", [])
        ]
    
    return {
        "key": issue_data["key"],
        "summary": issue_data["fields"]["summary"],
        "status": issue_data["fields"]["status"]["name"],
        "status_category": issue_data["fields"]["status"]["statusCategory"]["name"],
        "created": issue_data["fields"]["created"],
        "url": f"{base_url}/browse/{issue_key}",
        "transitions": transitions
    }

# API Endpoints
@router.post("/create-issue", response_model=IssueResponse)
async def create_test_issue(request: CreateIssueRequest):
    """Create a new test issue in INUA project"""
    try:
        # Initialize JIRA manager
        manager = JiraIssueManager(use_create_account=True)
        
        # Add timestamp to summary
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        full_summary = f"TEST_{timestamp} - {request.summary}"
        
        # Create issue
        issue = manager.create_issue(
            project_key="INUA",
            summary=full_summary,
            issue_type="NDP Photo / Video Service"
        )
        
        if not issue:
            raise HTTPException(status_code=400, detail="Failed to create issue")
        
        # Get full details including transitions
        issue_details = get_issue_details(issue["key"])
        
        return IssueResponse(**issue_details)
        
    except Exception as e:
        logger.error(f"Error creating issue: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/transition", response_model=TransitionResponse)
async def transition_issue(request: TransitionRequest):
    """Transition an issue to a new status"""
    try:
        # Handle field updates if needed
        if request.field_updates:
            for field_id, value in request.field_updates.items():
                if not update_issue_field(request.issue_key, field_id, value):
                    raise HTTPException(
                        status_code=400, 
                        detail=f"Failed to update field {field_id}"
                    )
        
        # Perform transition
        success = change_issue_status(
            issue_key=request.issue_key,
            target_status=request.target_status,
            comment_text=request.comment
        )
        
        if not success:
            return TransitionResponse(
                success=False,
                message=f"Failed to transition to {request.target_status}"
            )
        
        # Get new status
        issue_details = get_issue_details(request.issue_key)
        
        return TransitionResponse(
            success=True,
            message=f"Successfully transitioned to {issue_details['status']}",
            new_status=issue_details["status"]
        )
        
    except Exception as e:
        logger.error(f"Error transitioning issue: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/issue/{issue_key}", response_model=IssueResponse)
async def get_issue(issue_key: str):
    """Get current issue status and available transitions"""
    try:
        issue_details = get_issue_details(issue_key)
        return IssueResponse(**issue_details)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting issue: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/issue/{issue_key}")
async def delete_issue(issue_key: str):
    """Delete a test issue"""
    try:
        auth = get_jira_auth()
        base_url = "https://betteredits2.atlassian.net"
        url = f"{base_url}/rest/api/2/issue/{issue_key}"
        
        response = requests.delete(url, auth=auth)
        
        if response.status_code == 204:
            return {"success": True, "message": f"Issue {issue_key} deleted"}
        elif response.status_code == 404:
            raise HTTPException(status_code=404, detail="Issue not found")
        else:
            raise HTTPException(
                status_code=response.status_code, 
                detail="Failed to delete issue"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting issue: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/transitions/{issue_key}")
async def get_available_transitions(issue_key: str):
    """Get available transitions for an issue"""
    try:
        auth = get_jira_auth()
        base_url = "https://betteredits2.atlassian.net"
        url = f"{base_url}/rest/api/2/issue/{issue_key}/transitions"
        
        response = requests.get(url, auth=auth)
        
        if response.status_code != 200:
            raise HTTPException(status_code=404, detail="Issue not found")
        
        data = response.json()
        transitions = [
            {
                "id": t["id"],
                "name": t["name"],
                "to": t["to"]["name"],
                "fields": list(t.get("fields", {}).keys())
            }
            for t in data.get("transitions", [])
        ]
        
        return {"transitions": transitions}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting transitions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/workflow-info")
async def get_workflow_info():
    """Get INUA workflow information"""
    return {
        "workflow": [
            {"status": "Scheduled", "order": 1, "initial": True},
            {"status": "ACKNOWLEDGED", "order": 2},
            {"status": "At Listing", "order": 3},
            {"status": "Shoot Complete", "order": 4},
            {"status": "Uploaded", "order": 5, "requires_field": "customfield_12602"},
            {"status": "Edit", "order": 6},
            {"status": "Final Review", "order": 7},
            {"status": "Closed", "order": 8, "final": True},
            {"status": "Escalated Editing", "order": 8, "alternate": True, "requires_field": "customfield_10716"}
        ],
        "field_info": {
            "customfield_12602": {
                "name": "NDPU Number of Raw Photos",
                "type": "string",
                "description": "Number of photos taken (e.g., '25')"
            },
            "customfield_10716": {
                "name": "NDPU Edited Media Revision Notes",
                "type": "string",
                "description": "Notes for escalation (e.g., 'Needs color correction')"
            }
        }
    }