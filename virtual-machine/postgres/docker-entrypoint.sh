#!/bin/bash
set -e

# Wait for PostgreSQL to start
sleep 5

# Connect to PostgreSQL and create the database
psql -U "$POSTGRES_USER" -tc "SELECT 1 FROM pg_database WHERE datname = '$POSTGRES_DB'" | grep -q 1 || \
    psql -U "$POSTGRES_USER" -c "CREATE DATABASE IF NOT EXISTS $POSTGRES_DB;"

# Enable PostGIS extension (if needed)
psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "CREATE EXTENSION IF NOT EXISTS postgis;"

# Restore from backup if it exists
if [ -f /backup/db_backup.sql ]; then
    echo "Restoring database from backup..."
    psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" < /backup/db_backup.sql
elif [ -f /backup/db_backup.dump ]; then
    echo "Restoring database from dump..."
    pg_restore --no-owner --dbname="$POSTGRES_DB" -U "$POSTGRES_USER" /backup/db_backup.dump
else
    echo "No backup file found. Skipping restore."
fi

echo "Database setup complete."

exec docker-entrypoint.sh "$@"  # Continue with default PostgreSQL startup
