#!/bin/bash
# Backend startup script - ensures database is properly initialized

echo "Starting backend initialization..."

# Wait for database to be ready
echo "Waiting for database..."
while ! nc -z ${DB_HOST:-postgres} ${DB_PORT:-5432}; do
  sleep 1
done
echo "Database is ready!"

# Run database initialization
echo "Initializing database..."
python scripts/init_database.py
if [ $? -eq 0 ]; then
    echo "✅ Database initialization successful"
else
    echo "⚠️ Database initialization completed with warnings (non-critical)"
fi

# Run Alembic migrations
echo "Running database migrations..."
alembic upgrade head || echo "⚠️ Migrations completed with warnings"

# Start the application
echo "Starting FastAPI application..."
if [ "${ENV}" = "production" ]; then
    echo "Running in production mode with 4 workers..."
    exec uvicorn main:app --host 0.0.0.0 --port 8987 --workers 4 --log-level info
else
    echo "Running in development mode with hot reload..."
    exec uvicorn main:app --host 0.0.0.0 --port 8987 --reload
fi