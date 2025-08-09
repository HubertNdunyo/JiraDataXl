#!/usr/bin/env python3
"""
Direct transitions for INUA-456
"""

import os
import time
from dotenv import load_dotenv
import requests
from requests.auth import HTTPBasicAuth

load_dotenv()

def transition_issue(issue_key, transition_id, comment=None):
    """Execute a transition on an issue"""
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
    """Update a field on an issue"""
    email = os.getenv('JIRA_CREATE_EMAIL', '').strip('"')
    token = os.getenv('JIRA_CREATE_TOKEN', '').strip('"')
    auth = HTTPBasicAuth(email, token)
    
    base_url = "https://betteredits2.atlassian.net"
    url = f"{base_url}/rest/api/2/issue/{issue_key}"
    
    data = {"fields": {field_id: value}}
    
    response = requests.put(url, auth=auth, json=data)
    return response.status_code == 204

def get_transitions(issue_key):
    """Get available transitions for an issue"""
    email = os.getenv('JIRA_CREATE_EMAIL', '').strip('"')
    token = os.getenv('JIRA_CREATE_TOKEN', '').strip('"')
    auth = HTTPBasicAuth(email, token)
    
    base_url = "https://betteredits2.atlassian.net"
    trans_url = f"{base_url}/rest/api/2/issue/{issue_key}/transitions"
    
    response = requests.get(trans_url, auth=auth)
    if response.status_code == 200:
        transitions = response.json().get('transitions', [])
        return transitions
    return []

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
    print("Moving INUA-456: Uploaded → Edit → Final Review → Escalation")
    print("="*60)
    
    issue_key = "INUA-456"
    
    # Check current status
    status = get_status(issue_key)
    print(f"\nCurrent status: {status}")
    
    # 1. Uploaded → Edit (transition ID: 71)
    if status == "Uploaded":
        print("\n" + "-"*40)
        print("Step 1: Uploaded → Edit")
        print("-"*40)
        
        if transition_issue(issue_key, "71", "Starting photo editing process"):
            print("✅ Successfully moved to Edit")
            time.sleep(2)
            status = "Edit"
        else:
            print("❌ Failed to transition")
            return
    
    # 2. Edit → Final Review (transition ID: 81)
    if status == "Edit":
        print("\n" + "-"*40)
        print("Step 2: Edit → Final Review")
        print("-"*40)
        
        if transition_issue(issue_key, "81", "Editing complete, ready for quality review"):
            print("✅ Successfully moved to Final Review")
            time.sleep(2)
            status = "Final Review"
        else:
            print("❌ Failed to transition")
            return
    
    # 3. Final Review → Escalation Status
    if status == "Final Review":
        print("\n" + "-"*40)
        print("Step 3: Final Review → Escalation Status")
        print("-"*40)
        
        # First, get available transitions to find escalation
        print("\nChecking available transitions...")
        transitions = get_transitions(issue_key)
        
        escalation_trans = None
        for trans in transitions:
            print(f"  - {trans['name']} (ID: {trans['id']}) → {trans['to']['name']}")
            if 'escalat' in trans['name'].lower() or trans['to']['name'] == 'Escalation Status':
                escalation_trans = trans
        
        if escalation_trans:
            # Update required field first
            revision_notes = "Photos need additional color correction and exposure adjustments"
            print(f"\nUpdating NDPU Edited Media Revision Notes...")
            
            if update_field(issue_key, "customfield_10716", revision_notes):
                print("✅ Revision notes updated")
                time.sleep(2)
                
                # Now transition
                print(f"\nTransitioning to {escalation_trans['to']['name']}...")
                if transition_issue(issue_key, escalation_trans['id'], f"Escalated: {revision_notes}"):
                    print(f"✅ Successfully moved to {escalation_trans['to']['name']}")
                else:
                    print("❌ Failed to transition")
            else:
                print("❌ Failed to update revision notes")
        else:
            print("\n⚠️  No escalation transition found from Final Review")
            print("Available transition is to Closed (ID: 91)")
    
    # Final check
    final_status = get_status(issue_key)
    print("\n" + "="*60)
    print("Summary")
    print("="*60)
    print(f"\nIssue: {issue_key}")
    print(f"Final Status: {final_status}")
    print(f"URL: https://betteredits2.atlassian.net/browse/{issue_key}")
    
    if final_status in ["Escalation Status", "Closed"]:
        print("\n📝 Workflow demonstrated successfully!")
        print("\nConfirmed transitions:")
        print("✓ Uploaded → Edit (ID: 71)")
        print("✓ Edit → Final Review (ID: 81)")
        if final_status == "Escalation Status":
            print("✓ Final Review → Escalation Status (with customfield_10716)")
        else:
            print("✓ Final Review → Closed (ID: 91) - standard path")

if __name__ == "__main__":
    main()