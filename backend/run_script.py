#!/usr/bin/env python3
"""
Entry point for running backend scripts using proper package imports.
Usage: python -m run_script <script_name> [args]

Examples:
    python -m run_script analyze_jira_fields
    python -m run_script verify_field_mappings
    python -m run_script test_single_issue PROJ-123
"""

import sys
import importlib
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Map script names to their module paths
SCRIPT_MODULES = {
    # Utils scripts
    'analyze_jira_fields': 'utils.scripts.analyze_jira_fields',
    'analyze_specific_issues': 'utils.scripts.analyze_specific_issues',
    'check_project_mappings': 'utils.scripts.check_project_mappings',
    'examine_jira_project_names': 'utils.scripts.examine_jira_project_names',
    'test_single_issue': 'utils.scripts.test_single_issue',
    
    # Main scripts
    'verify_field_mappings': 'scripts.verify_field_mappings',
    'migrate_configs': 'scripts.migrate_configs',
    'extract_hardcoded_mappings': 'scripts.extract_hardcoded_mappings',
    
    # Maintenance scripts
    'clear_jira_data': 'utils.scripts.maintenance.clear_jira_data',
}

def main():
    if len(sys.argv) < 2:
        print("Usage: python -m run_script <script_name> [args]")
        print("\nAvailable scripts:")
        for name in sorted(SCRIPT_MODULES.keys()):
            print(f"  - {name}")
        sys.exit(1)
    
    script_name = sys.argv[1]
    
    if script_name not in SCRIPT_MODULES:
        print(f"Error: Unknown script '{script_name}'")
        print("\nAvailable scripts:")
        for name in sorted(SCRIPT_MODULES.keys()):
            print(f"  - {name}")
        sys.exit(1)
    
    # Remove script name from argv so the target script sees correct args
    sys.argv = [sys.argv[0]] + sys.argv[2:]
    
    # Import and run the script module
    module_path = SCRIPT_MODULES[script_name]
    try:
        module = importlib.import_module(module_path)
        
        # Look for a main() function or run at module level
        if hasattr(module, 'main'):
            module.main()
        # Module will execute its code when imported
        
    except ImportError as e:
        print(f"Error importing script module '{module_path}': {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error running script: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()