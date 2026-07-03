import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from cloud_sql_connector import DBConfig
from flask import Flask

from notify_delivery import create_app
from notify_delivery.utils.util import describe_database_target, log_sidecar_connection_evidence


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
    def test_create_app_with_gcp_database_connection(
        self, mock_setup_pg8000_listener, mock_setup_search_path_event_listener
    ):
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

    def test_create_app_sidecar_skips_cloud_sql_connector(self):
        """Sidecar mode skips the connector but keeps the schema search path and logs evidence."""
        with (
            patch("notify_delivery.config") as mock_config,
            patch("notify_delivery.db") as mock_db,
            patch("notify_delivery.queue"),
            patch("notify_delivery.register_endpoints"),
            patch("notify_delivery.DBConfig") as mock_db_config,
            patch("notify_delivery.log_sidecar_connection_evidence") as mock_log_evidence,
            patch("notify_delivery.setup_search_path_event_listener") as mock_setup_event_listener,
            patch("notify_delivery.setup_pg8000_close_event_listener") as mock_setup_pg8000_listener,
        ):
            # Arrange
            mock_config_obj = Mock()
            mock_config_obj.configure_mock(
                **{
                    "DB_INSTANCE_CONNECTION_NAME": "project:region:instance",
                    "CLOUD_SQL_PROXY_SIDECAR": True,
                    "DB_USER": "test_user",
                    "DB_NAME": "test_db",
                    "DB_IP_TYPE": "private",
                    "DB_PORT": "5432",
                    "SQLALCHEMY_DATABASE_URI": "postgresql+psycopg://test_user@127.0.0.1:5432/test_db",
                }
            )
            mock_config.__getitem__.return_value = mock_config_obj

            mock_engine = Mock()
            mock_db.engine = mock_engine

            # Act
            app = create_app("testing")

            # Assert - connector bypassed, schema + evidence still wired
            assert isinstance(app, Flask)
            mock_db.init_app.assert_called_once_with(app)
            mock_db_config.assert_not_called()
            mock_setup_event_listener.assert_called_once_with(mock_engine, "public")
            mock_setup_pg8000_listener.assert_called_once_with(mock_engine)
            mock_log_evidence.assert_called_once_with(mock_engine, "5432")

            # Sidecar mode still configures an explicit, resilient connection pool.
            assert app.config["SQLALCHEMY_ENGINE_OPTIONS"] == {
                "pool_size": 10,
                "max_overflow": 10,
                "pool_timeout": 30,
                "pool_recycle": 300,
                "pool_pre_ping": True,
                "connect_args": {"connect_timeout": 60},
            }

    def test_create_app_sidecar_honours_configured_pool_settings(self):
        """Sidecar pool options are sourced from the (env-driven) config values."""
        with (
            patch("notify_delivery.config") as mock_config,
            patch("notify_delivery.db") as mock_db,
            patch("notify_delivery.queue"),
            patch("notify_delivery.register_endpoints"),
            patch("notify_delivery.DBConfig") as mock_db_config,
            patch("notify_delivery.log_sidecar_connection_evidence"),
            patch("notify_delivery.setup_search_path_event_listener"),
            patch("notify_delivery.setup_pg8000_close_event_listener"),
        ):
            # Arrange
            mock_config_obj = Mock()
            mock_config_obj.configure_mock(
                **{
                    "DB_INSTANCE_CONNECTION_NAME": "project:region:instance",
                    "CLOUD_SQL_PROXY_SIDECAR": True,
                    "DB_USER": "test_user",
                    "DB_NAME": "test_db",
                    "DB_IP_TYPE": "private",
                    "DB_PORT": "5432",
                    "DB_POOL_SIZE": 3,
                    "DB_MAX_OVERFLOW": 7,
                    "DB_POOL_TIMEOUT": 15,
                    "DB_POOL_RECYCLE": 900,
                    "DB_CONNECT_TIMEOUT": 20,
                    "SQLALCHEMY_DATABASE_URI": "postgresql+psycopg://test_user@127.0.0.1:5432/test_db",
                }
            )
            mock_config.__getitem__.return_value = mock_config_obj

            mock_engine = Mock()
            mock_db.engine = mock_engine

            # Act
            app = create_app("testing")

            # Assert - configured values flow straight into the pool options
            mock_db_config.assert_not_called()
            assert app.config["SQLALCHEMY_ENGINE_OPTIONS"] == {
                "pool_size": 3,
                "max_overflow": 7,
                "pool_timeout": 15,
                "pool_recycle": 900,
                "pool_pre_ping": True,
                "connect_args": {"connect_timeout": 20},
            }


class TestDatabaseConnectionLogging(unittest.TestCase):
    """Test suite for database connection-mode description and sidecar evidence logging."""

    @staticmethod
    def test_describe_target_reports_sidecar_mode():
        """Sidecar flag yields the cloud-sql-proxy-sidecar mode."""
        app = SimpleNamespace(
            config={
                "CLOUD_SQL_PROXY_SIDECAR": True,
                "DB_INSTANCE_CONNECTION_NAME": "proj:region:inst",
                "SQLALCHEMY_DATABASE_URI": "postgresql+psycopg://sa-api%40c4hnrd-dev.iam@127.0.0.1:5432/notify",
            }
        )

        mode, safe_dsn = describe_database_target(app)

        assert mode == "cloud-sql-proxy-sidecar"
        assert "127.0.0.1:5432" in safe_dsn

    @staticmethod
    def test_describe_target_reports_connector_mode():
        """An instance connection name without the sidecar flag yields connector mode."""
        app = SimpleNamespace(
            config={
                "CLOUD_SQL_PROXY_SIDECAR": False,
                "DB_INSTANCE_CONNECTION_NAME": "proj:region:inst",
                "SQLALCHEMY_DATABASE_URI": "postgresql+pg8000://",
            }
        )

        mode, _ = describe_database_target(app)

        assert mode == "cloud-sql-connector"

    @staticmethod
    def test_describe_target_direct_mode_masks_password():
        """Direct mode is reported and the password is never present in the safe DSN."""
        app = SimpleNamespace(
            config={
                "CLOUD_SQL_PROXY_SIDECAR": False,
                "DB_INSTANCE_CONNECTION_NAME": None,
                "SQLALCHEMY_DATABASE_URI": "postgresql+pg8000://user:supersecret@db-host:5432/notify",
            }
        )

        mode, safe_dsn = describe_database_target(app)

        assert mode == "direct"
        assert "supersecret" not in safe_dsn
        assert "***" in safe_dsn

    @staticmethod
    def test_log_sidecar_evidence_registers_connect_listener():
        """The evidence helper registers a SQLAlchemy 'connect' event listener."""
        engine = Mock()

        with patch("notify_delivery.utils.util.event") as mock_event:
            log_sidecar_connection_evidence(engine, "5432")

        mock_event.listens_for.assert_called_once_with(engine, "connect")
