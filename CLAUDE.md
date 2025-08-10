# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

JIRA Sync Dashboard - A high-performance web application for synchronizing data between multiple JIRA instances with field mapping capabilities. The system achieves 500 issues/second throughput, syncing 45,000+ issues across 97 projects in ~90 seconds.

## Common Development Commands

### Frontend (Next.js 14)
```bash
cd frontend
npm install              # Install dependencies
npm run dev              # Start dev server on port 5648 (hot-reload)
npm run build            # Build for production
npm run lint             # Run ESLint checks
```

### Backend (FastAPI)
```bash
cd backend
./run.sh                 # Start FastAPI on port 8987 (includes venv setup)
python -m pytest tests/  # Run tests (requires pytest installation)
alembic upgrade head     # Apply database migrations
alembic revision --autogenerate -m "description"  # Create new migration
alembic stamp head       # Mark current schema as up to date
```

### Docker Development
```bash
docker-compose -f docker-compose.dev.yml up     # Start all services with hot-reload
docker-compose -f docker-compose.prod.yml up -d # Production deployment
docker-compose logs [service]                   # View service logs
docker-compose down                            # Stop all services
```

### Testing
```bash
# Backend tests use pytest
cd backend
pip install pytest  # If not installed
python -m pytest tests/ -v

# Run specific test
python -m pytest tests/test_sync_statistics_counts.py

# Frontend has no test setup yet - would need Jest/Vitest configuration
```

## Architecture Overview

### Backend Structure
The backend follows a modular architecture with clear separation:

- **API Layer** (`api/`) - FastAPI routes handling HTTP requests
  - `admin_routes_v2.py` (1,160 lines) - Admin operations, field mapping
  - `sync_routes.py` - Sync control endpoints
  - `config_routes.py`, `status_routes.py`, `scheduler_routes.py`

- **Core Business Logic** (`core/`)
  - `sync/` - Synchronization engine processing JIRA data
  - `jira/` - JIRA API client and field processor
  - `db/` - Database operations with repository pattern
  - `cache/` - Redis caching layer

- **Database** - PostgreSQL with Alembic migrations
  - Dynamic field mapping stored in DB
  - Sync history and audit logs
  - Project and issue storage

### Frontend Structure
Next.js 14 app with TypeScript and Tailwind CSS:

- **App Router** (`app/`) - Page components and routing
  - `/admin/*` - Admin pages with server-side authentication
  - `/api/admin/*` - Server-side proxy for admin API calls
  
- **Components** (`components/`) - Reusable UI components using shadcn/ui
- **Libraries** (`lib/`) - API client, session management, utilities

### Key Technical Details

1. **Authentication**: Admin panel uses server-side session authentication with HTTP-only cookies. Admin API key stored only in environment variables.

2. **Field Mapping**: Dynamic field discovery from JIRA instances (530+ fields). Mappings stored in PostgreSQL, not hardcoded.

3. **Performance**: Redis caching with 20x speed improvement. Processes 272 issues/second.

4. **Configuration**: All config in PostgreSQL database. Supports unlimited JIRA instances via JSON configuration.

5. **Security**: No API keys in frontend code. All admin requests proxied through server-side routes with session validation.

## Environment Setup

Required environment variables:

```bash
# Backend (.env)
ADMIN_API_KEY=secure-key-here  # Required for admin access
DB_NAME=jira_sync
DB_USER=postgres
DB_PASSWORD=password
DB_HOST=localhost  # Use 'postgres' for Docker
REDIS_HOST=localhost  # Use 'redis' for Docker

# Frontend (.env.local)
BACKEND_URL=http://backend:8987  # For Docker internal
ADMIN_API_KEY=same-as-backend
SESSION_SECRET=32-char-random-string
```

## Service URLs

- Frontend: http://localhost:5648
- Backend API: http://localhost:8987
- API Documentation: http://localhost:8987/docs
- PostgreSQL: localhost:5432
- Redis: localhost:6379

## Database Operations

```bash
# Apply migrations
cd backend && alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "description"

# Rollback migration
alembic downgrade -1
```

## Important Considerations

1. **Session Management**: Frontend uses iron-session with HTTP-only cookies. Sessions expire after 24 hours.

2. **Rate Limiting**: Login attempts limited to 5 per 15 minutes per IP.

3. **JIRA Integration**: Supports multiple JIRA instances via JSON config or environment variables.

4. **Field Synchronization**: Automatic database schema updates when new fields discovered.

5. **Caching Strategy**: Redis TTL set to 110 seconds (less than 2-minute sync interval).

6. **Error Handling**: Comprehensive logging with correlation IDs for debugging.

## Performance Tuning

### Current Optimized Settings
- **rate_limit_pause**: 0.5s (balanced for speed vs JIRA rate limits)
- **batch_size**: 400 issues per API request
- **max_workers**: 10 parallel workers
- **lookback_days**: 49 days of history
- **Performance**: 500 issues/second, ~90 seconds for full sync

### Performance Configuration UI
Access at http://localhost:5648/admin/performance to:
- Adjust sync performance parameters with visual sliders
- Test configuration impact before applying
- Monitor estimated sync times and resource usage
- Safe presets prevent aggressive settings that could trigger rate limits

### Database Performance
Indexes added on key columns for optimal query performance:
- issue_key (primary key)
- summary, status, project_name
- ndpu_order_number, ndpu_listing_address
- last_updated

## Field Mapping Configuration

⚠️ **Important**: Fields are currently not populated until field mappings are configured.

### Configure Field Mappings
1. Access admin panel at http://localhost:5648/admin/field-mappings
2. Use field discovery to find your JIRA custom field IDs
3. Map database columns to JIRA fields for each instance
4. Test mappings with sample data
5. Save and run sync to populate data

### Required Fields for Sync
The system dynamically collects field IDs from configured mappings and requests:
- System fields: key, summary, status, project, updated, created, issuetype
- All custom fields mapped in the configuration
- Changelog data for transition tracking

## Recent Fixes & Improvements

### Sync Issue Resolution (2025-01-10)
- Fixed missing 'fields' parameter in JIRA API calls
- Added `get_required_fields()` method to dynamically collect field IDs
- Sync now properly fetches configured fields from JIRA

### Performance Optimizations
- Reduced sync time from 3 minutes to 90 seconds
- Optimized rate limiting and batch sizes
- Added parallel processing for multiple projects
- Database indexes for faster queries