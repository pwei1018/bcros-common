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

from cloud_sql_connector import DBConfig, setup_search_path_event_listener
from flask import Flask
from notify_api.models import db
from structured_logging import StructuredLogging

from notify_delivery.config import config
from notify_delivery.metadata import APP_RUNNING_ENVIRONMENT
from notify_delivery.resources import register_endpoints
from notify_delivery.services.gcp_queue import queue

logger = StructuredLogging.get_logger()


def create_app(run_mode: str = APP_RUNNING_ENVIRONMENT) -> Flask:
    """Return a configured Flask App using the Factory method."""
    app = Flask(__name__)
    app.config.from_object(config[run_mode])

    db_user = app.config["DB_USER"]
    logger.info(db_user)

    db_instance_connection_name = app.config.get("DB_INSTANCE_CONNECTION_NAME")
    logger.info(f"DB_INSTANCE_CONNECTION_NAME: {db_instance_connection_name}")

    if db_instance_connection_name:
        db_config = DBConfig(
            instance_name=app.config["DB_INSTANCE_CONNECTION_NAME"],
            database=app.config["DB_NAME"],
            user=app.config["DB_USER"],
            ip_type=app.config["DB_IP_TYPE"],
            enable_iam_auth=True,
            driver="pg8000",
            # Connection pool configuration
            pool_size=10,
            max_overflow=10,
            pool_timeout=30,
            pool_recycle=300,
            pool_use_lifo=True,
            pool_pre_ping=True,
        )

        # Use the cloud-sql-connector's built-in engine options
        app.config["SQLALCHEMY_ENGINE_OPTIONS"] = db_config.get_engine_options()

    db.init_app(app)

    with app.app_context():
        engine = db.engine

        # Use the cloud-sql-connector's search path event listener
        schema = app.config.get("DB_SCHEMA", "public")
        if schema and app.config["DB_INSTANCE_CONNECTION_NAME"]:
            setup_search_path_event_listener(engine, schema)

    queue.init_app(app)

    register_endpoints(app)

    return app
