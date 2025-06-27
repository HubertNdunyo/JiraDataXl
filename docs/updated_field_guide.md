# JIRA Updated Field Integration Guide

## Overview
This guide documents the integration of the JIRA "updated" field into the sync process. The "updated" field captures the last time an issue was modified in JIRA.

## Changes Made

### 1. Field Mapping Configuration
Added the "updated" field to the system_fields group in `/config/field_mappings.json`:
```json
"updated": {
  "type": "datetime",
  "system_field": true,
  "required": false,
  "field_id": "updated",
  "description": "Last time the issue was updated in JIRA"
}
```

### 2. Issue Processing Updates
Modified `/core/jira/jira_issues.py` to:
- Extract the "updated" field from JIRA API responses
- Parse the timestamp using dateutil.parser (handles various timezone formats)
- Use the JIRA updated timestamp for the `last_updated` column instead of sync time

### 3. Database Column Mapping
The JIRA "updated" field now populates the existing `last_updated` column in the `jira_issues_v2` table.

## Field Format
The JIRA updated field returns timestamps in ISO 8601 format with timezone:
- Example: `2025-06-25T19:31:20.738+0800`

## Benefits
1. **Accurate Timeline**: The database now reflects when issues were actually modified in JIRA
2. **Better Tracking**: Can identify stale issues that haven't been updated recently
3. **Sync Optimization**: Future enhancement could use this to sync only recently updated issues

## Testing
To verify the integration:
1. Use the JIRA Query Dashboard (`/jira-dashboard`) to view the updated field
2. Check that the `last_updated` column in the database matches JIRA's updated time
3. Run a sync and confirm issues show their JIRA update time, not sync time

## Notes
- The field is available in both JIRA instances (betteredits.atlassian.net and betteredits2.atlassian.net)
- If parsing fails, the system falls back to using the current timestamp
- This is a non-breaking change that enhances data accuracy