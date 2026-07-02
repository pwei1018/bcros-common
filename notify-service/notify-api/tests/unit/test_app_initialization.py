from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from flask import Flask

from notify_api import create_app
from notify_api.utils.util import describe_database_target, log_sidecar_connection_evidence


class TestAppInitialization(unittest.TestCase):
    """Test suite for app initialization and configuration."""

    @patch("notify_api.setup_pg8000_close_event_listener")
    @patch("notify_api.setup_search_path_event_listener")
    @patch("notify_api.queue")
    @patch("notify_api.db")
    @patch("notify_api.config")
    def test_create_app_basic(
        self, mock_config, mock_db, mock_queue, mock_setup_event_listener, mock_setup_pg8000_listener
    ):
        """Test basic app creation."""
        # Arrange
        mock_config_obj = Mock()
        mock_config_obj.configure_mock(**{
            "get.return_value": None,
            "DB_INSTANCE_CONNECTION_NAME": None,
            "DB_USER": "test_user",
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        })
        mock_config.__getitem__.return_value = mock_config_obj

        # Mock the SQLAlchemy engine
        mock_engine = Mock()
        mock_db.engine = mock_engine

        # Act
        with (
            patch("notify_api.log_sidecar_connection_evidence") as mock_log_evidence,
            patch("notify_api.CORS"),
            patch("notify_api.setup_jwt_manager"),
            patch("notify_api.register_shellcontext"),
            patch("notify_api.ExceptionHandler"),
            patch("notify_api.meta_endpoint"),
            patch("notify_api.ops_endpoint"),
            patch("notify_api.v1_endpoint"),
            patch("notify_api.v2_endpoint"),
        ):
            app = create_app("unitTesting")

        # Assert
        assert isinstance(app, Flask)
        assert app.config is not None
        mock_db.init_app.assert_called_once_with(app)
        mock_queue.init_app.assert_called_once_with(app)
        mock_setup_pg8000_listener.assert_called_once_with(mock_engine)
        mock_log_evidence.assert_not_called()

    @patch("notify_api.setup_pg8000_close_event_listener")
    @patch("notify_api.setup_search_path_event_listener")
    @patch("notify_api.queue")
    @patch("notify_api.db")
    @patch("notify_api.config")
    def test_create_app_sidecar_skips_cloud_sql_connector(
        self,
        mock_config,
        mock_db,
        mock_queue,
        mock_setup_event_listener,
        mock_setup_pg8000_listener,
    ):
        """Sidecar mode skips connector engine options but still sets the schema search path."""
        # Arrange
        mock_config_obj = Mock()
        mock_config_obj.configure_mock(**{
            "get.return_value": "public",
            "DB_INSTANCE_CONNECTION_NAME": "project:region:instance",
            "CLOUD_SQL_PROXY_SIDECAR": True,
            "DB_USER": "test_user",
            "DB_NAME": "test_db",
            "DB_IP_TYPE": "private",
            "SQLALCHEMY_DATABASE_URI": "postgresql+psycopg://test_user@127.0.0.1:5432/test_db",
        })
        mock_config.__getitem__.return_value = mock_config_obj

        mock_engine = Mock()
        mock_db.engine = mock_engine

        # Act
        with (
            patch("notify_api.DBConfig") as mock_db_config,
            patch("notify_api.log_sidecar_connection_evidence") as mock_log_evidence,
            patch("notify_api.CORS"),
            patch("notify_api.setup_jwt_manager"),
            patch("notify_api.register_shellcontext"),
            patch("notify_api.ExceptionHandler"),
            patch("notify_api.meta_endpoint"),
            patch("notify_api.ops_endpoint"),
            patch("notify_api.v1_endpoint"),
            patch("notify_api.v2_endpoint"),
        ):
            app = create_app("unitTesting")

        # Assert
        assert isinstance(app, Flask)
        mock_db.init_app.assert_called_once_with(app)
        mock_queue.init_app.assert_called_once_with(app)
        mock_db_config.assert_not_called()
        mock_setup_event_listener.assert_called_once_with(mock_engine, "public")
        mock_setup_pg8000_listener.assert_called_once_with(mock_engine)
        mock_log_evidence.assert_called_once_with(mock_engine, "5432")

        # Sidecar mode still configures an explicit, resilient connection pool.
        assert app.config["SQLALCHEMY_ENGINE_OPTIONS"] == {
            "pool_size": 10,
            "max_overflow": 10,
            "pool_timeout": 30,
            "pool_recycle": 1800,
            "pool_pre_ping": True,
            "connect_args": {"connect_timeout": 60},
        }

    @patch("notify_api.setup_pg8000_close_event_listener")
    @patch("notify_api.setup_search_path_event_listener")
    @patch("notify_api.queue")
    @patch("notify_api.db")
    @patch("notify_api.config")
    def test_create_app_sidecar_honours_configured_pool_settings(
        self,
        mock_config,
        mock_db,
        mock_queue,
        mock_setup_event_listener,
        mock_setup_pg8000_listener,
    ):
        """Sidecar pool options are sourced from the (env-driven) config values."""
        # Arrange
        mock_config_obj = Mock()
        mock_config_obj.configure_mock(**{
            "get.return_value": "public",
            "DB_INSTANCE_CONNECTION_NAME": "project:region:instance",
            "CLOUD_SQL_PROXY_SIDECAR": True,
            "DB_USER": "test_user",
            "DB_NAME": "test_db",
            "DB_IP_TYPE": "private",
            "DB_POOL_SIZE": 3,
            "DB_MAX_OVERFLOW": 7,
            "DB_POOL_TIMEOUT": 15,
            "DB_POOL_RECYCLE": 900,
            "DB_CONNECT_TIMEOUT": 20,
            "SQLALCHEMY_DATABASE_URI": "postgresql+psycopg://test_user@127.0.0.1:5432/test_db",
        })
        mock_config.__getitem__.return_value = mock_config_obj

        mock_engine = Mock()
        mock_db.engine = mock_engine

        # Act
        with (
            patch("notify_api.DBConfig") as mock_db_config,
            patch("notify_api.log_sidecar_connection_evidence"),
            patch("notify_api.CORS"),
            patch("notify_api.setup_jwt_manager"),
            patch("notify_api.register_shellcontext"),
            patch("notify_api.ExceptionHandler"),
            patch("notify_api.meta_endpoint"),
            patch("notify_api.ops_endpoint"),
            patch("notify_api.v1_endpoint"),
            patch("notify_api.v2_endpoint"),
        ):
            app = create_app("unitTesting")

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

        with patch("notify_api.utils.util.event") as mock_event:
            log_sidecar_connection_evidence(engine, "5432")

        mock_event.listens_for.assert_called_once_with(engine, "connect")
