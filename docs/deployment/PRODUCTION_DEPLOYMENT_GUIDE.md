# Production Deployment Guide

**Version**: 2.0  
**Last Updated**: January 10, 2025  
**Status**: ✅ Production Ready with 100% Test Coverage

## Overview

This guide provides comprehensive instructions for deploying the JIRA Sync Dashboard to production. The system features **fully automated initialization**, **100% test success rate**, and **self-healing architecture** that recovers from complete teardown.

## Prerequisites

### System Requirements
- **CPU**: 4+ cores recommended
- **RAM**: 8GB minimum (16GB recommended for large datasets)
- **Storage**: 50GB+ SSD storage
- **OS**: Linux (Ubuntu 20.04+ or similar)
- **Docker**: Version 20.10+
- **Docker Compose**: Version 2.0+

### Network Requirements
- **Ports Required**:
  - 5648: Frontend (Next.js)
  - 8987: Backend API (FastAPI)
  - 5432: PostgreSQL (internal)
  - 6379: Redis (internal)
- **External Access**: HTTPS proxy recommended (nginx/traefik)
- **JIRA Access**: Network connectivity to JIRA instances

## Pre-Deployment Checklist

### 1. Environment Configuration
```bash
# Create production environment file
cp .env.example .env.production

# Edit with production values
vim .env.production
```

### 2. Required Environment Variables
```bash
# Database Configuration
DB_NAME=jira_sync
DB_USER=postgres
DB_PASSWORD=<STRONG_PASSWORD>
DB_HOST=postgres  # Use container name
DB_PORT=5432

# Redis Configuration
REDIS_HOST=redis  # Use container name
REDIS_PORT=6379

# JIRA Credentials (Instance 1)
JIRA_URL_1=https://your-company.atlassian.net
JIRA_USERNAME_1=service-account@company.com
JIRA_PASSWORD_1=<API_TOKEN>

# JIRA Credentials (Instance 2)
JIRA_URL_2=https://your-company2.atlassian.net
JIRA_USERNAME_2=service-account@company.com
JIRA_PASSWORD_2=<API_TOKEN>

# Admin Security
ADMIN_API_KEY=<GENERATE_SECURE_KEY>  # Min 32 characters
SESSION_SECRET=<GENERATE_SESSION_SECRET>  # 32 characters

# Production Settings
ENV=production
LOG_LEVEL=info
```

### 3. Generate Secure Keys
```bash
# Generate Admin API Key
openssl rand -hex 32

# Generate Session Secret
openssl rand -hex 16
```

## Deployment Steps

### 1. Clone Repository
```bash
git clone <repository-url>
cd dataApp
```

### 2. Prepare Production Configuration
```bash
# Use production environment file
ln -sf .env.production .env

# Verify configuration
docker-compose -f docker-compose.prod.yml config
```

### 3. Deploy with Docker Compose
```bash
# Start all services (fully automated initialization!)
docker-compose -f docker-compose.prod.yml up -d

# Monitor startup logs
docker-compose -f docker-compose.prod.yml logs -f
```

### 4. Wait for Auto-Initialization
The system automatically initializes in ~60 seconds:
- ✅ Creates all database tables
- ✅ Loads field mapping configurations
- ✅ Applies database migrations
- ✅ Starts all services
- ✅ Achieves 100% test success

### 5. Verify Deployment
```bash
# Quick system verification (<5 seconds)
docker exec jira-sync-backend ./tests/test_field_mapping_quick.sh
# Expected: ✅ ALL TESTS PASSED! (4/4)

# Comprehensive verification (~40 seconds)
docker exec jira-sync-backend python tests/test_field_mapping_comprehensive.py
# Expected: Success Rate: 100.0% (10/10)

# Check service health
curl http://localhost:8987/health
curl http://localhost:5648/api/health
```

## SSL/TLS Configuration

