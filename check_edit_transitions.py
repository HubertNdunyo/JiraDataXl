#!/usr/bin/env python3
"""
Check available transitions from Edit status
"""

import os
from dotenv import load_dotenv
import requests
from requests.auth import HTTPBasicAuth

load_dotenv()

def get_transitions(issue_key):
    """Get available transitions for an issue"""
    email = os.getenv('JIRA_CREATE_EMAIL', '').strip('"')
    token = os.getenv('JIRA_CREATE_TOKEN', '').strip('"')
    auth = HTTPBasicAuth(email, token)
    
    base_url = "https://betteredits2.atlassian.net"
    trans_url = f"{base_url}/rest/api/2/issue/{issue_key}/transitions"
    
    response = requests.get(trans_url, auth=auth)
    if response.status_code == 200:
        return response.json().get('transitions', [])
    return []

def get_issue_details(issue_key):
    """Get issue details"""
    email = os.getenv('JIRA_CREATE_EMAIL', '').strip('"')
    token = os.getenv('JIRA_CREATE_TOKEN', '').strip('"')
    auth = HTTPBasicAuth(email, token)
    
    base_url = "https://betteredits2.atlassian.net"
    url = f"{base_url}/rest/api/2/issue/{issue_key}?fields=status,customfield_12602,customfield_10716"
    
    response = requests.get(url, auth=auth)
    if response.status_code == 200:
        return response.json()
    return None

def main():
    issue_key = "INUA-456"
    
    print("="*60)
    print(f"Checking transitions for {issue_key}")
    print("="*60)
    
    # Get current details
    details = get_issue_details(issue_key)
    if details:
        status = details['fields']['status']['name']
        raw_photos = details['fields'].get('customfield_12602')
        revision_notes = details['fields'].get('customfield_10716')
        
        print(f"\nCurrent Status: {status}")
        print(f"NDPU Number of Raw Photos: {raw_photos}")
        print(f"NDPU Edited Media Revision Notes: {revision_notes}")
    
    # Get transitions
    transitions = get_transitions(issue_key)
    
    print(f"\nAvailable transitions from '{status}':")
    print("-" * 40)
    for trans in transitions:
        print(f"ID: {trans['id']:3} | {trans['name']:30} → {trans['to']['name']}")
        
        # Check if fields are required
        if 'fields' in trans:
            for field_id, field_info in trans['fields'].items():
                if field_info.get('required'):
                    print(f"         Required field: {field_info['name']} ({field_id})")

if __name__ == "__main__":
    main()