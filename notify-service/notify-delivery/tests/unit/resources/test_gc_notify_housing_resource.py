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
"""Test suite for GC Notify Housing resource handlers."""

import unittest
from http import HTTPStatus
from unittest.mock import Mock, patch

import pytest
from flask import Blueprint, Flask

from notify_delivery.resources.gc_notify_housing import bp, worker
from notify_delivery.resources.utils import process_notification as process_message
from notify_delivery.services.providers.gc_notify_housing import GCNotifyHousing


class TestGCNotifyHousingResource(unittest.TestCase):
    """Test suite for GC Notify Housing resource handlers."""

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

    @patch("notify_delivery.resources.utils.queue")
    @patch("notify_delivery.resources.utils.logger")
    def test_worker_no_request_data(self, mock_logger, mock_queue):
        """Test worker endpoint with no request data."""
        # Act
        with self.app.test_request_context("/", method="POST", data=""):
            response, status = worker()

        # Assert
        assert status == HTTPStatus.OK
        assert response == {}
        mock_logger.info.assert_called_with("No incoming raw message data")

    @patch("notify_delivery.resources.utils.queue")
    @patch("notify_delivery.resources.utils.logger")
    def test_worker_no_cloud_event(self, mock_logger, mock_queue):
        """Test worker endpoint with no cloud event."""
        # Arrange
        mock_queue.get_simple_cloud_event.return_value = None

        # Act
        with self.app.test_request_context("/", method="POST", data="test data"):
            response, status = worker()

        # Assert
        assert status == HTTPStatus.OK
        assert response == {}
        mock_logger.info.assert_called_with("No incoming cloud event message")

    @patch("notify_delivery.resources.gc_notify_housing.get_cloud_event")
    @patch("notify_delivery.resources.gc_notify_housing.validate_event_type")
    @patch("notify_delivery.resources.gc_notify_housing.process_notification")
    @patch("notify_delivery.resources.gc_notify_housing.logger")
    def test_worker_valid_housing_event(self, mock_logger, mock_process, mock_validate, mock_get_event):
        """Test worker endpoint with valid Housing cloud event."""
        # Arrange
        mock_ce = Mock()
        mock_ce.type = "bc.registry.notify.housing"
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
        # GCNotifyHousing is imported at the top, so we need to reference it properly
        mock_process.assert_called_once_with({"notificationId": "test_id"}, GCNotifyHousing)
        mock_logger.info.assert_any_call("Event Message Processed successfully: event_123")

    @patch("notify_delivery.resources.utils.queue")
    @patch("notify_delivery.resources.utils.logger")
    def test_worker_invalid_event_type(self, mock_logger, mock_queue):
        """Test worker endpoint with invalid event type."""
        # Arrange
        mock_ce = Mock()
        mock_ce.type = "invalid.type"
        mock_ce.data = {"notificationId": "test_id"}
        mock_queue.get_simple_cloud_event.return_value = mock_ce

        # Act
        with self.app.test_request_context("/", method="POST", data="test data"):
            response, status = worker()

        # Assert
        assert status == HTTPStatus.BAD_REQUEST
        assert response == {}
        mock_logger.error.assert_called_with(
            "Invalid queue message type: expected 'bc.registry.notify.housing', got 'invalid.type'"
        )

    @patch("notify_delivery.resources.gc_notify_housing.get_cloud_event")
    @patch("notify_delivery.resources.gc_notify_housing.validate_event_type")
    @patch("notify_delivery.resources.gc_notify_housing.process_notification")
    @patch("notify_delivery.resources.gc_notify_housing.logger")
    def test_worker_processing_exception(self, mock_logger, mock_process, mock_validate, mock_get_event):
        """Test worker endpoint with processing exception."""
        # Arrange
        mock_ce = Mock()
        mock_ce.type = "bc.registry.notify.housing"
        mock_ce.data = {"notificationId": "test_id"}
        mock_get_event.return_value = mock_ce
        mock_validate.return_value = True
        mock_process.side_effect = Exception("Processing error")

        # Act
        with self.app.test_request_context("/", method="POST", data="test data"):
            response, status = worker()

        # Assert
        assert status == HTTPStatus.INTERNAL_SERVER_ERROR
        assert response == {}
        mock_logger.error.assert_called_with(
            "Unexpected error processing queue message: Processing error", exc_info=True
        )

    @patch("notify_delivery.resources.gc_notify_housing.get_cloud_event")
    @patch("notify_delivery.resources.gc_notify_housing.validate_event_type")
    @patch("notify_delivery.resources.gc_notify_housing.process_notification")
    @patch("notify_delivery.resources.gc_notify_housing.logger")
    def test_worker_validation_error(self, mock_logger, mock_process, mock_validate, mock_get_event):
        """Test worker endpoint with validation error."""
        # Arrange
        mock_ce = Mock()
        mock_ce.type = "bc.registry.notify.housing"
        mock_ce.data = {"notificationId": "test_id"}
        mock_get_event.return_value = mock_ce
        mock_validate.return_value = True
        mock_process.side_effect = ValueError("Invalid notification data")

        # Act
        with self.app.test_request_context("/", method="POST", data="test data"):
            response, status = worker()

        # Assert
        assert status == HTTPStatus.BAD_REQUEST
        assert response == {}
        mock_logger.error.assert_called_with("Validation error processing queue message: Invalid notification data")

    @patch("notify_delivery.resources.utils.Notification")
    @patch("notify_delivery.services.providers.gc_notify_housing.GCNotifyHousing")
    @patch("notify_delivery.resources.utils.NotificationHistory")
    def test_process_message_successful_send(self, mock_history, mock_gc_notify_housing, mock_notification):
        """Test process_message with successful send."""
        # Arrange
        notification_data = {"notificationId": "test_123"}
        mock_notification_obj = Mock()
        mock_notification_obj.content = ["dummy_content"]
        mock_notification.find_notification_by_id.return_value = mock_notification_obj

        mock_response = Mock()
        mock_response.recipient = "test@example.com"
        mock_response.response_id = "response_123"

        mock_responses = Mock()
        mock_responses.recipients = [mock_response]

        mock_gc_notify_housing_instance = Mock()
        mock_gc_notify_housing_instance.send.return_value = mock_responses
        mock_gc_notify_housing.return_value = mock_gc_notify_housing_instance

        mock_history_obj = Mock()
        mock_history.create_history.return_value = mock_history_obj

        # Act
        result = process_message(notification_data, GCNotifyHousing)

        # Assert
        mock_notification.find_notification_by_id.assert_called_once_with("test_123")
        mock_gc_notify_housing.assert_called_once_with(mock_notification_obj)
        mock_gc_notify_housing_instance.send.assert_called_once()
        # Check that status was set (mocked object will have status_code attribute set)
        mock_notification_obj.update_notification.assert_called_once()
        mock_history.create_history.assert_called_once_with(mock_notification_obj, "test@example.com", "response_123")
        mock_notification_obj.delete_notification.assert_called_once()
        assert result == mock_history_obj

    @patch("notify_delivery.resources.utils.Notification")
    @patch("notify_delivery.services.providers.gc_notify_housing.GCNotifyHousing")
    def test_process_message_failed_send(self, mock_gc_notify_housing, mock_notification):
        """Test process_message with failed send."""
        # Arrange
        notification_data = {"notificationId": "test_123"}
        mock_notification_obj = Mock()
        mock_notification_obj.content = ["dummy_content"]
        mock_notification.find_notification_by_id.return_value = mock_notification_obj

        mock_gc_notify_housing_instance = Mock()
        mock_gc_notify_housing_instance.send.return_value = None  # Failed send
        mock_gc_notify_housing.return_value = mock_gc_notify_housing_instance

        # Act
        result = process_message(notification_data, GCNotifyHousing)

        # Assert
        mock_notification.find_notification_by_id.assert_called_once_with("test_123")
        mock_gc_notify_housing.assert_called_once_with(mock_notification_obj)
        mock_gc_notify_housing_instance.send.assert_called_once()
        # Check that status was set (mocked object will have status_code attribute set)
        mock_notification_obj.update_notification.assert_called_once()
        mock_notification_obj.delete_notification.assert_not_called()
        assert result == mock_notification_obj

    @patch("notify_delivery.resources.utils.Notification")
    def test_process_message_notification_not_found(self, mock_notification):
        """Test process_message with notification not found."""
        # Arrange
        notification_data = {"notificationId": "invalid_id"}
        mock_notification.find_notification_by_id.return_value = None

        # Act & Assert
        with pytest.raises(ValueError, match="Unknown notification for notificationId invalid_id"):
            process_message(notification_data, GCNotifyHousing)

        mock_notification.find_notification_by_id.assert_called_once_with("invalid_id")

    def test_blueprint_registration(self):
        """Test that blueprint is properly registered."""
        # Assert
        assert isinstance(bp, Blueprint)
        assert bp.name == "gcnotify-housing"

        # Check that routes are registered
        with self.app.test_request_context():
            rules = [rule.rule for rule in self.app.url_map.iter_rules()]
            assert "/" in rules
