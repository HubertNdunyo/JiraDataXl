# Guide to Adding New Fields to JIRA Sync

This guide explains how to add new fields to the JIRA synchronization system using the field discovery feature.

## Prerequisites

- Access to the admin interface (`/admin/field-mappings`)
- Admin API key configured
- Both JIRA instances accessible
- Database access for running SQL commands

## Step 1: Discover Available Fields

1. Navigate to **Admin Panel → Field Mappings**
2. Click the **"Discover Fields"** button in the top right
3. Wait for the discovery process to complete (usually takes 10-20 seconds)
4. The system will display statistics showing:
   - Total fields discovered from each instance
   - Number of custom vs system fields
   - Last discovery timestamp

### How Field Discovery Works
- Calls JIRA REST API endpoint `/rest/api/3/field` for each instance
- Extracts field metadata including ID, name, type, and schema
- Stores in `jira_field_cache` table for quick access
- Automatically detects custom fields (customfield_XXXXX pattern)
- Identifies array fields and complex object types

## Step 2: Find the Field You Want to Add

### Using the Admin Interface
1. Use the search box in the field mappings page
2. Type part of the field name or ID
3. Results show fields from both instances
4. Note the field ID and type for configuration

### Using the Search API
You can search for fields using the API:

```bash
# Search for fields containing "invoice"
curl "http://localhost:8987/api/admin/fields/search?term=invoice" \
  -H "X-Admin-Key: jira-admin-key-2024"

# Search in specific instance
curl "http://localhost:8987/api/admin/fields/search?term=invoice&instance=1" \
  -H "X-Admin-Key: jira-admin-key-2024"
```

### Using Field Suggestions
Get smart mapping suggestions based on field similarity:

```bash
curl -X POST "http://localhost:8987/api/admin/fields/suggest" \
  -H "X-Admin-Key: jira-admin-key-2024" \
  -H "Content-Type: application/json" \
  -d '{"field_name": "invoice", "instance": "1"}'
```

### Understanding Field Types

The system recognizes these field types:
- **System Fields**: Built-in JIRA fields (summary, status, assignee, etc.)
- **Custom Fields**: User-created fields (customfield_XXXXX)
- **Nested Fields**: Object properties (project.name, assignee.displayName, etc.)

### Field Type Mapping

| JIRA Type | Database Column Type | Notes |
|-----------|---------------------|-------|
| string | TEXT | Single line or multi-line text |
| number | NUMERIC | Decimal numbers |
| integer | INTEGER | Whole numbers |
| boolean | BOOLEAN | True/false values |
| date | DATE | Date only |
| datetime | TIMESTAMP | Date and time |
| array | TEXT or JSONB | Arrays stored as JSON |
| object | JSONB | Complex objects |

## Step 3: Add Database Column

Once you've identified the field, create a database column:

```sql
-- Example: Adding a new invoice number field
ALTER TABLE jira_sync.jira_issues_v2 
ADD COLUMN ndpu_invoice_number VARCHAR(255);

-- Example: Adding a numeric field
ALTER TABLE jira_sync.jira_issues_v2 
ADD COLUMN ndpu_invoice_amount NUMERIC(10,2);

-- Example: Adding a boolean field
ALTER TABLE jira_sync.jira_issues_v2 
ADD COLUMN ndpu_invoice_paid BOOLEAN DEFAULT false;

-- Example: Adding a date field
ALTER TABLE jira_sync.jira_issues_v2 
ADD COLUMN ndpu_invoice_date DATE;
```

## Step 4: Update Field Mappings Configuration

1. In the admin interface, click **"Edit Mode"**
2. Find the appropriate field group or create a new one
3. Add your field mapping:

```json
{
  "invoice_number": {
    "type": "string",
    "required": false,
    "instance_1": {
      "field_id": "customfield_12345",
      "name": "Invoice Number"
    },
    "instance_2": {
      "field_id": "customfield_67890",
      "name": "Invoice Number"
    },
    "description": "Customer invoice reference number"
  }
}
```

4. Click **"Validate"** to ensure the field IDs exist in JIRA
   - Validation checks against cached field data
   - Shows specific errors for each field
   - Supports nested field validation
5. Click **"Save"** to update the configuration
   - Creates automatic backup before saving
   - Increments version number
   - Logs change in configuration history

## Step 5: Update Backend Code

### 1. Update Column Constants

Edit `/backend/core/db/constants.py`:

```python
ISSUE_COLUMNS = [
    'issue_key',
    'summary',
    'status',
    # ... existing columns ...
    'ndpu_invoice_number',  # Add your new column
    'last_updated'
]
```

