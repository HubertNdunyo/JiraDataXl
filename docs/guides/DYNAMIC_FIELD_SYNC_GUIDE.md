# Dynamic Field Sync System Guide

**Last Updated**: August 10, 2025

## ⚠️ CRITICAL: Database Initialization Required

After any database reset or container recreation with `-v` flag:
```bash
docker exec jira-sync-backend python scripts/init_database.py
```
Without this, field mappings will NOT work!

## Overview

The JIRA sync system has been completely rebuilt to use **dynamic field mappings** stored in the database. This means you can now:
- ✅ Add/remove fields without touching any code
- ✅ Configure different field mappings for each JIRA instance
- ✅ Update field mappings through the UI and see changes immediately
- ✅ No more hardcoded custom field IDs

---

## Key Changes from Legacy System

### Before (Hardcoded)
```python
# Old system - hardcoded in jira_issues.py
order_number = extract_field_value(fields, 'customfield_10501')
client_name = extract_field_value(fields, 'customfield_10600')
# ... 30+ hardcoded field extractions
```

### After (Dynamic)
```python
# New system - reads from database configuration
for column in ISSUE_COLUMNS:
    # Column name mapping handles prefixes (ndpu_order_number -> order_number)
    field_key = get_field_key_for_column(column)
    mapping = get_field_mapping_for_column(field_key)
    value = extract_field_value(issue, mapping)
```

### Critical Fix (August 2025)
**Problem**: Database columns like `ndpu_order_number` didn't match field mapping keys like `order_number`
**Solution**: Added `core/db/column_mappings.py` to translate between them

---

## How It Works

### 1. Field Configuration Storage
Field mappings are stored in the `configurations` table in PostgreSQL:
```sql
SELECT config_value FROM configurations 
WHERE config_type = 'jira' AND config_key = 'field_mappings'
```

### 2. Configuration Structure
```json
{
  "field_groups": {
    "Group Name": {
      "fields": {
        "database_column_name": {
          "type": "string|integer|boolean|datetime",
          "instance_1": {
            "field_id": "customfield_xxxxx"
          },
          "instance_2": {
            "field_id": "customfield_yyyyy"
          }
        }
      }
    }
  }
}
```

### 3. Dynamic Extraction Process
1. **Load Configuration**: System reads field mappings from database
2. **Process Issues**: For each JIRA issue and database column:
   - Find the field mapping for that column
   - Extract value using the appropriate field ID for the instance
   - Sanitize and validate based on field type
3. **Store in Database**: Save processed data to `jira_issues_v2` table

---

## Troubleshooting Field Sync Issues

### Issue: Custom Fields Not Populating

**Symptoms**: 
- Sync runs successfully
- Issues are created in database
- But custom fields (ndpu_*) remain NULL

**Root Causes & Solutions**:

1. **Field mappings not loaded**
   ```bash
   # Initialize database with default mappings
   docker exec jira-sync-backend python scripts/init_database.py
   ```

2. **Column name mismatch**
   ```bash
   # Verify column mapping exists
   docker exec jira-sync-backend python -c "
   from core.db.column_mappings import get_field_key_for_column
   print(get_field_key_for_column('ndpu_order_number'))  # Should output: order_number
   "
   ```

3. **Field ID incorrect for instance**
   ```bash
   # Discover and verify field IDs
   curl -X POST http://localhost:8987/api/admin/fields/discover \
     -H "X-Admin-Key: secure-admin-key-2024"
   ```

4. **Backend not restarted after config change**
   ```bash
   docker-compose -f docker-compose.dev.yml restart backend
   ```

### Issue: Field Discovery Fails

**Solutions**:
1. Check JIRA credentials in environment
2. Verify JIRA API access
3. Check rate limiting

### Issue: Schema Sync Fails

**Solutions**:
1. Check database permissions
2. Verify column types match field types
3. Review migration logs

---

## Verifying Field Sync Success

