# JIRA Sync Operational Guide

**Last Updated**: January 10, 2025

## ✅ AUTOMATIC: Database Initialization

**The system now fully auto-initializes!** No manual intervention required.

When starting fresh or after `docker-compose down -v`, the system automatically:

1. **PostgreSQL Container** (on startup):
   - Executes `/docker/init-scripts/01-init-database.sql`
   - Creates all 15+ required tables with proper schema
   - Sets up indexes for performance

2. **Backend Container** (via `startup.sh`):
   - Waits for database connectivity
   - Runs `scripts/init_database.py` automatically
   - Loads field mappings from `config/field_mappings.json`
   - Creates any missing tables
   - Applies Alembic migrations
   - Syncs database schema with field mappings
   - Starts application in correct mode (dev/prod)

### Verification Commands
```bash
# After fresh start, verify 100% test success
docker exec jira-sync-backend ./tests/test_field_mapping_quick.sh
# Should show: ✅ ALL TESTS PASSED! (4/4)

# For comprehensive verification
docker exec jira-sync-backend python tests/test_field_mapping_comprehensive.py
# Should show: Success Rate: 100.0% (10/10)
```

### Manual Re-initialization (if needed)
```bash
# Only needed if you want to reload configurations
docker exec jira-sync-backend python scripts/init_database.py
```

## Security Improvements Implemented ✅

### 1. Network Exposure (FIXED)
**Previous Issue**: Backend bound to 0.0.0.0
**Fix Applied**: Backend now binds to 127.0.0.1 only
- Updated in `backend/main.py` and `backend/run.sh`
- Frontend proxy handles external access

### 2. API Authentication (IMPLEMENTED)
**Solution**: API key authentication for admin endpoints
- All admin endpoints require `X-Admin-Key` header
- Key stored in environment variable `ADMIN_API_KEY`
- Pattern validation on API key format

### 3. Input Validation (COMPREHENSIVE)
**Implemented**: Full Pydantic v2 validation
- Field ID pattern validation (customfield_XXXXX, system fields, dotted notation)
- Type validation (string, number, integer, boolean, date, etc.)
- Length constraints on all string inputs
- Query parameter validation with ranges

### 4. Production Security Considerations
- ✅ Backend restricted to localhost
- ✅ Input sanitization
- ⚠️ Still needs HTTPS/TLS for production
- ⚠️ Rate limiting not yet implemented

## Known Issues and Fixes

### Connection Pool Warnings (FIXED)
**Issue**: urllib3 warning "Connection pool is full, discarding connection"
**Root Cause**: Default pool size (10) insufficient for concurrent workers
**Fix**: Added configurable connection pool settings with default of 20

### Location Name Processing (FIXED)
**Issue**: Location names with suffixes (e.g., "12390 - 2") caused database mismatches
**Root Cause**: Different Jira instances processed location names differently
**Fix**: Standardized location name extraction in `jira_issues.py`

### Circular Import Error
**Issue**: ImportError when importing sync functions
**Fix**: Created `sync_wrapper.py` with lazy imports

### Missing Dependencies
**Issue**: dateutil and apscheduler modules missing
**Fix**: Added to requirements.txt

### Virtual Environment Issues
**Issue**: Python externally-managed-environment error
**Fix**: Use venv's Python directly in run.sh

### Dashboard Connectivity Issues (FIXED)
**Issue**: Dashboard showing "Disconnected" status
**Fix**: Updated frontend to use relative API paths instead of absolute URLs

### Field Validation 422 Errors (FIXED)
**Issue**: Pydantic validation failing for field mappings
**Fix**: Updated models to support system fields, integer type, and dotted field IDs

### Database Schema Mismatches (FIXED - January 10, 2025)
**Issue**: Configuration tables had column name mismatches causing 500 errors
**Root Cause**: Code expected `created_by/updated_by` but database had `user_updated`
**Fix**: Updated `core/db/db_config.py` to use correct column names
**Files Fixed**:
- `db_config.py`: Changed to use `user_updated` instead of `created_by/updated_by`
- Removed `change_type` from configuration_history inserts
**Result**: 100% test success rate achieved