### 2. Update Issue Processing

Edit `/backend/core/jira/jira_issues.py` in the `process_issue` method:

```python
# Add to the field processing section
invoice_number = extract_field_value(
    issue_data, 
    field_mappings, 
    'invoice_number',
    instance_key
)

# Add to the issue_dict
issue_dict = {
    # ... existing fields ...
    'ndpu_invoice_number': invoice_number,
    # ... rest of fields ...
}
```

### 3. Update Database Insert/Update

Edit `/backend/core/db/db_issues.py` to include the new column in the ON CONFLICT clause if it should be updated on sync.

## Step 6: Test the New Field

1. Run a single project sync to test:
   ```bash
   cd /backend
   ./venv/bin/python -c "
   from core.sync.sync_manager import SyncManager
   sm = SyncManager()
   sm.sync_projects(['PROJECT-KEY'])
   "
   ```

2. Check the database to verify data is being populated:
   ```sql
   SELECT issue_key, ndpu_invoice_number 
   FROM jira_sync.jira_issues_v2 
   WHERE ndpu_invoice_number IS NOT NULL 
   LIMIT 10;
   ```

## Common Field Patterns

### Text Fields
```json
{
  "field_name": {
    "type": "string",
    "instance_1": {"field_id": "customfield_XXX", "name": "Field Name"},
    "instance_2": {"field_id": "customfield_YYY", "name": "Field Name"}
  }
}
```

### Numeric Fields
```json
{
  "field_name": {
    "type": "number",
    "instance_1": {"field_id": "customfield_XXX", "name": "Amount"},
    "instance_2": {"field_id": "customfield_YYY", "name": "Amount"}
  }
}
```

### Date Fields
```json
{
  "field_name": {
    "type": "datetime",
    "instance_1": {"field_id": "customfield_XXX", "name": "Due Date"},
    "instance_2": {"field_id": "customfield_YYY", "name": "Due Date"}
  }
}
```

### Nested Fields (No JIRA field ID needed)
```json
{
  "project_name": {
    "type": "string",
    "instance_1": {"field_id": "project.name", "name": "Project Name"},
    "instance_2": {"field_id": "project.name", "name": "Project Name"}
  }
}
```

## Troubleshooting

### Field Not Found Error
- Run field discovery to refresh the cache
- Check field ID is correct (case-sensitive)
- Verify field exists in both instances
- Use search API to find correct field ID
- Check if field was recently added to JIRA

### Data Not Syncing
- Check database column exists and has correct type
- Verify field is in ISSUE_COLUMNS constant
- Check field extraction in process_issue method
- Look for errors in sync logs
- Run single project sync for testing
- Verify field has data in JIRA issues

### Type Mismatch
- Ensure database column type matches field type
- Check field value extraction handles the type correctly
- Consider type conversion if needed
- Review field schema in cached data
- Arrays may need JSONB storage

### Validation Errors
- **"Field not found in instance"**: Field doesn't exist or ID is wrong
- **"Invalid field type"**: Type in config doesn't match JIRA
- **"Pattern validation failed"**: Field ID format is incorrect
- **Nested fields**: These don't need JIRA validation (e.g., project.name)

## Best Practices

1. **Always validate** field mappings before saving
2. **Test with one project** before running full sync
3. **Document** the business purpose of new fields
4. **Use descriptive names** for database columns (ndpu_ prefix)
5. **Consider performance** - too many fields can slow sync
6. **Regular backups** before adding new fields
7. **Use field discovery** to ensure fields exist
8. **Check field suggestions** for optimal mapping
9. **Review field types** in cache before adding
10. **Monitor sync performance** after adding fields

## Advanced Features

### Bulk Field Operations (Coming Soon)
- Select multiple fields from discovery results
- Apply common settings to field groups
- Import field mappings from templates

### Field Mapping Wizard (In Development)
- Guided process for adding multiple fields
- Automatic type detection and validation
- Preview of field data before saving
- One-click setup for common field patterns

### Sample Data Preview (Planned)
- See actual JIRA data for fields
- Compare data between instances
- Validate data format before mapping
- Test transformations and conversions

## Field Naming Conventions

- Database columns: `ndpu_<field_purpose>` (lowercase, underscores)
- Config field keys: `<field_purpose>` (lowercase, underscores)
- Field names in UI: Title case with spaces

## Security Considerations

- Never store sensitive data (passwords, tokens) in custom fields
- Consider field visibility in JIRA permissions
- Audit field access if containing PII