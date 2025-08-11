# Database Initialization Checklist

## ✅ Complete Database Initialization Verification

This checklist ensures that ALL database components are properly created when starting from scratch.

## Tables (16 Required)

### Core Application Tables
- [ ] **jira_issues_v2** - Main issues storage
  - issue_key (PRIMARY KEY)
  - summary, status, project_name, location_name
  - All ndpu_* fields (order_number, client_name, listing_address, etc.)
  - All timestamp fields (scheduled, acknowledged, at_listing, etc.)
  - last_updated

- [ ] **project_mappings_v2** - Project to location mappings
  - id, project_key (UNIQUE), location_name
  - is_active, auto_discovered, approved
  - created_at, updated_at, created_by, approved_by
  - metadata (JSONB)

- [ ] **mapping_audit_log_v2** - Audit trail for mapping changes
  - id, project_key, action
  - old_value, new_value (JSONB)
  - performed_by, performed_at

### Sync Management Tables
- [ ] **sync_history** - Main sync run tracking
  - sync_id (UNIQUE), start_time, end_time
  - status, total_issues, issues_created, issues_updated, issues_failed
  - error_message, sync_type, triggered_by
  - duration_seconds, created_at

- [ ] **sync_project_details** - Per-project sync details
  - sync_id (FK), project_key, project_name
  - issues_synced, issues_created, issues_updated, issues_failed
  - sync_time, instance, start_time, end_time
  - duration_seconds, status, issues_processed
  - error_message, retry_count

- [ ] **sync_history_details** - Issue-level sync details
  - sync_id (FK), issue_key
  - action, status, error_message, timestamp

### Configuration Tables
- [ ] **configurations** - Dynamic configuration storage
  - config_type, config_key, config_value (JSONB)
  - version, is_active, user_updated, reason
  - created_at, updated_at
  - UNIQUE(config_type, config_key, version)

- [ ] **configuration_history** - Configuration change tracking
  - config_id, config_type, config_key
  - old_value, new_value (JSONB)
  - changed_by, change_reason, changed_at

- [ ] **configuration_backups** - Configuration backup storage
  - backup_name, backup_type, backup_data (JSONB)
  - created_at, created_by, description

- [ ] **sync_config** - Legacy sync configuration
  - config_key (UNIQUE), config_value
  - config_type, description
  - created_at, updated_at

### Field Management Tables
- [ ] **jira_field_cache** - JIRA field metadata cache
  - instance_type, field_id (UNIQUE together)
  - field_name, field_type, schema_type
  - custom, navigable, searchable
  - clauseNames, auto_complete_url, last_updated

- [ ] **field_mappings** - Field mapping configuration
  - jira_field_id, jira_field_name
  - db_column_name, field_type
  - is_custom, is_active, instance
  - created_at, updated_at
  - UNIQUE(jira_field_id, instance)

- [ ] **field_cache** - General field value cache
  - cache_key (UNIQUE), cache_value (JSONB)
  - expires_at, created_at, updated_at

### Audit & Logging Tables
- [ ] **audit_log** - General audit logging
  - timestamp, user_id, action
  - resource_type, resource_id
  - details (JSONB), ip_address, user_agent

- [ ] **update_log_v2** - Project update tracking
  - project_name, status, issues_count
  - error_message, timestamp
  - duration, records_processed, last_update_time

- [ ] **operation_log_v2** - Operation logging
  - operation_type, entity_type, entity_id
  - performed_by, performed_at
  - details (JSONB), status, duration, error_message

## Indexes (40+ Required)

### Performance-Critical Indexes
- [ ] idx_jira_issues_v2_location_name
- [ ] idx_jira_issues_v2_project
- [ ] idx_jira_issues_v2_status
- [ ] idx_jira_issues_v2_last_updated
- [ ] idx_jira_issues_v2_summary
- [ ] idx_jira_issues_v2_order_number
- [ ] idx_jira_issues_v2_listing_address

### All Other Required Indexes
- [ ] All sync_history indexes
- [ ] All sync_project_details indexes
- [ ] All configuration table indexes
- [ ] All field cache indexes
- [ ] All audit/log table indexes

## Default Configurations

