# Database Migrations with Alembic

This directory contains database migrations managed by Alembic.

## Setup

Alembic is already configured and ready to use. The configuration reads database credentials from environment variables.

## Usage

### Check current migration status
```bash
cd backend
alembic current
```

### Apply all pending migrations
```bash
cd backend
alembic upgrade head
```

### Downgrade to previous migration
```bash
cd backend
alembic downgrade -1
```

### Create a new migration
```bash
cd backend
alembic revision -m "description of changes"
```

### Auto-generate migration from model changes
```bash
cd backend
alembic revision --autogenerate -m "description of changes"
```

## Migration History

### 001_initial_schema
- Creates all initial tables:
  - jira_issues_v2
  - sync_history
  - sync_history_details
  - sync_project_details
  - field_mappings
  - sync_config
  - audit_log
  - field_cache
- Adds all necessary indexes
- Inserts default configuration values

## Docker Integration

To run migrations in Docker:

```bash
# Development
docker-compose -f docker-compose.dev.yml exec backend alembic upgrade head

# Production
docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head
```

## Environment Variables

The following environment variables are required:
- `DB_HOST`: Database host (default: localhost)
- `DB_PORT`: Database port (default: 5432)
- `DB_NAME`: Database name (default: jira_sync)
- `DB_USER`: Database user (default: postgres)
- `DB_PASSWORD`: Database password (default: postgres)

## Notes

- Migrations are stored in the `versions/` directory
- The current schema matches the tables created in `docker/init-scripts/01-init-database.sql`
- Future schema changes should be managed through Alembic migrations instead of modifying the init script