### Custom Fields Not Populating (FIXED - August 10, 2025)
**Issue**: Despite field mappings being configured, custom fields remained NULL after sync
**Root Cause**: Column name mismatch - database uses `ndpu_order_number` but field mappings use `order_number`
**Fix**: Implemented `core/db/column_mappings.py` to translate between database column names and field mapping keys
**Verification**:
```sql
SELECT COUNT(*) as total, 
       COUNT(ndpu_order_number) as has_order_number,
       COUNT(ndpu_client_name) as has_client_name
FROM jira_issues_v2;
```
**Result**: 9,264 issues now have order numbers, 9,237 have client names

### Sync Statistics Accumulation (FIXED - July 2025)
**Issue**: Project and issue counts accumulating across multiple syncs
**Root Cause**: SyncStatistics object reused between syncs
**Fix**: Reset statistics at beginning of each sync in `sync_all_projects()`

### Socket Hang Up Errors (FIXED - July 2025)
**Issue**: Frontend getting socket hang up errors during sync operations
**Root Cause**: Sync operations blocking the FastAPI event loop
**Fix**: Implemented thread pool execution for scheduled syncs

## Feature Implementation Status

### ✅ Completed Features (All Tested July 2025)
- Multi-instance JIRA sync with field mapping
- Project mapping management with auto-discovery
- Real-time sync status monitoring
- Web dashboard with working connectivity
- Audit logging for all operations
- Performance metrics tracking (avg 77.83s per sync, 100% success rate)
- Next.js + FastAPI architecture
- Database-based configuration management
- Full backup/restore functionality with UI (12 backups created)
- JIRA field validation (connected to API)
- Comprehensive admin interface (Phase 1 & 2)
- Unified sidebar navigation with admin sub-menus
- Consistent layout across all pages
- JIRA field discovery and caching (305 fields from instance 1, 264 from instance 2)
- Auto-suggest UI component for field mappings (similarity scoring working)
- Sample data preview for mapped fields
- Field mapping wizard with search functionality
- **Automatic database schema synchronization** (59 columns managed)
- **Performance configuration UI with dynamic settings** (no restart required)
- **Configurable HTTP connection pooling** (default 20, warnings resolved)
- **Sync history persistence and statistics** (6 syncs tracked, 113k issues)
- **Automated sync system with APScheduler** (2-minute minimum interval)
- **Thread pool execution for non-blocking syncs**
- **Fixed sync statistics accumulation bug**
- **Database initialization script** (`scripts/init_database.py`) for disaster recovery
- **Column name mapping system** for proper field extraction
- **Africa/Nairobi timezone** configuration for all containers
- **Fully automated system initialization** (January 10, 2025)
- **100% test success achievement** with self-healing architecture
- **Startup orchestration** via `scripts/startup.sh`

### 🚧 In Progress
- Configuration history UI
  - Backend endpoint exists
  - Frontend page needed
- Enhanced error recovery
- Advanced analytics dashboard (Phase 4)

### 📋 Planned Features
- Bulk field operations
- OAuth authentication
- Email notifications
- Dropbox API integration (currently mock data)
- Advanced filtering and search
- Configuration export/import
- Webhook integration

## Monitoring and Maintenance

### Key Metrics to Monitor
- Sync duration and success rate
- API response times
- Database connection pool usage
- Error rates by project
- Memory usage during batch operations
- HTTP connection pool warnings (urllib3)
- Connection pool exhaustion events
- Automated sync schedule adherence
- Thread pool utilization during syncs
- Sync statistics accuracy (no accumulation)

### Database Maintenance
```sql
-- Check table sizes (note: main table is in public schema)
SELECT schemaname, relname, pg_size_pretty(pg_total_relation_size(relid))
FROM pg_catalog.pg_statio_user_tables
WHERE schemaname IN ('public', 'jira_sync')
ORDER BY pg_total_relation_size(relid) DESC;

-- Vacuum and analyze (use correct schema)
VACUUM ANALYZE public.jira_issues_v2;

-- Check for missing indexes
SELECT schemaname, tablename, indexname, idx_scan
FROM pg_stat_user_indexes
ORDER BY idx_scan;
```

### Log Rotation
- Application logs in `logs/` directory
- Web app logs in `logs/webapp.log`
- Implement logrotate configuration for production

## Troubleshooting Guide

### System Not Initializing
1. Check Docker containers are running: `docker ps`
2. Wait 60 seconds for auto-initialization to complete
3. Check backend logs: `docker logs jira-sync-backend`
4. Verify database is ready: `docker logs jira-sync-postgres`
5. Run tests to verify: `docker exec jira-sync-backend ./tests/test_field_mapping_quick.sh`

