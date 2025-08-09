#!/usr/bin/env python3
"""
Create two INUA issues and move them to Shoot Complete status
"""

import time
from jira_issue_manager import JiraIssueManager
from change_issue_status import change_issue_status

def create_and_prepare_issues():
    """Create two issues and move them to Shoot Complete"""
    
    print("="*60)
    print("Creating Test Issues for Upload Transition")
    print("="*60)
    
    manager = JiraIssueManager(use_create_account=True)
    
    # Create first issue
    print("\n1. Creating first test issue...")
    issue1 = manager.create_issue(
        project_key="INUA",
        summary="Test Upload Issue 1 - 456 Oak Street Photography",
        issue_type="NDP Photo / Video Service"
    )
    
    if not issue1:
        print("Failed to create first issue")
        return None, None
    
    issue1_key = issue1['key']
    print(f"✅ Created: {issue1_key}")
    
    # Create second issue
    print("\n2. Creating second test issue...")
    issue2 = manager.create_issue(
        project_key="INUA",
        summary="Test Upload Issue 2 - 789 Pine Avenue Photography",
        issue_type="NDP Photo / Video Service"
    )
    
    if not issue2:
        print("Failed to create second issue")
        return issue1_key, None
    
    issue2_key = issue2['key']
    print(f"✅ Created: {issue2_key}")
    
    # Move both issues through workflow to Shoot Complete
    issues = [
        (issue1_key, "456 Oak Street"),
        (issue2_key, "789 Pine Avenue")
    ]
    
    for issue_key, location in issues:
        print(f"\n{'='*40}")
        print(f"Moving {issue_key} to Shoot Complete")
        print('='*40)
        
        # Scheduled → ACKNOWLEDGED
        print(f"\n→ Acknowledging assignment...")
        success = change_issue_status(
            issue_key=issue_key,
            target_status="ACKNOWLEDGED",
            comment_text=f"Photographer assigned for {location}"
        )
        if success:
            print("✅ ACKNOWLEDGED")
            time.sleep(1)
        
        # ACKNOWLEDGED → At Listing
        print(f"\n→ Arriving at listing...")
        success = change_issue_status(
            issue_key=issue_key,
            target_status="At Listing",
            comment_text=f"Photographer arrived at {location}"
        )
        if success:
            print("✅ At Listing")
            time.sleep(1)
        
        # At Listing → Shoot Complete
        print(f"\n→ Completing shoot...")
        success = change_issue_status(
            issue_key=issue_key,
            target_status="Shoot Complete",
            comment_text=f"Photography completed at {location}. 30 RAW photos taken."
        )
        if success:
            print("✅ Shoot Complete")
    
    # Summary
    print("\n" + "="*60)
    print("✅ Issues Ready for Upload Transition Test")
    print("="*60)
    print(f"\nIssue 1: {issue1_key}")
    print(f"URL: https://betteredits2.atlassian.net/browse/{issue1_key}")
    print(f"Status: Shoot Complete")
    print(f"\nIssue 2: {issue2_key}")
    print(f"URL: https://betteredits2.atlassian.net/browse/{issue2_key}")
    print(f"Status: Shoot Complete")
    print("\n📝 Next Steps:")
    print(f"1. You manually transition {issue1_key} to 'Uploaded' and note required fields")
    print(f"2. I'll use those fields to transition {issue2_key} programmatically")
    
    return issue1_key, issue2_key

if __name__ == "__main__":
    issue1, issue2 = create_and_prepare_issues()
    
    # Save issue keys for later use
    if issue1 and issue2:
        with open("upload_test_issues.txt", "w") as f:
            f.write(f"{issue1}\n{issue2}\n")
        print(f"\n💾 Issue keys saved to upload_test_issues.txt")