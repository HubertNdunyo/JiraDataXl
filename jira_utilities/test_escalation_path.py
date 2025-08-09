#!/usr/bin/env python3
"""
Test escalation path for INUA project
"""

import os
import time
from dotenv import load_dotenv
import requests
from requests.auth import HTTPBasicAuth
from jira_issue_manager import JiraIssueManager

load_dotenv()

def transition_issue(issue_key, transition_id, comment=None):
    """Execute a transition"""
    email = os.getenv('JIRA_CREATE_EMAIL', '').strip('"')
    token = os.getenv('JIRA_CREATE_TOKEN', '').strip('"')
    auth = HTTPBasicAuth(email, token)
    
    base_url = "https://betteredits2.atlassian.net"
    trans_url = f"{base_url}/rest/api/2/issue/{issue_key}/transitions"
    
    data = {"transition": {"id": str(transition_id)}}
    if comment:
        data["update"] = {"comment": [{"add": {"body": comment}}]}
    
    response = requests.post(trans_url, auth=auth, json=data)
    return response.status_code == 204

def update_field(issue_key, field_id, value):
    """Update a field"""
    email = os.getenv('JIRA_CREATE_EMAIL', '').strip('"')
    token = os.getenv('JIRA_CREATE_TOKEN', '').strip('"')
    auth = HTTPBasicAuth(email, token)
    
    base_url = "https://betteredits2.atlassian.net"
    url = f"{base_url}/rest/api/2/issue/{issue_key}"
    
    data = {"fields": {field_id: value}}
    
    response = requests.put(url, auth=auth, json=data)
    return response.status_code == 204

def get_status(issue_key):
    """Get current status"""
    email = os.getenv('JIRA_CREATE_EMAIL', '').strip('"')
    token = os.getenv('JIRA_CREATE_TOKEN', '').strip('"')
    auth = HTTPBasicAuth(email, token)
    
    base_url = "https://betteredits2.atlassian.net"
    url = f"{base_url}/rest/api/2/issue/{issue_key}?fields=status"
    
    response = requests.get(url, auth=auth)
    if response.status_code == 200:
        return response.json()['fields']['status']['name']
    return None

def main():
    print("="*60)
    print("Testing INUA Escalation Path")
    print("="*60)
    
    # Create a new test issue
    manager = JiraIssueManager(use_create_account=True)
    
    print("\n1. Creating new test issue...")
    issue = manager.create_issue(
        project_key="INUA",
        summary="Test Escalation Path - 321 Elm Street Photography",
        issue_type="NDP Photo / Video Service"
    )
    
    if not issue:
        print("❌ Failed to create issue")
        return
    
    issue_key = issue['key']
    print(f"✅ Created: {issue_key}")
    
    # Move through workflow quickly
    transitions = [
        ("31", "ACKNOWLEDGED", "Photographer assigned"),
        ("171", "At Listing", "Arrived at property"),
        ("201", "Shoot Complete", "25 photos taken")
    ]
    
    print("\n2. Moving through initial workflow...")
    for trans_id, status_name, comment in transitions:
        if transition_issue(issue_key, trans_id, comment):
            print(f"✅ {status_name}")
            time.sleep(1)
    
    # Upload with photo count
    print("\n3. Moving to Uploaded...")
    update_field(issue_key, "customfield_12602", "25")
    time.sleep(1)
    if transition_issue(issue_key, "51", "Photos uploaded"):
        print("✅ Uploaded")
    
    # Edit
    time.sleep(1)
    if transition_issue(issue_key, "71", "Starting editing"):
        print("✅ Edit")
    
    # Final Review
    time.sleep(1)
    if transition_issue(issue_key, "161", "Ready for review"):
        print("✅ Final Review")
    
    # Now test the Not Approved path
    print("\n4. Testing 'Not Approved' escalation path...")
    
    # Update revision notes
    revision_notes = "Major issues: Overexposed photos, color balance problems, needs reshoot"
    if update_field(issue_key, "customfield_10716", revision_notes):
        print("✅ Added revision notes")
    
    time.sleep(1)
    
    # Try Not Approved transition
    print("\nTransitioning via 'Not Approved' (ID: 181)...")
    if transition_issue(issue_key, "181", f"Not approved: {revision_notes}"):
        print("✅ Moved to Escalated Editing")
        
        # Check final status
        final_status = get_status(issue_key)
        print(f"\nFinal Status: {final_status}")
        print(f"URL: https://betteredits2.atlassian.net/browse/{issue_key}")
        
        print("\n📝 Discovery: The escalation path from Final Review is:")
        print("Final Review → 'Not Approved' (181) → Escalated Editing")
        print("This requires customfield_10716 (NDPU Edited Media Revision Notes)")
    else:
        print("❌ Failed to transition")

if __name__ == "__main__":
    main()