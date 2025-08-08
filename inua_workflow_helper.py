#!/usr/bin/env python3
"""
Helper functions for INUA workflow transitions with field requirements
"""

import os
from dotenv import load_dotenv
import requests
from requests.auth import HTTPBasicAuth
import time

load_dotenv()

def update_issue_field(issue_key, field_id, value):
    """Update a field on an issue"""
    email = os.getenv('JIRA_CREATE_EMAIL', '').strip('"')
    token = os.getenv('JIRA_CREATE_TOKEN', '').strip('"')
    auth = HTTPBasicAuth(email, token)
    
    base_url = "https://betteredits2.atlassian.net"
    url = f"{base_url}/rest/api/2/issue/{issue_key}"
    
    data = {"fields": {field_id: value}}
    
    response = requests.put(url, auth=auth, json=data)
    return response.status_code == 204

def transition_to_uploaded_with_photos(issue_key, num_photos):
    """
    Transition from Shoot Complete to Uploaded with required photo count
    
    Args:
        issue_key: JIRA issue key (e.g., "INUA-456")
        num_photos: Number of raw photos as string (e.g., "10")
    
    Returns:
        bool: True if successful
    """
    from change_issue_status import change_issue_status
    
    print(f"Processing upload for {issue_key} with {num_photos} photos...")
    
    # Step 1: Update the NDPU Number of Raw Photos field
    print("1. Updating photo count field...")
    if not update_issue_field(issue_key, "customfield_12602", str(num_photos)):
        print("❌ Failed to update photo count")
        return False
    
    print("✅ Photo count updated")
    time.sleep(1)  # Allow field update to propagate
    
    # Step 2: Transition to Uploaded
    print("2. Transitioning to Uploaded...")
    if change_issue_status(issue_key, "Uploaded", f"Uploaded {num_photos} raw photos"):
        print(f"✅ {issue_key} successfully moved to Uploaded!")
        return True
    
    return False

def transition_to_escalation_with_notes(issue_key, revision_notes):
    """
    Transition from Final Review to Escalation Status with required notes
    
    Args:
        issue_key: JIRA issue key
        revision_notes: Revision notes text
    
    Returns:
        bool: True if successful
    """
    from change_issue_status import change_issue_status
    
    print(f"Processing escalation for {issue_key}...")
    
    # Step 1: Update the revision notes field
    print("1. Updating revision notes...")
    if not update_issue_field(issue_key, "customfield_10716", revision_notes):
        print("❌ Failed to update revision notes")
        return False
    
    print("✅ Revision notes updated")
    time.sleep(1)
    
    # Step 2: Transition to Escalation Status
    print("2. Transitioning to Escalation Status...")
    if change_issue_status(issue_key, "Escalation Status", f"Escalated: {revision_notes}"):
        print(f"✅ {issue_key} successfully moved to Escalation Status!")
        return True
    
    return False

def complete_inua_workflow(issue_key, num_photos="30"):
    """
    Move an INUA issue through the complete standard workflow
    
    Path: Scheduled → ACKNOWLEDGED → At Listing → Shoot Complete → Uploaded → Edit → Final Review → Closed
    """
    from change_issue_status import change_issue_status
    
    transitions = [
        ("ACKNOWLEDGED", "Photographer assigned"),
        ("At Listing", "Arrived at property"),
        ("Shoot Complete", f"{num_photos} photos taken")
    ]
    
    # Standard transitions
    for target_status, comment in transitions:
        if not change_issue_status(issue_key, target_status, comment):
            print(f"❌ Failed at {target_status}")
            return False
        time.sleep(1)
    
    # Upload with photo count
    if not transition_to_uploaded_with_photos(issue_key, num_photos):
        return False
    
    # Continue through editing
    time.sleep(1)
    if not change_issue_status(issue_key, "Edit", "Starting photo editing"):
        return False
    
    time.sleep(1)
    if not change_issue_status(issue_key, "Final Review", "Editing complete, ready for review"):
        return False
    
    time.sleep(1)
    if not change_issue_status(issue_key, "Closed", "Media delivered to client"):
        return False
    
    print(f"\n✅ {issue_key} completed full workflow!")
    return True

if __name__ == "__main__":
    # Example usage
    print("INUA Workflow Helper")
    print("="*50)
    print("\nExample functions:")
    print("1. transition_to_uploaded_with_photos('INUA-123', '25')")
    print("2. transition_to_escalation_with_notes('INUA-123', 'Needs color correction')")
    print("3. complete_inua_workflow('INUA-123', '30')")
    print("\nField requirements:")
    print("- Shoot Complete → Uploaded: NDPU Number of Raw Photos (customfield_12602)")
    print("- Final Review → Escalation: NDPU Edited Media Revision Notes (customfield_10716)")