### Performance Configuration (sync.performance)
```json
{
  "max_workers": 14,
  "project_timeout": 300,
  "batch_size": 500,
  "lookback_days": 50,
  "max_retries": 3,
  "backoff_factor": 0.1,
  "rate_limit_pause": 0.1,
  "connection_pool_size": 20,
  "connection_pool_block": false
}
```

### Scheduler Configuration (sync.scheduler)
```json
{
  "enabled": true,
  "interval_minutes": 2
}
```

### Sync Settings (sync.settings)
```json
{
  "enabled": true,
  "lookback_days": 50,
  "batch_size": 500,
  "max_workers": 14,
  "rate_limit_pause": 0.1,
  "sync_interval_minutes": 2
}
```

### Sync Config Table Values
- sync_enabled: true
- sync_interval_minutes: 2
- batch_size: 500
- max_retries: 3
- timeout_seconds: 300
- max_workers: 14
- rate_limit_pause: 0.1
- lookback_days: 50

## Field Mappings
- [ ] Loaded from `config/field_mappings.json`
- [ ] Stored in configurations table
- [ ] Database columns created for all mapped fields

## Initialization Scripts

### Primary Script: `init_database_complete.py`
- Creates ALL tables with ALL columns
- Creates ALL indexes
- Loads ALL default configurations
- Verifies everything is ready

### Fallback Script: `init_database.py`
- Basic initialization
- Used if comprehensive script fails

### Startup Script: `startup.sh`
- Waits for database readiness
- Runs comprehensive initialization
- Falls back to basic if needed
- Applies Alembic migrations
- Starts application

### Docker SQL Init: `01-init-database.sql`
- Creates core tables on PostgreSQL container start
- Runs automatically on first container creation

## Verification Commands

### Check All Tables Exist
```bash
docker exec jira-sync-postgres psql -U postgres -d jira_sync -c "\dt" | wc -l
# Should show 18+ lines (16 tables + headers)
```

### Verify Configurations
```bash
docker exec jira-sync-postgres psql -U postgres -d jira_sync -c "SELECT config_type, config_key FROM configurations WHERE is_active = true;"
# Should show:
# - jira | field_mappings
# - sync | performance
# - sync | scheduler
# - sync | settings
```

### Test Comprehensive Script
```bash
docker exec jira-sync-backend python scripts/init_database_complete.py
# Should show all green checkmarks
```

### Run Field Mapping Tests
```bash
docker exec jira-sync-backend ./tests/test_field_mapping_quick.sh
# Should show: ✅ ALL TESTS PASSED! (4/4)

docker exec jira-sync-backend python tests/test_field_mapping_comprehensive.py
# Should show: Success Rate: 100.0% (10/10)
```

## Complete Teardown and Rebuild Test

```bash
# 1. Complete teardown
docker-compose -f docker-compose.dev.yml down -v

# 2. Rebuild from scratch
docker-compose -f docker-compose.dev.yml up -d

# 3. Wait for initialization (60 seconds)
sleep 60

# 4. Verify all tests pass
docker exec jira-sync-backend python tests/test_field_mapping_comprehensive.py

# 5. Check sync works
curl -X POST http://localhost:8987/api/sync/start -H "Content-Type: application/json" -d '{"force": false}'
```

## Success Criteria

✅ **System is ready when:**
1. All 16 tables exist with correct columns
2. All 40+ indexes are created
3. All default configurations are loaded
4. Field mappings are loaded from JSON
5. All tests pass with 100% success rate
6. Sync can run successfully
7. Dashboard shows stats correctly
8. System recovers from complete teardown automatically

## Troubleshooting

If initialization fails:
1. Check Docker logs: `docker-compose logs backend`
2. Verify database connection: `docker exec jira-sync-backend python -c "from core.database import check_db_connection; print(check_db_connection())"`
3. Run comprehensive script manually: `docker exec jira-sync-backend python scripts/init_database_complete.py`
4. Check for missing tables: `docker exec jira-sync-postgres psql -U postgres -d jira_sync -c "\dt"`
5. Verify configurations: `docker exec jira-sync-postgres psql -U postgres -d jira_sync -c "SELECT * FROM configurations;"`

---

**Important**: This system is designed to be completely self-healing. After `docker-compose down -v`, running `docker-compose up -d` should restore everything automatically within 60 seconds.