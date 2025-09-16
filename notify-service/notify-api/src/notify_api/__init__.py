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

from cloud_sql_connector import DBConfig, setup_search_path_event_listener
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

logger = StructuredLogging.get_logger()


def create_app(run_mode: str = APP_RUNNING_ENVIRONMENT) -> Flask:
    """Return a configured Flask App using the Factory method."""
    app = Flask(__name__)
    app.config.from_object(config[run_mode])
    app.url_map.strict_slashes = False

    CORS(app, resources="*")

    schema = app.config.get("DB_SCHEMA", "public")

    if app.config["DB_INSTANCE_CONNECTION_NAME"]:
        db_config = DBConfig(
            instance_name=app.config["DB_INSTANCE_CONNECTION_NAME"],
            database=app.config["DB_NAME"],
            user=app.config["DB_USER"],
            ip_type=app.config["DB_IP_TYPE"],
            schema=schema if run_mode != "migration" else None,
            enable_iam_auth=True,
            driver="pg8000",
            # Connection pool configuration
            pool_size=10,
            max_overflow=10,
            pool_timeout=30,
            pool_recycle=3600,  # 1 hour
            pool_pre_ping=True,
            connect_args={"check_same_thread": False, "connect_timeout": 60},
        )

        # Use the cloud-sql-connector's built-in engine options
        app.config["SQLALCHEMY_ENGINE_OPTIONS"] = db_config.get_engine_options()

    db.init_app(app)

    if run_mode != "migration":
        with app.app_context():
            engine = db.engine

            # Use the cloud-sql-connector's search path event listener
            if schema and app.config["DB_INSTANCE_CONNECTION_NAME"]:
                setup_search_path_event_listener(engine, schema)

    if run_mode == "migration":
        Migrate(app, db)
        logger.info("Running migration upgrade.")
        with app.app_context():
            upgrade(directory="migrations", revision="head", sql=False, tag=None)
        logger.info("Finished migration upgrade.")
    else:
        queue.init_app(app)
        meta_endpoint.init_app(app)
        ops_endpoint.init_app(app)
        v1_endpoint.init_app(app)
        v2_endpoint.init_app(app)

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