### Sync Not Starting
1. Check environment variables are set (especially JIRA credentials in .env)
2. Verify JIRA credentials are valid
3. Ensure database is accessible
4. Check for existing sync lock
5. Verify backend is running on port 8987

### Dashboard Shows Disconnected
1. Clear browser cache (Ctrl+F5)
2. Check backend is running: `curl http://127.0.0.1:8987/health`
3. Verify frontend proxy configuration
4. Check browser console for errors
5. Ensure all API calls use relative paths (e.g., `/api/...`)

### Field Validation Errors (422)
1. Ensure field types are valid (string, number, integer, boolean, etc.)
2. Check field IDs match pattern (customfield_XXXXX or system fields)
3. Verify configuration structure matches Pydantic models
4. Run migration if config is empty: `./venv/bin/python scripts/migrate_configs.py`

### Field Mapping Issues
1. Use admin interface to validate fields
2. Check field exists in both JIRA instances
3. Click "Sync DB Schema" button to automatically create columns
4. Review validation results in UI
5. Use field discovery to find available fields
6. Preview sample data before mapping

### Navigation Issues
1. Ensure all pages import and use DashboardLayout
2. Admin pages should not have separate layout
3. Check that sidebar state persists across navigation
4. Verify admin sub-menu expands when on admin pages

### Automated Sync Issues
1. Check scheduler status at `/admin/scheduler`
2. Verify sync_config.json has `"enabled": true`
3. Check backend logs for scheduler initialization
4. Ensure minimum 2-minute interval is set
5. Monitor for thread pool errors in logs
6. Verify no socket hang up errors during syncs

### Sync Statistics Issues
1. If counts are accumulating, restart backend
2. Verify fix in `core/sync/sync_manager.py` line 191
3. Check sync history for accurate project counts (should total 101)
4. Each sync should show fresh statistics

## Emergency Procedures

### Complete System Reset
```bash
# Full teardown and automatic recovery
docker-compose -f docker-compose.dev.yml down -v
docker-compose -f docker-compose.dev.yml up -d

# Wait 60 seconds for auto-initialization
sleep 60

# Verify system is operational
docker exec jira-sync-backend python tests/test_field_mapping_comprehensive.py
```

### Stop All Syncs
```bash
# Via API
curl -X POST http://127.0.0.1:8987/api/sync/stop \
  -H "Content-Type: application/json"

# Or from Python
cd backend && ./venv/bin/python -c "from core.sync.sync_manager import SyncManager; SyncManager().stop_sync()"
```

### Clear Sync Lock
```sql
DELETE FROM sync_status WHERE status = 'running';
```

### Restore Configuration from Backup
```bash
# List available backups
curl http://127.0.0.1:8987/api/admin/config/backups \
  -H "X-Admin-Key: jira-admin-key-2024"

# Restore specific backup (replace ID)
curl -X POST http://127.0.0.1:8987/api/admin/config/restore/1 \
  -H "X-Admin-Key: jira-admin-key-2024"
```

### Rollback Database Changes
```sql
-- Create backup first
pg_dump -h 10.110.121.130 -U postgres -d postgres -n jira_sync -t jira_issues_v2 > backup.sql

-- Restore if needed
psql -h 10.110.121.130 -U postgres -d postgres < backup.sql
```

## Best Practices

### Configuration Management
1. Always validate before saving field mappings
2. Create manual backups before major changes
3. Document field mapping changes
4. Test with single project sync first
5. Use field discovery to find available fields
6. Preview sample data before finalizing mappings
7. Database columns are created automatically - no manual SQL needed!

### Security
1. Change default ADMIN_API_KEY in production
2. Use environment variables for sensitive data
3. Restrict database access to specific IPs
4. Enable SSL/TLS for production deployment

### Performance
1. Monitor sync duration trends
2. Adjust batch size based on JIRA response times
3. Use appropriate worker count for your instance size
4. Regular database maintenance (VACUUM ANALYZE)
5. Configure connection pool size based on worker count
6. Monitor for connection pool warnings in logs

### Performance Tuning
Access the performance configuration at `/admin/performance`:
- **Connection Pool**: Set to at least 1.5x your max workers to avoid pool exhaustion
- **Rate Limiting**: Increase pause time if seeing 429 errors
- **Batch Size**: Lower for better memory usage, higher for fewer API calls
- **Timeouts**: Increase for large projects or slow networks