#!/usr/bin/env python3
"""
Automated Test Script for JIRA Card Creation and Workflow Testing

This script provides comprehensive testing of JIRA integration features including:
- Issue creation
- Workflow transitions
- Field updates
- Error handling
- Cleanup functionality
"""

import os
import sys
import time
import json
from datetime import datetime
from typing import List, Dict, Tuple, Optional
import argparse
from dotenv import load_dotenv
import requests
from requests.auth import HTTPBasicAuth

# Import our modules
from jira_issue_manager import JiraIssueManager
from change_issue_status import change_issue_status
from inua_workflow_helper import (
    update_issue_field,
    transition_to_uploaded_with_photos,
    transition_to_escalation_with_notes,
    complete_inua_workflow
)

# Load environment variables
load_dotenv()

class JiraAutomationTester:
    """Main test automation class"""
    
    def __init__(self, project_key="INUA", test_prefix="TEST_AUTO_", verbose=True):
        self.project_key = project_key
        self.test_prefix = test_prefix
        self.verbose = verbose
        self.created_issues = []
        self.test_results = []
        self.manager = JiraIssueManager(use_create_account=True)
        
        # Authentication for direct API calls
        self.email = os.getenv('JIRA_CREATE_EMAIL', '').strip('"')
        self.token = os.getenv('JIRA_CREATE_TOKEN', '').strip('"')
        self.auth = HTTPBasicAuth(self.email, self.token)
        self.base_url = "https://betteredits2.atlassian.net"
    
    def log(self, message: str, level: str = "INFO"):
        """Log messages with timestamp"""
        if self.verbose:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            prefix = {
                "INFO": "ℹ️",
                "SUCCESS": "✅",
                "ERROR": "❌",
                "WARNING": "⚠️",
                "TEST": "🧪"
            }.get(level, "📝")
            print(f"[{timestamp}] {prefix} {message}")
    
    def create_test_issue(self, test_name: str, scenario: str = "basic") -> Optional[str]:
        """Create a test issue with standardized naming"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        summary = f"{self.test_prefix}{test_name}_{timestamp} - {scenario}"
        
        self.log(f"Creating test issue: {summary}", "TEST")
        
        try:
            issue = self.manager.create_issue(
                project_key=self.project_key,
                summary=summary,
                issue_type="NDP Photo / Video Service"
            )
            
            if issue:
                issue_key = issue['key']
                self.created_issues.append(issue_key)
                self.log(f"Created issue: {issue_key}", "SUCCESS")
                return issue_key
            else:
                self.log(f"Failed to create issue for {test_name}", "ERROR")
                return None
                
        except Exception as e:
            self.log(f"Exception creating issue: {str(e)}", "ERROR")
            return None
    
    def delete_issue(self, issue_key: str) -> bool:
        """Delete a single issue"""
        url = f"{self.base_url}/rest/api/2/issue/{issue_key}"
        
        try:
            response = requests.delete(url, auth=self.auth)
            if response.status_code == 204:
                self.log(f"Deleted issue: {issue_key}", "SUCCESS")
                return True
            else:
                self.log(f"Failed to delete {issue_key}: {response.status_code}", "ERROR")
                return False
        except Exception as e:
            self.log(f"Exception deleting {issue_key}: {str(e)}", "ERROR")
            return False
    
    def record_result(self, test_name: str, success: bool, details: str = ""):
        """Record test result"""
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
    
    # TEST SCENARIOS
    
    def test_basic_creation(self) -> bool:
        """Test 1: Basic issue creation"""
        self.log("\n" + "="*60, "TEST")
        self.log("TEST 1: Basic Issue Creation", "TEST")
        self.log("="*60, "TEST")
        
        issue_key = self.create_test_issue("BasicCreation", "Minimal fields test")
        
        if issue_key:
            self.record_result("Basic Creation", True, f"Created {issue_key}")
            return True
        else:
            self.record_result("Basic Creation", False, "Failed to create issue")
            return False
    
    def test_complete_workflow(self) -> bool:
        """Test 2: Complete workflow path"""
        self.log("\n" + "="*60, "TEST")
        self.log("TEST 2: Complete Workflow Path", "TEST")
        self.log("="*60, "TEST")
        
        issue_key = self.create_test_issue("CompleteWorkflow", "Full workflow test")
        
        if not issue_key:
            self.record_result("Complete Workflow", False, "Failed to create issue")
            return False
        
        # Use the helper function for complete workflow
        try:
            self.log(f"Moving {issue_key} through complete workflow...", "INFO")
            success = complete_inua_workflow(issue_key, num_photos="25")
            
            if success:
                self.record_result("Complete Workflow", True, 
                    f"{issue_key} completed full workflow")
                return True
            else:
                self.record_result("Complete Workflow", False, 
                    f"{issue_key} failed during workflow")
                return False
                
        except Exception as e:
            self.log(f"Exception in workflow: {str(e)}", "ERROR")
            self.record_result("Complete Workflow", False, f"Exception: {str(e)}")
            return False
    
    def test_cancellation_path(self) -> bool:
        """Test 3: Cancellation/Failed shoot path"""
        self.log("\n" + "="*60, "TEST")
        self.log("TEST 3: Cancellation Path (Failed Shoot)", "TEST")
        self.log("="*60, "TEST")
        
        issue_key = self.create_test_issue("CancellationPath", "Failed shoot test")
        
        if not issue_key:
            self.record_result("Cancellation Path", False, "Failed to create issue")
            return False
        
        try:
            # Move to Shoot Complete
            transitions = [
                ("ACKNOWLEDGED", "Photographer assigned"),
                ("At Listing", "Arrived at property"),
                ("Shoot Complete", "Weather conditions prevented shoot")
            ]
            
            for status, comment in transitions:
                if not change_issue_status(issue_key, status, comment):
                    self.record_result("Cancellation Path", False, 
                        f"Failed at {status}")
                    return False
                time.sleep(1)
            
            # Now use failed shoot transition
            self.log("Executing failed shoot transition...", "INFO")
            if change_issue_status(issue_key, "Closed", 
                    "Shoot cancelled due to weather - client will reschedule"):
                self.record_result("Cancellation Path", True, 
                    f"{issue_key} successfully cancelled")
                return True
            else:
                self.record_result("Cancellation Path", False, 
                    "Failed to close via cancellation")
                return False
                
        except Exception as e:
            self.log(f"Exception in cancellation: {str(e)}", "ERROR")
            self.record_result("Cancellation Path", False, f"Exception: {str(e)}")
            return False
    
    def test_escalation_path(self) -> bool:
        """Test 4: Escalation path for quality issues"""
        self.log("\n" + "="*60, "TEST")
        self.log("TEST 4: Escalation Path (Quality Issues)", "TEST")
        self.log("="*60, "TEST")
        
        issue_key = self.create_test_issue("EscalationPath", "Quality escalation test")
        
        if not issue_key:
            self.record_result("Escalation Path", False, "Failed to create issue")
            return False
        
        try:
            # Move through workflow to Final Review
            transitions = [
                ("ACKNOWLEDGED", "Photographer assigned"),
                ("At Listing", "Arrived at property"),
                ("Shoot Complete", "35 photos taken")
            ]
            
            for status, comment in transitions:
                if not change_issue_status(issue_key, status, comment):
                    self.record_result("Escalation Path", False, f"Failed at {status}")
                    return False
                time.sleep(1)
            
            # Upload with photos
            if not transition_to_uploaded_with_photos(issue_key, "35"):
                self.record_result("Escalation Path", False, "Failed at Upload")
                return False
            
            time.sleep(1)
            
            # Continue to Final Review
            if not change_issue_status(issue_key, "Edit", "Starting editing"):
                self.record_result("Escalation Path", False, "Failed at Edit")
                return False
            
            time.sleep(1)
            
            if not change_issue_status(issue_key, "Final Review", "Ready for review"):
                self.record_result("Escalation Path", False, "Failed at Final Review")
                return False
            
            # Now test escalation with revision notes
            revision_notes = "Major quality issues: Overexposed, needs complete re-edit"
            
            self.log(f"Testing escalation with notes: {revision_notes}", "INFO")
            
            # Update field first
            if not update_issue_field(issue_key, "customfield_10716", revision_notes):
                self.record_result("Escalation Path", False, "Failed to update revision notes")
                return False
            
            time.sleep(1)
            
            # Use direct transition for "Not Approved"
            url = f"{self.base_url}/rest/api/2/issue/{issue_key}/transitions"
            data = {
                "transition": {"id": "181"},  # Not Approved
                "update": {
                    "comment": [{
                        "add": {"body": f"Not approved: {revision_notes}"}
                    }]
                }
            }
            
            response = requests.post(url, auth=self.auth, json=data)
            
            if response.status_code == 204:
                self.record_result("Escalation Path", True, 
                    f"{issue_key} successfully escalated")
                return True
            else:
                self.record_result("Escalation Path", False, 
                    f"Failed to escalate: {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"Exception in escalation: {str(e)}", "ERROR")
            self.record_result("Escalation Path", False, f"Exception: {str(e)}")
            return False
    
    def test_field_validation(self) -> bool:
        """Test 5: Field validation requirements"""
        self.log("\n" + "="*60, "TEST")
        self.log("TEST 5: Field Validation Requirements", "TEST")
        self.log("="*60, "TEST")
        
        issue_key = self.create_test_issue("FieldValidation", "Field requirements test")
        
        if not issue_key:
            self.record_result("Field Validation", False, "Failed to create issue")
            return False
        
        try:
            # Move to Shoot Complete
            transitions = [
                ("ACKNOWLEDGED", "Testing field requirements"),
                ("At Listing", "Ready to test"),
                ("Shoot Complete", "Testing upload requirements")
            ]
            
            for status, comment in transitions:
                if not change_issue_status(issue_key, status, comment):
                    self.record_result("Field Validation", False, f"Failed at {status}")
                    return False
                time.sleep(1)
            
            # Test 1: Try transition WITHOUT required field
            self.log("Testing upload transition WITHOUT required field...", "INFO")
            url = f"{self.base_url}/rest/api/2/issue/{issue_key}/transitions"
            data = {
                "transition": {"id": "51"},  # Upload Raw Media
                "update": {
                    "comment": [{
                        "add": {"body": "Testing without required field"}
                    }]
                }
            }
            
            response = requests.post(url, auth=self.auth, json=data)
            
            if response.status_code != 204:
                self.log("Good: Transition correctly failed without required field", "SUCCESS")
            else:
                self.log("Bad: Transition succeeded without required field!", "ERROR")
                self.record_result("Field Validation", False, 
                    "Upload transition succeeded without required field")
                return False
            
            # Test 2: Now WITH required field
            self.log("Testing upload transition WITH required field...", "INFO")
            if transition_to_uploaded_with_photos(issue_key, "20"):
                self.log("Good: Transition succeeded with required field", "SUCCESS")
                self.record_result("Field Validation", True, 
                    "Field validation working correctly")
                return True
            else:
                self.record_result("Field Validation", False, 
                    "Upload transition failed even with required field")
                return False
                
        except Exception as e:
            self.log(f"Exception in field validation: {str(e)}", "ERROR")
            self.record_result("Field Validation", False, f"Exception: {str(e)}")
            return False
    
    def cleanup_test_issues(self, confirm: bool = True) -> int:
        """Clean up all created test issues"""
        if not self.created_issues:
            self.log("No test issues to clean up", "INFO")
            return 0
        
        self.log(f"\nFound {len(self.created_issues)} test issues to clean up", "WARNING")
        
        if confirm:
            response = input("Delete all test issues? (y/N): ")
            if response.lower() != 'y':
                self.log("Cleanup cancelled", "INFO")
                return 0
        
        deleted = 0
        for issue_key in self.created_issues:
            if self.delete_issue(issue_key):
                deleted += 1
            time.sleep(0.5)  # Rate limiting
        
        self.log(f"Cleaned up {deleted} of {len(self.created_issues)} issues", "INFO")
        return deleted
    
    def find_and_cleanup_old_tests(self, days_old: int = 7) -> int:
        """Find and clean up old test issues"""
        self.log(f"\nSearching for test issues older than {days_old} days...", "INFO")
        
        # Search for issues with test prefix
        jql = f'project = {self.project_key} AND summary ~ "{self.test_prefix}*" ORDER BY created DESC'
        url = f"{self.base_url}/rest/api/2/search"
        params = {
            "jql": jql,
            "fields": "key,summary,created",
            "maxResults": 100
        }
        
        try:
            response = requests.get(url, auth=self.auth, params=params)
            if response.status_code == 200:
                issues = response.json().get('issues', [])
                self.log(f"Found {len(issues)} test issues", "INFO")
                
                # Filter old issues
                old_issues = []
                cutoff_date = datetime.now().timestamp() - (days_old * 24 * 60 * 60)
                
                for issue in issues:
                    created = datetime.fromisoformat(
                        issue['fields']['created'].replace('Z', '+00:00')
                    ).timestamp()
                    
                    if created < cutoff_date:
                        old_issues.append(issue['key'])
                        self.log(f"  - {issue['key']}: {issue['fields']['summary']}", "INFO")
                
                if old_issues:
                    response = input(f"\nDelete {len(old_issues)} old test issues? (y/N): ")
                    if response.lower() == 'y':
                        deleted = 0
                        for issue_key in old_issues:
                            if self.delete_issue(issue_key):
                                deleted += 1
                            time.sleep(0.5)
                        return deleted
                
                return 0
            else:
                self.log(f"Failed to search for test issues: {response.status_code}", "ERROR")
                return 0
                
        except Exception as e:
            self.log(f"Exception searching for old tests: {str(e)}", "ERROR")
            return 0
    
    def generate_report(self) -> str:
        """Generate test report"""
        report = []
        report.append("\n" + "="*60)
        report.append("JIRA AUTOMATION TEST REPORT")
        report.append("="*60)
        report.append(f"Test Run: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Project: {self.project_key}")
        report.append(f"Total Tests: {len(self.test_results)}")
        
        passed = sum(1 for r in self.test_results if r['success'])
        failed = len(self.test_results) - passed
        
        report.append(f"Passed: {passed}")
        report.append(f"Failed: {failed}")
        report.append(f"Success Rate: {(passed/len(self.test_results)*100):.1f}%" 
                     if self.test_results else "N/A")
        
        report.append("\nDETAILED RESULTS:")
        report.append("-" * 40)
        
        for result in self.test_results:
            status = "✅ PASS" if result['success'] else "❌ FAIL"
            report.append(f"\n{status} {result['test']}")
            if result['details']:
                report.append(f"   Details: {result['details']}")
        
        report.append("\nCREATED ISSUES:")
        report.append("-" * 40)
        for issue in self.created_issues:
            report.append(f"- {issue}")
        
        report_text = "\n".join(report)
        
        # Save to file
        filename = f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(filename, 'w') as f:
            f.write(report_text)
        
        self.log(f"Report saved to: {filename}", "INFO")
        
        return report_text
    
    def run_all_tests(self) -> bool:
        """Run all test scenarios"""
        self.log("\n" + "="*80, "TEST")
        self.log("🚀 STARTING JIRA AUTOMATION TEST SUITE", "TEST")
        self.log("="*80, "TEST")
        
        tests = [
            ("Basic Creation", self.test_basic_creation),
            ("Complete Workflow", self.test_complete_workflow),
            ("Cancellation Path", self.test_cancellation_path),
            ("Escalation Path", self.test_escalation_path),
            ("Field Validation", self.test_field_validation)
        ]
        
        all_passed = True
        
        for test_name, test_func in tests:
            try:
                passed = test_func()
                if not passed:
                    all_passed = False
                time.sleep(2)  # Pause between tests
            except Exception as e:
                self.log(f"Unexpected error in {test_name}: {str(e)}", "ERROR")
                self.record_result(test_name, False, f"Unexpected error: {str(e)}")
                all_passed = False
        
        # Generate and display report
        report = self.generate_report()
        print(report)
        
        return all_passed


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="JIRA Automation Testing Suite")
    parser.add_argument('--project', default='INUA', help='Project key (default: INUA)')
    parser.add_argument('--prefix', default='TEST_AUTO_', help='Test issue prefix')
    parser.add_argument('--cleanup', action='store_true', help='Cleanup after tests')
    parser.add_argument('--cleanup-old', type=int, metavar='DAYS', 
                       help='Clean up test issues older than DAYS')
    parser.add_argument('--no-confirm', action='store_true', 
                       help='Skip confirmation prompts')
    parser.add_argument('--tests', nargs='+', 
                       choices=['basic', 'workflow', 'cancel', 'escalate', 'fields'],
                       help='Run specific tests only')
    
    args = parser.parse_args()
    
    # Initialize tester
    tester = JiraAutomationTester(
        project_key=args.project,
        test_prefix=args.prefix
    )
    
    # Clean up old tests if requested
    if args.cleanup_old:
        deleted = tester.find_and_cleanup_old_tests(args.cleanup_old)
        print(f"\nDeleted {deleted} old test issues")
        return
    
    # Run tests
    try:
        if args.tests:
            # Run specific tests
            test_map = {
                'basic': tester.test_basic_creation,
                'workflow': tester.test_complete_workflow,
                'cancel': tester.test_cancellation_path,
                'escalate': tester.test_escalation_path,
                'fields': tester.test_field_validation
            }
            
            for test in args.tests:
                test_map[test]()
            
            # Generate report
            report = tester.generate_report()
            print(report)
        else:
            # Run all tests
            tester.run_all_tests()
        
        # Cleanup if requested
        if args.cleanup:
            tester.cleanup_test_issues(confirm=not args.no_confirm)
            
    except KeyboardInterrupt:
        print("\n\nTest run interrupted by user")
        if tester.created_issues:
            print(f"\nCreated {len(tester.created_issues)} test issues:")
            for issue in tester.created_issues:
                print(f"  - {issue}")
            response = input("\nClean up test issues? (y/N): ")
            if response.lower() == 'y':
                tester.cleanup_test_issues(confirm=False)


if __name__ == "__main__":
    main()