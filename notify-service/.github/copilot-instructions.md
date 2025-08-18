# AI Coding Instructions for BC Registries Notify Service

This document provides instructions for an AI coding assistant to work on the BC Registries Notify Service. The project is a dual-microservice system built with Python and Flask, designed for secure and reliable notification delivery within the BC Government ecosystem.

---

## 🏛️ Architecture Overview

The system consists of two main services that communicate asynchronously via a shared database and a message queue.

-   **`notify-api` (API Gateway):**
    -   Receives and validates incoming notification requests.
    -   Queues requests for processing.
    -   Handles user authentication and authorization.
-   **`notify-delivery` (Worker Service):**
    -   Processes queued messages.
    -   Dispatches notifications through various providers based on business rules.

### Cross-Service Communication

-   **Shared Database:** Both services use the same PostgreSQL database, with models defined in `notify_api.models`.
-   **Message Queue:** Google Cloud Pub/Sub is used for asynchronous messaging.
-   **Standardized Format:** Cloud Events are used for consistent message formatting.

### Notification Provider Selection

The `notify_api/services/notify_service.py` module contains the logic for selecting the appropriate notification provider:

1.  **Housing Provider:** Used for requests where `request_by` is "STRR".
2.  **SMTP Provider:** Used for emails with large attachments (>6MB) or HTML content.
3.  **GC Notify Provider:** The default provider for all other standard email notifications.

---

## 🔧 Development Environment

### Core Technology Stack

-   **Python:** 3.12+
-   **Framework:** Flask 3.1.0+
-   **Async:** UVLoop 0.21.0+
-   **HTTP Client:** HTTPX 0.28.0+ (do not use `requests`)
-   **Validation:** Pydantic 2.9.0+ (do not use `Marshmallow`)
-   **Database:** Flask-SQLAlchemy with the `cloud-sql-connector` for Google Cloud SQL.
-   **Linting/Formatting:** Ruff (120-character line length, Python 3.12 target).

### Local Setup

To set up the local development environment, run the following command in the `notify-api` directory:

```bash
./run_local.sh
```

This script starts the PostgreSQL container and the Flask development server.

### Essential Commands

All dependency management and development tasks should be performed using `uv`.

-   **Install/Sync Dependencies:**
    ```bash
    uv sync
    ```
-   **Add a Dependency:**
    ```bash
    uv add <package>
    ```
-   **Run Tests:**
    ```bash
    uv run python -m pytest
    ```
-   **Format and Lint Code:**
    ```bash
    uv run ruff format . && uv run ruff check --fix .
    ```
-   **Run Dev Server:**
    ```bash
    uv run flask run --debug
    ```
-   **Generate Coverage Report:**
    ```bash
    uv run coverage run -m pytest && uv run coverage html
    ```

### Database Migrations

Alembic is used for database migrations. The `DEPLOYMENT_ENV` environment variable must be set to `migration` to perform database operations.

```bash
# Set the environment variable
export DEPLOYMENT_ENV=migration

# Create a new revision
uv run flask db revision -m "Your migration description"

# Apply the migration
uv run flask db upgrade
```

---

## 💻 Coding Standards

### General Principles

-   **Style:** Follow `snake_case.py` for file naming and use descriptive variable names (e.g., `is_authenticated`, `has_permission`).
-   **Functions:** Use `def` with proper type hints for all function definitions.
-   **Error Handling:** Prioritize guard clauses and early returns to keep the "happy path" at the end of the function.
-   **Structure:** Use Flask app factories and blueprints to organize the application.
-   **Imports:** Group BC Gov libraries separately from standard and third-party imports.

### Database

-   **ORM:** Use Flask-SQLAlchemy for all database operations.
-   **Connections:** Use the `cloud-sql-connector` for connecting to BC Gov's Cloud SQL instances with IAM authentication.
-   **Schema:** The database schema is configurable via the `DB_SCHEMA` environment variable.

---

## 🔒 Security Requirements

Security is a critical aspect of this project. Adhere to the following BC Government standards.

### Authentication & Authorization

-   **OIDC:** Use `flask-jwt-oidc` for OIDC integration (do not use `Flask-JWT-Extended`).
-   **Roles:** Access control is based on `realm_access.roles` from the JWT token.

### Data Handling

-   **Validation:** Use Pydantic and `Flask-Pydantic` for modern, auto-validating decorators. Type hints are required.
-   **Logging:** **NEVER log sensitive data.** Use the BC Gov `structured-logging` library and only log safe information.

**Example of Safe Logging:**

```python
# ❌ NEVER DO THIS
# logger.info(f"Password: {password}")
# logger.info(f"JWT token: {token}")

# ✅ ALWAYS DO THIS
logger.info("Authentication successful", extra={
    'user_id': user_info.get('sub'),  # Safe to log
    'endpoint': request.endpoint
})
```

---

## ✅ Testing

### Framework and Coverage

-   **Framework:** Use `pytest` as the primary testing framework.
-   **Coverage:** A minimum of 80% test coverage is required for production deployments.
-   **Markers:** Use `@pytest.mark.unit` and `@pytest.mark.integration` to distinguish test types.
-   **Parallelism:** Use `pytest-xdist` for faster, parallel test execution.

### Mocks and Utilities

-   **Mocking:** Mock all external services, including GCP Pub/Sub and notification providers.
-   **Test Utilities:** Use `pytest-mock`, `faker`, and `freezegun` for comprehensive and reliable tests.

---

## 📁 Key Files and Integration Points

### Key Configuration Files

-   `pyproject.toml`: Project dependencies, `pytest` configuration, and `ruff` settings.
-   `src/notify_api/config.py`: Environment-specific configurations.
-   `migrations/`: Alembic database migrations.
-   `tests/conftest.py`: Shared test fixtures and mocks.
-   `run_local.sh`: Local development startup script.

### External Dependencies

-   **Google Cloud Pub/Sub:** Message queuing.
-   **Google Cloud SQL:** PostgreSQL database with IAM authentication.
-   **BC Gov OIDC:** Keycloak-based authentication.
-   **Provider APIs:** GC Notify, SMTP servers, and the Housing service.

---

## 🤖 AI Assistant Guidelines

### Communication Style

-   **Be Concise:** Provide direct and actionable responses.
-   **Be Context-Aware:** Always consider the dual-microservice architecture.
-   **Prioritize Security:** Adhere strictly to BC Government security requirements.
-   **Ask for Clarity:** Do not make assumptions about ambiguous requests.

### Code Generation

-   **Use Type Hints:** All generated code must include proper type hints.
-   **Handle Errors:** Implement guard clauses and early returns.
-   **Use Approved Libraries:** Only use the approved technology stack (Pydantic, HTTPX, etc.).
-   **Log Safely:** Never generate code that logs sensitive information.

### Workflow and Best Practices

-   **Write Tests:** Suggest `pytest` tests with appropriate markers.
-   **Use `uv`:** All commands for dependency management and scripts must use `uv`.
-   **Aim for Coverage:** Target 80%+ test coverage.
-   **Handle Migrations Safely:** Remind users to set `DEPLOYMENT_ENV=migration` for database changes.