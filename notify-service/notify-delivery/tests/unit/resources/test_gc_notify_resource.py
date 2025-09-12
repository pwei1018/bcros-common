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
"""Test suite for GC Notify resource handlers."""

import unittest
from http import HTTPStatus
from unittest.mock import Mock, patch

from flask import Blueprint, Flask

from notify_delivery.resources.gc_notify import bp, worker
from notify_delivery.services.providers.gc_notify import GCNotify


class TestGCNotifyResource(unittest.TestCase):
    """Test suite for GC Notify resource handlers."""

    def setUp(self):
        """Set up test fixtures."""
        self.app = Flask(__name__)
        self.app.config.update(
            {
                "TESTING": True,
                "VERIFY_PUBSUB_VIA_JWT": False,  # Disable JWT verification for tests
            }
        )
        self.app.register_blueprint(bp)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        """Clean up test fixtures."""
        self.app_context.pop()

    @patch("notify_delivery.resources.gc_notify.get_cloud_event")
    @patch("notify_delivery.resources.gc_notify.validate_event_type")
    @patch("notify_delivery.resources.gc_notify.process_notification")
    @patch("notify_delivery.resources.gc_notify.logger")
    def test_worker_valid_gc_notify_event(self, mock_logger, mock_process, mock_validate, mock_get_event):
        """Test worker endpoint with valid GC Notify cloud event."""
        # Arrange
        mock_ce = Mock()
        mock_ce.type = "bc.registry.notify.gc_notify"
        mock_ce.data = {"notificationId": "test_id"}
        mock_ce.id = "event_123"
        mock_get_event.return_value = mock_ce
        mock_validate.return_value = True

        # Act
        with self.app.test_request_context("/", method="POST", data="test data"):
            response, status = worker()

        # Assert
        assert status == HTTPStatus.OK
        assert response == {}
        # Need to import the actual GCNotify class for the assertion
        mock_process.assert_called_once_with(mock_ce.data, GCNotify)
        mock_logger.info.assert_any_call(f"Event Message Processed successfully: {mock_ce.id}")

    @patch("notify_delivery.resources.gc_notify.get_cloud_event")
    @patch("notify_delivery.resources.gc_notify.logger")
    def test_worker_no_cloud_event(self, mock_logger, mock_get_event):
        """Test worker endpoint with no cloud event."""
        # Arrange
        mock_get_event.return_value = None

        # Act
        with self.app.test_request_context("/", method="POST", data=""):
            response, status = worker()

        # Assert
        assert status == HTTPStatus.OK
        assert response == {}

    @patch("notify_delivery.resources.gc_notify.get_cloud_event")
    @patch("notify_delivery.resources.gc_notify.validate_event_type")
    @patch("notify_delivery.resources.gc_notify.logger")
    def test_worker_invalid_event_type(self, mock_logger, mock_validate, mock_get_event):
        """Test worker endpoint with invalid event type."""
        # Arrange
        mock_ce = Mock()
        mock_ce.type = "wrong.event.type"
        mock_get_event.return_value = mock_ce
        mock_validate.return_value = False

        # Act
        with self.app.test_request_context("/", method="POST", data="test data"):
            response, status = worker()

        # Assert
        assert status == HTTPStatus.BAD_REQUEST
        assert response == {}

    @patch("notify_delivery.resources.gc_notify.get_cloud_event")
    @patch("notify_delivery.resources.gc_notify.validate_event_type")
    @patch("notify_delivery.resources.gc_notify.process_notification")
    @patch("notify_delivery.resources.gc_notify.logger")
    def test_worker_validation_error(self, mock_logger, mock_process, mock_validate, mock_get_event):
        """Test worker endpoint with validation error."""
        # Arrange
        mock_ce = Mock()
        mock_ce.type = "bc.registry.notify.gc_notify"
        mock_ce.data = {"notificationId": "test_id"}
        mock_get_event.return_value = mock_ce
        mock_validate.return_value = True
        mock_process.side_effect = ValueError("Validation failed")

        # Act
        with self.app.test_request_context("/", method="POST", data="test data"):
            response, status = worker()

        # Assert
        assert status == HTTPStatus.BAD_REQUEST
        assert response == {}
        mock_logger.error.assert_called_with("Validation error processing queue message: Validation failed")

    @patch("notify_delivery.resources.gc_notify.get_cloud_event")
    @patch("notify_delivery.resources.gc_notify.validate_event_type")
    @patch("notify_delivery.resources.gc_notify.process_notification")
    @patch("notify_delivery.resources.gc_notify.logger")
    def test_worker_general_exception(self, mock_logger, mock_process, mock_validate, mock_get_event):
        """Test worker endpoint with general exception."""
        # Arrange
        mock_ce = Mock()
        mock_ce.type = "bc.registry.notify.gc_notify"
        mock_ce.data = {"notificationId": "test_id"}
        mock_get_event.return_value = mock_ce
        mock_validate.return_value = True
        mock_process.side_effect = Exception("Database connection failed")

        # Act
        with self.app.test_request_context("/", method="POST", data="test data"):
            response, status = worker()

        # Assert
        assert status == HTTPStatus.INTERNAL_SERVER_ERROR
        assert response == {}
        mock_logger.error.assert_called_with(
            "Unexpected error processing queue message: Database connection failed",
            exc_info=True,
        )

    def test_blueprint_registration(self):
        """Test that blueprint is properly registered."""
        # Assert
        assert isinstance(bp, Blueprint)
        assert bp.name == "gcnotify"

        # Check that routes are registered
        with self.app.test_request_context():
            rules = [rule.rule for rule in self.app.url_map.iter_rules()]
            assert "/" in rules
