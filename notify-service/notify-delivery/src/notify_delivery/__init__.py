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

from dataclasses import dataclass

from flask import Flask
from google.cloud.sql.connector import Connector
from notify_api.models import db
from sqlalchemy import event
from structured_logging import StructuredLogging

from notify_delivery.config import config
from notify_delivery.metadata import APP_RUNNING_ENVIRONMENT
from notify_delivery.resources import register_endpoints
from notify_delivery.services.gcp_queue import queue

logger = StructuredLogging.get_logger()


@dataclass
class DBConfig:
    """Database configuration settings."""

    instance_name: str
    database: str
    user: str
    ip_type: str
    schema: str



def getconn(connector: Connector, db_config: DBConfig) -> object:
    """Create a database connection.

    Args:
        connector (Connector): The Google Cloud SQL connector instance.
        db_config (DBConfig): The database configuration.

    Returns:
        object: A connection object to the database.
    """
    conn = connector.connect(
        instance_connection_string=db_config.instance_name,
        db=db_config.database,
        user=db_config.user,
        ip_type=db_config.ip_type,
        driver="pg8000",
        enable_iam_auth=True,
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
    schema = app.config.get("DB_SCHEMA", None)

    if app.config["DB_INSTANCE_CONNECTION_NAME"]:
        connector = Connector(refresh_strategy="lazy")
        db_config = DBConfig(
            instance_name=app.config["DB_INSTANCE_CONNECTION_NAME"],
            database=app.config["DB_NAME"],
            user=app.config["DB_USER"],
            ip_type=app.config["DB_IP_TYPE"],
            schema=schema
        )
        app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {"creator": lambda: getconn(connector, db_config)}

    db.init_app(app)

    with app.app_context():
        engine = db.engine
        @event.listens_for(engine, "checkout")
        def set_search_path_on_checkout(dbapi_connection, connection_record, connection_proxy):
            cursor = dbapi_connection.cursor()
            cursor.execute(f"SET search_path TO {schema},public")
            cursor.close()

    queue.init_app(app)

    register_endpoints(app)

    return app