### Quick Verification Query
```sql
-- Run after sync to verify field population
SELECT 
    COUNT(*) as total_issues,
    COUNT(ndpu_order_number) as has_order_number,
    COUNT(ndpu_client_name) as has_client_name,
    COUNT(ndpu_listing_address) as has_address,
    ROUND(100.0 * COUNT(ndpu_order_number) / NULLIF(COUNT(*), 0), 2) as pct_populated
FROM jira_issues_v2
WHERE last_updated > NOW() - INTERVAL '1 hour';
```

### Check Specific Project
```sql
SELECT 
    issue_key,
    ndpu_order_number,
    ndpu_client_name,
    ndpu_listing_address,
    status,
    last_updated
FROM jira_issues_v2
WHERE project_name = 'YOUR_PROJECT'
AND ndpu_order_number IS NOT NULL
LIMIT 5;
```

### Monitor Field Extraction
```bash
# Watch real-time field mapping activity
docker logs -f jira-sync-backend | grep -E "Loaded field mappings|Required fields|Field groups"
```

---

## Managing Field Mappings

### Using the UI (Recommended)

1. **Navigate to Field Mappings**
   ```
   http://localhost:5648/admin/field-mappings
   ```

2. **Discover Available Fields**
   - Click "Discover Fields" to fetch all fields from both JIRA instances
   - Fields are cached for performance

3. **Add New Fields**
   - Click "Setup Wizard" or "Add Field"
   - Search for the field by name
   - Select the JIRA field for each instance
   - Configure field type and options
   - Save configuration

4. **Remove Fields**
   - Find the field in the list
   - Click remove/delete icon
   - Confirm removal

### Using the API

```bash
# Get current configuration
curl http://localhost:5649/api/admin/field-mappings

# Update configuration
curl -X POST http://localhost:5649/api/admin/field-mappings \
  -H "Content-Type: application/json" \
  -d @new_mappings.json
```

### Direct Database Update

```sql
-- View current configuration
SELECT jsonb_pretty(config_value) 
FROM configurations 
WHERE config_type = 'jira' 
  AND config_key = 'field_mappings' 
  AND is_active = true;

-- Update configuration (creates new version)
INSERT INTO configurations (config_type, config_key, config_value, version)
VALUES ('jira', 'field_mappings', '{"field_groups": {...}}', 
  (SELECT MAX(version) + 1 FROM configurations 
   WHERE config_type = 'jira' AND config_key = 'field_mappings')
);
```

---

## Adding New Fields

### Step 1: Identify the Field
```python
# Use field discovery to find field IDs
python3 scripts/discover_fields.py --search "order number"
```

### Step 2: Add to Configuration
Use the UI wizard or manually add:
```json
{
  "field_groups": {
    "Business Fields": {
      "fields": {
        "order_number": {
          "type": "string",
          "description": "Order Number",
          "instance_1": {
            "field_id": "customfield_10501",
            "name": "NDPU Order Number"
          },
          "instance_2": {
            "field_id": "customfield_10502",
            "name": "Order Num"
          }
        }
      }
    }
  }
}
```

### Step 3: Add Database Column (if needed)
```sql
ALTER TABLE jira_issues_v2 
ADD COLUMN IF NOT EXISTS order_number VARCHAR(100);
```

### Step 4: Test Sync
- Run sync for a small project
- Verify field is populated correctly

---

## Field Types and Validation

### Supported Field Types

| Type | Description | Database Type | Example Values |
|------|-------------|---------------|----------------|
| `string` | Text fields | VARCHAR/TEXT | "ABC123" |
| `integer` | Whole numbers | INTEGER | 42 |
| `float` | Decimal numbers | NUMERIC | 3.14 |
| `boolean` | True/False | BOOLEAN | true, false |
| `datetime` | Timestamps | TIMESTAMP | 2025-01-09T10:30:00 |
| `json` | Complex objects | JSONB | {"key": "value"} |

