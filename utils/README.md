# Utility Scripts and Tests

This directory contains utility scripts, tests, and maintenance tools for the Jira Data Sync Application.

## Directory Structure

### tests/
Test and verification scripts for database and sync operations.

- **dbtest.py**: Database testing utilities
- **verify_sync.py**: Sync verification tool
- **verify_project_names.py**: Project name verification tool

### scripts/

#### migrations/
Database migration and schema update scripts.

- **add_location_column.py**: Script to add location_name column to jira_issues table
- **fix_duplicates.py**: Script to fix duplicate project names
- **migrate_project_names.py**: Script to migrate project names to new format

#### maintenance/
Maintenance and cleanup scripts.

- **check_duplicates.py**: Script to check for project name inconsistencies
- **clear_jira_data.py**: Script to clear Jira data (use with caution)

## Usage

### Running Tests
```bash
python3 utils/tests/verify_sync.py
python3 utils/tests/verify_project_names.py
python3 utils/tests/dbtest.py
```

### Running Migrations
```bash
python3 utils/scripts/migrations/add_location_column.py
python3 utils/scripts/migrations/fix_duplicates.py
python3 utils/scripts/migrations/migrate_project_names.py
```

### Maintenance Tasks
```bash
python3 utils/scripts/maintenance/check_duplicates.py
python3 utils/scripts/maintenance/clear_jira_data.py
```

## Important Notes

1. Migration scripts should be run in order of creation
2. Always backup data before running migration scripts
3. Maintenance scripts should be run during off-peak hours
4. Test scripts can be run at any time as they don't modify data
