# Copyright © 2019 Province of British Columbia
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
"""The Notify API service.

This module is the API for the BC Registries Notify application.
"""

from cloud_sql_connector import DBConfig, setup_pg8000_close_event_listener, setup_search_path_event_listener
from flask import Flask
from flask_cors import CORS
from flask_migrate import Migrate, upgrade
from structured_logging import StructuredLogging

from notify_api import models
from notify_api.config import config
from notify_api.exceptions import ExceptionHandler
from notify_api.metadata import APP_RUNNING_ENVIRONMENT
from notify_api.models import db
from notify_api.resources import meta_endpoint, ops_endpoint, v1_endpoint, v2_endpoint
from notify_api.services.gcp_queue import queue
from notify_api.utils.auth import jwt
from notify_api.utils.util import describe_database_target, log_sidecar_connection_evidence

logger = StructuredLogging.get_logger()


def create_app(run_mode: str = APP_RUNNING_ENVIRONMENT) -> Flask:
    """Return a configured Flask App using the Factory method."""
    app = Flask(__name__)
    app.config.from_object(config[run_mode])
    app.url_map.strict_slashes = False

    CORS(app, resources="*")

    schema = app.config.get("DB_SCHEMA", "public")

    db_mode, db_safe_dsn = describe_database_target(app)
    logger.info("Database connection mode: %s", db_mode)
    logger.debug("Database target (password hidden): %s", db_safe_dsn)

    if app.config["DB_INSTANCE_CONNECTION_NAME"] and not app.config.get("CLOUD_SQL_PROXY_SIDECAR", False):
        db_config = DBConfig(
            instance_name=app.config["DB_INSTANCE_CONNECTION_NAME"],
            database=app.config["DB_NAME"],
            user=app.config["DB_USER"],
            ip_type=app.config["DB_IP_TYPE"],
            schema=schema if run_mode != "migration" else None,
            enable_iam_auth=True,
            driver="pg8000",
            # Connection pool configuration
            pool_size=app.config.get("DB_POOL_SIZE", 10),
            max_overflow=app.config.get("DB_MAX_OVERFLOW", 10),
            pool_timeout=app.config.get("DB_POOL_TIMEOUT", 30),
            pool_recycle=app.config.get("DB_POOL_RECYCLE", 1800),
            pool_pre_ping=True,
            connect_args={"check_same_thread": False, "connect_timeout": app.config.get("DB_CONNECT_TIMEOUT", 60)},
        )

        # Use the cloud-sql-connector's built-in engine options
        app.config["SQLALCHEMY_ENGINE_OPTIONS"] = db_config.get_engine_options()
    elif app.config.get("CLOUD_SQL_PROXY_SIDECAR", False):
        # The Cloud SQL Auth Proxy sidecar exposes a plain psycopg TCP endpoint on
        # localhost, so SQLAlchemy builds its default QueuePool. Configure it
        # explicitly here — otherwise pool_pre_ping and pool_recycle default to off
        # and the pool can hand out connections the proxy has already dropped
        # (idle timeout, proxy restart), failing the next request.
        app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
            "pool_size": app.config.get("DB_POOL_SIZE", 10),
            "max_overflow": app.config.get("DB_MAX_OVERFLOW", 10),
            "pool_timeout": app.config.get("DB_POOL_TIMEOUT", 30),
            "pool_recycle": app.config.get("DB_POOL_RECYCLE", 1800),
            "pool_pre_ping": True,
            "connect_args": {"connect_timeout": app.config.get("DB_CONNECT_TIMEOUT", 60)},
        }

    db.init_app(app)

    if run_mode != "migration":
        with app.app_context():
            engine = db.engine

            # Set the search path for the configured schema. This generic listener
            # applies to both the cloud-sql-connector and the Cloud SQL Auth Proxy
            # sidecar (plain pg8000) connections.
            if schema and app.config["DB_INSTANCE_CONNECTION_NAME"]:
                setup_search_path_event_listener(engine, schema)

            # Suppress pg8000 InterfaceError on connection close during teardown
            setup_pg8000_close_event_listener(engine)

            # When using the Cloud SQL Auth Proxy sidecar, log one-time evidence
            # (localhost socket peer + server-side session info) confirming the
            # connection is tunneled through the proxy.
            if app.config.get("CLOUD_SQL_PROXY_SIDECAR", False):
                log_sidecar_connection_evidence(engine, app.config.get("DB_PORT", "5432"))

    if run_mode == "migration":
        Migrate(app, db)
        logger.info("Running migration upgrade.")
        with app.app_context():
            if app.config.get("CLOUD_SQL_PROXY_SIDECAR", False):
                log_sidecar_connection_evidence(db.engine, app.config.get("DB_PORT", "5432"))
            upgrade(directory="migrations", revision="head", sql=False, tag=None)
        logger.info("Finished migration upgrade.")
    else:
        queue.init_app(app)
        meta_endpoint.init_app(app)
        ops_endpoint.init_app(app)
        v1_endpoint.init_app(app)
        v2_endpoint.init_app(app)

        # Swagger UI
        from flask_swagger_ui import get_swaggerui_blueprint

        swagger_url = "/docs"
        api_url = "/static/openapi.yaml"
        swaggerui_blueprint = get_swaggerui_blueprint(
            swagger_url,
            api_url,
            config={"app_name": "BC Registries Notify API"},
        )
        app.register_blueprint(swaggerui_blueprint, url_prefix=swagger_url)

        ExceptionHandler(app)
        setup_jwt_manager(app, jwt)
        register_shellcontext(app)

    return app


def setup_jwt_manager(app, jwt_manager):
    """Use flask app to configure the JWTManager to work for a particular Realm."""

    def get_roles(a_dict):
        return a_dict["realm_access"]["roles"]  # pragma: no cover

    app.config["JWT_ROLE_CALLBACK"] = get_roles

    jwt_manager.init_app(app)


def register_shellcontext(app):
    """Register shell context objects."""

    def shell_context():
        """Shell context objects."""
        return {"app": app, "jwt": jwt, "db": db, "models": models}  # pragma: no cover

    app.shell_context_processor(shell_context)
