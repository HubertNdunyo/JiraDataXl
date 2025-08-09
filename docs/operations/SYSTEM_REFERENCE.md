# JIRA Sync System Reference

**Last Updated**: July 2025

## Environment Configuration
```bash
# Required environment variables
JIRA_ACCESS_TOKEN="[YOUR_TOKEN]"
JIRA_EMAIL="jmwangi@inuaai.net"
JIRA_INSTANCE_1="https://betteredits.atlassian.net/"  # 24 projects
JIRA_INSTANCE_2="https://betteredits2.atlassian.net/"  # 77 projects
DATABASE_URL="postgresql://postgres:[PASSWORD]@10.110.121.130:5432/postgres?sslmode=prefer&application_name=jira_sync"
DB_SCHEMA="jira_sync"

# Admin interface
ADMIN_API_KEY="jira-admin-key-2024"

# Legacy compatibility (optional)
JIRA_USERNAME_1="jmwangi@inuaai.net"
JIRA_PASSWORD_1="[YOUR_TOKEN]"
JIRA_USERNAME_2="jmwangi@inuaai.net"
JIRA_PASSWORD_2="[YOUR_TOKEN]"
```

## Database Schema

**Important Note**: The main issues table is located in the `public` schema, not `jira_sync` as some documentation suggests.

```sql
-- Main issue table (in public schema)
CREATE TABLE public.jira_issues_v2 (
    issue_key VARCHAR(255) PRIMARY KEY,
    summary TEXT,
    status VARCHAR(255),
    ndpu_order_number VARCHAR(255),
    ndpu_raw_photos INTEGER,
    dropbox_raw_link TEXT,
    dropbox_edited_link TEXT,
    same_day_delivery BOOLEAN,
    escalated_editing BOOLEAN,
    edited_media_revision_notes TEXT,
    ndpu_editing_team VARCHAR(255),
    scheduled TIMESTAMP,
    acknowledged TIMESTAMP,
    at_listing TIMESTAMP,
    shoot_complete TIMESTAMP,
    uploaded TIMESTAMP,
    edit_start TIMESTAMP,
    final_review TIMESTAMP,
    closed TIMESTAMP,
    ndpu_service VARCHAR(255),
    project_name TEXT,
    location_name TEXT,
    ndpu_client_name TEXT,
    ndpu_client_email TEXT,
    ndpu_listing_address TEXT,
    ndpu_comments TEXT,
    ndpu_editor_notes TEXT,
    ndpu_access_instructions TEXT,
    ndpu_special_instructions TEXT,
    last_updated TIMESTAMP DEFAULT now()
);

-- Project mappings
CREATE TABLE project_mappings_v2 (
    id SERIAL PRIMARY KEY,
    project_key VARCHAR(255) NOT NULL UNIQUE,
    location_name TEXT NOT NULL,
    is_active BOOLEAN DEFAULT true,
    auto_discovered BOOLEAN DEFAULT false,
    approved BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(255),
    approved_by VARCHAR(255),
    metadata JSONB
);

-- Indexes (in public schema)
CREATE INDEX idx_jira_issues_v2_location_name ON public.jira_issues_v2(location_name);
CREATE INDEX idx_jira_issues_v2_status ON public.jira_issues_v2(status);
CREATE INDEX ix_jira_issues_v2_project_name ON public.jira_issues_v2(project_name);
CREATE INDEX idx_project_mappings_v2_active ON project_mappings_v2(is_active);

-- Configuration tables (NEW)
CREATE TABLE configurations (
    id SERIAL PRIMARY KEY,
    config_type VARCHAR(50) NOT NULL,
    config_key VARCHAR(100) NOT NULL,
    config_value JSONB NOT NULL,
    version INTEGER DEFAULT 1,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(255),
    updated_by VARCHAR(255),
    UNIQUE(config_type, config_key, version)
);

CREATE TABLE configuration_history (
    id SERIAL PRIMARY KEY,
    config_id INTEGER REFERENCES configurations(id),
    config_type VARCHAR(50) NOT NULL,
    config_key VARCHAR(100) NOT NULL,
    old_value JSONB,
    new_value JSONB NOT NULL,
    change_type VARCHAR(20) NOT NULL, -- 'create', 'update', 'delete'
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    changed_by VARCHAR(255),
    change_reason TEXT
);

CREATE TABLE configuration_backups (
    id SERIAL PRIMARY KEY,
    backup_name VARCHAR(255) NOT NULL,
    backup_type VARCHAR(50) NOT NULL, -- 'manual', 'auto', 'pre_update'
    backup_data JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(255),
    description TEXT
);

-- JIRA field cache (NEW)
CREATE TABLE jira_sync.jira_field_cache (
    id SERIAL PRIMARY KEY,
    instance VARCHAR(50) NOT NULL,
    field_id VARCHAR(255) NOT NULL,
    field_name VARCHAR(255) NOT NULL,
    field_type VARCHAR(100),
    is_custom BOOLEAN DEFAULT false,
    is_array BOOLEAN DEFAULT false,
    schema_info JSONB,
    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(instance, field_id)
);

-- Indexes for field cache
CREATE INDEX idx_field_cache_instance ON jira_field_cache(instance);
CREATE INDEX idx_field_cache_field_name ON jira_field_cache(field_name);
CREATE INDEX idx_field_cache_field_id ON jira_field_cache(field_id);
```

