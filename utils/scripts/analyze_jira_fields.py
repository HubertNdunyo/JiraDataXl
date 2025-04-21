#!/usr/bin/env python3
"""
Script to analyze JIRA field metadata from both instances and output in markdown format.
This helps identify the correct field IDs for various fields like location names.
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

def get_jira_fields(jira_config: Dict[str, str]) -> List[Dict[str, Any]]:
    """
    Retrieve field metadata from a JIRA instance.
    
    Args:
        jira_config: Dictionary containing JIRA connection details
        
    Returns:
        List of field metadata dictionaries
    """
    url = f"{jira_config['url']}/rest/api/2/field"
    auth = HTTPBasicAuth(jira_config['username'], jira_config['password'])
    
    try:
        response = requests.get(url, auth=auth)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching fields from {jira_config['name']}: {e}")
        return []

def categorize_fields(fields: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Categorize fields by their type.
    
    Args:
        fields: List of field metadata dictionaries
        
    Returns:
        Dictionary mapping field categories to lists of fields
    """
    categories = {
        "System Fields": [],
        "Custom Fields": []
    }
    
    for field in fields:
        if field.get("custom", False):
            categories["Custom Fields"].append(field)
        else:
            categories["System Fields"].append(field)
            
    return categories

def generate_markdown_table(fields: List[Dict[str, Any]]) -> str:
    """
    Generate a markdown table from field metadata.
    
    Args:
        fields: List of field metadata dictionaries
        
    Returns:
        Markdown table as a string
    """
    table = "| Field ID | Name | Type |\n"
    table += "| --- | --- | --- |\n"
    
    for field in sorted(fields, key=lambda x: x.get("name", "")):
        field_id = field.get("id", "")
        name = field.get("name", "")
        field_type = field.get("schema", {}).get("type", "") if "schema" in field else ""
        
        table += f"| {field_id} | {name} | {field_type} |\n"
        
    return table

def main():
    """Main function to analyze JIRA fields and generate markdown output."""
    output = "# JIRA Fields Analysis\n\n"
    
    for jira_config in JIRA_CONFIGS:
        logger.info(f"Fetching fields from {jira_config['name']}...")
        fields = get_jira_fields(jira_config)
        
        if not fields:
            logger.warning(f"No fields retrieved from {jira_config['name']}")
            continue
            
        output += f"## {jira_config['name']} ({jira_config['url']})\n\n"
        
        categories = categorize_fields(fields)
        
        for category, category_fields in categories.items():
            output += f"### {category}\n\n"
            output += generate_markdown_table(category_fields)
            output += "\n"
    
    # Write output to file
    output_file = "jira_fields_analysis.md"
    with open(output_file, "w") as f:
        f.write(output)
        
    logger.info(f"Analysis complete. Results written to {output_file}")
    
    # Also print a summary to console
    print(f"Retrieved {sum(len(get_jira_fields(config)) for config in JIRA_CONFIGS)} fields from {len(JIRA_CONFIGS)} JIRA instances")
    print(f"Results written to {output_file}")

if __name__ == "__main__":
    main()