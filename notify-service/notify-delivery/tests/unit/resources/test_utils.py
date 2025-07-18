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
"""Tests for utility functions."""

from unittest.mock import Mock, patch

import pytest
from notify_api.models import Notification

from notify_delivery.resources.utils import (
    fetch_notification,
    get_cloud_event,
    process_notification,
    send_notification,
    validate_event_type,
    validate_notification_content,
)


class TestGetCloudEvent:
    """Test get_cloud_event function."""

    @patch("notify_delivery.resources.utils.queue")
    @patch("notify_delivery.resources.utils.logger")
    def test_get_cloud_event_no_data(self, mock_logger, mock_queue, app):
        """Test get_cloud_event with no request data."""
        with app.test_request_context("/", method="POST", data=""):
            result = get_cloud_event()

        assert result is None
        mock_logger.info.assert_called_with("No incoming raw message data")

    @patch("notify_delivery.resources.utils.queue")
    @patch("notify_delivery.resources.utils.logger")
    def test_get_cloud_event_none_data(self, mock_logger, mock_queue, app):
        """Test get_cloud_event with None request data."""
        with (
            app.test_request_context("/", method="POST"),
            patch("notify_delivery.resources.utils.request") as mock_request,
        ):
            # Flask doesn't allow setting request.data to None directly,
            # so we'll mock it
            mock_request.data = None
            result = get_cloud_event()

        assert result is None
        mock_logger.info.assert_called_with("No incoming raw message data")

    @patch("notify_delivery.resources.utils.queue")
    @patch("notify_delivery.resources.utils.logger")
    def test_get_cloud_event_no_cloud_event(self, mock_logger, mock_queue, app):
        """Test get_cloud_event when queue returns None."""
        mock_queue.get_simple_cloud_event.return_value = None

        with app.test_request_context("/", method="POST", data="test data"):
            result = get_cloud_event()

        assert result is None
        mock_queue.get_simple_cloud_event.assert_called()
        mock_logger.info.assert_called_with("No incoming cloud event message")

    @patch("notify_delivery.resources.utils.queue")
    @patch("notify_delivery.resources.utils.logger")
    def test_get_cloud_event_success(self, mock_logger, mock_queue, app):
        """Test get_cloud_event with successful cloud event."""
        mock_cloud_event = Mock()
        mock_queue.get_simple_cloud_event.return_value = mock_cloud_event

        with app.test_request_context("/", method="POST", data="test data"):
            result = get_cloud_event()

        assert result == mock_cloud_event
        mock_queue.get_simple_cloud_event.assert_called()
        mock_logger.info.assert_called_with(f"Event Message Received: {mock_cloud_event}")


class TestValidateEventType:
    """Test validate_event_type function."""

    @patch("notify_delivery.resources.utils.logger")
    def test_validate_event_type_invalid(self, mock_logger):
        """Test validate_event_type with invalid event type."""
        mock_cloud_event = Mock()
        mock_cloud_event.type = "wrong.type"
        expected_type = "correct.type"

        result = validate_event_type(mock_cloud_event, expected_type)

        assert result is False
        mock_logger.error.assert_called_with(
            f"Invalid queue message type: expected '{expected_type}', got '{mock_cloud_event.type}'"
        )

    @patch("notify_delivery.resources.utils.logger")
    def test_validate_event_type_valid(self, mock_logger):
        """Test validate_event_type with valid event type."""
        mock_cloud_event = Mock()
        mock_cloud_event.type = "correct.type"
        expected_type = "correct.type"

        result = validate_event_type(mock_cloud_event, expected_type)

        assert result is True
        mock_logger.error.assert_not_called()


