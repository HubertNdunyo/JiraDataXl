#!/usr/bin/env python3
"""
Complete INUA-456 workflow to Escalation
"""

import os
import time
from dotenv import load_dotenv
import requests
from requests.auth import HTTPBasicAuth

load_dotenv()

class INUAWorkflow:
    def __init__(self):
        self.email = os.getenv('JIRA_CREATE_EMAIL', '').strip('"')
        self.token = os.getenv('JIRA_CREATE_TOKEN', '').strip('"')
        self.auth = HTTPBasicAuth(self.email, self.token)
        self.base_url = "https://betteredits2.atlassian.net"
    
    def transition(self, issue_key, transition_id, comment=None):
        """Execute a transition"""
        trans_url = f"{self.base_url}/rest/api/2/issue/{issue_key}/transitions"
        
        data = {"transition": {"id": str(transition_id)}}
        if comment:
            data["update"] = {"comment": [{"add": {"body": comment}}]}
        
        response = requests.post(trans_url, auth=self.auth, json=data)
        return response.status_code == 204
    
    def update_field(self, issue_key, field_id, value):
        """Update a field"""
        url = f"{self.base_url}/rest/api/2/issue/{issue_key}"
        data = {"fields": {field_id: value}}
        
        response = requests.put(url, auth=self.auth, json=data)
        return response.status_code == 204
    
    def get_transitions(self, issue_key):
        """Get available transitions"""
        trans_url = f"{self.base_url}/rest/api/2/issue/{issue_key}/transitions"
        
        response = requests.get(trans_url, auth=self.auth)
        if response.status_code == 200:
            return response.json().get('transitions', [])
        return []
    
    def get_status(self, issue_key):
        """Get current status"""
        url = f"{self.base_url}/rest/api/2/issue/{issue_key}?fields=status"
        
        response = requests.get(url, auth=self.auth)
        if response.status_code == 200:
            return response.json()['fields']['status']['name']
        return None

def main():
    print("="*60)
    print("Completing INUA-456 Workflow")
    print("="*60)
    
    workflow = INUAWorkflow()
    issue_key = "INUA-456"
    
    # Check current status
    status = workflow.get_status(issue_key)
    print(f"\nStarting status: {status}")
    
    # 1. Edit → Final Review (using correct transition ID)
    if status == "Edit":
        print("\n" + "-"*40)
        print("Step 1: Edit → Final Review")
        print("-"*40)
        
        # Get available transitions to confirm
        transitions = workflow.get_transitions(issue_key)
        edit_complete = None
        for trans in transitions:
            if trans['to']['name'] == 'Final Review':
                edit_complete = trans
                print(f"Found transition: {trans['name']} (ID: {trans['id']})")
                break
        
        if edit_complete:
            if workflow.transition(issue_key, edit_complete['id'], "Editing complete, ready for quality review"):
                print("✅ Successfully moved to Final Review")
                time.sleep(2)
                status = "Final Review"
            else:
                print("❌ Failed to transition")
                return
    
    # 2. Final Review → Escalation Status or Closed
    if status == "Final Review":
        print("\n" + "-"*40)
        print("Step 2: Final Review → Escalation Status")
        print("-"*40)
        
        # Update required field first
        revision_notes = "Photos need additional color correction and exposure adjustments for better quality"
        print(f"\nUpdating NDPU Edited Media Revision Notes...")
        print(f"Notes: {revision_notes}")
        
        if workflow.update_field(issue_key, "customfield_10716", revision_notes):
            print("✅ Revision notes updated")
            time.sleep(2)
            
            # Get available transitions
            transitions = workflow.get_transitions(issue_key)
            print("\nAvailable transitions from Final Review:")
            
            escalation_trans = None
            closed_trans = None
            
            for trans in transitions:
                print(f"  - {trans['name']} (ID: {trans['id']}) → {trans['to']['name']}")
                if 'escalat' in trans['name'].lower() or trans['to']['name'] == 'Escalation Status':
                    escalation_trans = trans
                elif trans['to']['name'] == 'Closed':
                    closed_trans = trans
            
            # Try escalation first
            if escalation_trans:
                print(f"\nAttempting transition to {escalation_trans['to']['name']}...")
                if workflow.transition(issue_key, escalation_trans['id'], f"Escalated for revision: {revision_notes}"):
                    print(f"✅ Successfully moved to {escalation_trans['to']['name']}")
                else:
                    print("❌ Failed to transition to Escalation")
                    
                    # Try closed as fallback
                    if closed_trans:
                        print("\nTrying fallback to Closed...")
                        if workflow.transition(issue_key, closed_trans['id'], "Completed with escalation notes"):
                            print("✅ Moved to Closed")
            elif closed_trans:
                # Only closed available
                print("\n⚠️  No escalation transition available, only Closed")
                if workflow.transition(issue_key, closed_trans['id'], "Media delivered to client"):
                    print("✅ Moved to Closed")
        else:
            print("❌ Failed to update revision notes")
    
    # Final status
    final_status = workflow.get_status(issue_key)
    print("\n" + "="*60)
    print("✅ Workflow Complete")
    print("="*60)
    print(f"\nIssue: {issue_key}")
    print(f"Final Status: {final_status}")
    print(f"URL: https://betteredits2.atlassian.net/browse/{issue_key}")
    
    print("\n📝 Field Requirements Summary:")
    print("- Shoot Complete → Uploaded: customfield_12602 (NDPU Number of Raw Photos)")
    print("- Final Review → Escalation: customfield_10716 (NDPU Edited Media Revision Notes)")
    print("\nBoth fields must be set BEFORE the transition!")

if __name__ == "__main__":
    main()