## Field Mappings Configuration
**Note**: Configuration is now stored in the database. The JSON files in `config/` are reference only.

### Automatic Database Schema Synchronization (NEW)
The system now automatically creates database columns when fields are added through the UI:
- **Auto-sync on Save**: When field mappings are saved, columns are automatically created
- **Manual Sync**: Click "Sync DB Schema" button in the admin interface
- **Type Mapping**: Automatic conversion from field types to PostgreSQL data types
- **Safety**: Only adds columns, never removes or modifies existing ones

Key mappings between instances:

| Field | Instance 1 | Instance 2 | Database Column |
|-------|------------|------------|-----------------|
| Order Number | customfield_10501 | customfield_10501 | ndpu_order_number |
| Raw Photos | customfield_12581 | customfield_12602 | ndpu_raw_photos |
| Editing Team | customfield_12644 | customfield_12648 | ndpu_editing_team |
| Service | customfield_10509 | customfield_10509 | ndpu_service |
| Client Name | customfield_10514 | customfield_10514 | ndpu_client_name |
| Client Email | customfield_10515 | customfield_10515 | ndpu_client_email |
| Access Instructions | customfield_12594 | customfield_12611 | ndpu_access_instructions |
| Special Instructions | customfield_12595 | customfield_12612 | ndpu_special_instructions |

## Adding New Fields (Simplified Process with Auto-Sync)

### Quick Steps
1. **Discover Fields**: Click "Discover Fields" button in admin interface
   - Automatically caches all fields from both JIRA instances
   - Shows statistics: custom vs system fields
   - Updates the `jira_field_cache` table

2. **Use Field Mapping Wizard**: 
   - Click "Setup Wizard" button
   - Select fields from discovered list
   - Search for specific fields
   - Map to both instances

3. **Save Configuration**: 
   - Review mappings
   - Click "Complete Setup"
   - Database columns are **automatically created**
   - No manual SQL required!

4. **Alternative: Manual Addition**:
   - Click "Edit Mode" in field mappings
   - Add field with auto-suggest support
   - Validate and save
   - Columns created automatically

5. **Update Backend Code** (if needed): 
   - Add to `ISSUE_COLUMNS` in constants.py
   - Update `process_issue` method
   - Include in sync operations

6. **Test**: 
   - Run single project sync
   - Verify data population
   - Check database for new columns

### Field Discovery Features
- **Auto-discovery**: Fetches all fields from JIRA REST API
- **Caching**: Stores field metadata for quick access
- **Search**: Find fields by name or ID
- **Suggestions**: Get smart mapping recommendations
- **Validation**: Real-time field existence checking

### Detailed Guide
See `/docs/ADDING_NEW_FIELDS_GUIDE.md` for comprehensive instructions including:
- Field type mapping reference
- SQL examples for each data type
- Code update templates
- Troubleshooting guide
- Best practices

**Note**: The configuration is now database-driven with field discovery support.

## Project Structure
```
jiraData/
├── backend/
│   ├── main.py                 # FastAPI entry point (port 8987)
│   ├── core/
│   │   ├── config/            # Configuration management
│   │   ├── db/                # Database operations
│   │   ├── jira/              # JIRA API integration
│   │   └── sync/              # Sync coordination
│   └── run.sh                 # Startup script
├── frontend/                   # Next.js app (port 5648)
│   └── app/
│       ├── dashboard-layout.tsx  # Unified sidebar navigation
│       ├── page.tsx             # Main dashboard
│       ├── history/             # Sync history page
│       ├── settings/            # Settings page
│       └── admin/               # Admin pages (all use DashboardLayout)
├── config/
│   └── field_mappings.json    # Field mapping configuration (reference only)
└── logs/                      # Application logs
```

