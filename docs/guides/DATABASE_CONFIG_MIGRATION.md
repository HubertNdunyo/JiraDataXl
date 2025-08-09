# Database Configuration Migration Guide

## Overview

As of January 2025, all configuration has been migrated from file-based storage to database storage. This provides better consistency, easier management, and eliminates file permission issues.

## What Changed

### Old System (Deprecated)
- Configuration stored in JSON files:
  - `/backend/config/sync_config.json` - Scheduler settings
  - `/backend/config/field_mappings.json` - Field mappings
  - `/backend/config/performance_config.json` - Performance settings

### New System (Current)
- All configuration stored in PostgreSQL `configurations` table
- Accessed via API endpoints
- Managed through Admin Panel UI
- No file system dependencies

## Configuration Types

The database stores different configuration types:

| Type | Key | Description | API Endpoint |
|------|-----|-------------|--------------|
| `sync` | `scheduler` | Scheduler settings (interval, enabled) | `/api/scheduler/config` |
| `field_mappings` | `mappings` | JIRA field mappings | `/api/admin/field-mappings` |
| `performance` | `settings` | Performance tuning | `/api/admin/performance` |

## Migration Steps

### 1. Automatic Migration

If you have existing file-based configurations, run the migration script:

```bash
cd backend
python -m scripts.migrate_configs
```

This will:
- Read existing JSON configuration files
- Import them into the database
- Preserve all existing settings

### 2. Manual Migration

If automatic migration fails, you can manually migrate using the API:

```bash
# Migrate scheduler config
curl -X PUT http://localhost:8987/api/scheduler/config \
  -H "Content-Type: application/json" \
  -d '{
    "enabled": true,
    "interval_minutes": 30
  }'

# Migrate performance config
curl -X PUT http://localhost:8987/api/admin/performance \
  -H "Content-Type: application/json" \
  -H "X-Admin-Key: your-admin-key" \
  -d '{
    "max_workers": 12,
    "batch_size": 500,
    "lookback_days": 60,
    "rate_limit_pause": 0.5
  }'
```

### 3. Verify Migration

Check that configuration is loaded correctly:

```bash
# Check scheduler status
curl http://localhost:8987/api/scheduler/status

# Check performance settings (requires admin key)
curl http://localhost:8987/api/admin/performance \
  -H "X-Admin-Key: your-admin-key"
```

## Accessing Configuration

### Via API

```python
# Example: Get scheduler configuration
import requests

response = requests.get("http://localhost:8987/api/scheduler/status")
config = response.json()
print(f"Scheduler enabled: {config['enabled']}")
print(f"Interval: {config['interval_minutes']} minutes")
```

### Via Database

```sql
-- View all configurations
SELECT * FROM configurations;

-- Get specific configuration
SELECT config_value 
FROM configurations 
WHERE config_type = 'sync' 
  AND config_key = 'scheduler'
  AND is_active = true;
```

### Via Admin Panel

1. Navigate to Admin Panel (`/admin`)
2. Use the respective sections:
   - Scheduler → For sync scheduling
   - Field Mappings → For field configuration
   - Performance → For tuning settings

## Backup and Restore

### Backup Configuration

```sql
-- Backup all active configurations
COPY (
  SELECT * FROM configurations 
  WHERE is_active = true
) TO '/tmp/config_backup.csv' WITH CSV HEADER;
```

### Restore Configuration

```sql
-- Restore from backup
COPY configurations FROM '/tmp/config_backup.csv' WITH CSV HEADER;
```

## Troubleshooting

### Configuration Not Loading

1. **Check database connection**:
   ```bash
   psql -h localhost -U postgres -d jira_sync -c "SELECT 1;"
   ```

2. **Verify configuration exists**:
   ```sql
   SELECT config_type, config_key, created_at 
   FROM configurations 
   WHERE is_active = true;
   ```

3. **Check application logs**:
   ```bash
   tail -f backend/logs/app.log | grep "config"
   ```

### Reverting to File-Based Config

⚠️ **Not Recommended** - File-based configuration is deprecated.

If absolutely necessary during transition:

1. Set environment variable:
   ```bash
   export USE_FILE_CONFIG=true
   ```

2. Ensure JSON files exist in `/backend/config/`

3. Restart the application

## Benefits of Database Configuration

1. **Centralized Management**: All config in one place
2. **Version History**: Track who changed what and when
3. **No File Permissions**: Eliminates file system permission issues
4. **Atomic Updates**: Configuration changes are transactional
5. **Multi-Instance Support**: Multiple app instances share same config
6. **Backup/Restore**: Easy with database dumps
7. **API Access**: RESTful endpoints for all operations
8. **Audit Trail**: Built-in tracking of changes

## API Reference

### Scheduler Configuration

```http
GET /api/scheduler/status
PUT /api/scheduler/config
POST /api/scheduler/enable
POST /api/scheduler/disable
```

### Field Mappings

```http
GET /api/admin/field-mappings
POST /api/admin/field-mappings
PUT /api/admin/field-mappings/{id}
DELETE /api/admin/field-mappings/{id}
```

### Performance Settings

```http
GET /api/admin/performance
PUT /api/admin/performance
POST /api/admin/performance/reset
```

## Security Notes

- Admin endpoints require `X-Admin-Key` header
- Configuration changes are logged with user information
- Sensitive values (API keys, passwords) should still use environment variables
- Database credentials remain in `.env` file

## FAQ

**Q: Can I still use JSON files for configuration?**
A: No, file-based configuration is deprecated. Use the database or API.

**Q: How do I change settings in production?**
A: Use the Admin Panel UI or make API calls with proper authentication.

**Q: What happens to my old config files?**
A: After migration, they can be deleted or kept as backup. They're no longer used.

**Q: Can I export configuration to JSON?**
A: Yes, use the API to fetch configuration and save as JSON if needed.

**Q: How often is configuration cached?**
A: Configuration is loaded on startup and when explicitly updated via API.