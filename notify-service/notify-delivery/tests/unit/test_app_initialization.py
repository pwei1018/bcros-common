import unittest
from unittest.mock import Mock, patch

from cloud_sql_connector import DBConfig
from flask import Flask

from notify_delivery import create_app


class TestAppInitialization(unittest.TestCase):
    """Test suite for app initialization and configuration."""

    def test_create_app_basic(self):
        """Test basic app creation."""
        with (
            patch("notify_delivery.config") as mock_config,
            patch("notify_delivery.db") as mock_db,
            patch("notify_delivery.queue") as mock_queue,
            patch("notify_delivery.register_endpoints") as mock_register,
            patch("notify_delivery.setup_search_path_event_listener"),
            patch("notify_delivery.setup_pg8000_close_event_listener") as mock_setup_pg8000_listener,
        ):
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
            app = create_app("testing")

            # Assert
            assert isinstance(app, Flask)
            assert app.config is not None
            mock_db.init_app.assert_called_once_with(app)
            mock_queue.init_app.assert_called_once_with(app)
            mock_register.assert_called_once_with(app)
            mock_setup_pg8000_listener.assert_called_once_with(mock_engine)

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

    @patch("notify_delivery.setup_search_path_event_listener")
    @patch("notify_delivery.setup_pg8000_close_event_listener")
    def test_create_app_with_gcp_database_connection(self, mock_setup_pg8000_listener, mock_setup_search_path_event_listener):
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
                    "DB_SCHEMA": "test_schema",
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
            mock_setup_pg8000_listener.assert_called_once_with(mock_engine)
            mock_setup_search_path_event_listener.assert_called_once_with(mock_engine, "test_schema")

    def test_create_app_with_schema_checkout_event(self):
        """Test app creation with schema checkout event listener."""
        with (
            patch("notify_delivery.config") as mock_config,
            patch("notify_delivery.db") as mock_db,
            patch("notify_delivery.queue"),
            patch("notify_delivery.register_endpoints"),
            patch("notify_delivery.setup_search_path_event_listener") as mock_setup_event_listener,
            patch("notify_delivery.setup_pg8000_close_event_listener") as mock_setup_pg8000_listener,
        ):
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
            create_app("testing")

            # Assert - verify the connect event listener was registered
            mock_setup_event_listener.assert_called_once_with(mock_engine, "test_schema")
            mock_setup_pg8000_listener.assert_called_once_with(mock_engine)

