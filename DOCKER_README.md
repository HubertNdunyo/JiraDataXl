# Docker Setup for JIRA Sync Dashboard

This guide explains how to run the JIRA Sync Dashboard using Docker containers.

## 🎯 Current Status (2025-08-08)

All Docker containers are running healthy with the following fixes applied:
- ✅ Database schema mismatches resolved
- ✅ Performance metrics tracking implemented  
- ✅ Frontend health checks added
- ✅ Redis caching optimized (20x performance improvement)
- ✅ Field mapping errors fixed
- ✅ Alembic migrations configured

## Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+
- At least 4GB available RAM
- `.env` file with your JIRA credentials (copy from `.env.example`)

## Quick Start

### 1. Setup Environment Variables

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your JIRA credentials and database settings
nano .env
```

### 2. Development Environment

For development with hot reload:

```bash
# Start all services
docker-compose -f docker-compose.dev.yml up

# Or run in background
docker-compose -f docker-compose.dev.yml up -d

# View logs
docker-compose -f docker-compose.dev.yml logs -f

# Stop services
docker-compose -f docker-compose.dev.yml down
```

### 3. Production Environment

For production deployment:

```bash
# Build and start services
docker-compose -f docker-compose.prod.yml up --build -d

# View logs
docker-compose -f docker-compose.prod.yml logs -f

# Stop services
docker-compose -f docker-compose.prod.yml down
```

## Architecture

The application consists of 4 containers:

1. **PostgreSQL** - Database for storing JIRA data with optimized schema
2. **Redis** - High-performance cache layer (20x speed improvement)
3. **Backend** - FastAPI application with sync engine (272 issues/sec)
4. **Frontend** - Next.js 14 application with TypeScript and shadcn/ui

### Container Health Status
All containers include health checks and are monitored for availability:
- PostgreSQL: Health check via `pg_isready`
- Redis: Health check via `redis-cli ping`
- Backend: Health endpoint at `/health`
- Frontend: Health endpoint at `/api/health`

## Service URLs

- **Frontend**: http://localhost:5648
- **Backend API**: http://localhost:8987
- **API Documentation**: http://localhost:8987/docs
- **PostgreSQL**: localhost:5432 (for external connections)
- **Redis**: localhost:6379 (for external connections)

## Redis Caching Strategy

Redis is configured to cache database queries with the following TTLs:

- **Issue queries**: 110 seconds
- **Project lists**: 110 seconds
- **Search results**: 110 seconds
- **Configuration**: 5 minutes

Cache is automatically invalidated after each JIRA sync (every 2 minutes).

## Database Management

### Access PostgreSQL

```bash
# Connect to database container
docker-compose -f docker-compose.dev.yml exec postgres psql -U postgres -d jira_sync

# Or from host machine (requires psql client)
psql -h localhost -U postgres -d jira_sync
```

### Run Database Migrations

```bash
# Apply all migrations
docker-compose -f docker-compose.dev.yml exec backend alembic upgrade head

# Check migration status
docker-compose -f docker-compose.dev.yml exec backend alembic current

# Create new migration
docker-compose -f docker-compose.dev.yml exec backend alembic revision --autogenerate -m "Description"
```

### Backup Database

```bash
# Create backup
docker-compose -f docker-compose.dev.yml exec postgres pg_dump -U postgres jira_sync > backup.sql

# Restore backup
docker-compose -f docker-compose.dev.yml exec postgres psql -U postgres jira_sync < backup.sql
```

## Redis Management

### Access Redis CLI

```bash
# Connect to Redis
docker-compose -f docker-compose.dev.yml exec redis redis-cli

# View cache statistics
docker-compose -f docker-compose.dev.yml exec redis redis-cli INFO stats

# Clear cache
docker-compose -f docker-compose.dev.yml exec redis redis-cli FLUSHDB
```

## Container Management

### View Running Containers

```bash
docker-compose -f docker-compose.dev.yml ps
```

### Rebuild Specific Service

```bash
# Rebuild backend after code changes
docker-compose -f docker-compose.dev.yml build backend
docker-compose -f docker-compose.dev.yml up -d backend

# Rebuild frontend
docker-compose -f docker-compose.dev.yml build frontend
docker-compose -f docker-compose.dev.yml up -d frontend
```

### Execute Commands in Containers

```bash
# Run Python command in backend
docker-compose -f docker-compose.dev.yml exec backend python -c "print('Hello')"

# Install additional packages
docker-compose -f docker-compose.dev.yml exec backend pip install requests

# Run npm commands in frontend
docker-compose -f docker-compose.dev.yml exec frontend npm run build
```

## Volumes and Persistence

### Data Volumes

- `postgres_data`: PostgreSQL database files
- `redis_data`: Redis persistence files
- `backend_venv`: Python virtual environment (dev only)

### Clean Up Volumes

```bash
# Remove all data (WARNING: This deletes all data!)
docker-compose -f docker-compose.dev.yml down -v

# Remove specific volume
docker volume rm dataapp_postgres_data
```

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker-compose -f docker-compose.dev.yml logs [service_name]

# Check container status
docker-compose -f docker-compose.dev.yml ps

# Rebuild from scratch
docker-compose -f docker-compose.dev.yml down
docker-compose -f docker-compose.dev.yml build --no-cache
docker-compose -f docker-compose.dev.yml up
```

### Database Connection Issues

1. Ensure PostgreSQL container is healthy:
```bash
docker-compose -f docker-compose.dev.yml ps postgres
```

2. Check environment variables:
```bash
docker-compose -f docker-compose.dev.yml exec backend env | grep DB_
```