## Frontend Architecture

### Navigation System
- **Unified Sidebar**: All pages use `dashboard-layout.tsx` component
- **Admin Sub-menus**: Collapsible admin section with nested navigation
- **Consistent Layout**: Every page wrapped with DashboardLayout for consistency
- **Relative API Paths**: All frontend API calls use relative paths (e.g., `/api/...`)

### Key Frontend Routes
- `/` - Main dashboard with system status
- `/history` - Sync history and logs
- `/settings` - General settings
- `/admin` - Admin overview
- `/admin/field-mappings` - Field mapping configuration with:
  - Field discovery button
  - Search functionality
  - Edit mode with validation
  - Visual and JSON views
- `/admin/sync-config` - Sync interval settings
- `/admin/backups` - Backup management
- `/admin/performance` - Performance configuration with:
  - Interactive sliders for all settings
  - Real-time configuration testing
  - Impact estimation warnings
  - Connection pool management

### UI Components
- **Field Discovery Stats**: Shows discovered fields count
- **Field Search**: Real-time search with auto-complete
- **Edit Dialog**: Modal for field property editing
- **Validation Feedback**: Inline error messages
- **Toast Notifications**: Success/error feedback

### Planned UI Features
- **Auto-Suggest Component**: Dropdown with field suggestions
- **Sample Data Preview**: Modal showing actual JIRA data
- **Field Mapping Wizard**: Step-by-step guided setup
- **Drag-and-Drop Mapper**: Visual field mapping interface

## API Endpoints

### Sync Operations
- `GET /api/sync/status` - Current sync status
- `POST /api/sync/start` - Start sync process
- `POST /api/sync/stop` - Stop sync process
- `GET /api/sync/history` - Sync history

### Admin Operations (Requires X-Admin-Key header)

#### Configuration Management
- `GET /api/admin/config/field-mappings` - Get field mappings
- `PUT /api/admin/config/field-mappings` - Update field mappings
- `POST /api/admin/config/field-mappings/validate` - Validate full config
- `POST /api/admin/config/field-mappings/validate-field` - Validate single field
- `GET /api/admin/config/sync` - Get sync configuration
- `PUT /api/admin/config/sync` - Update sync settings
- `GET /api/admin/config/performance` - Get performance configuration
- `PUT /api/admin/config/performance` - Update performance settings
- `POST /api/admin/config/performance/test` - Test performance configuration

#### Backup and Restore
- `GET /api/admin/config/backups` - List backups
- `POST /api/admin/config/backups` - Create manual backup
- `POST /api/admin/config/restore/{id}` - Restore from backup

#### Field Discovery (NEW)
- `POST /api/admin/fields/discover` - Discover and cache JIRA fields
- `GET /api/admin/fields/cached?instance=1` - Get cached fields
- `GET /api/admin/fields/search?term=invoice&instance=2` - Search fields
- `POST /api/admin/fields/suggest` - Get field mapping suggestions
- `POST /api/admin/fields/preview` - Preview sample field data

#### Database Schema Management (NEW)
- `POST /api/admin/schema/sync` - Sync database schema with field mappings
- `GET /api/admin/schema/columns` - Get list of database columns

#### Automated Sync Management (NEW - July 2025)
- `GET /api/scheduler/status` - Get scheduler status and next run time
- `PUT /api/scheduler/config` - Update scheduler configuration
- `POST /api/scheduler/enable` - Enable automated syncs
- `POST /api/scheduler/disable` - Disable automated syncs

#### Planned Endpoints
- `GET /api/admin/config/history` - Configuration history (backend ready)
- `POST /api/admin/config/export` - Export configuration (not implemented)
- `POST /api/admin/config/import` - Import configuration (not implemented)

### System Status
- `GET /api/status/system` - System health and connectivity
- `GET /api/stats` - System statistics
- `GET /health` - Health check endpoint

