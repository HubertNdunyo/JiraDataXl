#!/usr/bin/env python3
"""
Update NDPU Number of Raw Photos field first, then transition to Uploaded
"""

import os
from dotenv import load_dotenv
import requests
from requests.auth import HTTPBasicAuth
import time

load_dotenv()

def update_raw_photos_field(issue_key, num_photos):
    """Update the NDPU Number of Raw Photos field"""
    email = os.getenv('JIRA_CREATE_EMAIL', '').strip('"')
    token = os.getenv('JIRA_CREATE_TOKEN', '').strip('"')
    auth = HTTPBasicAuth(email, token)
    
    base_url = "https://betteredits2.atlassian.net"
    url = f"{base_url}/rest/api/2/issue/{issue_key}"
    
    # Update the field
    data = {
        "fields": {
            "customfield_12602": str(num_photos)  # NDPU Number of Raw Photos
        }
    }
    
    print(f"Updating {issue_key} - NDPU Number of Raw Photos: {num_photos}")
    response = requests.put(url, auth=auth, json=data)
    
    if response.status_code == 204:
        print("✅ Field updated successfully")
        return True
    else:
        print(f"❌ Failed to update field: {response.status_code}")
        if response.text:
            print(f"Response: {response.text}")
        return False

def transition_to_uploaded(issue_key):
    """Transition issue to Uploaded status"""
    email = os.getenv('JIRA_CREATE_EMAIL', '').strip('"')
    token = os.getenv('JIRA_CREATE_TOKEN', '').strip('"')
    auth = HTTPBasicAuth(email, token)
    
    base_url = "https://betteredits2.atlassian.net"
    trans_url = f"{base_url}/rest/api/2/issue/{issue_key}/transitions"
    
    # Simple transition without fields
    data = {
        "transition": {"id": "51"},  # Upload Raw Media
        "update": {
            "comment": [{
                "add": {
                    "body": "Raw photos uploaded to system"
                }
            }]
        }
    }
    
    print(f"\nTransitioning {issue_key} to Uploaded...")
    response = requests.post(trans_url, auth=auth, json=data)
    
    if response.status_code == 204:
        print("✅ Successfully transitioned to Uploaded!")
        return True
    else:
        print(f"❌ Failed to transition: {response.status_code}")
        if response.text:
            print(f"Response: {response.text}")
        return False

def check_issue_status(issue_key):
    """Check current status and field value"""
    email = os.getenv('JIRA_CREATE_EMAIL', '').strip('"')
    token = os.getenv('JIRA_CREATE_TOKEN', '').strip('"')
    auth = HTTPBasicAuth(email, token)
    
    base_url = "https://betteredits2.atlassian.net"
    url = f"{base_url}/rest/api/2/issue/{issue_key}?fields=status,customfield_12602"
    
    response = requests.get(url, auth=auth)
    if response.status_code == 200:
        data = response.json()
        status = data['fields']['status']['name']
        raw_photos = data['fields'].get('customfield_12602')
        print(f"\nCurrent state of {issue_key}:")
        print(f"  Status: {status}")
        print(f"  NDPU Number of Raw Photos: {raw_photos}")
        return status, raw_photos
    return None, None

def main():
    print("="*60)
    print("Update Field Then Transition to Uploaded")
    print("="*60)
    
    issue_key = "INUA-456"
    num_photos = "10"  # As specified by user
    
    # Check initial state
    print("\nInitial state:")
    status, photos = check_issue_status(issue_key)
    
    if status != "Shoot Complete":
        print(f"\n⚠️  Issue is not in Shoot Complete status (current: {status})")
        return
    
    # Step 1: Update the field
    print("\n" + "-"*40)
    print("Step 1: Update NDPU Number of Raw Photos")
    print("-"*40)
    
    if update_raw_photos_field(issue_key, num_photos):
        # Wait a moment for the update to propagate
        time.sleep(2)
        
        # Verify the field was updated
        status, photos = check_issue_status(issue_key)
        
        # Step 2: Transition to Uploaded
        print("\n" + "-"*40)
        print("Step 2: Transition to Uploaded")
        print("-"*40)
        
        if transition_to_uploaded(issue_key):
            # Final check
            time.sleep(1)
            final_status, final_photos = check_issue_status(issue_key)
            
            print("\n" + "="*60)
            print("✅ SUCCESS!")
            print("="*60)
            print(f"\nIssue {issue_key} successfully moved to Uploaded!")
            print(f"URL: https://betteredits2.atlassian.net/browse/{issue_key}")
            print("\n📝 Confirmed Field Requirements:")
            print("- Shoot Complete → Uploaded requires:")
            print("  • customfield_12602 (NDPU Number of Raw Photos)")
            print("  • Must be set BEFORE transition")
            print("  • Format: String number (e.g., '10')")

if __name__ == "__main__":
    main()