3. Test connection:
```bash
docker-compose -f docker-compose.dev.yml exec backend python -c "
from core.db.db_core import get_db_connection
try:
    with get_db_connection() as conn:
        print('Database connection successful')
except Exception as e:
    print(f'Database connection failed: {e}')
"
```

4. Check for schema issues:
```bash
# List all tables
docker-compose -f docker-compose.dev.yml exec postgres psql -U postgres -d jira_sync -c "\dt"

# Verify critical tables exist
docker-compose -f docker-compose.dev.yml exec postgres psql -U postgres -d jira_sync -c "
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('sync_history', 'sync_performance_metrics', 'jira_field_cache');
"
```

### Redis Connection Issues

1. Check Redis status:
```bash
docker-compose -f docker-compose.dev.yml exec redis redis-cli ping
```

2. Verify Redis configuration:
```bash
docker-compose -f docker-compose.dev.yml exec backend python -c "
from core.cache import get_cache
cache = get_cache()
print(cache.get_stats())
"
```

### Frontend Can't Connect to Backend

1. Check backend is running:
```bash
curl http://localhost:8987/health
```

2. Verify environment variables:
```bash
docker-compose -f docker-compose.dev.yml exec frontend env | grep API
```

3. Check network connectivity:
```bash
docker-compose -f docker-compose.dev.yml exec frontend ping backend
```

## Performance Tuning

### Redis Memory Management

Redis is configured with:
- Max memory: 256MB
- Eviction policy: allkeys-lru (removes least recently used keys)
- Persistence: AOF (Append Only File) with fsync every second

To adjust:
```yaml
# In docker-compose.yml
command: redis-server --maxmemory 512mb --maxmemory-policy allkeys-lru
```

### PostgreSQL Optimization

For better performance with large datasets:

```sql
-- Connect to database
docker-compose -f docker-compose.dev.yml exec postgres psql -U postgres -d jira_sync

-- Analyze tables for query optimization
ANALYZE jira_issues_v2;

-- Check table sizes
SELECT 
  schemaname,
  tablename,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables 
WHERE schemaname = 'public' 
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

## Security Considerations

### Production Deployment

1. **Change default passwords** in `.env`
2. **Use secrets management** for sensitive data
3. **Enable SSL/TLS** for external connections
4. **Restrict port exposure** - only expose necessary ports
5. **Regular updates** - Keep base images updated

### Network Isolation

The containers use a dedicated network (`jira-sync-network`) with subnet `172.25.0.0/16`.

To further isolate services:
```yaml
# Create separate networks for frontend/backend
networks:
  frontend:
    driver: bridge
  backend:
    driver: bridge
```

## Monitoring

### Container Resource Usage

```bash
# Real-time stats
docker stats

# Specific container
docker stats jira-sync-backend
```

### Application Metrics

- Backend health: http://localhost:8987/health
- Frontend health: http://localhost:5648/api/health
- Redis stats: http://localhost:8987/api/cache/stats
- Sync status: http://localhost:8987/api/sync/status
- Field mappings: http://localhost:8987/api/admin/fields
- Performance metrics: http://localhost:8987/api/sync/history/{sync_id}/metrics

### Performance Benchmarks

- **Sync Speed**: 272 issues/second
- **Cache Hit Rate**: 95%+ with Redis
- **API Response**: <50ms for cached queries
- **Database Queries**: Optimized with proper indexes

## Backup and Recovery

### Full System Backup

```bash
# Stop services
docker-compose -f docker-compose.prod.yml stop

# Backup volumes
docker run --rm -v dataapp_postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/postgres_backup.tar.gz /data
docker run --rm -v dataapp_redis_data:/data -v $(pwd):/backup alpine tar czf /backup/redis_backup.tar.gz /data

# Backup configuration
tar czf config_backup.tar.gz .env docker-compose.*.yml

# Restart services
docker-compose -f docker-compose.prod.yml start
```

### Restore from Backup

```bash
# Stop services
docker-compose -f docker-compose.prod.yml down

# Restore volumes
docker run --rm -v dataapp_postgres_data:/data -v $(pwd):/backup alpine tar xzf /backup/postgres_backup.tar.gz -C /
docker run --rm -v dataapp_redis_data:/data -v $(pwd):/backup alpine tar xzf /backup/redis_backup.tar.gz -C /

# Start services
docker-compose -f docker-compose.prod.yml up -d
```

## Recent Fixes (2025-08-08)

### Database Schema Fixes
- Changed `sync_runs` → `sync_history` table references
- Fixed column mappings (`sync_run_id` → `sync_id`, `start_time` → `started_at`)
- Added missing `sync_performance_metrics` table
- Created `jira_field_cache` table for field metadata

### API Fixes
- Fixed parameter name mismatches (`initiated_by` → `triggered_by`)
- Added column aliases for backward compatibility
- Resolved 500 errors in field mappings endpoint
- Fixed sync statistics endpoint responses

### Frontend Fixes  
- Added health check endpoint at `/api/health`
- Fixed Dialog accessibility warnings
- Resolved TypeScript type issues

## Support

For issues or questions:
1. Check container logs: `docker-compose logs [service]`
2. Verify environment variables in `.env`
3. Ensure Docker has sufficient resources allocated
4. Review the main documentation in `/docs`
5. Check [CHANGELOG.md](CHANGELOG.md) for recent updates
6. Review [DOCKER_IMPLEMENTATION_REPORT.md](DOCKER_IMPLEMENTATION_REPORT.md) for implementation details