#!/usr/bin/env python3
"""
Update field first, then transition
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
    
    data = {
        "fields": {
            field_id: value
        }
    }
    
    response = requests.put(url, auth=auth, json=data)
    return response.status_code == 204

def transition_issue_simple(issue_key, transition_id, comment=None):
    """Execute a simple transition"""
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

def transition_to_uploaded_method2(issue_key, num_photos):
    """Try different approach - update field then transition"""
    
    print(f"\nMethod 2: Update field first, then transition")
    print(f"Issue: {issue_key}")
    
    # First, try to update the field
    print(f"\n1. Updating NDPU Number of Raw Photos to: {num_photos}")
    success = update_issue_field(issue_key, "customfield_12602", str(num_photos))
    
    if success:
        print("✅ Field updated successfully")
    else:
        print("❌ Could not update field directly")
    
    # Wait a moment
    time.sleep(1)
    
    # Now try transition
    print("\n2. Attempting transition to Uploaded...")
    success = transition_issue_simple(issue_key, "51", f"Uploaded {num_photos} raw photos")
    
    if success:
        print("✅ Successfully transitioned to Uploaded!")
        return True
    else:
        print("❌ Transition failed")
        
        # Try transition with field in update section
        print("\n3. Trying transition with field in update section...")
        
        email = os.getenv('JIRA_CREATE_EMAIL', '').strip('"')
        token = os.getenv('JIRA_CREATE_TOKEN', '').strip('"')
        auth = HTTPBasicAuth(email, token)
        
        base_url = "https://betteredits2.atlassian.net"
        trans_url = f"{base_url}/rest/api/2/issue/{issue_key}/transitions"
        
        data = {
            "transition": {"id": "51"},
            "update": {
                "customfield_12602": [{
                    "set": str(num_photos)
                }],
                "comment": [{
                    "add": {"body": f"Uploaded {num_photos} raw photos"}
                }]
            }
        }
        
        response = requests.post(trans_url, auth=auth, json=data)
        
        if response.status_code == 204:
            print("✅ Success with update method!")
            return True
        else:
            print(f"❌ Failed: {response.status_code}")
            if response.text:
                print(f"Response: {response.text}")
            return False

def check_field_value(issue_key):
    """Check if field has a value"""
    email = os.getenv('JIRA_CREATE_EMAIL', '').strip('"')
    token = os.getenv('JIRA_CREATE_TOKEN', '').strip('"')
    auth = HTTPBasicAuth(email, token)
    
    base_url = "https://betteredits2.atlassian.net"
    url = f"{base_url}/rest/api/2/issue/{issue_key}?fields=customfield_12602,status"
    
    response = requests.get(url, auth=auth)
    if response.status_code == 200:
        data = response.json()
        raw_photos = data['fields'].get('customfield_12602')
        status = data['fields']['status']['name']
        print(f"\nCurrent state of {issue_key}:")
        print(f"  Status: {status}")
        print(f"  NDPU Number of Raw Photos: {raw_photos}")

def main():
    print("="*60)
    print("Testing Upload Transition with Required Field")
    print("="*60)
    
    issue_key = "INUA-456"
    
    # Check current state
    check_field_value(issue_key)
    
    # Try to transition
    success = transition_to_uploaded_method2(issue_key, "30")
    
    if success:
        # Check final state
        check_field_value(issue_key)
        
        print("\n" + "="*60)
        print("📝 Field Requirements Confirmed:")
        print("="*60)
        print("\n1. Shoot Complete → Uploaded")
        print("   Required: customfield_12602 (NDPU Number of Raw Photos)")
        print("   Format: String number ('0' if not applicable)")
        print("\n2. Final Review → Escalation Status")
        print("   Required: customfield_10716 (NDPU Edited Media Revision Notes)")
        print("   Format: Text string")

if __name__ == "__main__":
    main()