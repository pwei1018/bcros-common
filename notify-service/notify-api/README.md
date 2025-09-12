# BC Registries Notify API

BC Registries Notify API service for sending notifications via multiple providers.

## Background

This service provides a unified API for sending notifications through various providers including:

- GC Notify for standard email notifications
- SMTP for HTML emails and large attachments (>6MB)
- Housing service for STRR-specific notifications

## Technology Stack Used

- Python 3.12, Flask
- PostgreSQL with SQLAlchemy, pg8000 & alembic
- uv for dependency management
- Google Cloud Pub/Sub for message queuing
- Docker for containerization

## Security

This application follows BC Government security standards and best practices.

## Files in this repository

```
notify-api/
├── src/notify_api/          # Main application code
├── tests/                   # Test suite
├── migrations/              # Database migrations
├── devops/                  # Deployment configurations
├── pyproject.toml           # Project configuration and dependencies
├── Dockerfile               # Container definition
└── README.md                # This file
```

## Environment Variables

Copy '.env.sample' to '.env' and replace the values with your configuration.

## Development Setup

### Prerequisites

- Python 3.12+
- uv

### Quick Setup with uv

```bash
# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## Development Commands

### Using uv

```bash
# Activeate the virtual environment
uv venv

# Install/update dependencies
uv sync

# Add new dependency
uv add <package-name>

```

### Linting

```bash
# Run linting
uv run ruff check .

# Format code
uv run ruff format .

```

### Running Unit Tests

```bash
# All tests (basic run)
uv run python -m pytest

# All tests with verbose output
uv run python -m pytest -v

# Run without coverage for faster execution
uv run python -m pytest --no-cov

# Specific file
uv run python -m pytest tests/unit/models/test_email.py -v

# Specific test method
uv run python -m pytest tests/unit/models/test_email.py::TestEmailValidator::test_email_validator_creation_mocked -v

# With coverage report
uv run python -m pytest --cov=notify_api --cov-report=term-missing

# Run specific marker (if defined)
uv run python -m pytest -m unit -v

# Quick test of just one module for debugging
uv run python -m pytest tests/unit/models/ -v --no-cov
```

### Run the application in local

```bash
.././run_local.sh
```

## Database Operations

### Running Database Migrations

```bash
export DEPLOYMENT_ENV=migration

# Create new migration
uv run flask db revision -m "description of changes"

# Apply migrations
uv run flask db upgrade

# Rollback migrations
uv run flask db downgrade
```

## CI/CD

See <https://github.com/bcgov/bcros-common/blob/main/.github/workflows/notify-api-ci.yaml>
See <https://github.com/bcgov/bcros-common/blob/main/.github/workflows/notify-api-cd.yaml>

## License

Copyright 2025 Province of British Columbia

Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.
3. Neither the name of the Province of British Columbia nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
