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

from cloud_sql_connector import DBConfig
from flask import Flask
from pg8000.exceptions import InterfaceError

from notify_delivery import create_app


class TestAppInitialization(unittest.TestCase):
    """Test suite for app initialization and configuration."""

    @patch("notify_delivery.setup_search_path_event_listener")
    @patch("notify_delivery.register_endpoints")
    @patch("notify_delivery.queue")
    @patch("notify_delivery.db")
    @patch("notify_delivery.config")
    def test_create_app_basic(self, mock_config, mock_db, mock_queue, mock_register, mock_setup_event_listener):
        """Test basic app creation."""
        # Arrange
        mock_config_obj = Mock()
        mock_config_obj.configure_mock(
            **{
                "get.return_value": None,
                "DB_INSTANCE_CONNECTION_NAME": None,
                "DB_USER": "test_user",
                "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            }
        )
        mock_config.__getitem__.return_value = mock_config_obj

        # Mock the SQLAlchemy engine
        mock_engine = Mock()
        mock_db.engine = mock_engine

        # Act
        with patch("notify_delivery.event.listens_for"):
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
            instance_name="test-instance",
            database="test_db",
            user="test_user",
            ip_type="private",
            schema="test_schema",
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

    @patch("sqlalchemy.event.listens_for")
    def test_create_app_with_gcp_database_connection(self, mock_listens_for):
        """Test app creation with GCP database connection configuration."""
        with (
            patch("notify_delivery.config") as mock_config,
            patch("notify_delivery.db") as mock_db,
            patch("notify_delivery.queue"),
            patch("notify_delivery.register_endpoints"),
        ):
            # Arrange - Mock config object with SQLALCHEMY_ENGINE_OPTIONS already set by cloud-sql-connector
            mock_config_obj = Mock()
            mock_config_obj.configure_mock(
                **{
                    "DB_INSTANCE_CONNECTION_NAME": "test-project:region:instance",
                    "DB_NAME": "test_db",
                    "DB_USER": "test_user",
                    "DB_IP_TYPE": "private",
                    "SQLALCHEMY_DATABASE_URI": "postgresql://user:pass@localhost/db",
                    "SQLALCHEMY_ENGINE_OPTIONS": {"creator": Mock()},  # Mock engine options from cloud-sql-connector
                }
            )
            mock_config.__getitem__.return_value = mock_config_obj

            # Mock database components
            mock_engine = Mock()
            mock_db.engine = mock_engine

            # Act
            app = create_app("testing")

            # Assert
            assert isinstance(app, Flask)
            assert "SQLALCHEMY_ENGINE_OPTIONS" in app.config
            mock_db.init_app.assert_called_once_with(app)

    @patch("notify_delivery.setup_search_path_event_listener")
    @patch("notify_delivery.register_endpoints")
    @patch("notify_delivery.queue")
    @patch("notify_delivery.db")
    @patch("notify_delivery.config")
    def test_create_app_with_schema_checkout_event(
        self, mock_config, mock_db, mock_queue, mock_register, mock_setup_event_listener
    ):
        """Test app creation with schema checkout event listener."""
        # Arrange
        mock_config_obj = Mock()
        mock_config_obj.configure_mock(
            **{
                "DB_SCHEMA": "test_schema",  # Set the schema attribute
                "DB_INSTANCE_CONNECTION_NAME": "test-project:region:instance",
                "DB_USER": "test_user",
                "DB_NAME": "test_db",
                "DB_IP_TYPE": "private",
                "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            }
        )
        mock_config.__getitem__.return_value = mock_config_obj

        # Mock the SQLAlchemy engine
        mock_engine = Mock()
        mock_db.engine = mock_engine

        # Act
        with patch("notify_delivery.event.listens_for") as mock_listens_for:
            create_app("testing")

        # Assert - verify the connect event listener was registered
        mock_listens_for.assert_any_call(mock_engine, "connect")
        mock_setup_event_listener.assert_called_once_with(mock_engine, "test_schema")


class TestSafeCloseWrapper(unittest.TestCase):
    """Test suite for the dbapi connection close() wrapper registered via event.listens_for."""

    @patch("notify_delivery.setup_search_path_event_listener")
    @patch("notify_delivery.register_endpoints")
    @patch("notify_delivery.queue")
    @patch("notify_delivery.db")
    @patch("notify_delivery.config")
    def test_connect_listener_wraps_close_and_suppresses_interface_error(
        self, mock_config, mock_db, mock_queue, mock_register, mock_setup_event_listener
    ):
        """Test that the on_connect listener wraps close() to suppress InterfaceError."""
        # Arrange
        mock_config_obj = Mock()
        mock_config_obj.configure_mock(
            **{
                "get.return_value": None,
                "DB_INSTANCE_CONNECTION_NAME": None,
                "DB_USER": "test_user",
                "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            }
        )
        mock_config.__getitem__.return_value = mock_config_obj
        mock_engine = Mock()
        mock_db.engine = mock_engine

        # Capture the on_connect listener
        captured_listener = None

        def capture_listens_for(target, event_name):
            def decorator(fn):
                nonlocal captured_listener
                if event_name == "connect":
                    captured_listener = fn
                return fn

            return decorator

        with patch("notify_delivery.event.listens_for", side_effect=capture_listens_for):
            create_app("testing")

        assert captured_listener is not None, "on_connect listener was not registered"

        # Simulate a connection whose close() raises InterfaceError
        mock_dbapi_conn = Mock()
        original_close = Mock(side_effect=InterfaceError("connection is closed"))
        mock_dbapi_conn.close = original_close

        captured_listener(mock_dbapi_conn, Mock())

        # After wrapping, calling close() should suppress InterfaceError
        mock_dbapi_conn.close()
        original_close.assert_called_once()

    @patch("notify_delivery.setup_search_path_event_listener")
    @patch("notify_delivery.register_endpoints")
    @patch("notify_delivery.queue")
    @patch("notify_delivery.db")
    @patch("notify_delivery.config")
    def test_connect_listener_propagates_non_interface_errors(
        self, mock_config, mock_db, mock_queue, mock_register, mock_setup_event_listener
    ):
        """Test that non-InterfaceError exceptions are not suppressed."""
        # Arrange
        mock_config_obj = Mock()
        mock_config_obj.configure_mock(
            **{
                "get.return_value": None,
                "DB_INSTANCE_CONNECTION_NAME": None,
                "DB_USER": "test_user",
                "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            }
        )
        mock_config.__getitem__.return_value = mock_config_obj
        mock_engine = Mock()
        mock_db.engine = mock_engine

        captured_listener = None

        def capture_listens_for(target, event_name):
            def decorator(fn):
                nonlocal captured_listener
                if event_name == "connect":
                    captured_listener = fn
                return fn

            return decorator

        with patch("notify_delivery.event.listens_for", side_effect=capture_listens_for):
            create_app("testing")

        assert captured_listener is not None

        # Simulate a connection whose close() raises a non-InterfaceError
        mock_dbapi_conn = Mock()
        mock_dbapi_conn.close = Mock(side_effect=RuntimeError("unexpected"))

        captured_listener(mock_dbapi_conn, Mock())

        with self.assertRaises(RuntimeError):
            mock_dbapi_conn.close()
