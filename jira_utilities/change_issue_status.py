#!/usr/bin/env python3
"""
Change JIRA issue status - demonstration script
"""

import os
from pathlib import Path
import requests
from requests.auth import HTTPBasicAuth
import json
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def change_issue_status(issue_key, target_status=None, comment_text=None):
    """
    Change the status of a JIRA issue
    
    Args:
        issue_key: The issue key (e.g., 'IT-1')
        target_status: The desired status name (e.g., 'In Progress', 'Done')
        comment_text: Optional comment to add when transitioning
    """
    
    email = os.getenv('JIRA_EMAIL')
    token = os.getenv('JIRA_ACCESS_TOKEN')
    
    if not email or not token:
        print("❌ Missing credentials in .env")
        return False
    
    auth = HTTPBasicAuth(email, token)
    
    # Determine which instance based on issue key
    if issue_key.startswith(('IT-', 'KZOO-', 'NECLT-', 'DENVER-')):
        base_url = "https://betteredits2.atlassian.net"
        instance = "Instance 2"
    else:
        base_url = "https://betteredits.atlassian.net"
        instance = "Instance 1"
    
    print(f"🔧 Working with {instance}: {base_url}")
    
    # 1. Get current issue status
    issue_url = f"{base_url}/rest/api/2/issue/{issue_key}"
    issue_response = requests.get(issue_url, auth=auth)
    
    if issue_response.status_code != 200:
        print(f"❌ Failed to get issue: {issue_response.status_code}")
        return False
    
    issue_data = issue_response.json()
    current_status = issue_data['fields']['status']['name']
    summary = issue_data['fields']['summary']
    
    print(f"\n📋 Issue: {issue_key}")
    print(f"   Summary: {summary}")
    print(f"   Current Status: {current_status}")
    
    # 2. Get available transitions
    trans_url = f"{base_url}/rest/api/2/issue/{issue_key}/transitions"
    trans_response = requests.get(trans_url, auth=auth)
    
    if trans_response.status_code != 200:
        print(f"❌ Failed to get transitions: {trans_response.status_code}")
        return False
    
    transitions = trans_response.json().get('transitions', [])
    
    if not transitions:
        print(f"❌ No transitions available from '{current_status}'")
        return False
    
    print(f"\n📊 Available transitions from '{current_status}':")
    for trans in transitions:
        print(f"   - {trans['name']} (id: {trans['id']}) → {trans['to']['name']}")
    
    # 3. Find the target transition
    if not target_status:
        print("\n❓ No target status specified. Options:")
        for i, trans in enumerate(transitions):
            print(f"   {i+1}. {trans['to']['name']}")
        
        choice = input("\nSelect target status (number): ").strip()
        try:
            selected_trans = transitions[int(choice) - 1]
        except:
            print("❌ Invalid selection")
            return False
    else:
        # Find transition by target status name
        selected_trans = None
        for trans in transitions:
            if trans['to']['name'].lower() == target_status.lower():
                selected_trans = trans
                break
        
        if not selected_trans:
            print(f"❌ Cannot transition to '{target_status}' from '{current_status}'")
            print("   Available targets:", [t['to']['name'] for t in transitions])
            return False
    
    # 4. Perform the transition
    print(f"\n🚀 Transitioning: {current_status} → {selected_trans['to']['name']}")
    
    transition_data = {
        "transition": {
            "id": selected_trans['id']
        }
    }
    
    # Add comment if provided
    if comment_text:
        transition_data["update"] = {
            "comment": [
                {
                    "add": {
                        "body": comment_text
                    }
                }
            ]
        }
    
    # Execute transition
    transition_response = requests.post(
        trans_url,
        auth=auth,
        json=transition_data,
        headers={'Content-Type': 'application/json'}
    )
    
    if transition_response.status_code == 204:
        print(f"✅ Successfully transitioned to '{selected_trans['to']['name']}'!")
        
        # Verify the change
        verify_response = requests.get(issue_url, auth=auth)
        if verify_response.status_code == 200:
            new_status = verify_response.json()['fields']['status']['name']
            print(f"   Verified: Issue is now in '{new_status}' status")
        
        return True
    else:
        print(f"❌ Failed to transition: {transition_response.status_code}")
        print(f"   Response: {transition_response.text}")
        return False


def main():
    """Main function for interactive use"""
    print("="*60)
    print("JIRA Issue Status Changer")
    print("="*60)
    
    # Test with IT-1
    print("\n1. Testing with IT-1 issue...")
    
    # Change from To Do → In Progress
    success = change_issue_status(
        issue_key="IT-1",
        target_status="In Progress",
        comment_text="Testing status transition via JIRA Sync API"
    )
    
    if success:
        print("\n2. Would you like to move it to 'Done'? (y/n)")
        if input().lower().startswith('y'):
            change_issue_status(
                issue_key="IT-1",
                target_status="Done",
                comment_text="Completing test issue"
            )
            
            # Optionally move it back to To Do
            print("\n3. Move it back to 'To Do'? (y/n)")
            if input().lower().startswith('y'):
                change_issue_status(
                    issue_key="IT-1",
                    target_status="To Do",
                    comment_text="Resetting for future tests"
                )
    
    print("\n" + "="*60)
    print("💡 You can use this function in your code:")
    print("   change_issue_status('IT-1', 'In Progress', 'Optional comment')")
    print("="*60)


if __name__ == "__main__":
    main()