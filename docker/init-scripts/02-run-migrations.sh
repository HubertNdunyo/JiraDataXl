#!/bin/bash
# Run additional SQL migrations from the project

echo "Running additional database migrations..."

# Run migration files in order
for migration in /migrations/*.sql; do
    if [ -f "$migration" ]; then
        echo "Running migration: $(basename $migration)"
        psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f "$migration"
    fi
done

# Run any additional schema files
for schema_file in /docker-entrypoint-initdb.d/database/scripts/*.sql; do
    if [ -f "$schema_file" ]; then
        echo "Running schema file: $(basename $schema_file)"
        psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f "$schema_file"
    fi
done

echo "Database migrations completed"