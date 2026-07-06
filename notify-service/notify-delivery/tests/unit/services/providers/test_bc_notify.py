# Copyright © 2024 Province of British Columbia
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
"""Test suite for BC Notify service provider."""

import unittest
from unittest.mock import Mock, patch

from flask import Flask
from notifications_python_client.errors import HTTPError
from notify_api.models import Notification
from notify_api.models.content import Content as NotificationContent

from notify_delivery.services.providers.bc_notify import BCNotify
from notify_delivery.services.providers.gc_notify import GCNotify

# ---------------------------------------------------------------------------
# Shared valid-looking GC Notify API key format used across tests
# ---------------------------------------------------------------------------
_VALID_API_KEY = "a1b2c3d4-e5f6-g7h8-i9j0-k1l2m3n4o5p6-q1r2s3t4-u5v6-w7x8-y9z0-a1b2c3d4e5f6"
_GC_NOTIFY_URL = "https://api.notification.alpha.canada.ca"


class TestBCNotify(unittest.TestCase):
    """Test suite for BC Notify service provider."""

    def setUp(self):
        """Set up test fixtures with both BC Notify and base GC Notify config keys."""
        self.app = Flask(__name__)
        self.app.config.update(
            {
                # BC Notify-specific keys
                "BC_NOTIFY_API_KEY": _VALID_API_KEY,
                "BC_NOTIFY_TEMPLATE_ID": "bc_notify_template_123",
                "BC_NOTIFY_EMAIL_REPLY_TO_ID": "bc_notify_reply_to_456",
                # Base GC Notify fallback keys
                "GC_NOTIFY_API_KEY": _VALID_API_KEY,
                "GC_NOTIFY_API_URL": _GC_NOTIFY_URL,
                "GC_NOTIFY_TEMPLATE_ID": "default_template",
                "GC_NOTIFY_EMAIL_REPLY_TO_ID": "default_reply_to",
                "DEPLOYMENT_ENV": "production",
            }
        )
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        """Clean up test fixtures."""
        self.app_context.pop()

    # ------------------------------------------------------------------
    # Initialisation tests
    # ------------------------------------------------------------------

    @patch("notify_delivery.services.providers.bc_notify.NotificationsAPIClient")
    @patch("notify_delivery.services.providers.gc_notify.NotificationsAPIClient")
    def test_init_bc_notify_config_override(self, mock_base_client, mock_bc_client):
        """BCNotify should pick up BC-specific config when all three keys are present."""
        mock_notification = Mock(spec=Notification)

        bc_notify = BCNotify(mock_notification)

        self.assertEqual(bc_notify.api_key, _VALID_API_KEY)
        self.assertEqual(bc_notify.gc_notify_template_id, "bc_notify_template_123")
        self.assertEqual(bc_notify.gc_notify_email_reply_to_id, "bc_notify_reply_to_456")
        # The re-initialised client should use the BC Notify API key
        mock_bc_client.assert_called_once_with(api_key=_VALID_API_KEY, base_url=_GC_NOTIFY_URL)

    @patch("notify_delivery.services.providers.bc_notify.NotificationsAPIClient")
    @patch("notify_delivery.services.providers.gc_notify.NotificationsAPIClient")
    def test_init_bc_notify_config_missing_falls_back_to_gc_notify_defaults(self, mock_base_client, mock_bc_client):
        """BCNotify should fall back to GC Notify defaults when BC-specific keys are absent."""
        self.app.config.pop("BC_NOTIFY_API_KEY", None)
        self.app.config.pop("BC_NOTIFY_TEMPLATE_ID", None)
        self.app.config.pop("BC_NOTIFY_EMAIL_REPLY_TO_ID", None)
        mock_notification = Mock(spec=Notification)

        bc_notify = BCNotify(mock_notification)

        self.assertEqual(bc_notify.api_key, _VALID_API_KEY)
        self.assertEqual(bc_notify.gc_notify_template_id, "default_template")
        self.assertEqual(bc_notify.gc_notify_email_reply_to_id, "default_reply_to")
        # Client should still be created with the fallback key
        mock_bc_client.assert_called_once_with(api_key=_VALID_API_KEY, base_url=_GC_NOTIFY_URL)

    @patch("notify_delivery.services.providers.bc_notify.NotificationsAPIClient")
    @patch("notify_delivery.services.providers.gc_notify.NotificationsAPIClient")
    def test_init_no_api_key_client_is_none(self, mock_base_client, mock_bc_client):
        """BCNotify should set client to None and emit a warning when no API key exists."""
        self.app.config.pop("BC_NOTIFY_API_KEY", None)
        self.app.config.pop("GC_NOTIFY_API_KEY", None)
        mock_notification = Mock(spec=Notification)

        bc_notify = BCNotify(mock_notification)

        self.assertIsNone(bc_notify.api_key)
        self.assertIsNone(bc_notify.client)
        mock_bc_client.assert_not_called()

    @patch("notify_delivery.services.providers.bc_notify.NotificationsAPIClient")
    @patch("notify_delivery.services.providers.gc_notify.NotificationsAPIClient")
    def test_init_empty_bc_notify_config_falls_back_to_defaults(self, mock_base_client, mock_bc_client):
        """Blank (empty-string) BC Notify values should fall back to GC Notify defaults."""
        self.app.config.update(
            {
                "BC_NOTIFY_API_KEY": "",
                "BC_NOTIFY_TEMPLATE_ID": "",
                "BC_NOTIFY_EMAIL_REPLY_TO_ID": "",
            }
        )
        mock_notification = Mock(spec=Notification)

        bc_notify = BCNotify(mock_notification)

        self.assertEqual(bc_notify.gc_notify_template_id, "default_template")
        self.assertEqual(bc_notify.gc_notify_email_reply_to_id, "default_reply_to")

    @patch("notify_delivery.services.providers.bc_notify.NotificationsAPIClient")
    @patch("notify_delivery.services.providers.gc_notify.NotificationsAPIClient")
    def test_init_partial_bc_notify_config(self, mock_base_client, mock_bc_client):
        """When only the BC Notify API key is set, template/reply-to should fall back."""
        self.app.config.pop("BC_NOTIFY_TEMPLATE_ID", None)
        self.app.config.pop("BC_NOTIFY_EMAIL_REPLY_TO_ID", None)
        mock_notification = Mock(spec=Notification)

        bc_notify = BCNotify(mock_notification)

        self.assertEqual(bc_notify.api_key, _VALID_API_KEY)
        self.assertEqual(bc_notify.gc_notify_template_id, "default_template")
        self.assertEqual(bc_notify.gc_notify_email_reply_to_id, "default_reply_to")

    # ------------------------------------------------------------------
    # Inheritance tests
    # ------------------------------------------------------------------

    def test_bc_notify_inherits_from_gc_notify(self):
        """BCNotify must inherit GCNotify so send() and _prepare_personalisation() are available."""
        mock_notification = Mock(spec=Notification)
        bc_notify = BCNotify(mock_notification)

        self.assertIsInstance(bc_notify, GCNotify)
        self.assertTrue(hasattr(bc_notify, "send"))
        self.assertTrue(hasattr(bc_notify, "_prepare_personalisation"))

    def test_bc_notify_config_keys_constant(self):
        """BC_NOTIFY_CONFIG_KEYS should map the expected environment-variable names."""
        expected = {
            "api_key": "BC_NOTIFY_API_KEY",
            "template_id": "BC_NOTIFY_TEMPLATE_ID",
            "reply_to_id": "BC_NOTIFY_EMAIL_REPLY_TO_ID",
        }
        self.assertEqual(BCNotify.BC_NOTIFY_CONFIG_KEYS, expected)

    # ------------------------------------------------------------------
    # Send / integration tests
    # ------------------------------------------------------------------

    @patch("notify_delivery.services.providers.bc_notify.NotificationsAPIClient")
    @patch("notify_delivery.services.providers.gc_notify.NotificationsAPIClient")
    def test_send_uses_bc_notify_template(self, mock_base_client, mock_bc_client):
        """send() should use the BC-specific template ID and reply-to ID."""
        mock_content = Mock(spec=NotificationContent)
        mock_content.subject = "BC Notify Test"
        mock_content.body = "Plain text body"
        mock_content.attachments = None

        mock_notification = Mock(spec=Notification)
        mock_notification.content = [mock_content]
        mock_notification.recipients = "user@example.com"

        mock_client_instance = Mock()
        mock_client_instance.send_email_notification.return_value = {"id": "bc-response-id"}
        mock_bc_client.return_value = mock_client_instance

        bc_notify = BCNotify(mock_notification)
        result = bc_notify.send()

        self.assertIsNotNone(result)
        self.assertEqual(len(result.recipients), 1)
        self.assertEqual(result.recipients[0].response_id, "bc-response-id")
        self.assertEqual(result.recipients[0].recipient, "user@example.com")

        call_kwargs = mock_client_instance.send_email_notification.call_args.kwargs
        self.assertEqual(call_kwargs["template_id"], "bc_notify_template_123")
        self.assertEqual(call_kwargs["email_reply_to_id"], "bc_notify_reply_to_456")

    @patch("notify_delivery.services.providers.bc_notify.NotificationsAPIClient")
    @patch("notify_delivery.services.providers.gc_notify.NotificationsAPIClient")
    def test_send_multiple_recipients(self, mock_base_client, mock_bc_client):
        """send() should send to every recipient and return a response per recipient."""
        mock_content = Mock(spec=NotificationContent)
        mock_content.subject = "Subject"
        mock_content.body = "Body"
        mock_content.attachments = None

        mock_notification = Mock(spec=Notification)
        mock_notification.content = [mock_content]
        mock_notification.recipients = "alice@example.com, bob@example.com"

        mock_client_instance = Mock()
        mock_client_instance.send_email_notification.side_effect = [
            {"id": "id-alice"},
            {"id": "id-bob"},
        ]
        mock_bc_client.return_value = mock_client_instance

        bc_notify = BCNotify(mock_notification)
        result = bc_notify.send()

        self.assertEqual(len(result.recipients), 2)
        self.assertEqual(mock_client_instance.send_email_notification.call_count, 2)

    @patch("notify_delivery.services.providers.bc_notify.NotificationsAPIClient")
    @patch("notify_delivery.services.providers.gc_notify.NotificationsAPIClient")
    def test_send_no_content_returns_empty(self, mock_base_client, mock_bc_client):
        """send() should return an empty recipients list when notification has no content."""
        mock_notification = Mock(spec=Notification)
        mock_notification.content = []
        mock_notification.recipients = "user@example.com"

        bc_notify = BCNotify(mock_notification)
        result = bc_notify.send()

        self.assertEqual(len(result.recipients), 0)
        mock_bc_client.return_value.send_email_notification.assert_not_called()

    @patch("notify_delivery.services.providers.gc_notify.time.sleep")
    @patch("notify_delivery.services.providers.bc_notify.NotificationsAPIClient")
    @patch("notify_delivery.services.providers.gc_notify.NotificationsAPIClient")
    def test_send_retries_on_rate_limit(self, mock_base_client, mock_bc_client, mock_sleep):
        """send() should retry when the API returns a 429 rate-limit response."""
        mock_content = Mock(spec=NotificationContent)
        mock_content.subject = "Subject"
        mock_content.body = "Body"
        mock_content.attachments = None

        mock_notification = Mock(spec=Notification)
        mock_notification.content = [mock_content]
        mock_notification.recipients = "user@example.com"

        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.json.return_value = {"errors": [{"error": "RateLimitError", "message": "Exceeded rate limit"}]}
        rate_limit_error = HTTPError(response=mock_response)

        mock_client_instance = Mock()
        mock_client_instance.send_email_notification.side_effect = [
            rate_limit_error,
            {"id": "success-after-retry"},
        ]
        mock_bc_client.return_value = mock_client_instance

        bc_notify = BCNotify(mock_notification)
        result = bc_notify.send()

        self.assertEqual(len(result.recipients), 1)
        self.assertEqual(result.recipients[0].response_id, "success-after-retry")
        mock_sleep.assert_called_once()

    @patch("notify_delivery.services.providers.bc_notify.NotificationsAPIClient")
    @patch("notify_delivery.services.providers.gc_notify.NotificationsAPIClient")
    def test_get_bc_notify_config_value_whitespace_only_falls_back(self, mock_base_client, mock_bc_client):
        """Config values that are whitespace-only should be treated as absent."""
        self.app.config.update(
            {
                "BC_NOTIFY_TEMPLATE_ID": "   ",
                "BC_NOTIFY_EMAIL_REPLY_TO_ID": "\t",
            }
        )
        mock_notification = Mock(spec=Notification)

        bc_notify = BCNotify(mock_notification)

        self.assertEqual(bc_notify.gc_notify_template_id, "default_template")
        self.assertEqual(bc_notify.gc_notify_email_reply_to_id, "default_reply_to")