## Performance Metrics (Verified July 2025)
- Sync Speed: 265-315 issues/second (actual measured)
- Batch Size: 400 issues/request (current setting)
- Workers: 10 concurrent threads (current setting)
- Full Sync: ~30-35 seconds for 8,000-41,000 issues
- Connection Pool: 20 connections (no warnings)
- Success Rate: 100% (268 syncs tracked)
- Total Issues Synced: 833,783 in last 7 days
- Automated Sync: Every 2 minutes (APScheduler)
- Thread Pool: Prevents socket hang up errors

### Performance Configuration
Performance settings can be configured through the admin interface at `/admin/performance`:
- **Max Workers**: 1-16 concurrent threads
- **Project Timeout**: 60-1800 seconds
- **Batch Size**: 50-1000 issues per request
- **Lookback Days**: 1-365 days of history
- **Rate Limit Pause**: 0-10 seconds between requests
- **Connection Pool Size**: 5-50 connections
- **Connection Pool Block**: Whether to block when pool exhausted

## Quick Commands
```bash
# Start backend (listens on 127.0.0.1:8987)
cd backend && ./run.sh

# Start frontend (listens on 0.0.0.0:5648)
cd frontend && ./run.sh

# Run configuration migration
cd backend && ./venv/bin/python scripts/migrate_configs.py

# Test admin API
curl -X GET http://localhost:8987/api/admin/test \
  -H "X-Admin-Key: jira-admin-key-2024"

# Full sync (from backend directory)
./venv/bin/python main.py

# Test single issue
./venv/bin/python utils/scripts/test_single_issue.py
```

## Security Notes
- Backend binds to 127.0.0.1 only (not accessible externally)
- Frontend can be accessed externally (0.0.0.0:5648)
- Admin API requires X-Admin-Key header
- All inputs validated with Pydantic v2
- Automatic backups before configuration changes
- Field validation against actual JIRA instances
- Database-driven configuration with version control
- Configuration history tracking for audit trail

## Latest Technical Details

### Field Discovery Process
1. **API Call**: POST to `/api/admin/fields/discover`
2. **JIRA Integration**: Fetches fields from `/rest/api/3/field`
3. **Data Processing**: Extracts field metadata and schema
4. **Database Storage**: Upserts into `jira_field_cache`
5. **Statistics**: Returns count of discovered fields

### Field Validation Flow
1. **Check Cache**: Look up field in `jira_field_cache`
2. **Validate Type**: Ensure field type matches configuration
3. **Nested Fields**: Special handling for dotted notation
4. **Error Reporting**: Detailed messages for each field

### Configuration Storage
- **Version Control**: Auto-incrementing version numbers
- **Active Flag**: Only one active version at a time
- **History Tracking**: All changes logged with user and timestamp
- **Backup Strategy**: Automatic pre-update backups
- **Rollback Support**: Easy restoration from any backup

## Database Structure (As Discovered July 2025)

### Actual Table Locations
The database has tables in two schemas:

**Public Schema** (main data):
- `public.jira_issues_v2` - 50,291 issues (main sync target)
- `public.jiradata` - 11,713 rows (legacy/different structure)
- `public.jira_raw_data` - 0 rows (deprecated)
- `public.project_mappings_v2` - Project to location mappings

**jira_sync Schema** (metadata):
- `jira_sync.sync_runs` - 294 sync operations
- `jira_sync.sync_project_details` - 28,129 project sync records
- `jira_sync.sync_performance_metrics` - 874 performance metrics
- `jira_sync.jira_field_cache` - 569 field definitions
- `jira_sync.configurations` - System configurations
- `jira_sync.configuration_history` - Change tracking
- `jira_sync.configuration_backups` - Backup storage

**Note**: Despite some code references to `jira_sync.jira_issues_v2`, the actual issues table is in the `public` schema.

## Recent Bug Fixes (July 2025)

### Statistics Accumulation Bug
- **Issue**: Project and issue counts were accumulating across syncs
- **Fix**: Reset SyncStatistics object at start of each sync
- **Location**: `core/sync/sync_manager.py` line 191
- **Result**: Accurate project counts (e.g., 47/101 instead of 235/505)

### Socket Hang Up Errors
- **Issue**: Frontend disconnections during sync operations
- **Fix**: Implemented thread pool for scheduled syncs
- **Location**: `core/scheduler.py` - ThreadPoolExecutor
- **Result**: API remains responsive during syncs

### Sync Stats Summary
- **Issue**: Only analyzing first 100 of 268 syncs
- **Fix**: Increased limit from 100 to 1000 in API endpoint
- **Location**: `api/sync_routes.py` line 165
- **Result**: Accurate success rate calculations