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

from dataclasses import dataclass

from flask import Flask
from flask_cors import CORS
from google.cloud.sql.connector import Connector
from sqlalchemy import event
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


@dataclass
class DBConfig:
    """Database configuration settings."""

    instance_name: str
    database: str
    user: str
    ip_type: str
    schema: str


def getconn(db_config: DBConfig) -> object:
    """Create a database connection.

    Args:
        db_config (DBConfig): The database configuration.

    Returns:
        object: A connection object to the database.
    """
    with Connector(refresh_strategy="lazy") as connector:
        conn = connector.connect(
            instance_connection_string=db_config.instance_name,
            db=db_config.database,
            user=db_config.user,
            ip_type=db_config.ip_type,
            driver="pg8000",
            enable_iam_auth=True
        )

        if db_config.schema:
            cursor = conn.cursor()
            cursor.execute(f"SET search_path TO {db_config.schema},public")
            cursor.execute(f"SET LOCAL search_path TO {db_config.schema}, public;")
            cursor.close()

        return conn


def create_app(run_mode=APP_RUNNING_ENVIRONMENT):
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
            ip_type="private",
            schema=schema if run_mode != "migration" else None
        )

        app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
            "creator": lambda: getconn(db_config),
            "pool_pre_ping": True,
            "pool_recycle": 300
        }

    db.init_app(app)

    if run_mode != "migration":
        with app.app_context():
            engine = db.engine
            @event.listens_for(engine, "checkout")
            def set_search_path_on_checkout(dbapi_connection, connection_record, connection_proxy):
                cursor = dbapi_connection.cursor()
                cursor.execute(f"SET search_path TO {schema},public")
                cursor.close()

    if run_mode == "migration":
        from flask_migrate import Migrate, upgrade

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