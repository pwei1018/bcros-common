# Copyright © 2022 Province of British Columbia
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Test suite for GCP authentication service."""

import contextlib
import functools
import unittest
from http import HTTPStatus
from unittest.mock import Mock, patch

import pytest
from flask import Flask
from werkzeug.exceptions import Unauthorized

from notify_delivery.services.gcp_queue.gcp_auth import ensure_authorized_queue_user, verify_jwt


class TestGCPAuth(unittest.TestCase):
    """Test suite for GCP authentication service."""

    def setUp(self):
        """Set up test fixtures."""
        self.app = Flask(__name__)
        self.app.config.update(
            {
                "NOTIFY_SUB_AUDIENCE": "test-audience",
                "VERIFY_PUBSUB_EMAIL": "test@example.com",
                "DEBUG_REQUEST": False,
                "VERIFY_PUBSUB_VIA_JWT": True,
            }
        )
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        """Clean up test fixtures."""
        self.app_context.pop()

    def test_verify_jwt_valid_token(self):
        """Test verify_jwt with valid token and claims."""
        # Arrange
        mock_session = Mock()

        with (
            self.app.test_request_context(headers={"Authorization": "Bearer valid_jwt_token"}),
            patch("notify_delivery.services.gcp_queue.gcp_auth.id_token") as mock_id_token,
        ):
            mock_claims = {"email_verified": True, "email": "test@example.com"}
            mock_id_token.verify_oauth2_token.return_value = mock_claims

            # Act
            result = verify_jwt(mock_session)

            # Assert
            assert result is None
            mock_id_token.verify_oauth2_token.assert_called_once()

    def test_verify_jwt_email_not_verified(self):
        """Test verify_jwt with unverified email."""
        # Arrange
        mock_session = Mock()

        with (
            self.app.test_request_context(headers={"Authorization": "Bearer valid_jwt_token"}),
            patch("notify_delivery.services.gcp_queue.gcp_auth.id_token") as mock_id_token,
        ):
            mock_claims = {"email_verified": False, "email": "test@example.com"}
            mock_id_token.verify_oauth2_token.return_value = mock_claims

            # Act
            result = verify_jwt(mock_session)

            # Assert
            assert result == ("Email not verified or does not match", 401)

    def test_verify_jwt_wrong_email(self):
        """Test verify_jwt with wrong email."""
        # Arrange
        mock_session = Mock()

        with (
            self.app.test_request_context(headers={"Authorization": "Bearer valid_jwt_token"}),
            patch("notify_delivery.services.gcp_queue.gcp_auth.id_token") as mock_id_token,
        ):
            mock_claims = {"email_verified": True, "email": "wrong@example.com"}
            mock_id_token.verify_oauth2_token.return_value = mock_claims

            # Act
            result = verify_jwt(mock_session)

            # Assert
            assert result == ("Email not verified or does not match", 401)

    def test_verify_jwt_invalid_token(self):
        """Test verify_jwt with invalid token."""
        # Arrange
        mock_session = Mock()

        with (
            self.app.test_request_context(headers={"Authorization": "Bearer invalid_jwt_token"}),
            patch("notify_delivery.services.gcp_queue.gcp_auth.id_token") as mock_id_token,
        ):
            mock_id_token.verify_oauth2_token.side_effect = Exception("Invalid token")

            # Act
            result = verify_jwt(mock_session)

            # Assert
            expected_error_code = HTTPStatus.BAD_REQUEST
            assert result[0] == "Invalid token: Invalid token"
            assert result[1] == expected_error_code

    def test_verify_jwt_no_authorization_header(self):
        """Test verify_jwt with no authorization header."""
        # Arrange
        mock_session = Mock()

        # Act
        with self.app.test_request_context():
            result = verify_jwt(mock_session)

        # Assert
        assert result is not None
        assert "Invalid token:" in result[0]
        assert result[1] == HTTPStatus.BAD_REQUEST

    def test_verify_jwt_malformed_authorization_header(self):
        """Test verify_jwt with malformed authorization header."""
        # Arrange
        mock_session = Mock()

        # Act
        with self.app.test_request_context(headers={"Authorization": "InvalidFormat"}):
            result = verify_jwt(mock_session)

        # Assert
        assert result is not None
        assert "Invalid token:" in result[0]
        assert result[1] == HTTPStatus.BAD_REQUEST

    @patch("notify_delivery.services.gcp_queue.gcp_auth.verify_jwt")
    @patch("notify_delivery.services.gcp_queue.gcp_auth.CacheControl")
    @patch("notify_delivery.services.gcp_queue.gcp_auth.logger")
    def test_ensure_authorized_queue_user_valid(self, mock_logger, mock_cache_control, mock_verify_jwt):
        """Test ensure_authorized_queue_user decorator with valid JWT."""
        # Arrange
        mock_verify_jwt.return_value = None  # Valid JWT
        mock_session = Mock()
        mock_cache_control.return_value = mock_session

        @ensure_authorized_queue_user
        def test_function():
            return "success"

        # Act
        with self.app.test_request_context():
            result = test_function()

        # Assert
        assert result == "success"
        mock_verify_jwt.assert_called_once_with(mock_session)

    @patch("notify_delivery.services.gcp_queue.gcp_auth.verify_jwt")
    @patch("notify_delivery.services.gcp_queue.gcp_auth.CacheControl")
    @patch("notify_delivery.services.gcp_queue.gcp_auth.logger")
    @patch("notify_delivery.services.gcp_queue.gcp_auth.abort")
    def test_ensure_authorized_queue_user_invalid(self, mock_abort, mock_logger, mock_cache_control, mock_verify_jwt):
        """Test ensure_authorized_queue_user decorator with invalid JWT."""
        # Arrange
        mock_verify_jwt.return_value = ("Invalid token", 401)  # Invalid JWT
        mock_session = Mock()
        mock_cache_control.return_value = mock_session

        @ensure_authorized_queue_user
        def test_function():
            return "success"

        # Act
        with self.app.test_request_context():
            test_function()

        # Assert
        mock_abort.assert_called_once_with(HTTPStatus.UNAUTHORIZED)

    @patch("notify_delivery.services.gcp_queue.gcp_auth.verify_jwt")
    @patch("notify_delivery.services.gcp_queue.gcp_auth.CacheControl")
    @patch("notify_delivery.services.gcp_queue.gcp_auth.logger")
    def test_ensure_authorized_queue_user_jwt_disabled(self, mock_logger, mock_cache_control, mock_verify_jwt):
        """Test ensure_authorized_queue_user decorator with JWT verification disabled."""
        # Arrange
        self.app.config["VERIFY_PUBSUB_VIA_JWT"] = False

        @ensure_authorized_queue_user
        def test_function():
            return "success"

        # Act
        with self.app.test_request_context():
            result = test_function()

        # Assert
        assert result == "success"
        mock_verify_jwt.assert_not_called()

    @patch("notify_delivery.services.gcp_queue.gcp_auth.verify_jwt")
    @patch("notify_delivery.services.gcp_queue.gcp_auth.CacheControl")
    @patch("notify_delivery.services.gcp_queue.gcp_auth.logger")
    def test_ensure_authorized_queue_user_debug_mode(self, mock_logger, mock_cache_control, mock_verify_jwt):
        """Test ensure_authorized_queue_user decorator with debug mode enabled."""
        # Arrange
        self.app.config["DEBUG_REQUEST"] = True
        mock_verify_jwt.return_value = None

        @ensure_authorized_queue_user
        def test_function():
            return "success"

        # Act
        with self.app.test_request_context(headers={"Authorization": "Bearer test_token"}):
            result = test_function()

        # Assert
        assert result == "success"
        mock_logger.info.assert_called_once()  # Called with headers info

    @patch("notify_delivery.services.gcp_queue.gcp_auth.logger")
    def test_decorator_logs_verify_jwt_setting(self, mock_logger):
        """Test that decorator logs the verifyJWT setting."""

        # Arrange
        @ensure_authorized_queue_user
        def test_function():
            return "success"

        # Act
        with self.app.test_request_context(), contextlib.suppress(Exception):
            test_function()  # We expect this to fail due to JWT verification

        # Assert
        mock_logger.debug.assert_called_with("verifyJWT: True")

    def test_ensure_authorized_queue_user_preserves_function_metadata(self):
        """Test ensure_authorized_queue_user decorator preserves function metadata."""

        # Arrange
        @ensure_authorized_queue_user
        def test_function():
            """Test function docstring."""
            return "success"

        # Assert
        assert test_function.__name__ == "test_function"
        assert test_function.__doc__ == "Test function docstring."

    @patch("notify_delivery.services.gcp_queue.gcp_auth.verify_jwt")
    @patch("notify_delivery.services.gcp_queue.gcp_auth.CacheControl")
    @patch("notify_delivery.services.gcp_queue.gcp_auth.logger")
    def test_ensure_authorized_queue_user_with_args_kwargs(self, mock_logger, mock_cache_control, mock_verify_jwt):
        """Test ensure_authorized_queue_user decorator with function arguments."""
        # Arrange
        mock_verify_jwt.return_value = None

        @ensure_authorized_queue_user
        def test_function(arg1, arg2, kwarg1=None):
            return f"{arg1}-{arg2}-{kwarg1}"

        # Act
        with self.app.test_request_context():
            result = test_function("test1", "test2", kwarg1="test3")

        # Assert
        assert result == "test1-test2-test3"
