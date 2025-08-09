# Configuration Files - LEGACY

⚠️ **IMPORTANT**: These JSON configuration files are **LEGACY** and no longer used by the application.

## Current Configuration System

As of January 2025, all configuration is stored in the PostgreSQL database in the `configurations` table. Configuration is managed through:

1. **Admin Panel UI** - `/admin` routes for visual configuration
2. **API Endpoints** - RESTful APIs for programmatic access
3. **Database** - PostgreSQL `configurations` table for persistence

## Legacy Files

The following files are kept for reference only and are NOT used by the application:

- `field_mappings.json` - **LEGACY** - Field mappings now in database
- `sync_config.json` - **LEGACY** - Sync configuration now in database
- `core_field_mappings.json` - **LEGACY** - Core fields now in database
- `legacy_field_mappings.json` - **LEGACY** - Historical reference only

## Active Files

- `jira_instances.example.json` - Example configuration for JIRA instances (for documentation purposes)

## Migration

If you need to migrate from file-based to database configuration:

```bash
cd /path/to/backend
python -m scripts.migrate_configs
```

## Accessing Current Configuration

### Via API:
- GET `/api/config/field-mappings` - Get field mappings
- GET `/api/scheduler/status` - Get scheduler configuration
- GET `/api/admin/performance` - Get performance settings

### Via Database:
```sql
SELECT * FROM configurations WHERE is_active = true;
```

## Do NOT:
- ❌ Edit these JSON files expecting changes to take effect
- ❌ Use these files for new deployments
- ❌ Reference these files in code

## Do:
- ✅ Use the Admin Panel to configure settings
- ✅ Use API endpoints for programmatic access
- ✅ Store all configuration in the database