### Type Conversion
The system automatically handles:
- String "Yes"/"No" → Boolean true/false
- ISO timestamps → datetime objects
- Nested objects → extracted values
- Multiple fields → combined strings

---

## Special Field Configurations

### System Fields
```json
{
  "issue_key": {
    "system_field": true,
    "field_path": "key"
  },
  "status": {
    "system_field": true,
    "field_path": "fields.status.name"
  }
}
```

### Combined Fields
```json
{
  "access_instructions": {
    "field_ids": ["customfield_10700", "customfield_12594"],
    "combine_method": "space"
  }
}
```

### Transition-Based Fields
```json
{
  "shoot_complete": {
    "source": "transitions",
    "transition_name": "shoot_complete",
    "type": "datetime"
  }
}
```

---

## Troubleshooting

### Field Not Syncing

1. **Check Configuration Exists**
```sql
SELECT * FROM configurations 
WHERE config_type = 'jira' 
  AND config_key = 'field_mappings' 
  AND is_active = true;
```

2. **Verify Field Mapping**
```python
# Check if field is mapped
python3 scripts/verify_field_mappings.py --field "field_name"
```

3. **Check Database Column**
```sql
-- Verify column exists
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'jira_issues_v2' 
  AND column_name = 'your_field_name';
```

4. **Review Sync Logs**
```bash
docker logs jira-sync-backend --tail 100 | grep "field_name"
```

### Performance Issues

- **Too Many Fields**: Sync only essential fields
- **Complex Extractions**: Simplify combined fields
- **Large Changelogs**: Reduce transition tracking

---

## Migration from Legacy System

If you have existing hardcoded fields:

1. **Export Legacy Mappings**
```bash
python3 scripts/extract_hardcoded_mappings.py
```

2. **Load into Database**
```bash
python3 scripts/load_legacy_mappings.py
```

3. **Verify All Fields**
```bash
python3 scripts/verify_field_mappings.py
```

4. **Test with Small Project**
```bash
python3 scripts/test_sync.py --project TEST
```

---

## Best Practices

### 1. Field Naming
- Use snake_case for database columns
- Match business terminology
- Be consistent across instances

### 2. Field Types
- Use appropriate types for validation
- Consider future data analysis needs
- Document special handling requirements

### 3. Configuration Management
- Always backup before major changes
- Use versioning for tracking changes
- Document why fields were added/removed

### 4. Performance
- Only sync fields you actually use
- Avoid complex field combinations
- Monitor sync performance metrics

---

## API Reference

### Get Field Mappings
```http
GET /api/admin/field-mappings
```

### Update Field Mappings
```http
POST /api/admin/field-mappings
Content-Type: application/json

{
  "field_groups": {
    ...
  }
}
```

### Discover Fields
```http
POST /api/admin/fields/discover
```

### Get Cached Fields
```http
GET /api/admin/fields/cached
```

---

## Database Schema

### Key Tables

| Table | Purpose |
|-------|---------|
| `configurations` | Stores field mapping configuration |
| `jira_field_cache` | Caches discovered JIRA fields |
| `jira_issues_v2` | Stores synced issue data |
| `configuration_history` | Tracks configuration changes |

### Configuration Table Structure
```sql
CREATE TABLE configurations (
    id SERIAL PRIMARY KEY,
    config_type VARCHAR(50),    -- 'jira'
    config_key VARCHAR(100),     -- 'field_mappings'
    config_value JSONB,          -- Field configuration
    version INTEGER,             -- Version number
    is_active BOOLEAN,           -- Current version flag
    updated_at TIMESTAMP
);
```

---

## Summary

The new dynamic field sync system provides:
- **Flexibility**: Add/remove fields without code changes
- **Maintainability**: All configuration in one place
- **Scalability**: Easy to add new field types
- **Auditability**: Full history of configuration changes
- **Performance**: Optimized field extraction

No more hardcoded field IDs! 🎉

---

*Last Updated: 2025-01-09*
*Version: 2.0 (Dynamic System)*