class TestProcessNotification:
    """Test process_notification function."""

    @patch("notify_delivery.resources.utils.logger")
    def test_process_notification_empty_data(self, mock_logger):
        """Test process_notification with empty data."""
        with pytest.raises(ValueError, match="Invalid queue message data - empty data"):
            process_notification({}, Mock())

        mock_logger.error.assert_called_with("No message content in queue data")

    @patch("notify_delivery.resources.utils.logger")
    def test_process_notification_none_data(self, mock_logger):
        """Test process_notification with None data."""
        with pytest.raises(ValueError, match="Invalid queue message data - empty data"):
            process_notification(None, Mock())

        mock_logger.error.assert_called_with("No message content in queue data")

    @patch("notify_delivery.resources.utils.logger")
    def test_process_notification_missing_notification_id(self, mock_logger):
        """Test process_notification with missing notificationId."""
        data = {"someOtherField": "value"}

        with pytest.raises(ValueError, match="Invalid queue message data - missing notificationId"):
            process_notification(data, Mock())

        mock_logger.error.assert_called_with("Missing notificationId in queue data")

    @patch("notify_delivery.resources.utils.logger")
    def test_process_notification_empty_notification_id(self, mock_logger):
        """Test process_notification with empty notificationId."""
        data = {"notificationId": ""}

        with pytest.raises(ValueError, match="Invalid queue message data - missing notificationId"):
            process_notification(data, Mock())

        mock_logger.error.assert_called_with("Missing notificationId in queue data")

    @patch("notify_delivery.resources.utils.send_notification")
    @patch("notify_delivery.resources.utils.validate_notification_content")
    @patch("notify_delivery.resources.utils.fetch_notification")
    def test_process_notification_success(self, mock_fetch, mock_validate, mock_send):
        """Test process_notification with successful flow."""
        data = {"notificationId": "test123"}
        provider_class = Mock()
        mock_notification = Mock()
        mock_result = Mock()

        mock_fetch.return_value = mock_notification
        mock_send.return_value = mock_result

        result = process_notification(data, provider_class)

        assert result == mock_result
        mock_fetch.assert_called_with("test123")
        mock_validate.assert_called_with(mock_notification)
        mock_send.assert_called_with(mock_notification, provider_class)


class TestFetchNotification:
    """Test fetch_notification function."""

    @patch("notify_delivery.resources.utils.Notification")
    @patch("notify_delivery.resources.utils.logger")
    def test_fetch_notification_database_error(self, mock_logger, mock_notification_class):
        """Test fetch_notification with database error."""
        notification_id = "test123"
        mock_notification_class.find_notification_by_id.side_effect = Exception("DB Connection failed")

        with pytest.raises(ValueError, match=f"Failed to fetch notification for notificationId {notification_id}"):
            fetch_notification(notification_id)

        mock_logger.error.assert_called_with(
            f"Database error while fetching notification {notification_id}: DB Connection failed"
        )

    @patch("notify_delivery.resources.utils.Notification")
    @patch("notify_delivery.resources.utils.logger")
    def test_fetch_notification_not_found(self, mock_logger, mock_notification_class):
        """Test fetch_notification when notification is not found."""
        notification_id = "test123"
        mock_notification_class.find_notification_by_id.return_value = None

        with pytest.raises(ValueError, match=f"Unknown notification for notificationId {notification_id}"):
            fetch_notification(notification_id)

        mock_logger.error.assert_called_with(f"Unknown notification for notificationId {notification_id}")

    @patch("notify_delivery.resources.utils.Notification")
    def test_fetch_notification_success(self, mock_notification_class):
        """Test fetch_notification with successful retrieval."""
        notification_id = "test123"
        mock_notification = Mock()
        mock_notification_class.find_notification_by_id.return_value = mock_notification

        result = fetch_notification(notification_id)

        assert result == mock_notification
        mock_notification_class.find_notification_by_id.assert_called_with(notification_id)


class TestValidateNotificationContent:
    """Test validate_notification_content function."""

    @patch("notify_delivery.resources.utils.logger")
    def test_validate_notification_content_empty_content(self, mock_logger):
        """Test validate_notification_content with empty content list."""
        mock_notification = Mock()
        mock_notification.id = "test123"
        mock_notification.content = []

        with pytest.raises(ValueError, match=f"No message content for notificationId {mock_notification.id}"):
            validate_notification_content(mock_notification)

        mock_logger.error.assert_called_with(f"No message content for notificationId {mock_notification.id}")

    @patch("notify_delivery.resources.utils.logger")
    def test_validate_notification_content_none_content(self, mock_logger):
        """Test validate_notification_content with None content."""
        mock_notification = Mock()
        mock_notification.id = "test123"
        mock_notification.content = None

        with pytest.raises(ValueError, match=f"No message content for notificationId {mock_notification.id}"):
            validate_notification_content(mock_notification)

        mock_logger.error.assert_called_with(f"No message content for notificationId {mock_notification.id}")

    def test_validate_notification_content_success(self):
        """Test validate_notification_content with valid content."""
        mock_notification = Mock()
        mock_notification.content = ["some content"]

        # Should not raise any exception
        validate_notification_content(mock_notification)