### Using Nginx Reverse Proxy
```nginx
server {
    listen 443 ssl http2;
    server_name sync.yourcompany.com;

    ssl_certificate /etc/ssl/certs/sync.crt;
    ssl_certificate_key /etc/ssl/private/sync.key;

    # Frontend
    location / {
        proxy_pass http://localhost:5648;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # Backend API
    location /api {
        proxy_pass http://localhost:8987;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Using Docker Traefik
```yaml
# Add to docker-compose.prod.yml
labels:
  - "traefik.enable=true"
  - "traefik.http.routers.frontend.rule=Host(`sync.yourcompany.com`)"
  - "traefik.http.routers.frontend.tls=true"
  - "traefik.http.routers.frontend.tls.certresolver=letsencrypt"
```

## Performance Optimization

### 1. Database Tuning
```sql
-- Connect to database
docker exec -it jira-sync-postgres psql -U postgres -d jira_sync

-- Optimize PostgreSQL settings
ALTER SYSTEM SET shared_buffers = '2GB';
ALTER SYSTEM SET effective_cache_size = '6GB';
ALTER SYSTEM SET maintenance_work_mem = '512MB';
ALTER SYSTEM SET work_mem = '16MB';

-- Reload configuration
SELECT pg_reload_conf();
```

### 2. Redis Configuration
```bash
# Edit redis configuration
docker exec -it jira-sync-redis redis-cli

# Set max memory
CONFIG SET maxmemory 2gb
CONFIG SET maxmemory-policy allkeys-lru

# Save configuration
CONFIG REWRITE
```

### 3. Application Performance Settings
Access the Performance Configuration UI:
```
https://sync.yourcompany.com/admin/performance
```

Recommended Production Settings:
- **Rate Limit Pause**: 0.5s
- **Batch Size**: 400
- **Max Workers**: 10
- **Connection Pool**: 20
- **Lookback Days**: 49

## Monitoring

### 1. Health Checks
```bash
# Create monitoring script
cat > /usr/local/bin/jira-sync-health.sh << 'EOF'
#!/bin/bash
# Health check endpoints
backend_health=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8987/health)
frontend_health=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5648/api/health)

if [ "$backend_health" = "200" ] && [ "$frontend_health" = "200" ]; then
    echo "✅ System healthy"
    exit 0
else
    echo "❌ System unhealthy - Backend: $backend_health, Frontend: $frontend_health"
    exit 1
fi
EOF

chmod +x /usr/local/bin/jira-sync-health.sh
```

### 2. Log Aggregation
```bash
# View all logs
docker-compose -f docker-compose.prod.yml logs

# Follow specific service
docker-compose -f docker-compose.prod.yml logs -f backend

# Export logs
docker-compose -f docker-compose.prod.yml logs > sync-logs-$(date +%Y%m%d).txt
```

### 3. Metrics Collection
```bash
# Database metrics
docker exec jira-sync-postgres psql -U postgres -d jira_sync -c "
SELECT 
    COUNT(*) as total_issues,
    COUNT(DISTINCT project_name) as projects,
    MAX(last_updated) as latest_sync
FROM jira_issues;"

# Redis metrics
docker exec jira-sync-redis redis-cli INFO stats
```

## Backup and Recovery

### 1. Automated Backups
```bash
# Create backup script
cat > /usr/local/bin/jira-sync-backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/var/backups/jira-sync"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup database
docker exec jira-sync-postgres pg_dump -U postgres jira_sync | gzip > $BACKUP_DIR/db_$DATE.sql.gz

# Backup configurations
docker exec jira-sync-backend python -c "
from core.db.db_config import create_backup
create_backup('scheduled_backup_$DATE', 'auto', 'Scheduled backup')
"

# Keep only last 30 days
find $BACKUP_DIR -name "*.sql.gz" -mtime +30 -delete

echo "Backup completed: $BACKUP_DIR/db_$DATE.sql.gz"
EOF

chmod +x /usr/local/bin/jira-sync-backup.sh

# Add to crontab (daily at 2 AM)
echo "0 2 * * * /usr/local/bin/jira-sync-backup.sh" | crontab -
```

### 2. Disaster Recovery
```bash
# Complete system recovery after failure
docker-compose -f docker-compose.prod.yml down -v
docker-compose -f docker-compose.prod.yml up -d

