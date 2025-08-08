#!/usr/bin/env python3
"""
Transition INUA-456 to Uploaded with required NDPU Number of Raw Photos field
"""

import os
from dotenv import load_dotenv
import requests
from requests.auth import HTTPBasicAuth

load_dotenv()

def transition_to_uploaded(issue_key, num_raw_photos):
    """
    Transition issue from Shoot Complete to Uploaded with required field
    
    Required field:
    - customfield_12602: NDPU Number of Raw Photos (must have a value, use '0' if not applicable)
    """
    
    email = os.getenv('JIRA_CREATE_EMAIL', '').strip('"')
    token = os.getenv('JIRA_CREATE_TOKEN', '').strip('"')
    auth = HTTPBasicAuth(email, token)
    
    base_url = "https://betteredits2.atlassian.net"
    trans_url = f"{base_url}/rest/api/2/issue/{issue_key}/transitions"
    
    print(f"Transitioning {issue_key} to Uploaded...")
    print(f"Setting NDPU Number of Raw Photos: {num_raw_photos}")
    
    # Transition data with required field
    data = {
        "transition": {
            "id": "51"  # Upload Raw Media
        },
        "fields": {
            "customfield_12602": str(num_raw_photos)  # NDPU Number of Raw Photos
        },
        "update": {
            "comment": [{
                "add": {
                    "body": f"Uploaded {num_raw_photos} raw photos to system"
                }
            }]
        }
    }
    
    response = requests.post(trans_url, auth=auth, json=data)
    
    if response.status_code == 204:
        print(f"✅ Successfully transitioned to Uploaded!")
        return True
    else:
        print(f"❌ Failed to transition: {response.status_code}")
        if response.text:
            print(f"Response: {response.text}")
        return False

def transition_to_closed_via_escalation(issue_key, revision_notes):
    """
    Transition from Final Review to Closed with Escalation Status
    
    Required field:
    - customfield_10716: NDPU Edited Media Revision Notes
    """
    
    email = os.getenv('JIRA_CREATE_EMAIL', '').strip('"')
    token = os.getenv('JIRA_CREATE_TOKEN', '').strip('"')
    auth = HTTPBasicAuth(email, token)
    
    base_url = "https://betteredits2.atlassian.net"
    trans_url = f"{base_url}/rest/api/2/issue/{issue_key}/transitions"
    
    print(f"\nTransitioning {issue_key} from Final Review to Escalation Status...")
    print(f"Setting revision notes: {revision_notes}")
    
    # Get available transitions to find the right one
    response = requests.get(trans_url, auth=auth)
    if response.status_code == 200:
        transitions = response.json().get('transitions', [])
        
        # Find escalation transition
        escalation_trans = None
        for trans in transitions:
            if 'escalat' in trans['name'].lower() or trans['to']['name'] == 'Escalation Status':
                escalation_trans = trans
                break
        
        if escalation_trans:
            data = {
                "transition": {
                    "id": escalation_trans['id']
                },
                "fields": {
                    "customfield_10716": revision_notes  # NDPU Edited Media Revision Notes
                },
                "update": {
                    "comment": [{
                        "add": {
                            "body": f"Escalated for revision: {revision_notes}"
                        }
                    }]
                }
            }
            
            response = requests.post(trans_url, auth=auth, json=data)
            
            if response.status_code == 204:
                print(f"✅ Successfully transitioned to Escalation Status!")
                return True
            else:
                print(f"❌ Failed: {response.status_code}")
                return False

def main():
    print("="*60)
    print("Testing Required Fields for INUA Transitions")
    print("="*60)
    
    # Transition INUA-456 to Uploaded
    issue_key = "INUA-456"
    num_photos = "30"  # Setting 30 raw photos
    
    print(f"\n1. Testing Shoot Complete → Uploaded transition")
    print(f"   Issue: {issue_key}")
    print(f"   Required field: NDPU Number of Raw Photos = {num_photos}")
    
    success = transition_to_uploaded(issue_key, num_photos)
    
    if success:
        print(f"\n✅ {issue_key} is now in Uploaded status!")
        print(f"   https://betteredits2.atlassian.net/browse/{issue_key}")
        
        # Continue moving through workflow if you want
        print("\nWould need to continue through:")
        print("- Uploaded → Edit")
        print("- Edit → Final Review")
        print("- Final Review → Escalation Status (requires revision notes)")
        print("- Or Final Review → Closed")

if __name__ == "__main__":
    main()