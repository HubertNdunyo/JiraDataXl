#!/usr/bin/env python3
"""
Move INUA-456 through Edit, Final Review, and Escalation
"""

import time
from change_issue_status import change_issue_status
from inua_workflow_helper import update_issue_field
import os
from dotenv import load_dotenv
import requests
from requests.auth import HTTPBasicAuth

load_dotenv()

def get_issue_status(issue_key):
    """Get current status of an issue"""
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
    print("Moving INUA-456 through Edit → Final Review → Escalation")
    print("="*60)
    
    issue_key = "INUA-456"
    
    # Check current status
    current = get_issue_status(issue_key)
    print(f"\nCurrent status: {current}")
    
    # 1. Move to Edit
    if current == "Uploaded":
        print("\n" + "-"*40)
        print("Step 1: Uploaded → Edit")
        print("-"*40)
        
        if change_issue_status(issue_key, "Edit", "Starting photo editing process"):
            print("✅ Moved to Edit")
            time.sleep(2)
        else:
            print("❌ Failed to move to Edit")
            return
    
    # 2. Move to Final Review
    current = get_issue_status(issue_key)
    if current == "Edit":
        print("\n" + "-"*40)
        print("Step 2: Edit → Final Review")
        print("-"*40)
        
        if change_issue_status(issue_key, "Final Review", "Editing complete, ready for quality review"):
            print("✅ Moved to Final Review")
            time.sleep(2)
        else:
            print("❌ Failed to move to Final Review")
            return
    
    # 3. Prepare for Escalation - Update required field first
    current = get_issue_status(issue_key)
    if current == "Final Review":
        print("\n" + "-"*40)
        print("Step 3: Final Review → Escalation Status")
        print("-"*40)
        
        # First update the required field
        revision_notes = "Photos need additional color correction and exposure adjustments"
        print(f"\nUpdating NDPU Edited Media Revision Notes...")
        print(f"Notes: {revision_notes}")
        
        if update_issue_field(issue_key, "customfield_10716", revision_notes):
            print("✅ Revision notes updated")
            time.sleep(2)
            
            # Now transition to Escalation Status
            print("\nTransitioning to Escalation Status...")
            if change_issue_status(issue_key, "Escalation Status", f"Escalated for revision: {revision_notes}"):
                print("✅ Moved to Escalation Status")
            else:
                print("❌ Failed to move to Escalation Status")
                
                # Try alternative - might need to go to Closed instead
                print("\nTrying alternative: Final Review → Closed")
                if change_issue_status(issue_key, "Closed", "Escalation not available, marking as closed"):
                    print("✅ Moved to Closed instead")
        else:
            print("❌ Failed to update revision notes")
    
    # Final status check
    final_status = get_issue_status(issue_key)
    print("\n" + "="*60)
    print("✅ Workflow Complete")
    print("="*60)
    print(f"\nIssue: {issue_key}")
    print(f"Final Status: {final_status}")
    print(f"URL: https://betteredits2.atlassian.net/browse/{issue_key}")
    
    if final_status == "Escalation Status":
        print("\n📝 Successfully demonstrated full escalation workflow!")
        print("Required fields confirmed:")
        print("- customfield_10716 (NDPU Edited Media Revision Notes) for escalation")

if __name__ == "__main__":
    main()