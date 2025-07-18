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

from cloud_sql_connector import setup_search_path_event_listener
from flask import Flask
from notify_api.models import db
from structured_logging import StructuredLogging

from notify_delivery.config import config
from notify_delivery.metadata import APP_RUNNING_ENVIRONMENT
from notify_delivery.resources import register_endpoints
from notify_delivery.services.gcp_queue import queue

logger = StructuredLogging.get_logger()


def create_app(run_mode=APP_RUNNING_ENVIRONMENT):
    """Return a configured Flask App using the Factory method."""
    app = Flask(__name__)
    app.config.from_object(config[run_mode])
    schema = app.config.get("DB_SCHEMA", None)

    # Use SQLALCHEMY_ENGINE_OPTIONS from config if using cloud-sql-connector
    if hasattr(app.config, "SQLALCHEMY_ENGINE_OPTIONS") and app.config.SQLALCHEMY_ENGINE_OPTIONS:
        # Cloud SQL connection using cloud-sql-connector (configured in config.py)
        pass
    else:
        # Fallback to default engine options for direct connections
        app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
            "pool_pre_ping": True,
            "pool_recycle": 3600,
            "pool_size": 10,
            "max_overflow": 10,
            "pool_timeout": 30,
            "connect_args": {"check_same_thread": False, "connect_timeout": 60},
        }

    db.init_app(app)

    # Set up schema search path event listener if schema is configured
    if schema:
        with app.app_context():
            engine = db.engine
            setup_search_path_event_listener(engine, schema)

    queue.init_app(app)

    register_endpoints(app)

    return app
