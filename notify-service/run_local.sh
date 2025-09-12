#!/bin/bash
# run_local.sh - Run notify-api locally for development

set -euo pipefail

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Cleanup function
cleanup() {
    print_status "Shutting down..."
    $DOCKER_COMPOSE_CMD down
    kill 0
    print_success "Cleanup complete"
}

# Set trap to cleanup on exit
trap cleanup EXIT

echo "Starting BC Registries Notify Service locally..."
echo "Running from directory: $SCRIPT_DIR"
echo "============================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if uv is available
if ! command -v uv &> /dev/null; then
    print_error "uv is not installed. Please install uv first:"
    echo "curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# Check if docker is available
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if docker compose is available (try both versions)
DOCKER_COMPOSE_CMD=""
if docker compose version &> /dev/null; then
    DOCKER_COMPOSE_CMD="docker compose"
elif command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE_CMD="docker-compose"
else
    print_error "Docker Compose is not available. Please install Docker Compose."
    print_error "Try: sudo apt-get install docker-compose-plugin"
    exit 1
fi

print_status "Using Docker Compose command: $DOCKER_COMPOSE_CMD"

print_status "Setting up local environment..."

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    print_error "Try: cp .env.sample .env then edit .env file"
    exit 1
fi

print_status "Starting PostgreSQL database..."

# Start PostgreSQL using detected docker compose command
$DOCKER_COMPOSE_CMD up -d postgres

# Wait for postgres to be ready
print_status "Waiting for PostgreSQL to be ready..."
timeout=60
counter=0
while ! $DOCKER_COMPOSE_CMD exec postgres pg_isready -U notifyuser -d notify -h localhost &> /dev/null; do
    if [ $counter -ge $timeout ]; then
        print_error "PostgreSQL failed to start within $timeout seconds"
        exit 1
    fi
    sleep 2
    counter=$((counter + 2))
    printf "."
done
echo ""
print_success "PostgreSQL is ready!"

cd $SCRIPT_DIR/notify-api

print_status "Installing dependencies with uv..."
uv sync

print_status "Running database migrations..."
export DEPLOYMENT_ENV=migration
if ! uv run flask db upgrade; then
    print_warning "Database migrations failed. This might be expected for first run."
    print_status "Initializing database..."
    uv run flask db init || true
    uv run flask db migrate -m "Initial migration" || true
    uv run flask db upgrade || true
fi
export DEPLOYMENT_ENV=development

print_status "Starting Flask development server..."
print_success "Setup complete! Starting the notify API..."
echo ""
echo "API will be available at: http://localhost:5001"
echo "Database: PostgreSQL on localhost:5433"
echo ""
echo "Press Ctrl+C to stop the server"
echo "============================================"

# Run the Flask application using our improved runner
uv run flask run --port=5001 &

cd $SCRIPT_DIR/notify-delivery

print_status "Installing dependencies with uv..."
uv sync

export DEPLOYMENT_ENV=development

print_status "Starting Flask development server..."
print_success "Setup complete! Starting the notify delivery..."
echo ""
echo "API will be available at: http://localhost:5002"
echo "Database: PostgreSQL on localhost:5433"
echo ""
echo "Press Ctrl+C to stop the server"
echo "============================================"

# Run the Flask application using our improved runner
uv run flask run --port=5002 &

wait