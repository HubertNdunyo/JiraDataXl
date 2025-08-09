#!/usr/bin/env python3
"""
Script to check the project_mappings_v2 table and verify location name mappings.
"""

import os
import logging

from ...core.db.db_projects import get_all_project_mappings
from ...core.config.logging_config import setup_logging

# Configure logging
setup_logging()
logger = logging.getLogger(__name__)

def check_project_mappings():
    """Check the project_mappings_v2 table for location name mappings."""
    try:
        # Get all project mappings
        mappings = get_all_project_mappings(include_inactive=True)
        
        if not mappings:
            logger.info("No project mappings found in the database.")
            print("No project mappings found in the database.")
            print("You need to add mappings to the project_mappings_v2 table.")
            return
        
        # Print the mappings
        print(f"Found {len(mappings)} project mappings:")
        print("-" * 80)
        print(f"{'Project Key':<15} {'Location Name':<30} {'Active':<10} {'Approved':<10}")
        print("-" * 80)
        
        for mapping in mappings:
            print(f"{mapping['project_key']:<15} {mapping['location_name']:<30} {str(mapping['is_active']):<10} {str(mapping['approved']):<10}")
        
        # Check for specific projects mentioned in the logs
        projects_to_check = ['SPACE', 'GLBAY', 'RALEIGH', 'NECLT', 'CINWEST', 'SQHNVLY', 'SWFL', 'MYRTLE']
        missing_projects = []
        
        for project in projects_to_check:
            found = False
            for mapping in mappings:
                if mapping['project_key'] == project:
                    found = True
                    break
            if not found:
                missing_projects.append(project)
        
        if missing_projects:
            print("\nMissing mappings for these projects:")
            for project in missing_projects:
                print(f"- {project}")
            print("\nYou need to add mappings for these projects to the project_mappings_v2 table.")
        else:
            print("\nAll checked projects have mappings in the database.")
        
    except Exception as e:
        logger.error(f"Error checking project mappings: {e}")
        print(f"Error checking project mappings: {e}")

if __name__ == "__main__":
    check_project_mappings()