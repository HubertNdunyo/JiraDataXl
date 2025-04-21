#!/usr/bin/env python3
"""
Script to analyze specific JIRA issues to identify the correct location name field.
"""

import os
import sys
import json
import logging
from typing import Dict, List, Any
import requests
from dotenv import load_dotenv
from requests.auth import HTTPBasicAuth

# Add the project root to the path so we can import from core
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# JIRA instance configurations
JIRA_CONFIGS = [
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

# Issue keys to analyze
ISSUE_KEYS = ["RALEIGH-36764", "SPACE-33622"]

def get_jira_issue(jira_config: Dict[str, str], issue_key: str) -> Dict[str, Any]:
    """
    Retrieve a specific JIRA issue.
    
    Args:
        jira_config: Dictionary containing JIRA connection details
        issue_key: The JIRA issue key
        
    Returns:
        Dictionary containing issue data or empty dict if not found
    """
    url = f"{jira_config['url']}/rest/api/2/issue/{issue_key}?expand=names,schema"
    auth = HTTPBasicAuth(jira_config['username'], jira_config['password'])
    
    try:
        response = requests.get(url, auth=auth)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching issue {issue_key} from {jira_config['name']}: {e}")
        return {}

def analyze_issue_fields(issue_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze the fields of a JIRA issue to identify potential location name fields.
    
    Args:
        issue_data: Dictionary containing issue data
        
    Returns:
        Dictionary containing analyzed field data
    """
    if not issue_data:
        return {}
        
    result = {
        "issue_key": issue_data.get("key", "Unknown"),
        "summary": issue_data.get("fields", {}).get("summary", "Unknown"),
        "potential_location_fields": []
    }
    
    # Get field names mapping
    field_names = issue_data.get("names", {})
    
    # Analyze fields
    fields = issue_data.get("fields", {})
    for field_id, value in fields.items():
        # Skip empty values
        if value is None or value == "" or (isinstance(value, (list, dict)) and not value):
            continue
            
        # Get field name
        field_name = field_names.get(field_id, field_id)
        
        # Check if field might contain location information
        is_potential_location = False
        field_value_str = str(value)
        
        # Check if field name contains location-related keywords
        location_keywords = ["location", "address", "place", "site", "property", "listing"]
        if any(keyword in field_name.lower() for keyword in location_keywords):
            is_potential_location = True
            
        # Check if field value looks like an address
        address_indicators = [
            "street", "avenue", "road", "drive", "lane", "blvd", "boulevard", 
            "apt", "suite", "unit", "floor", "st.", "ave.", "rd.", "dr."
        ]
        if any(indicator in field_value_str.lower() for indicator in address_indicators):
            is_potential_location = True
            
        # Add to potential location fields if it matches criteria
        if is_potential_location:
            result["potential_location_fields"].append({
                "field_id": field_id,
                "field_name": field_name,
                "value": field_value_str if len(field_value_str) < 100 else field_value_str[:100] + "..."
            })
            
    return result

def main():
    """Main function to analyze specific JIRA issues."""
    results = []
    
    for issue_key in ISSUE_KEYS:
        logger.info(f"Analyzing issue {issue_key}...")
        
        # Try to find the issue in each JIRA instance
        issue_data = None
        instance_name = None
        
        for jira_config in JIRA_CONFIGS:
            data = get_jira_issue(jira_config, issue_key)
            if data and "key" in data:
                issue_data = data
                instance_name = jira_config["name"]
                break
                
        if not issue_data:
            logger.warning(f"Issue {issue_key} not found in any JIRA instance")
            continue
            
        # Analyze the issue fields
        analysis = analyze_issue_fields(issue_data)
        analysis["jira_instance"] = instance_name
        
        # Add raw fields data for reference
        analysis["raw_fields"] = {
            field_id: value for field_id, value in issue_data.get("fields", {}).items()
            if not isinstance(value, (dict, list)) or (isinstance(value, (dict, list)) and value)
        }
        
        results.append(analysis)
    
    # Write results to file
    output_file = "jira_issue_analysis.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2, default=str)
        
    # Also create a markdown summary
    md_output = "# JIRA Issue Analysis for Location Fields\n\n"
    
    for result in results:
        md_output += f"## {result['issue_key']} ({result['jira_instance']})\n\n"
        md_output += f"**Summary:** {result['summary']}\n\n"
        
        md_output += "### Potential Location Fields\n\n"
        md_output += "| Field ID | Field Name | Value |\n"
        md_output += "| --- | --- | --- |\n"
        
        for field in result["potential_location_fields"]:
            md_output += f"| {field['field_id']} | {field['field_name']} | {field['value']} |\n"
            
        md_output += "\n### All Fields\n\n"
        md_output += "| Field ID | Value |\n"
        md_output += "| --- | --- |\n"
        
        for field_id, value in result["raw_fields"].items():
            md_output += f"| {field_id} | {value} |\n"
            
        md_output += "\n\n"
    
    md_output_file = "jira_issue_analysis.md"
    with open(md_output_file, "w") as f:
        f.write(md_output)
        
    logger.info(f"Analysis complete. Results written to {output_file} and {md_output_file}")
    
    # Print a summary
    print(f"Analyzed {len(results)} issues")
    print(f"Results written to {output_file} and {md_output_file}")

if __name__ == "__main__":
    main()