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
"""Test suite for GC Notify service provider."""

import unittest
from unittest.mock import MagicMock, Mock, patch

from flask import Flask
from notifications_python_client.errors import HTTPError
from notify_api.models import Notification
from notify_api.models.content import Content as NotificationContent

from notify_delivery.services.providers.gc_notify import GCNotify


class TestGCNotify(unittest.TestCase):
    """Test suite for GC Notify service provider."""

    def setUp(self):
        """Set up test fixtures."""
        self.app = Flask(__name__)
        self.app.config.update(
            {
                "GC_NOTIFY_API_KEY": "test_api_key",
                "GC_NOTIFY_API_URL": "https://api.notification.alpha.canada.ca",
                "GC_NOTIFY_TEMPLATE_ID": "template_123",
                "GC_NOTIFY_EMAIL_REPLY_TO_ID": "reply_to_456",
                "DEPLOYMENT_ENV": "dev",
            }
        )
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        """Clean up test fixtures."""
        self.app_context.pop()

    @patch("notify_delivery.services.providers.gc_notify.NotificationsAPIClient")
    def test_send_no_content(self, mock_notifications_client):
        """Test sending with no notification content."""
        notification = MagicMock(spec=Notification)
        notification.content = []
        notification.recipients = "test@example.com"
        gc_notify = GCNotify(notification)
        responses = gc_notify.send()
        self.assertEqual(len(responses.recipients), 0)
        mock_notifications_client.return_value.send_email_notification.assert_not_called()

    @patch("notify_delivery.services.providers.gc_notify.NotificationsAPIClient")
    def test_send_invalid_content_structure(self, mock_notifications_client):
        """Test sending with invalid content structure."""
        content = MagicMock(spec=NotificationContent)
        del content.subject
        notification = MagicMock(spec=Notification)
        notification.recipients = "test@example.com"
        notification.content = [content]
        gc_notify = GCNotify(notification)
        responses = gc_notify.send()
        self.assertEqual(len(responses.recipients), 0)
        mock_notifications_client.return_value.send_email_notification.assert_not_called()

    @patch("notify_delivery.services.providers.gc_notify.NotificationsAPIClient")
    def test_send_with_attachments(self, mock_notifications_client):
        """Test sending with attachments."""
        attachment = MagicMock()
        attachment.file_bytes = b"test file content"
        attachment.file_name = "test.pdf"
        content = MagicMock(spec=NotificationContent)
        content.subject = "Test Subject"
        content.body = "Test Body"
        content.attachments = [attachment]
        notification = MagicMock(spec=Notification)
        notification.recipients = "test@example.com"
        notification.content = [content]
        gc_notify = GCNotify(notification)
        gc_notify.send()
        mock_notifications_client.return_value.send_email_notification.assert_called_once()
        personalisation = mock_notifications_client.return_value.send_email_notification.call_args.kwargs[
            "personalisation"
        ]
        self.assertIn("attachment1", personalisation)
        self.assertEqual(personalisation["attachment1"]["filename"], "test.pdf")

    @patch("notify_delivery.services.providers.gc_notify.NotificationsAPIClient")
    def test_send_multiple_recipients(self, mock_notifications_client):
        """Test sending to multiple recipients."""
        content = MagicMock(spec=NotificationContent)
        content.subject = "Test Subject"
        content.body = "Test Body"
        content.attachments = None
        notification = MagicMock(spec=Notification)
        notification.recipients = "test1@example.com, test2@example.com"
        notification.content = [content]
        gc_notify = GCNotify(notification)
        gc_notify.send()
        self.assertEqual(
            mock_notifications_client.return_value.send_email_notification.call_count,
            2,
        )

    @patch("notify_delivery.services.providers.gc_notify.NotificationsAPIClient")
    def test_send_exception_handling(self, mock_notifications_client):
        """Test exception handling during send."""
        mock_notifications_client.return_value.send_email_notification.side_effect = Exception("Test error")
        content = MagicMock(spec=NotificationContent)
        content.subject = "Test Subject"
        content.body = "Test Body"
        content.attachments = None
        notification = MagicMock(spec=Notification)
        notification.recipients = "test@example.com"
        notification.content = [content]
        gc_notify = GCNotify(notification)
        responses = gc_notify.send()
        self.assertEqual(len(responses.recipients), 0)

    @patch("notify_delivery.services.providers.gc_notify.time.sleep")
    @patch("notify_delivery.services.providers.gc_notify.NotificationsAPIClient")
    def test_send_retries_on_rate_limit(self, mock_notifications_client, mock_sleep):
        """Test that 429 rate limit errors trigger retry with backoff."""
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.json.return_value = {"errors": [{"error": "RateLimitError", "message": "Exceeded rate limit"}]}
        rate_limit_error = HTTPError(response=mock_response)

        mock_client = mock_notifications_client.return_value
        mock_client.send_email_notification.side_effect = [
            rate_limit_error,
            rate_limit_error,
            {"id": "success-id"},
        ]

        content = MagicMock(spec=NotificationContent)
        content.subject = "Test Subject"
        content.body = "Test Body"
        content.attachments = None
        notification = MagicMock(spec=Notification)
        notification.recipients = "test@example.com"
        notification.content = [content]

        gc_notify = GCNotify(notification)
        responses = gc_notify.send()

        self.assertEqual(len(responses.recipients), 1)
        self.assertEqual(responses.recipients[0].response_id, "success-id")
        self.assertEqual(mock_client.send_email_notification.call_count, 3)
        self.assertEqual(mock_sleep.call_count, 2)
        mock_sleep.assert_any_call(10)
        mock_sleep.assert_any_call(20)

    @patch("notify_delivery.services.providers.gc_notify.time.sleep")
    @patch("notify_delivery.services.providers.gc_notify.NotificationsAPIClient")
    def test_send_raises_after_max_retries(self, mock_notifications_client, mock_sleep):
        """Test that 429 errors raise after exhausting retries."""
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.json.return_value = {"errors": [{"error": "RateLimitError", "message": "Exceeded rate limit"}]}
        rate_limit_error = HTTPError(response=mock_response)

        mock_client = mock_notifications_client.return_value
        mock_client.send_email_notification.side_effect = rate_limit_error

        content = MagicMock(spec=NotificationContent)
        content.subject = "Test Subject"
        content.body = "Test Body"
        content.attachments = None
        notification = MagicMock(spec=Notification)
        notification.recipients = "test@example.com"
        notification.content = [content]

        gc_notify = GCNotify(notification)
        responses = gc_notify.send()

        self.assertEqual(len(responses.recipients), 0)
        self.assertEqual(mock_client.send_email_notification.call_count, 4)  # 1 initial + 3 retries
        self.assertEqual(mock_sleep.call_count, 3)

    @patch("notify_delivery.services.providers.gc_notify.time.sleep")
    @patch("notify_delivery.services.providers.gc_notify.NotificationsAPIClient")
    def test_send_retries_on_503_server_error(self, mock_notifications_client, mock_sleep):
        """Test that 503 server errors trigger retry with backoff."""
        mock_response = Mock()
        mock_response.status_code = 503
        mock_response.json.return_value = {"errors": [{"error": "ServerError", "message": "Request failed"}]}
        server_error = HTTPError(response=mock_response)

        mock_client = mock_notifications_client.return_value
        mock_client.send_email_notification.side_effect = [
            server_error,
            {"id": "success-after-503"},
        ]

        content = MagicMock(spec=NotificationContent)
        content.subject = "Test Subject"
        content.body = "Test Body"
        content.attachments = None
        notification = MagicMock(spec=Notification)
        notification.recipients = "test@example.com"
        notification.content = [content]

        gc_notify = GCNotify(notification)
        responses = gc_notify.send()

        self.assertEqual(len(responses.recipients), 1)
        self.assertEqual(responses.recipients[0].response_id, "success-after-503")
        self.assertEqual(mock_client.send_email_notification.call_count, 2)
        mock_sleep.assert_called_once_with(10)
