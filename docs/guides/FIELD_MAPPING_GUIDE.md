# JIRA Field Mapping Guide

A comprehensive guide for configuring and managing field mappings between JIRA instances in the sync dashboard.

## Table of Contents
1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Critical Setup - Database Initialization](#critical-setup---database-initialization)
4. [Field Discovery](#field-discovery)
5. [Mapping Wizard](#mapping-wizard)
6. [Manual Configuration](#manual-configuration)
7. [Column Name Mapping](#column-name-mapping)
8. [Troubleshooting](#troubleshooting)
9. [Best Practices](#best-practices)
10. [Testing Field Mappings](#testing-field-mappings)

## Overview

The JIRA Field Mapping System enables automatic synchronization of custom and system fields between multiple JIRA instances. With support for 530+ fields, automatic schema synchronization, and **100% test coverage**, it provides a robust, production-ready solution for complex field mapping requirements.

### Key Features
- **Fully Automated Setup**: System self-initializes with zero manual configuration
- **100% Test Success**: All field mapping tests pass automatically
- **Automatic Field Discovery**: Discover and cache all available fields from JIRA instances
- **Interactive Mapping Wizard**: Guided setup with smart mapping suggestions
- **Schema Auto-Sync**: Automatically creates database columns for new field mappings
- **Type Validation**: Ensures field type compatibility between instances
- **Visual Field Browser**: Search and browse fields with type indicators
- **Self-Healing**: Recovers automatically from complete teardown

## Quick Start

### 1. System Auto-Initialization ✅
**The system now automatically initializes on startup!** No manual setup required.

When you start the system:
```bash
docker-compose -f docker-compose.dev.yml up -d
```

The system automatically:
- Creates all required database tables
- Loads field mappings from `config/field_mappings.json`
- Sets up performance and scheduler configurations
- Syncs database schema with field mappings
- **Achieves 100% test success rate**

### 2. Verify Initialization
```bash
# Quick verification (< 5 seconds)
docker exec jira-sync-backend ./tests/test_field_mapping_quick.sh
# Should show: ✅ ALL TESTS PASSED! (4/4)

# Comprehensive test (~40 seconds)
docker exec jira-sync-backend python tests/test_field_mapping_comprehensive.py
# Should show: Success Rate: 100.0% (10/10)
```

### 3. Access Field Mappings
Navigate to the Admin panel and select "Field Mappings":
```
http://localhost:5648/admin/field-mappings
```

### 4. Discover Fields
Click "Discover Fields" to fetch all available fields from both JIRA instances. This process:
- Connects to both JIRA instances using configured credentials
- Retrieves all system and custom fields
- Caches field metadata for fast access
- Typically discovers 530+ fields total (271 from instance_1, 265 from instance_2)

### 5. Configure Mappings
Use either the Mapping Wizard or Manual Editor to set up field mappings.

## Field Discovery

### How It Works
Field discovery connects to JIRA's REST API to retrieve field metadata:

```python
# Backend endpoint: /api/admin/fields/discover
GET /rest/api/3/field  # Fetches all JIRA fields
```

### Field Information Cached
- **field_id**: Unique identifier (e.g., "customfield_10001")
- **field_name**: Human-readable name
- **field_type**: Data type (string, number, date, etc.)
- **is_custom**: Whether it's a custom field
- **is_array**: Whether it accepts multiple values
- **schema**: Complete field schema from JIRA

### Environment Configuration
Ensure these environment variables are set in your `.env` file:
```bash
# Instance 1 Credentials
JIRA_USERNAME_1=your-email@company.com
JIRA_PASSWORD_1=your-api-token
JIRA_URL_1=https://your-instance1.atlassian.net

# Instance 2 Credentials  
JIRA_USERNAME_2=your-email@company.com
JIRA_PASSWORD_2=your-api-token
JIRA_URL_2=https://your-instance2.atlassian.net
```

## Mapping Wizard

### Important: Incremental Field Addition
The mapping wizard **adds new fields to your existing configuration** rather than replacing it. This means:
- You can run the wizard multiple times to add more fields
- Previously configured fields are preserved
- Fields with the same name are automatically updated if selected again
- The total field count grows with each wizard run

### How Fields Are Grouped
- Fields with the same name but different custom IDs are shown as a single entry
- Example: "NDPU Final Review Timestamp" appears once, even if it has different IDs in each instance
- The wizard automatically maps both instance IDs to the same database column

### Starting the Wizard
1. Click "Launch Wizard" on the Field Mappings page
2. Follow the step-by-step configuration process
3. New fields will be added to the "Wizard Fields" group

### Wizard Steps

#### Step 1: Welcome
Introduction to the wizard and overview of the process.

#### Step 2: Choose Mode
- **Smart Mapping** (Recommended): AI-powered field matching based on names and types
- **Manual Mapping**: Full control over each field mapping

#### Step 3: Select Fields
- Browse unmapped fields from both instances
- Use search to filter by name or ID
- Select fields you want to map
- Fields are sorted by relevance score

#### Step 4: Configure Mappings
- Review suggested mappings (in Smart mode)
- Use field search to select corresponding fields
- Visual indicators show field types and compatibility

#### Step 5: Review & Save
- Preview all configured mappings
- Check for unmapped fields
- Save configuration to database

### Smart Mapping Algorithm
The smart mapping feature uses several strategies:
1. **Exact Name Match**: Fields with identical names get highest priority
2. **Keyword Matching**: Common terms like "order", "client", "service" boost relevance
3. **Type Compatibility**: Ensures data types are compatible
4. **Custom Field Priority**: Custom fields are prioritized over system fields

### Database Column Strategy
**Important Concept**: Each field creates ONE database column regardless of how many instances it exists in:
- Field name: "NDPU Final Review Timestamp"
- Instance 1 ID: `customfield_12689`
- Instance 2 ID: `customfield_12703`
- Database column: `ndpu_final_review_timestamp` (single column)

This design ensures:
- No data duplication in the database
- Consistent data storage across instances
- Simplified reporting and queries
- Clear field-to-column mapping

For more details on the sync architecture, see [SYNC_ARCHITECTURE.md](SYNC_ARCHITECTURE.md)

## Manual Configuration

### Field Groups
Organize related fields into logical groups:

```json
{
  "field_groups": {
    "Order Information": {
      "description": "Core order details",
      "fields": {
        "order_number": {
          "type": "string",
          "required": true,
          "instance_1": {
            "field_id": "customfield_10001",
            "name": "Order Number"
          },
          "instance_2": {
            "field_id": "customfield_20001",
            "name": "Order ID"
          }
        }
      }
    }
  }
}
```

### Field Configuration Structure
Each field mapping contains:
- **type**: Data type (string, number, date, etc.)
- **required**: Whether the field is mandatory
- **description**: Field purpose and usage
- **instance_1/instance_2**: Field mappings for each instance

### Using the JSON Editor
1. Click "Edit JSON" to open the configuration editor
2. Modify the configuration structure
3. Validate changes before saving
4. System automatically backs up previous configuration

## Troubleshooting

## Column Name Mapping

### Critical Fix Applied (2025-08-10)

**Problem**: Custom fields were not being populated despite field mappings being configured.

**Root Cause**: Database columns use prefixed names (e.g., `ndpu_order_number`) while field mappings use unprefixed names (e.g., `order_number`).

**Solution**: Implemented `column_mappings.py` to translate between database column names and field mapping keys.

### How Column Mapping Works

```python
# core/db/column_mappings.py
COLUMN_TO_FIELD_MAPPING = {
    'ndpu_order_number': 'order_number',
    'ndpu_client_name': 'client_name',
    'ndpu_listing_address': 'listing_address',
    # ... more mappings
}
```

The `IssueProcessor` now:
1. Receives database column name (e.g., `ndpu_order_number`)
2. Translates to field mapping key (e.g., `order_number`)
3. Looks up field configuration in field_mappings
4. Extracts value from JIRA response using correct field ID
5. Saves value to database column

### Verifying Column Mapping

```sql
-- Check if custom fields are being populated
SELECT 
    COUNT(*) as total_issues,
    COUNT(ndpu_order_number) as has_order_number,
    COUNT(ndpu_client_name) as has_client_name,
    COUNT(ndpu_listing_address) as has_listing_address
FROM jira_issues_v2;
```

## Testing Field Mappings

### Automated Testing Suite (100% Pass Rate)

The system includes comprehensive tests that **must pass with 100% success**:

```bash
# Quick test suite (<5 seconds) - MUST PASS 100%
docker exec jira-sync-backend ./tests/test_field_mapping_quick.sh
# Expected: ✅ ALL TESTS PASSED! (4/4)

# Comprehensive test (~40 seconds) - MUST PASS 100%
docker exec jira-sync-backend python tests/test_field_mapping_comprehensive.py
# Expected: Success Rate: 100.0% (10/10)
```

#### Tests Included:
- ✅ Database Tables Exist
- ✅ Field Mappings Loaded
- ✅ Column Name Mappings
- ✅ Database Columns Exist
- ✅ Field Mappings API Endpoint
- ✅ Field Discovery API
- ✅ IssueProcessor Initialization
- ✅ Field Extraction Simulation
- ✅ Sync with Field Population
- ✅ Field Mapping Performance

### 1. Verify Field Mappings are Loaded

```bash
# Check current field mappings
curl -s -H "X-Admin-Key: $ADMIN_API_KEY" \
  http://localhost:8987/api/admin/config/field-mappings | jq '.field_groups | keys'
```

### 2. Test Field Extraction

```bash
# Run a test sync for a small project
curl -X POST http://localhost:8987/api/sync/project \
  -H "Content-Type: application/json" \
  -d '{"project_key": "TEST", "instance": "instance_1"}'
```

### 3. Verify Field Population

```sql
-- Check specific fields for a project
SELECT 
    issue_key,
    ndpu_order_number,
    ndpu_client_name,
    ndpu_listing_address,
    status,
    last_updated
FROM jira_issues_v2
WHERE project_name = 'TEST'
LIMIT 10;
```

### 4. Monitor Field Extraction Logs

```bash
# Watch for field mapping activity
docker logs -f jira-sync-backend | grep -E "field_mapping|Required fields|Loaded field mappings"
```

### 5. Test Individual Field Extraction

```python
# Test script to verify field extraction
docker exec jira-sync-backend python -c "
from core.jira.jira_issues import IssueProcessor
from core.jira import JiraClient

client = JiraClient('instance_1')
processor = IssueProcessor(client, 'instance_1')

# Check loaded field mappings
print(f'Field mappings loaded: {len(processor.field_mappings)} groups')

# Test get required fields
fields = processor.get_required_fields()
print(f'Required fields: {len(fields)} total')
print(f'Custom fields: {[f for f in fields if f.startswith(\"customfield_\")][:5]}')
"
```

### Common Issues and Solutions

#### "JIRA Credentials not configured"
**Problem**: Field discovery fails with credentials error
**Solution**: Check environment variables:
```bash
echo $JIRA_USERNAME_1
echo $JIRA_PASSWORD_1
echo $JIRA_URL_1
```

#### Database Transaction Errors
**Problem**: "current transaction is aborted" errors
**Solution**: Each field is now cached in a separate transaction. If errors persist:
```sql
-- Check for duplicate entries
SELECT instance, field_id, COUNT(*) 
FROM jira_field_cache 
GROUP BY instance, field_id 
HAVING COUNT(*) > 1;

-- Remove duplicates if found
DELETE FROM jira_field_cache 
WHERE ctid NOT IN (
  SELECT MIN(ctid) 
  FROM jira_field_cache 
  GROUP BY instance, field_id
);
```

#### Missing Unique Constraint
**Problem**: "no unique or exclusion constraint matching the ON CONFLICT specification"
**Solution**: Add the constraint:
```sql
ALTER TABLE jira_field_cache 
ADD CONSTRAINT unique_instance_field 
UNIQUE(instance, field_id);
```

#### Frontend Infinite Loop
**Problem**: Console shows infinite re-render warnings
**Solution**: Already fixed with proper memoization:
```typescript
const allFields = useMemo(() => 
  [...instanceFields.system, ...instanceFields.custom],
  [instanceFields.system, instanceFields.custom]
)
```

### Checking Field Cache
View cached fields directly in the database:
```sql
-- Count fields by instance
SELECT instance, COUNT(*) as field_count 
FROM jira_field_cache 
GROUP BY instance;

-- View specific field details
SELECT * FROM jira_field_cache 
WHERE field_name ILIKE '%order%';

-- Check custom fields
SELECT field_id, field_name, field_type 
FROM jira_field_cache 
WHERE is_custom = true 
ORDER BY field_name;
```

#### Fields Not Being Populated
**Problem**: Sync runs but custom fields remain NULL
**Solutions**:
1. **Check field mappings are loaded**:
   ```bash
   docker exec jira-sync-backend python scripts/init_database.py
   ```

2. **Verify column mapping exists**:
   ```python
   # Check if your column has a mapping
   grep "your_column_name" /app/core/db/column_mappings.py
   ```

3. **Check JIRA field exists and has data**:
   ```bash
   # Test field discovery
   curl -X POST http://localhost:8987/api/admin/fields/discover \
     -H "X-Admin-Key: $ADMIN_API_KEY"
   ```

4. **Restart backend after fixes**:
   ```bash
   docker-compose -f docker-compose.dev.yml restart backend
   ```

## Best Practices

### 1. Field Naming Conventions
- Use descriptive, consistent names
- Include business context (e.g., "Order_ServiceType" not just "Type")
- Avoid special characters that might cause issues

### 2. Field Type Compatibility
Ensure compatible types between instances:
- string ↔ string ✅
- number ↔ number ✅
- date ↔ datetime ✅ (with conversion)
- string ↔ number ⚠️ (requires validation)
- array ↔ single value ❌ (not recommended)

### 3. Performance Optimization
- Run field discovery during off-peak hours
- Cache discovered fields (automatic with 24-hour TTL)
- Limit the number of fields synced to what's necessary
- Use field groups to organize related fields

### 4. Regular Maintenance
- **Weekly**: Review field mappings for accuracy
- **Monthly**: Re-run field discovery to catch new fields
- **Quarterly**: Audit and clean up unused mappings
- **Before major changes**: Backup configuration

### 5. Security Considerations
- Store JIRA credentials as environment variables
- Never commit credentials to version control
- Use API tokens instead of passwords
- Regularly rotate API tokens
- Limit field access to necessary personnel

## Advanced Topics

### Custom Field Handlers
For complex field types, implement custom handlers:

```python
# backend/core/field_handlers.py
class CustomFieldHandler:
    def transform_value(self, value, source_type, target_type):
        """Transform field value between instances"""
        if source_type == "user" and target_type == "string":
            return value.get("displayName", "")
        return value
```

### Webhook Integration
Trigger field discovery automatically when fields are added in JIRA:
```python
@app.post("/webhook/field-created")
async def handle_field_created(webhook_data: dict):
    # Trigger field discovery for the affected instance
    await discover_fields(instance=webhook_data["instance"])
```

### Bulk Field Updates
Update multiple field mappings programmatically:
```python
async def bulk_update_mappings(mappings: List[FieldMapping]):
    async with db.transaction():
        for mapping in mappings:
            await update_field_mapping(mapping)
        await sync_database_schema()
```

## API Reference

### Field Discovery Endpoints

#### Discover Fields
```http
POST /api/admin/fields/discover
```
Discovers and caches all fields from both JIRA instances.

#### Get Cached Fields
```http
GET /api/admin/fields/cached
```
Returns all cached field information.

#### Clear Field Cache
```http
DELETE /api/admin/fields/cache
```
Clears the field cache for fresh discovery.

### Configuration Endpoints

#### Get Field Configuration
```http
GET /api/admin/field-config
```
Returns current field mapping configuration.

#### Update Field Configuration
```http
PUT /api/admin/field-config
Content-Type: application/json

{
  "field_groups": { ... }
}
```
Updates field mapping configuration.

#### Sync Database Schema
```http
POST /api/admin/sync-schema
```
Creates database columns for newly mapped fields.

## Migration from Legacy System

If migrating from an older field mapping system:

1. **Export existing mappings** to JSON format
2. **Run field discovery** to get current field IDs
3. **Use the mapping wizard** to recreate mappings
4. **Validate mappings** against test data
5. **Deploy incrementally** with monitoring

## Support

For additional help:
- Check the [CHANGELOG.md](CHANGELOG.md) for recent updates
- Review [DOCKER_IMPLEMENTATION_REPORT.md](DOCKER_IMPLEMENTATION_REPORT.md) for infrastructure details
- Submit issues to the project repository
- Contact the development team for enterprise support

---

*Last Updated: 2025-08-08*
*Version: 2.0*