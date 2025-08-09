# Core Business Fields Documentation

## Overview

This document describes the core business fields used in the JIRA synchronization system. These fields represent the essential data points for tracking photography orders, editing workflows, and client information.

## Field Categories

### 1. **Core System Fields**
Basic JIRA system fields that exist in both instances:
- `issue_key` - Unique issue identifier
- `summary` - Issue title/summary
- `status` - Current workflow status
- `project_name` - Project the issue belongs to
- `last_updated` - Last modification timestamp

### 2. **Order Information**
Fields related to order and client details:
- `ndpu_order_number` - Unique order identifier
- `ndpu_client_name` - Client's full name
- `ndpu_client_email` - Client's email address
- `ndpu_listing_address` - Property address for the shoot

### 3. **Media and Delivery**
Fields for tracking media files and delivery:
- `ndpu_raw_photos` - Count of raw photos taken
- `dropbox_raw_link` - Link to raw media in Dropbox
- `dropbox_edited_link` - Link to edited media in Dropbox
- `same_day_delivery` - Priority delivery flag

### 4. **Editing and Production**
Fields for managing the editing workflow:
- `escalated_editing` - Priority editing flag
- `edited_media_revision_notes` - Revision notes
- `ndpu_editing_team` - Assigned editing team
- `ndpu_service` - Type of service (e.g., photography, video, drone)

### 5. **Workflow Timestamps**
Critical timestamps for tracking order progress:
- `scheduled` - When the shoot was scheduled
- `acknowledged` - When order was acknowledged
- `at_listing` - Photographer arrival time
- `shoot_complete` - Photography completion time
- `uploaded` - Media upload completion
- `edit_start` - Editing start time
- `final_review` - Final review completion
- `closed` - Issue closure time

### 6. **Location and Instructions**
Additional information fields:
- `location_name` - Geographic location/region
- `ndpu_comments` - General order comments
- `ndpu_editor_notes` - Specific notes for editors
- `ndpu_access_instructions` - Property access details
- `ndpu_special_instructions` - Special shoot requirements

## Database Schema

All these fields are stored in the `jira_issues_v2` table with appropriate data types:

```sql
CREATE TABLE jira_issues_v2 (
    -- Core fields
    issue_key VARCHAR(50) PRIMARY KEY,
    summary TEXT,
    status VARCHAR(50),
    project_name VARCHAR(100),
    last_updated TIMESTAMP,
    
    -- Order information
    ndpu_order_number VARCHAR(100),
    ndpu_client_name VARCHAR(255),
    ndpu_client_email VARCHAR(255),
    ndpu_listing_address TEXT,
    
    -- Media and delivery
    ndpu_raw_photos INTEGER,
    dropbox_raw_link TEXT,
    dropbox_edited_link TEXT,
    same_day_delivery VARCHAR(50),
    
    -- Editing and production
    escalated_editing VARCHAR(50),
    edited_media_revision_notes TEXT,
    ndpu_editing_team VARCHAR(255),
    ndpu_service VARCHAR(255),
    
    -- Workflow timestamps
    scheduled TIMESTAMP,
    acknowledged TIMESTAMP,
    at_listing TIMESTAMP,
    shoot_complete TIMESTAMP,
    uploaded TIMESTAMP,
    edit_start TIMESTAMP,
    final_review TIMESTAMP,
    closed TIMESTAMP,
    
    -- Location and instructions
    location_name VARCHAR(255),
    ndpu_comments TEXT,
    ndpu_editor_notes TEXT,
    ndpu_access_instructions TEXT,
    ndpu_special_instructions TEXT
);
```

## Field Mapping Configuration

The field mappings are defined in `/backend/config/core_field_mappings.json`. This file maps database columns to JIRA custom field IDs for each instance.

### Example Mapping:
```json
{
  "ndpu_order_number": {
    "type": "string",
    "description": "NDPU Order Number",
    "instance_1": {
      "field_id": "customfield_10501",
      "name": "NDPU Order Number"
    },
    "instance_2": {
      "field_id": "customfield_10502",  // Different ID, same field
      "name": "NDPU Order Number"
    }
  }
}
```

## Setting Up Field Mappings

### 1. Run Field Discovery
```bash
# From the frontend admin panel
Navigate to: http://localhost:5648/admin/field-mappings
Click: "Discover Fields"
```

### 2. Verify Field Mappings
```bash
# Run the verification script
cd backend
python scripts/verify_field_mappings.py

# Search for a specific field
python scripts/verify_field_mappings.py --search "order number"
```

### 3. Apply Database Migration
```bash
# Run the migration to add columns
psql -U your_user -d your_database -f migrations/006_add_core_business_fields.sql
```

### 4. Configure Missing Mappings
Use the Field Mapping Wizard in the admin panel to:
1. Select unmapped fields
2. Configure instance mappings
3. Save the configuration

## Important Notes

### Field ID Differences
The same business field often has different custom field IDs in each JIRA instance:
- Instance 1: `customfield_12689` (NDPU Final Review Timestamp)
- Instance 2: `customfield_12703` (NDPU Final Review Timestamp)

The mapping configuration handles this translation automatically during sync.

### Database Column Naming
Database columns use normalized names:
- JIRA field: "NDPU Final Review Timestamp"
- Database column: `final_review`

This simplifies queries and maintains consistency.

### Missing Field Mappings
Some fields may not have mappings for Instance 2 initially. These need to be:
1. Identified using field discovery
2. Mapped using the wizard
3. Verified using the verification script

## Sync Process

When syncing issues between instances:

1. **Read from Source**: Get field value using source instance's field ID
2. **Store in Database**: Save to the normalized column name
3. **Write to Target**: Set field value using target instance's field ID

Example:
```
Instance 1 (customfield_10501) → Database (ndpu_order_number) → Instance 2 (customfield_10502)
```

## Troubleshooting

### Field Not Syncing
1. Check if field is mapped in both instances
2. Verify field IDs are correct
3. Ensure database column exists
4. Check field type compatibility

### Finding Field IDs
```bash
# Use the search script
python scripts/verify_field_mappings.py --search "field_name"

# Or use the admin panel
Field Mappings → Discover Fields → Search
```

### Updating Mappings
1. Edit `/backend/config/core_field_mappings.json`
2. Or use the Field Mapping Wizard
3. Run sync schema to create any new columns

---

*Last Updated: 2025-01-09*
*Version: 1.0*