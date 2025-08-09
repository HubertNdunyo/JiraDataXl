#!/usr/bin/env python3
"""
Script to examine JIRA project names and structure to determine the correct query for location name.
"""

import os
import json
import logging
from typing import Dict, Any, List

from ...core.jira.jira_client import JiraClient
from ...core.config.logging_config import setup_logging
from dotenv import load_dotenv

# Configure logging
setup_logging()
logger = logging.getLogger(__name__)

def examine_jira_project_names():
    """Examine JIRA project names to determine the correct query for location name."""
    try:
        # Load environment variables
        load_dotenv()
        
        # JIRA instance configurations
        jira_configs = [
            {
                "name": "Primary JIRA",
                "url": os.getenv("JIRA_URL_1"),
                "username": os.getenv("JIRA_USERNAME_1"),
                "password": os.getenv("JIRA_PASSWORD_1")
            },
            {
                "name": "Secondary JIRA",
                "url": os.getenv("JIRA_URL_2"),
                "username": os.getenv("JIRA_USERNAME_2"),
                "password": os.getenv("JIRA_PASSWORD_2")
            }
        ]
        
        # Projects to examine
        projects_to_check = ['SPACE', 'GLBAY', 'RALEIGH', 'NECLT', 'CINWEST']
        
        for config in jira_configs:
            print(f"\nExamining projects in {config['name']} ({config['url']}):")
            print("-" * 80)
            
            try:
                # Create JIRA client
                client = JiraClient(
                    url=config['url'],
                    username=config['username'],
                    password=config['password']
                )
                
                # Get all projects
                all_projects = client.get_projects()
                
                if not all_projects:
                    print(f"No projects found in {config['name']}")
                    continue
                
                print(f"Found {len(all_projects)} projects")
                
                # Print project details for the projects we're interested in
                for project in all_projects:
                    if project.get('key') in projects_to_check:
                        print(f"\nProject Key: {project.get('key')}")
                        print(f"Project Name: {project.get('name')}")
                        print(f"Project ID: {project.get('id')}")
                        print("Full Project Data:")
                        print(json.dumps(project, indent=2))
                        
                        # Get a sample issue from this project
                        jql = f"project = {project.get('key')} ORDER BY updated DESC"
                        response = client.search_issues(
                            jql=jql,
                            fields=['summary', 'project'],
                            max_results=1
                        )
                        
                        issues = response.get('issues', [])
                        if issues:
                            issue = issues[0]
                            print("\nSample Issue:")
                            print(f"Issue Key: {issue.get('key')}")
                            print(f"Issue Summary: {issue.get('fields', {}).get('summary')}")
                            print("Issue Project Data:")
                            print(json.dumps(issue.get('fields', {}).get('project', {}), indent=2))
                            
                            # Extract and print the project name from the issue
                            project_name = issue.get('fields', {}).get('project', {}).get('name')
                            print(f"\nExtracted Project Name: {project_name}")
                            
                            # Show the exact path to access the project name
                            print("Path to access project name in issue data:")
                            print("issue['fields']['project']['name']")
                
            except Exception as e:
                print(f"Error examining projects in {config['name']}: {e}")
        
    except Exception as e:
        logger.error(f"Error examining JIRA project names: {e}")
        print(f"Error examining JIRA project names: {e}")

if __name__ == "__main__":
    examine_jira_project_names()