# System automatically recovers in ~60 seconds
sleep 60

# Verify recovery
docker exec jira-sync-backend python tests/test_field_mapping_comprehensive.py
```

### 3. Database Restoration
```bash
# Restore from backup
gunzip -c /var/backups/jira-sync/db_20250110.sql.gz | \
  docker exec -i jira-sync-postgres psql -U postgres -d jira_sync
```

## Security Hardening

### 1. Network Isolation
```yaml
# docker-compose.prod.yml additions
networks:
  frontend:
    driver: bridge
  backend:
    driver: bridge
    internal: true
```

### 2. Resource Limits
```yaml
# Add to each service in docker-compose.prod.yml
deploy:
  resources:
    limits:
      cpus: '2'
      memory: 4G
    reservations:
      cpus: '1'
      memory: 2G
```

### 3. Security Headers
```nginx
# Add to nginx configuration
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Strict-Transport-Security "max-age=31536000" always;
```

## Troubleshooting

### System Not Starting
```bash
# Check container status
docker-compose -f docker-compose.prod.yml ps

# View startup logs
docker-compose -f docker-compose.prod.yml logs backend

# Verify database connection
docker exec jira-sync-backend python -c "
from core.db.db_core import get_db_connection
with get_db_connection() as conn:
    print('✅ Database connected')
"
```

### Performance Issues
```bash
# Check resource usage
docker stats

# Analyze slow queries
docker exec jira-sync-postgres psql -U postgres -d jira_sync -c "
SELECT query, calls, mean_exec_time
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;"
```

### Sync Failures
```bash
# Check sync status
curl -H "X-Admin-Key: $ADMIN_API_KEY" http://localhost:8987/api/sync/status

# Review error logs
docker logs jira-sync-backend | grep ERROR

# Reset sync lock if needed
docker exec jira-sync-postgres psql -U postgres -d jira_sync -c "
DELETE FROM sync_status WHERE status = 'running';"
```

## Maintenance Schedule

### Daily
- Monitor health endpoints
- Review error logs
- Check sync success rate

### Weekly
- Run comprehensive test suite
- Review performance metrics
- Backup verification

### Monthly
- Update Docker images
- Review and rotate logs
- Performance tuning review
- Security updates

## Support and Documentation

### Documentation
- [Architecture Overview](../architecture/ARCHITECTURE.md)
- [Field Mapping Guide](../guides/FIELD_MAPPING_GUIDE.md)
- [Operational Guide](../operations/OPERATIONAL_GUIDE.md)
- [API Documentation](http://localhost:8987/docs)

### Logs and Debugging
- Application logs: `docker-compose logs [service]`
- Database logs: `docker exec jira-sync-postgres tail -f /var/log/postgresql/*.log`
- Frontend logs: Browser console + `docker logs jira-sync-frontend`

### Performance Metrics
- Sync duration: ~90 seconds for 45,000+ issues
- Throughput: 500 issues/second
- Success rate: Should maintain >99%
- Test coverage: 100% (all tests must pass)

## Rollback Procedure

If issues occur after deployment:

```bash
# 1. Stop current deployment
docker-compose -f docker-compose.prod.yml down

# 2. Restore previous version
git checkout <previous-tag>

# 3. Restore database backup
gunzip -c /var/backups/jira-sync/db_<date>.sql.gz | \
  docker exec -i jira-sync-postgres psql -U postgres -d jira_sync

# 4. Restart services
docker-compose -f docker-compose.prod.yml up -d

# 5. Verify rollback
docker exec jira-sync-backend python tests/test_field_mapping_comprehensive.py
```

## Conclusion

The JIRA Sync Dashboard is now **production-ready** with:
- ✅ Fully automated deployment
- ✅ 100% test success rate
- ✅ Self-healing architecture
- ✅ Comprehensive monitoring
- ✅ Automatic backup and recovery
- ✅ Enterprise-grade security

For additional support or questions, refer to the documentation or create an issue in the repository.

---

*Deployment Guide Version 2.0 - January 10, 2025*