#!/usr/bin/env python3
"""
Move INUA-455 and INUA-456 to Shoot Complete status
"""

import time
import os
from dotenv import load_dotenv
import requests
from requests.auth import HTTPBasicAuth

load_dotenv()

def transition_issue(issue_key, transition_id, comment=None):
    """Execute a transition on an issue"""
    email = os.getenv('JIRA_CREATE_EMAIL', '').strip('"')
    token = os.getenv('JIRA_CREATE_TOKEN', '').strip('"')
    auth = HTTPBasicAuth(email, token)
    
    # INUA is on instance 2
    base_url = "https://betteredits2.atlassian.net"
    trans_url = f"{base_url}/rest/api/2/issue/{issue_key}/transitions"
    
    data = {"transition": {"id": str(transition_id)}}
    if comment:
        data["update"] = {"comment": [{"add": {"body": comment}}]}
    
    response = requests.post(trans_url, auth=auth, json=data)
    return response.status_code == 204

def get_issue_status(issue_key):
    """Get current status of an issue"""
    email = os.getenv('JIRA_CREATE_EMAIL', '').strip('"')
    token = os.getenv('JIRA_CREATE_TOKEN', '').strip('"')
    auth = HTTPBasicAuth(email, token)
    
    base_url = "https://betteredits2.atlassian.net"
    url = f"{base_url}/rest/api/2/issue/{issue_key}"
    
    response = requests.get(url, auth=auth)
    if response.status_code == 200:
        return response.json()['fields']['status']['name']
    return None

def move_to_shoot_complete(issue_key, location):
    """Move issue through workflow to Shoot Complete"""
    
    print(f"\nMoving {issue_key} to Shoot Complete...")
    print("-" * 40)
    
    # Check current status
    current_status = get_issue_status(issue_key)
    print(f"Current status: {current_status}")
    
    transitions = [
        {
            "from": "Scheduled",
            "to": "ACKNOWLEDGED",
            "id": "31",
            "comment": f"Photographer assigned for {location}"
        },
        {
            "from": "ACKNOWLEDGED",
            "to": "At Listing",
            "id": "171",
            "comment": f"Photographer arrived at {location}"
        },
        {
            "from": "At Listing",
            "to": "Shoot Complete",
            "id": "201",
            "comment": f"Photography completed at {location}. 30 RAW photos taken."
        }
    ]
    
    # Execute transitions
    for trans in transitions:
        current = get_issue_status(issue_key)
        
        if current == trans["from"]:
            print(f"\n→ Moving from {trans['from']} to {trans['to']}...")
            success = transition_issue(issue_key, trans["id"], trans["comment"])
            
            if success:
                print(f"✅ Now in: {trans['to']}")
                time.sleep(1)
            else:
                print(f"❌ Failed to transition")
                break
        elif current == trans["to"]:
            print(f"✓ Already in {trans['to']}")
    
    # Final status check
    final_status = get_issue_status(issue_key)
    print(f"\nFinal status: {final_status}")
    return final_status == "Shoot Complete"

def main():
    print("="*60)
    print("Moving Test Issues to Shoot Complete")
    print("="*60)
    
    # Read issue keys
    with open("upload_test_issues.txt", "r") as f:
        lines = f.readlines()
        issue1_key = lines[0].strip()
        issue2_key = lines[1].strip()
    
    print(f"\nIssue 1: {issue1_key}")
    print(f"Issue 2: {issue2_key}")
    
    # Move both issues
    success1 = move_to_shoot_complete(issue1_key, "456 Oak Street")
    success2 = move_to_shoot_complete(issue2_key, "789 Pine Avenue")
    
    # Summary
    print("\n" + "="*60)
    print("✅ Issues Ready for Upload Test")
    print("="*60)
    
    if success1:
        print(f"\n📸 {issue1_key} - Ready at Shoot Complete")
        print(f"   https://betteredits2.atlassian.net/browse/{issue1_key}")
        print("   👉 Please manually transition this to 'Uploaded' and note the required fields")
    
    if success2:
        print(f"\n📸 {issue2_key} - Ready at Shoot Complete")
        print(f"   https://betteredits2.atlassian.net/browse/{issue2_key}")
        print("   👉 I'll transition this one programmatically once you share the field requirements")

if __name__ == "__main__":
    main()