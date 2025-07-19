# Copyright © 2022 Province of British Columbia
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
"""Test suite for app initialization and database connection."""

import unittest
from unittest.mock import Mock, patch

import pytest
from flask import Flask

from notify_delivery import DBConfig, create_app


class TestAppInitialization(unittest.TestCase):
    """Test suite for app initialization and configuration."""

    @patch("notify_delivery.event")
    @patch("notify_delivery.register_endpoints")
    @patch("notify_delivery.queue")
    @patch("notify_delivery.db")
    @patch("notify_delivery.config")
    def test_create_app_basic(self, mock_config, mock_db, mock_queue, mock_register, mock_event):
        """Test basic app creation."""
        # Arrange
        mock_config_obj = Mock()
        mock_config_obj.configure_mock(
            **{
                "get.return_value": None,
                "DB_INSTANCE_CONNECTION_NAME": None,
                "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            }
        )
        mock_config.__getitem__.return_value = mock_config_obj

        # Mock the SQLAlchemy engine and event system
        mock_engine = Mock()
        mock_db.engine = mock_engine
        mock_event.listens_for.return_value = lambda f: f  # Mock decorator

        # Act
        app = create_app("testing")

        # Assert
        assert isinstance(app, Flask)
        assert app.config is not None
        mock_db.init_app.assert_called_once_with(app)
        mock_queue.init_app.assert_called_once_with(app)
        mock_register.assert_called_once_with(app)

    def test_db_config_creation(self):
        """Test DBConfig dataclass creation."""
        # Act
        db_config = DBConfig(
            instance_name="test-instance", database="test_db", user="test_user", ip_type="private", schema="test_schema"
        )

        # Assert
        assert db_config.instance_name == "test-instance"
        assert db_config.database == "test_db"
        assert db_config.user == "test_user"
        assert db_config.ip_type == "private"
        assert db_config.schema == "test_schema"

    def test_db_config_optional_schema(self):
        """Test DBConfig with optional schema."""
        # Act
        db_config = DBConfig(
            instance_name="test-instance", database="test_db", user="test_user", ip_type="private", schema=None
        )

        # Assert
        assert db_config.schema is None

    def test_create_app_with_gcp_database_connection(self):
        """Test app creation with GCP database connection."""
        with (
            patch("notify_delivery.Connector") as mock_connector_class,
            patch("notify_delivery.config") as mock_config,
            patch("notify_delivery.db") as mock_db,
            patch("notify_delivery.queue"),
            patch("notify_delivery.register_endpoints"),
            patch("notify_delivery.event") as mock_event,
        ):
            # Arrange
            mock_config_obj = Mock()
            mock_config_obj.configure_mock(
                **{
                    "get.side_effect": lambda key, default=None: {
                        "DB_INSTANCE_CONNECTION_NAME": "test-project:region:instance",
                        "DB_NAME": "test_db",
                        "DB_USER": "test_user",
                        "DB_IP_TYPE": "private",
                        "DB_SCHEMA": "test_schema",
                    }.get(key, default),
                    "DB_INSTANCE_CONNECTION_NAME": "test-project:region:instance",
                    "DB_NAME": "test_db",
                    "DB_USER": "test_user",
                    "DB_IP_TYPE": "private",
                    "SQLALCHEMY_DATABASE_URI": "postgresql://user:pass@localhost/db",
                }
            )
            mock_config.__getitem__.return_value = mock_config_obj

            # Mock connector and database components
            mock_connector = Mock()
            mock_connector_class.return_value = mock_connector
            mock_engine = Mock()
            mock_db.engine = mock_engine
            mock_event.listens_for.return_value = lambda f: f

            # Act
            app = create_app("testing")

            # Assert
            assert isinstance(app, Flask)
            mock_connector_class.assert_called_once_with(refresh_strategy="lazy")
            assert "SQLALCHEMY_ENGINE_OPTIONS" in app.config
            mock_db.init_app.assert_called_once_with(app)
            mock_event.listens_for.assert_called_once()

    @patch("notify_delivery.config")
    @patch("notify_delivery.db")
    @patch("notify_delivery.queue")
    @patch("notify_delivery.register_endpoints")
    @patch("notify_delivery.event")
    def test_create_app_with_schema_checkout_event(self, mock_event, mock_register, mock_queue, mock_db, mock_config):
        """Test app creation with schema checkout event listener."""
        # Arrange
        mock_config_obj = Mock()
        mock_config_obj.configure_mock(
            **{
                "get.side_effect": lambda key, default=None: {"DB_SCHEMA": "test_schema"}.get(key, default),
                "DB_INSTANCE_CONNECTION_NAME": None,
                "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            }
        )
        mock_config.__getitem__.return_value = mock_config_obj

        # Mock the SQLAlchemy engine and event system
        mock_engine = Mock()
        mock_db.engine = mock_engine

        # Track the event listener function
        captured_listener = None

        def capture_listener(engine, event_name):
            def decorator(func):
                nonlocal captured_listener
                captured_listener = func
                return func

            return decorator

        mock_event.listens_for.side_effect = capture_listener

        # Act
        app = create_app("testing")

        # Assert
        assert isinstance(app, Flask)
        assert captured_listener is not None
        mock_event.listens_for.assert_called_once_with(mock_engine, "checkout")

    def test_getconn_with_schema(self):
        """Test database connection with schema configuration."""
        # Arrange
        mock_connector = Mock()
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_connection.cursor.return_value = mock_cursor
        mock_connector.connect.return_value = mock_connection

        db_config = DBConfig(
            instance_name="test-instance", database="test_db", user="test_user", ip_type="private", schema="test_schema"
        )

        # Import and call the function being tested
        from notify_delivery import getconn

        # Act
        result = getconn(mock_connector, db_config)

        # Assert
        assert result == mock_connection
        mock_connector.connect.assert_called_once_with(
            instance_connection_string="test-instance",
            db="test_db",
            user="test_user",
            ip_type="private",
            driver="pg8000",
            enable_iam_auth=True,
        )
        mock_cursor.execute.assert_any_call("SET search_path TO test_schema,public")
        mock_cursor.execute.assert_any_call("SET LOCAL search_path TO test_schema, public;")
        mock_cursor.close.assert_called_once()

    def test_getconn_without_schema(self):
        """Test database connection without schema configuration."""
        # Arrange
        mock_connector = Mock()
        mock_connection = Mock()
        mock_connector.connect.return_value = mock_connection

        db_config = DBConfig(
            instance_name="test-instance", database="test_db", user="test_user", ip_type="private", schema=None
        )

        # Import and call the function being tested
        from notify_delivery import getconn

        # Act
        result = getconn(mock_connector, db_config)

        # Assert
        assert result == mock_connection
        mock_connector.connect.assert_called_once()
        # Should not call cursor operations when schema is None
        mock_connection.cursor.assert_not_called()
