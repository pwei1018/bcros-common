#!/bin/bash

set -e

# Simple configuration - edit these values directly when needed
SCHEMA="public" 

# Set environment variables
export NOTIFY_DATABASE_SCHEMA=$SCHEMA

# Start services if not running
docker compose up -d postgres

# Wait for postgres to be ready
echo "Waiting for Postgres to be ready..."
docker compose exec postgres sh -c "until pg_isready -U notifyuser; do sleep 2; done;"
echo "Postgres is ready!"
