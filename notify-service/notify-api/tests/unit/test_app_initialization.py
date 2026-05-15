import unittest
from unittest.mock import Mock, patch

from flask import Flask

from notify_api import create_app


class TestAppInitialization(unittest.TestCase):
    """Test suite for app initialization and configuration."""

    @patch("notify_api.setup_pg8000_close_event_listener")
    @patch("notify_api.setup_search_path_event_listener")
    @patch("notify_api.queue")
    @patch("notify_api.db")
    @patch("notify_api.config")
    def test_create_app_basic(self, mock_config, mock_db, mock_queue, mock_setup_event_listener, mock_setup_pg8000_listener):
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
        with patch("notify_api.CORS"), \
             patch("notify_api.setup_jwt_manager"), \
             patch("notify_api.register_shellcontext"), \
             patch("notify_api.ExceptionHandler"), \
             patch("notify_api.meta_endpoint"), \
             patch("notify_api.ops_endpoint"), \
             patch("notify_api.v1_endpoint"), \
             patch("notify_api.v2_endpoint"):
            app = create_app("unitTesting")

        # Assert
        assert isinstance(app, Flask)
        assert app.config is not None
        mock_db.init_app.assert_called_once_with(app)
        mock_queue.init_app.assert_called_once_with(app)
        mock_setup_pg8000_listener.assert_called_once_with(mock_engine)

