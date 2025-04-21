# Bugs and Fixes

## Location Name Issue

### Bug Description
The application was incorrectly displaying the client name in the location name field. This caused confusion in the UI where both the "Location Name" and "NDPU Client Name" columns showed identical values.

### Investigation
1. We first examined the code in `core/jira/jira_issues.py` and found that in the `process_issue` method, the same value (`client_name`) was being used for both the `location_name` and `ndpu_client_name` fields:

```python
record = (
    # ...
    project_key,                  # project_name
    datetime.now(),               # last_updated
    client_name,                  # location_name
    client_name,                  # ndpu_client_name
    # ...
)
```

2. We created a script (`utils/scripts/analyze_jira_fields.py`) to analyze all JIRA fields to identify potential location name fields.

3. We created another script (`utils/scripts/analyze_specific_issues.py`) to analyze specific JIRA issues (RALEIGH-36764 and SPACE-33622) to determine the correct field for location name.

4. Based on our analysis, we initially thought the correct field was `customfield_10603` (NDPU Listing Address), but further clarification revealed that the project name should be used.

### First Fix Attempt
We updated the code to use the project name for the location name:

```python
record = (
    # ...
    project_key,                  # project_name
    datetime.now(),               # last_updated
    self.field_processor.extract_field_value(fields, 'project.name'),  # location_name - use project name
    client_name,                  # ndpu_client_name
    # ...
)
```

However, this didn't work because the `extract_field_value` method didn't properly handle nested fields like 'project.name'.

### Second Fix Attempt
We modified the code to directly access the project name from the fields dictionary:

```python
record = (
    # ...
    project_key,                  # project_name
    datetime.now(),               # last_updated
    fields.get('project', {}).get('name', project_key),  # location_name - use project name or fallback to project_key
    client_name,                  # ndpu_client_name
    # ...
)
```

This fix successfully set the location name to the project name, but it appears this is still not the correct solution.

## Database Connection Issue in Clear JIRA Data Script

### Bug Description
The `clear_jira_data.py` script was failing with an error: `'_GeneratorContextManager' object has no attribute 'cursor'`.

### Investigation
The script was not properly using the database connection context manager.

### Fix
We updated the script to use the `execute_query` function directly, which handles the connection management internally:

```python
def clear_jira_issues():
    """Clear all data from the jira_issues_v2 table and its dependent tables."""
    try:
        # Get count before truncate
        count_before = execute_query("SELECT COUNT(*) FROM jira_issues_v2", fetch=True)[0][0]
        logger.info(f"Current number of records in jira_issues_v2: {count_before}")

        # Truncate the tables with CASCADE
        logger.info("Truncating jira_issues_v2 and dependent tables...")
        execute_query("TRUNCATE TABLE jira_issues_v2 CASCADE")
        logger.info("Successfully cleared all data from jira_issues_v2 and dependent tables")

        # Verify the tables are empty
        count_after = execute_query("SELECT COUNT(*) FROM jira_issues_v2", fetch=True)[0][0]
        logger.info(f"Records in jira_issues_v2 after truncate: {count_after}")

        if count_after == 0:
            logger.info("Data cleared successfully")
        else:
            logger.warning(f"Table not empty after truncate: {count_after} records remain")

    except Exception as e:
        logger.error(f"Error clearing data: {e}")
        raise
```

### Third Fix Attempt
We identified that the application should be using the `project_mappings_v2` table to get the location name, rather than directly using the project name from JIRA. This table provides a mapping between project keys and their full location names.

We modified the code to:
1. Import the `get_project_mapping` function from the db_projects module
2. Add a `_get_location_name` method to the IssueFetcher class that:
   - First tries to get the location name from the project_mappings_v2 table
   - Falls back to the JIRA project name if no mapping is found
   - Falls back to the project key as a last resort
3. Update the process_issue method to use the new _get_location_name method

However, this approach required manual configuration of the project_mappings_v2 table, which was not desired.

### Fourth Fix Attempt
We modified the _get_location_name method to prioritize the JIRA project name over the project_mappings_v2 table:

```python
def _get_location_name(self, project_key: str, fields: Dict[str, Any]) -> str:
    """
    Get location name from JIRA project name.
    
    Args:
        project_key: Project key
        fields: JIRA issue fields
        
    Returns:
        Location name string
    """
    try:
        # First try to get the project name directly from JIRA
        project_name = fields.get('project', {}).get('name')
        if project_name:
            return project_name
            
        # If no project name in JIRA, try to get from project_mappings_v2 table
        project_mapping = get_project_mapping(project_key)
        if project_mapping and project_mapping.get('location_name'):
            return project_mapping['location_name']
            
        # Last resort: use project key
        return project_key
        
    except Exception as e:
        logger.debug(f"Error getting location name for {project_key}: {e}")
        # Fall back to project key
        return project_key
```

However, this fix alone wasn't sufficient.

### Fifth Fix Attempt (Current Solution)
We discovered that the 'project' field wasn't being requested from JIRA in the API calls. In the IssueFetcher.__init__ method, we added 'project' to the list of fields that are always included:

```python
# Initialize field processor with config and load fields
self.field_processor = FieldProcessor(field_config_path)
self.fields = ['summary', 'status', 'project']  # Always include basic fields
```

This ensures that the JIRA API response includes the project information, which contains the full project name. With this change, the application can now correctly extract the location name from the JIRA project name.

For example:
- "SPACE" project name is "Space Coast"
- "GLBAY" project name is "Great Lakes Bay"
- "NECLT" project name is "Charlotte"
- "RALEIGH" project name is "Raleigh"
- "CINWEST" project name is "Cincinnati West"

This solution ensures that the application automatically uses the project name from JIRA as the location name, without requiring any manual configuration of the project_mappings_v2 table.