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

from flask import Flask
from notify_api.models import db
from structured_logging import StructuredLogging

from notify_delivery.config import config
from notify_delivery.metadata import APP_RUNNING_ENVIRONMENT
from notify_delivery.resources import register_endpoints
from notify_delivery.services.gcp_queue import queue

logger = StructuredLogging.get_logger()


def create_app(service_environment=APP_RUNNING_ENVIRONMENT, **kwargs):
    """Return a configured Flask App using the Factory method."""
    app = Flask(__name__)
    app.config.from_object(config[service_environment])

    if app.config.get("DB_INSTANCE_CONNECTION_NAME"):
        from google.cloud.sql.connector import Connector

        connector = Connector(refresh_strategy="lazy")

        connection = connector.connect(
            app.config["DB_INSTANCE_CONNECTION_NAME"],
            "pg8000",
            ip_type="app.config["DB_IP_TYPE"]",
            db=app.config["DB_NAME"],
            user=app.config["DB_USER"],
            enable_iam_auth=True,
        )

        # configure Flask-SQLAlchemy to use Python Connector
        app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql+pg8000://"
        app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {"creator": lambda: connection}

    db.init_app(app)

    queue.init_app(app)

    register_endpoints(app)

    return app
