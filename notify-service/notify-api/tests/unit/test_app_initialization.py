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
"""Test suite for the safe_close connection wrapper in notify-api."""

import unittest
from unittest.mock import Mock, patch

from pg8000.exceptions import InterfaceError

from notify_api import create_app


class TestSafeCloseWrapper(unittest.TestCase):
    """Test suite for the dbapi connection close() wrapper registered via event.listens_for."""

    @patch("notify_api.setup_search_path_event_listener")
    @patch("notify_api.queue")
    @patch("notify_api.db")
    @patch("notify_api.config")
    def test_connect_listener_wraps_close_and_suppresses_interface_error(
        self, mock_config, mock_db, mock_queue, mock_setup_event_listener
    ):
        """Test that the on_connect listener wraps close() to suppress InterfaceError."""
        # Arrange
        mock_config_obj = Mock()
        mock_config_obj.configure_mock(**{
            "get.return_value": None,
            "DB_INSTANCE_CONNECTION_NAME": None,
            "DB_USER": "test_user",
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        })
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

        with patch("notify_api.event.listens_for", side_effect=capture_listens_for):
            create_app("unitTesting")

        assert captured_listener is not None, "on_connect listener was not registered"

        # Simulate a connection whose close() raises InterfaceError
        mock_dbapi_conn = Mock()
        original_close = Mock(side_effect=InterfaceError("connection is closed"))
        mock_dbapi_conn.close = original_close

        captured_listener(mock_dbapi_conn, Mock())

        # After wrapping, calling close() should suppress InterfaceError
        mock_dbapi_conn.close()
        original_close.assert_called_once()

    @patch("notify_api.setup_search_path_event_listener")
    @patch("notify_api.queue")
    @patch("notify_api.db")
    @patch("notify_api.config")
    def test_connect_listener_propagates_non_interface_errors(
        self, mock_config, mock_db, mock_queue, mock_setup_event_listener
    ):
        """Test that non-InterfaceError exceptions are not suppressed."""
        # Arrange
        mock_config_obj = Mock()
        mock_config_obj.configure_mock(**{
            "get.return_value": None,
            "DB_INSTANCE_CONNECTION_NAME": None,
            "DB_USER": "test_user",
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        })
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

        with patch("notify_api.event.listens_for", side_effect=capture_listens_for):
            create_app("unitTesting")

        assert captured_listener is not None

        # Simulate a connection whose close() raises a non-InterfaceError
        mock_dbapi_conn = Mock()
        mock_dbapi_conn.close = Mock(side_effect=RuntimeError("unexpected"))

        captured_listener(mock_dbapi_conn, Mock())

        with self.assertRaises(RuntimeError):
            mock_dbapi_conn.close()
