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

import pytest
from flask import Blueprint, Flask
from notify_api.models import Notification, NotificationHistory, NotificationSendResponses

from notify_delivery.resources.gc_notify import bp, process_message, worker


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

    @patch("notify_delivery.resources.gc_notify.queue")
    @patch("notify_delivery.resources.gc_notify.logger")
    def test_worker_no_request_data(self, mock_logger, mock_queue):
        """Test worker endpoint with no request data."""
        # Act
        with self.app.test_request_context("/", method="POST", data=""):
            response, status = worker()

        # Assert
        assert status == HTTPStatus.OK
        assert response == {}
        mock_logger.info.assert_called_with("No incoming raw msg.")

    @patch("notify_delivery.resources.gc_notify.queue")
    @patch("notify_delivery.resources.gc_notify.logger")
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
        mock_logger.info.assert_called_with("No incoming cloud event msg.")

    @patch("notify_delivery.resources.gc_notify.queue")
    @patch("notify_delivery.resources.gc_notify.process_message")
    @patch("notify_delivery.resources.gc_notify.logger")
    def test_worker_valid_gc_notify_event(self, mock_logger, mock_process, mock_queue):
        """Test worker endpoint with valid GC Notify cloud event."""
        # Arrange
        mock_ce = Mock()
        mock_ce.type = "bc.registry.notify.gc_notify"
        mock_ce.data = {"notificationId": "test_id"}
        mock_ce.id = "event_123"
        mock_queue.get_simple_cloud_event.return_value = mock_ce

        # Act
        with self.app.test_request_context("/", method="POST", data="test data"):
            response, status = worker()

        # Assert
        assert status == HTTPStatus.OK
        assert response == {}
        mock_process.assert_called_once_with({"notificationId": "test_id"})
        mock_logger.info.assert_any_call(f"Event Message Received: {mock_ce}")
        mock_logger.info.assert_any_call("Event Message Processed: event_123")

    @patch("notify_delivery.resources.gc_notify.queue")
    @patch("notify_delivery.resources.gc_notify.logger")
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
            "Invalid queue message type: expected 'bc.registry.notify.gc_notify', got 'invalid.type'"
        )

    @patch("notify_delivery.resources.gc_notify.queue")
    @patch("notify_delivery.resources.gc_notify.process_message")
    @patch("notify_delivery.resources.gc_notify.logger")
    def test_worker_processing_exception(self, mock_logger, mock_process, mock_queue):
        """Test worker endpoint with processing exception."""
        # Arrange
        mock_ce = Mock()
        mock_ce.type = "bc.registry.notify.gc_notify"
        mock_ce.data = {"notificationId": "test_id"}
        mock_queue.get_simple_cloud_event.return_value = mock_ce
        mock_process.side_effect = Exception("Processing error")

        # Act
        with self.app.test_request_context("/", method="POST", data="test data"):
            response, status = worker()

        # Assert
        assert status == HTTPStatus.INTERNAL_SERVER_ERROR
        assert response == {}
        mock_logger.error.assert_called_with("Failed to process queue message: Processing error")

    @patch("notify_delivery.resources.gc_notify.Notification")
    @patch("notify_delivery.resources.gc_notify.GCNotify")
    @patch("notify_delivery.resources.gc_notify.NotificationHistory")
    def test_process_message_successful_send(self, mock_history, mock_gc_notify, mock_notification):
        """Test process_message with successful send."""
        # Arrange
        notification_data = {"notificationId": "test_123"}
        mock_notification_obj = Mock()
        mock_notification_obj.content = ["dummy_content"]  # Add content that supports len()
        mock_notification.find_notification_by_id.return_value = mock_notification_obj

        mock_response = Mock()
        mock_response.recipient = "test@example.com"
        mock_response.response_id = "response_123"

        mock_responses = Mock()
        mock_responses.recipients = [mock_response]

        mock_gc_notify_instance = Mock()
        mock_gc_notify_instance.send.return_value = mock_responses
        mock_gc_notify.return_value = mock_gc_notify_instance

        mock_history_obj = Mock()
        mock_history.create_history.return_value = mock_history_obj

        # Act
        result = process_message(notification_data)

        # Assert
        mock_notification.find_notification_by_id.assert_called_once_with("test_123")
        mock_gc_notify.assert_called_once_with(mock_notification_obj)
        mock_gc_notify_instance.send.assert_called_once()
        # Check that status was set (mocked object will have status_code attribute set)
        assert hasattr(mock_notification_obj, "status_code")
        mock_notification_obj.update_notification.assert_called_once()
        mock_history.create_history.assert_called_once_with(mock_notification_obj, "test@example.com", "response_123")
        mock_notification_obj.delete_notification.assert_called_once()
        assert result == mock_history_obj

    @patch("notify_delivery.resources.gc_notify.Notification")
    @patch("notify_delivery.resources.gc_notify.GCNotify")
    def test_process_message_failed_send(self, mock_gc_notify, mock_notification):
        """Test process_message with failed send."""
        # Arrange
        notification_data = {"notificationId": "test_123"}
        mock_notification_obj = Mock()
        mock_notification_obj.content = ["dummy_content"]  # Add content that supports len()
        mock_notification.find_notification_by_id.return_value = mock_notification_obj

        mock_gc_notify_instance = Mock()
        mock_gc_notify_instance.send.return_value = None  # Failed send
        mock_gc_notify.return_value = mock_gc_notify_instance

        # Act
        result = process_message(notification_data)

        # Assert
        mock_notification.find_notification_by_id.assert_called_once_with("test_123")
        mock_gc_notify.assert_called_once_with(mock_notification_obj)
        mock_gc_notify_instance.send.assert_called_once()
        # Check that status was set (mocked object will have status_code attribute set)
        assert hasattr(mock_notification_obj, "status_code")
        mock_notification_obj.update_notification.assert_called_once()
        mock_notification_obj.delete_notification.assert_not_called()
        assert result == mock_notification_obj

    @patch("notify_delivery.resources.gc_notify.Notification")
    def test_process_message_notification_not_found(self, mock_notification):
        """Test process_message with notification not found."""
        # Arrange
        notification_data = {"notificationId": "invalid_id"}
        mock_notification.find_notification_by_id.return_value = None

        # Act & Assert
        with pytest.raises(ValueError, match="Unknown notification for notificationId invalid_id"):
            process_message(notification_data)

        mock_notification.find_notification_by_id.assert_called_once_with("invalid_id")

    @patch("notify_delivery.resources.gc_notify.Notification")
    @patch("notify_delivery.resources.gc_notify.GCNotify")
    @patch("notify_delivery.resources.gc_notify.NotificationHistory")
    def test_process_message_multiple_recipients(self, mock_history, mock_gc_notify, mock_notification):
        """Test process_message with multiple recipients."""
        # Arrange
        notification_data = {"notificationId": "test_123"}
        mock_notification_obj = Mock()
        mock_notification_obj.content = ["dummy_content"]  # Add content that supports len()
        mock_notification.find_notification_by_id.return_value = mock_notification_obj

        mock_response1 = Mock()
        mock_response1.recipient = "test1@example.com"
        mock_response1.response_id = "response_123"

        mock_response2 = Mock()
        mock_response2.recipient = "test2@example.com"
        mock_response2.response_id = "response_456"

        mock_responses = Mock()
        mock_responses.recipients = [mock_response1, mock_response2]

        mock_gc_notify_instance = Mock()
        mock_gc_notify_instance.send.return_value = mock_responses
        mock_gc_notify.return_value = mock_gc_notify_instance

        mock_history_obj1 = Mock()
        mock_history_obj2 = Mock()
        mock_history.create_history.side_effect = [mock_history_obj1, mock_history_obj2]

        # Act
        result = process_message(notification_data)

        # Assert
        expected_history_calls = 2
        assert mock_history.create_history.call_count == expected_history_calls
        mock_history.create_history.assert_any_call(mock_notification_obj, "test1@example.com", "response_123")
        mock_history.create_history.assert_any_call(mock_notification_obj, "test2@example.com", "response_456")
        assert result == mock_history_obj2  # Returns last history object

    def test_blueprint_registration(self):
        """Test that blueprint is properly registered."""
        # Assert
        assert isinstance(bp, Blueprint)
        assert bp.name == "gcnotify"

        # Check that routes are registered
        with self.app.test_request_context():
            rules = [rule.rule for rule in self.app.url_map.iter_rules()]
            assert "/" in rules
