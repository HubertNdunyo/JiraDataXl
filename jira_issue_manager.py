#!/usr/bin/env python3
"""
JIRA Issue Manager - Create, Clone, and Manage Issues
"""

import os
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
import requests
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class JiraIssueManager:
    """Manager for creating, cloning, and managing JIRA issues"""
    
    def __init__(self, use_create_account=True):
        """
        Initialize the JIRA Issue Manager
        
        Args:
            use_create_account: If True, use jira@inuaai.com credentials
                              If False, use jmwangi@inuaai.net credentials
        """
        if use_create_account:
            self.email = os.getenv('JIRA_CREATE_EMAIL', '').strip('"')
            self.token = os.getenv('JIRA_CREATE_TOKEN', '').strip('"')
        else:
            self.email = os.getenv('JIRA_EMAIL', '').strip('"')
            self.token = os.getenv('JIRA_ACCESS_TOKEN', '').strip('"')
        
        if not self.email or not self.token:
            raise ValueError("Missing JIRA credentials in .env file")
        
        self.auth = HTTPBasicAuth(self.email, self.token)
        
        # Instance URLs
        self.instances = {
            "instance_1": "https://betteredits.atlassian.net",
            "instance_2": "https://betteredits2.atlassian.net"
        }
    
    def determine_instance(self, project_key: str) -> str:
        """Determine which instance a project belongs to"""
        # Try both instances
        for name, url in self.instances.items():
            response = requests.get(
                f"{url}/rest/api/3/project/{project_key}",
                auth=self.auth
            )
            if response.status_code == 200:
                return url
        
        raise ValueError(f"Project {project_key} not found in any instance")
    
    def create_issue(
        self,
        project_key: str,
        summary: str,
        issue_type: str = "Task",
        description: str = "",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create a new JIRA issue
        
        Args:
            project_key: Project key (e.g., 'IT', 'NECLT')
            summary: Issue summary/title
            issue_type: Issue type (Task, Bug, Story, etc.)
            description: Issue description
            **kwargs: Additional fields (assignee, priority, labels, etc.)
        
        Returns:
            Dict with created issue details
        """
        try:
            base_url = self.determine_instance(project_key)
            
            # Get issue types for the project
            types_url = f"{base_url}/rest/api/3/issue/createmeta"
            types_params = {
                'projectKeys': project_key,
                'expand': 'projects.issuetypes.fields'
            }
            
            types_response = requests.get(types_url, auth=self.auth, params=types_params)
            
            if types_response.status_code != 200:
                raise Exception(f"Failed to get issue types: {types_response.text}")
            
            # Find the issue type
            create_meta = types_response.json()
            projects = create_meta.get('projects', [])
            
            if not projects:
                raise Exception(f"Project {project_key} not found or no access")
            
            issue_types = projects[0].get('issuetypes', [])
            selected_type = None
            
            for it in issue_types:
                if it['name'].lower() == issue_type.lower():
                    selected_type = it
                    break
            
            if not selected_type and issue_types:
                selected_type = issue_types[0]  # Use first available type
                print(f"Issue type '{issue_type}' not found, using '{selected_type['name']}'")
            
            if not selected_type:
                raise Exception("No issue types available")
            
            # Build issue data
            issue_data = {
                "fields": {
                    "project": {"key": project_key},
                    "summary": summary,
                    "issuetype": {"id": selected_type['id']}
                }
            }
            
            # Only add description if provided and not empty
            if description:
                issue_data['fields']['description'] = description
            
            # Add additional fields
            for key, value in kwargs.items():
                if key == 'assignee' and value:
                    issue_data['fields']['assignee'] = {"accountId": value}
                elif key == 'priority' and value:
                    issue_data['fields']['priority'] = {"name": value}
                elif key == 'labels' and value:
                    issue_data['fields']['labels'] = value if isinstance(value, list) else [value]
                elif key and value:
                    issue_data['fields'][key] = value
            
            # Create the issue
            create_url = f"{base_url}/rest/api/2/issue"
            response = requests.post(create_url, auth=self.auth, json=issue_data)
            
            if response.status_code == 201:
                result = response.json()
                issue_key = result['key']
                
                # Get full issue details
                issue_details = self.get_issue(issue_key)
                
                print(f"✅ Created issue: {issue_key}")
                print(f"   Summary: {summary}")
                print(f"   Type: {selected_type['name']}")
                print(f"   URL: {base_url}/browse/{issue_key}")
                
                return issue_details
            else:
                raise Exception(f"Failed to create issue: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"❌ Error creating issue: {str(e)}")
            raise
    
    def clone_issue(
        self,
        source_issue_key: str,
        target_project_key: Optional[str] = None,
        summary_prefix: str = "Clone of ",
        link_to_original: bool = True
    ) -> Dict[str, Any]:
        """
        Clone an existing JIRA issue
        
        Args:
            source_issue_key: Issue to clone (e.g., 'IT-1')
            target_project_key: Target project (if None, uses same project)
            summary_prefix: Prefix for cloned issue summary
            link_to_original: Whether to link clone to original
        
        Returns:
            Dict with cloned issue details
        """
        try:
            # Get source issue details
            source_issue = self.get_issue(source_issue_key, expand="names,schema")
            
            if not source_issue:
                raise Exception(f"Source issue {source_issue_key} not found")
            
            # Extract fields
            source_fields = source_issue['fields']
            source_project = source_fields['project']['key']
            
            # Determine target project
            if not target_project_key:
                target_project_key = source_project
            
            # Build clone data
            clone_summary = f"{summary_prefix}{source_fields.get('summary', 'Untitled')}"
            
            # Fields to copy (customize as needed)
            fields_to_copy = [
                'description', 'priority', 'labels', 'components',
                'fixVersions', 'versions', 'environment'
            ]
            
            kwargs = {}
            for field in fields_to_copy:
                if field in source_fields and source_fields[field]:
                    kwargs[field] = source_fields[field]
            
            # Create the clone
            cloned_issue = self.create_issue(
                project_key=target_project_key,
                summary=clone_summary,
                issue_type=source_fields['issuetype']['name'],
                **kwargs
            )
            
            # Link to original if requested
            if link_to_original and cloned_issue:
                try:
                    self.link_issues(
                        source_issue_key,
                        cloned_issue['key'],
                        link_type="Cloners"
                    )
                    print(f"   Linked to original: {source_issue_key}")
                except:
                    print("   Note: Could not create link (link type might not exist)")
            
            return cloned_issue
            
        except Exception as e:
            print(f"❌ Error cloning issue: {str(e)}")
            raise
    
    def get_issue(self, issue_key: str, expand: str = "") -> Optional[Dict[str, Any]]:
        """Get issue details"""
        try:
            base_url = self.determine_instance(issue_key.split('-')[0])
            url = f"{base_url}/rest/api/2/issue/{issue_key}"
            
            params = {}
            if expand:
                params['expand'] = expand
            
            response = requests.get(url, auth=self.auth, params=params)
            
            if response.status_code == 200:
                return response.json()
            else:
                return None
                
        except:
            return None
    
    def link_issues(
        self,
        inward_issue: str,
        outward_issue: str,
        link_type: str = "Relates"
    ):
        """Create a link between two issues"""
        try:
            base_url = self.determine_instance(inward_issue.split('-')[0])
            link_url = f"{base_url}/rest/api/2/issueLink"
            
            link_data = {
                "type": {"name": link_type},
                "inwardIssue": {"key": inward_issue},
                "outwardIssue": {"key": outward_issue}
            }
            
            response = requests.post(link_url, auth=self.auth, json=link_data)
            
            if response.status_code in [200, 201]:
                return True
            else:
                return False
                
        except:
            return False
    
    def bulk_create_issues(
        self,
        issues_data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Create multiple issues at once
        
        Args:
            issues_data: List of dicts with issue data
                        Each dict should have: project_key, summary, issue_type, etc.
        
        Returns:
            List of created issues
        """
        created_issues = []
        
        for issue_data in issues_data:
            try:
                issue = self.create_issue(**issue_data)
                created_issues.append(issue)
            except Exception as e:
                print(f"Failed to create issue: {e}")
                created_issues.append(None)
        
        return created_issues


# Example usage functions
def demo_create_issue():
    """Demo creating a new issue"""
    manager = JiraIssueManager(use_create_account=True)
    
    issue = manager.create_issue(
        project_key="IT",
        summary="Test Issue Created via API",
        issue_type="Task",
        description="This issue was created using the JIRA Issue Manager",
        labels=["api-created", "test"]
    )
    
    return issue


def demo_clone_issue():
    """Demo cloning an issue"""
    manager = JiraIssueManager(use_create_account=True)
    
    cloned = manager.clone_issue(
        source_issue_key="IT-1",
        summary_prefix="API Clone of "
    )
    
    return cloned


if __name__ == "__main__":
    print("JIRA Issue Manager")
    print("="*60)
    
    print("\n1. Testing issue creation...")
    new_issue = demo_create_issue()
    
    if new_issue:
        print("\n2. Testing issue cloning...")
        cloned_issue = demo_clone_issue()
    
    print("\n✅ Issue creation and cloning functionality ready!")