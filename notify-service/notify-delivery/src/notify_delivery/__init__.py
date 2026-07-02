# Copyright © 2024 Province of British Columbia
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""The Reconciliations queue service.

The service worker for applying payments, receipts and account balance to payment system.
"""

from __future__ import annotations

from cloud_sql_connector import DBConfig, setup_pg8000_close_event_listener, setup_search_path_event_listener
from flask import Flask
from notify_api.models import db
from structured_logging import StructuredLogging

from notify_delivery.config import config
from notify_delivery.metadata import APP_RUNNING_ENVIRONMENT
from notify_delivery.resources import register_endpoints
from notify_delivery.services.gcp_queue import queue
from notify_delivery.utils.util import describe_database_target, log_sidecar_connection_evidence

logger = StructuredLogging.get_logger()


def create_app(run_mode: str = APP_RUNNING_ENVIRONMENT) -> Flask:
    """Return a configured Flask App using the Factory method."""
    app = Flask(__name__)
    app.config.from_object(config[run_mode])

    schema = app.config.get("DB_SCHEMA", "public")
    db_instance_connection_name = app.config.get("DB_INSTANCE_CONNECTION_NAME")
    cloud_sql_proxy_sidecar = app.config.get("CLOUD_SQL_PROXY_SIDECAR", False)

    db_mode, db_safe_dsn = describe_database_target(app)
    logger.info("Database connection mode: %s", db_mode)
    logger.debug("Database target (password hidden): %s", db_safe_dsn)

    # The Cloud SQL Auth Proxy sidecar terminates IAM auth on localhost, so the
    # cloud-sql-connector (and its pg8000 creator) must be bypassed in that mode.
    if db_instance_connection_name and not cloud_sql_proxy_sidecar:
        db_config = DBConfig(
            instance_name=db_instance_connection_name,
            database=app.config.get("DB_NAME"),
            user=app.config.get("DB_USER"),
            ip_type=app.config.get("DB_IP_TYPE"),
            enable_iam_auth=True,
            driver="pg8000",
            schema=schema,
            # Connection pool configuration
            pool_size=app.config.get("DB_POOL_SIZE", 10),
            max_overflow=app.config.get("DB_MAX_OVERFLOW", 10),
            pool_timeout=app.config.get("DB_POOL_TIMEOUT", 30),
            pool_recycle=app.config.get("DB_POOL_RECYCLE", 300),
            pool_pre_ping=True,
        )

        # Use the cloud-sql-connector's built-in engine options
        app.config["SQLALCHEMY_ENGINE_OPTIONS"] = db_config.get_engine_options()
    elif cloud_sql_proxy_sidecar:
        # The Cloud SQL Auth Proxy sidecar exposes a plain psycopg TCP endpoint on
        # localhost, so SQLAlchemy builds its default QueuePool. Configure it
        # explicitly here — otherwise pool_pre_ping and pool_recycle default to off
        # and the pool can hand out connections the proxy has already dropped
        # (idle timeout, proxy restart), failing the next request.
        app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
            "pool_size": app.config.get("DB_POOL_SIZE", 10),
            "max_overflow": app.config.get("DB_MAX_OVERFLOW", 10),
            "pool_timeout": app.config.get("DB_POOL_TIMEOUT", 30),
            "pool_recycle": app.config.get("DB_POOL_RECYCLE", 300),
            "pool_pre_ping": True,
            "connect_args": {"connect_timeout": app.config.get("DB_CONNECT_TIMEOUT", 60)},
        }

    db.init_app(app)

    with app.app_context():
        engine = db.engine

        # Set the search path for the configured schema. This generic listener
        # applies to both the cloud-sql-connector and the Cloud SQL Auth Proxy
        # sidecar connections.
        if schema and db_instance_connection_name:
            setup_search_path_event_listener(engine, schema)

        # Suppress pg8000 InterfaceError on connection close during teardown
        setup_pg8000_close_event_listener(engine)

        # When using the Cloud SQL Auth Proxy sidecar, log one-time evidence
        # (localhost socket peer + server-side session info) confirming the
        # connection is tunneled through the proxy.
        if cloud_sql_proxy_sidecar:
            log_sidecar_connection_evidence(engine, app.config.get("DB_PORT", "5432"))

    queue.init_app(app)

    register_endpoints(app)

    return app
