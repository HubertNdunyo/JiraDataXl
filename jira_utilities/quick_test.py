#!/usr/bin/env python3
"""
Quick Test Script - Simple JIRA automation test

Usage:
    python3 quick_test.py              # Run quick test
    python3 quick_test.py --cleanup    # Clean up test issues
"""

import sys
import time
from datetime import datetime
from jira_issue_manager import JiraIssueManager
from change_issue_status import change_issue_status
from inua_workflow_helper import transition_to_uploaded_with_photos

def quick_test():
    """Run a quick test of JIRA automation"""
    print("\n" + "="*60)
    print("🚀 QUICK JIRA AUTOMATION TEST")
    print("="*60)
    
    # Initialize manager
    manager = JiraIssueManager(use_create_account=True)
    
    # Create test issue
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    summary = f"QUICK_TEST_{timestamp} - Automated test"
    
    print(f"\n1️⃣ Creating test issue...")
    issue = manager.create_issue(
        project_key="INUA",
        summary=summary,
        issue_type="NDP Photo / Video Service"
    )
    
    if not issue:
        print("❌ Failed to create issue")
        return None
    
    issue_key = issue['key']
    print(f"✅ Created: {issue_key}")
    print(f"   URL: https://betteredits2.atlassian.net/browse/{issue_key}")
    
    # Test transitions
    print(f"\n2️⃣ Testing workflow transitions...")
    
    transitions = [
        ("ACKNOWLEDGED", "Quick test - photographer assigned"),
        ("At Listing", "Quick test - arrived at property"),
        ("Shoot Complete", "Quick test - 20 photos taken")
    ]
    
    for status, comment in transitions:
        print(f"   ➡️ Moving to {status}...")
        if change_issue_status(issue_key, status, comment):
            print(f"   ✅ {status}")
        else:
            print(f"   ❌ Failed at {status}")
            return issue_key
        time.sleep(1)
    
    # Test field requirement
    print(f"\n3️⃣ Testing field requirement for Upload...")
    if transition_to_uploaded_with_photos(issue_key, "20"):
        print("   ✅ Successfully uploaded with required field")
    else:
        print("   ❌ Failed to upload")
        return issue_key
    
    print(f"\n✨ Test completed successfully!")
    print(f"\nTest issue: {issue_key}")
    print("Run with --cleanup to delete the test issue")
    
    return issue_key

def cleanup_test_issues():
    """Clean up test issues"""
    print("\n🧹 Searching for test issues...")
    
    from requests.auth import HTTPBasicAuth
    import requests
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    email = os.getenv('JIRA_CREATE_EMAIL', '').strip('"')
    token = os.getenv('JIRA_CREATE_TOKEN', '').strip('"')
    auth = HTTPBasicAuth(email, token)
    base_url = "https://betteredits2.atlassian.net"
    
    # Search for quick test issues
    jql = 'project = INUA AND summary ~ "QUICK_TEST_*" ORDER BY created DESC'
    url = f"{base_url}/rest/api/2/search"
    params = {
        "jql": jql,
        "fields": "key,summary,created",
        "maxResults": 50
    }
    
    response = requests.get(url, auth=auth, params=params)
    
    if response.status_code == 200:
        issues = response.json().get('issues', [])
        print(f"\nFound {len(issues)} quick test issues:")
        
        for issue in issues:
            print(f"  - {issue['key']}: {issue['fields']['summary']}")
        
        if issues:
            confirm = input("\nDelete all quick test issues? (y/N): ")
            if confirm.lower() == 'y':
                deleted = 0
                for issue in issues:
                    issue_key = issue['key']
                    del_url = f"{base_url}/rest/api/2/issue/{issue_key}"
                    del_response = requests.delete(del_url, auth=auth)
                    
                    if del_response.status_code == 204:
                        print(f"  ✅ Deleted {issue_key}")
                        deleted += 1
                    else:
                        print(f"  ❌ Failed to delete {issue_key}")
                    
                    time.sleep(0.5)
                
                print(f"\n🎉 Deleted {deleted} test issues")
            else:
                print("Cleanup cancelled")
        else:
            print("No quick test issues found")
    else:
        print(f"❌ Failed to search for issues: {response.status_code}")

def main():
    """Main entry point"""
    if len(sys.argv) > 1 and sys.argv[1] == '--cleanup':
        cleanup_test_issues()
    else:
        issue_key = quick_test()
        if issue_key:
            print(f"\n💡 Tip: Run 'python3 quick_test.py --cleanup' to clean up test issues")

if __name__ == "__main__":
    main()