class TestSendNotification:
    """Test send_notification function."""

    @patch("notify_delivery.resources.utils.logger")
    def test_send_notification_provider_exception(self, mock_logger):
        """Test send_notification when provider raises exception."""
        mock_notification = Mock()
        mock_notification.id = "test123"
        mock_provider_class = Mock()
        mock_provider_class.side_effect = Exception("Provider initialization failed")

        with pytest.raises(ValueError, match=f"Failed to send notification {mock_notification.id}"):
            send_notification(mock_notification, mock_provider_class)

        mock_logger.error.assert_called_with(
            f"Error sending notification {mock_notification.id}: Provider initialization failed"
        )
        assert mock_notification.status_code == Notification.NotificationStatus.FAILURE
        mock_notification.update_notification.assert_called()

    @patch("notify_delivery.resources.utils.logger")
    def test_send_notification_send_exception(self, mock_logger):
        """Test send_notification when provider.send() raises exception."""
        mock_notification = Mock()
        mock_notification.id = "test123"
        mock_provider_class = Mock()
        mock_provider = Mock()
        mock_provider.send.side_effect = Exception("Send failed")
        mock_provider_class.return_value = mock_provider

        with pytest.raises(ValueError, match=f"Failed to send notification {mock_notification.id}"):
            send_notification(mock_notification, mock_provider_class)

        mock_logger.error.assert_called_with(f"Error sending notification {mock_notification.id}: Send failed")
        assert mock_notification.status_code == Notification.NotificationStatus.FAILURE
        mock_notification.update_notification.assert_called()

    @patch("notify_delivery.resources.utils.logger")
    def test_send_notification_no_responses(self, mock_logger):
        """Test send_notification when no responses are returned."""
        mock_notification = Mock()
        mock_notification.id = "test123"
        mock_provider_class = Mock()
        mock_provider = Mock()
        mock_provider.send.return_value = None
        mock_provider_class.return_value = mock_provider

        result = send_notification(mock_notification, mock_provider_class)

        assert result == mock_notification
        assert mock_notification.status_code == Notification.NotificationStatus.FAILURE
        mock_notification.update_notification.assert_called()
        mock_logger.warning.assert_called_with(
            f"Failed to send notification {mock_notification.id} - no valid responses"
        )

    @patch("notify_delivery.resources.utils.logger")
    def test_send_notification_empty_recipients(self, mock_logger):
        """Test send_notification when responses have no recipients."""
        mock_notification = Mock()
        mock_notification.id = "test123"
        mock_provider_class = Mock()
        mock_provider = Mock()
        mock_responses = Mock()
        mock_responses.recipients = []
        mock_provider.send.return_value = mock_responses
        mock_provider_class.return_value = mock_provider

        result = send_notification(mock_notification, mock_provider_class)

        assert result == mock_notification
        assert mock_notification.status_code == Notification.NotificationStatus.FAILURE
        mock_notification.update_notification.assert_called()
        mock_logger.warning.assert_called_with(
            f"Failed to send notification {mock_notification.id} - no valid responses"
        )

    @patch("notify_delivery.resources.utils.NotificationHistory")
    @patch("notify_delivery.resources.utils.logger")
    def test_send_notification_success(self, mock_logger, mock_history_class):
        """Test send_notification with successful send."""
        mock_notification = Mock()
        mock_notification.id = "test123"
        mock_provider_class = Mock()
        mock_provider = Mock()

        mock_response1 = Mock()
        mock_response1.recipient = "test1@example.com"
        mock_response1.response_id = "resp1"

        mock_response2 = Mock()
        mock_response2.recipient = "test2@example.com"
        mock_response2.response_id = "resp2"

        mock_responses = Mock()
        mock_responses.recipients = [mock_response1, mock_response2]
        mock_provider.send.return_value = mock_responses
        mock_provider_class.return_value = mock_provider

        mock_history = Mock()
        mock_history_class.create_history.return_value = mock_history

        result = send_notification(mock_notification, mock_provider_class)

        assert result == mock_history
        assert mock_notification.status_code == Notification.NotificationStatus.SENT
        mock_notification.update_notification.assert_called()
        mock_notification.delete_notification.assert_called()

        recipient_count = 2
        # Verify history created for each recipient
        assert mock_history_class.create_history.call_count == recipient_count
        mock_history_class.create_history.assert_any_call(mock_notification, "test1@example.com", "resp1")
        mock_history_class.create_history.assert_any_call(mock_notification, "test2@example.com", "resp2")

        mock_logger.info.assert_called_with(f"Notification {mock_notification.id} sent successfully to 2 recipients")
