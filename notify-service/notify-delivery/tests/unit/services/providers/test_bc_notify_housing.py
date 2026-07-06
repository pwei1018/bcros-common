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
"""Test suite for BC Notify Housing service provider."""

import unittest
from unittest.mock import Mock, patch

from flask import Flask
from notify_api.models import Notification
from notify_api.models.content import Content as NotificationContent

from notify_delivery.services.providers.bc_notify import BCNotify
from notify_delivery.services.providers.bc_notify_housing import BCNotifyHousing
from notify_delivery.services.providers.gc_notify import GCNotify

# ---------------------------------------------------------------------------
# Shared valid-looking GC Notify API key format used across tests
# ---------------------------------------------------------------------------
_VALID_API_KEY = "a1b2c3d4-e5f6-g7h8-i9j0-k1l2m3n4o5p6-q1r2s3t4-u5v6-w7x8-y9z0-a1b2c3d4e5f6"
_GC_NOTIFY_URL = "https://api.notification.alpha.canada.ca"


class TestBCNotifyHousing(unittest.TestCase):
    """Test suite for BC Notify Housing service provider."""

    def setUp(self):
        """Set up test fixtures with BC Notify Housing, BC Notify and base GC Notify config keys."""
        self.app = Flask(__name__)
        self.app.config.update(
            {
                # BC Notify Housing-specific keys
                "BC_NOTIFY_HOUSING_API_KEY": _VALID_API_KEY,
                "BC_NOTIFY_HOUSING_TEMPLATE_ID": "bc_notify_housing_template_123",
                "BC_NOTIFY_HOUSING_EMAIL_REPLY_TO_ID": "bc_notify_housing_reply_to_456",
                # BC Notify fallback keys
                "BC_NOTIFY_API_KEY": _VALID_API_KEY,
                "BC_NOTIFY_TEMPLATE_ID": "bc_notify_template",
                "BC_NOTIFY_EMAIL_REPLY_TO_ID": "bc_notify_reply_to",
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

    @patch("notify_delivery.services.providers.bc_notify_housing.NotificationsAPIClient")
    @patch("notify_delivery.services.providers.bc_notify.NotificationsAPIClient")
    @patch("notify_delivery.services.providers.gc_notify.NotificationsAPIClient")
    def test_init_housing_config_override(self, mock_base_client, mock_bc_client, mock_housing_client):
        """BCNotifyHousing should pick up housing-specific config when present."""
        mock_notification = Mock(spec=Notification)

        housing = BCNotifyHousing(mock_notification)

        self.assertEqual(housing.api_key, _VALID_API_KEY)
        self.assertEqual(housing.gc_notify_template_id, "bc_notify_housing_template_123")
        self.assertEqual(housing.gc_notify_email_reply_to_id, "bc_notify_housing_reply_to_456")
        mock_housing_client.assert_called_once_with(api_key=_VALID_API_KEY, base_url=_GC_NOTIFY_URL)

    @patch("notify_delivery.services.providers.bc_notify_housing.NotificationsAPIClient")
    @patch("notify_delivery.services.providers.bc_notify.NotificationsAPIClient")
    @patch("notify_delivery.services.providers.gc_notify.NotificationsAPIClient")
    def test_init_housing_config_missing_falls_back_to_bc_notify(
        self, mock_base_client, mock_bc_client, mock_housing_client
    ):
        """Missing housing keys should fall back to the BC Notify (non-housing) values."""
        self.app.config.pop("BC_NOTIFY_HOUSING_API_KEY", None)
        self.app.config.pop("BC_NOTIFY_HOUSING_TEMPLATE_ID", None)
        self.app.config.pop("BC_NOTIFY_HOUSING_EMAIL_REPLY_TO_ID", None)
        mock_notification = Mock(spec=Notification)

        housing = BCNotifyHousing(mock_notification)

        self.assertEqual(housing.api_key, _VALID_API_KEY)
        self.assertEqual(housing.gc_notify_template_id, "bc_notify_template")
        self.assertEqual(housing.gc_notify_email_reply_to_id, "bc_notify_reply_to")

    @patch("notify_delivery.services.providers.bc_notify_housing.NotificationsAPIClient")
    @patch("notify_delivery.services.providers.bc_notify.NotificationsAPIClient")
    @patch("notify_delivery.services.providers.gc_notify.NotificationsAPIClient")
    def test_init_housing_and_bc_missing_falls_back_to_gc_notify_defaults(
        self, mock_base_client, mock_bc_client, mock_housing_client
    ):
        """When both housing and BC Notify keys are absent, GC Notify defaults are used."""
        for key in (
            "BC_NOTIFY_HOUSING_API_KEY",
            "BC_NOTIFY_HOUSING_TEMPLATE_ID",
            "BC_NOTIFY_HOUSING_EMAIL_REPLY_TO_ID",
            "BC_NOTIFY_API_KEY",
            "BC_NOTIFY_TEMPLATE_ID",
            "BC_NOTIFY_EMAIL_REPLY_TO_ID",
        ):
            self.app.config.pop(key, None)
        mock_notification = Mock(spec=Notification)

        housing = BCNotifyHousing(mock_notification)

        self.assertEqual(housing.api_key, _VALID_API_KEY)
        self.assertEqual(housing.gc_notify_template_id, "default_template")
        self.assertEqual(housing.gc_notify_email_reply_to_id, "default_reply_to")

    @patch("notify_delivery.services.providers.bc_notify_housing.NotificationsAPIClient")
    @patch("notify_delivery.services.providers.bc_notify.NotificationsAPIClient")
    @patch("notify_delivery.services.providers.gc_notify.NotificationsAPIClient")
    def test_init_no_api_key_client_is_none(self, mock_base_client, mock_bc_client, mock_housing_client):
        """No API key anywhere should leave the client as None."""
        for key in ("BC_NOTIFY_HOUSING_API_KEY", "BC_NOTIFY_API_KEY", "GC_NOTIFY_API_KEY"):
            self.app.config.pop(key, None)
        mock_notification = Mock(spec=Notification)

        housing = BCNotifyHousing(mock_notification)

        self.assertIsNone(housing.api_key)
        self.assertIsNone(housing.client)
        mock_housing_client.assert_not_called()

    @patch("notify_delivery.services.providers.bc_notify_housing.NotificationsAPIClient")
    @patch("notify_delivery.services.providers.bc_notify.NotificationsAPIClient")
    @patch("notify_delivery.services.providers.gc_notify.NotificationsAPIClient")
    def test_init_empty_housing_config_falls_back(self, mock_base_client, mock_bc_client, mock_housing_client):
        """Blank housing values should fall back to BC Notify values."""
        self.app.config.update(
            {
                "BC_NOTIFY_HOUSING_API_KEY": "",
                "BC_NOTIFY_HOUSING_TEMPLATE_ID": "",
                "BC_NOTIFY_HOUSING_EMAIL_REPLY_TO_ID": "",
            }
        )
        mock_notification = Mock(spec=Notification)

        housing = BCNotifyHousing(mock_notification)

        self.assertEqual(housing.gc_notify_template_id, "bc_notify_template")
        self.assertEqual(housing.gc_notify_email_reply_to_id, "bc_notify_reply_to")

    @patch("notify_delivery.services.providers.bc_notify_housing.NotificationsAPIClient")
    @patch("notify_delivery.services.providers.bc_notify.NotificationsAPIClient")
    @patch("notify_delivery.services.providers.gc_notify.NotificationsAPIClient")
    def test_init_whitespace_housing_config_falls_back(self, mock_base_client, mock_bc_client, mock_housing_client):
        """Whitespace-only housing values should be treated as absent."""
        self.app.config.update(
            {
                "BC_NOTIFY_HOUSING_TEMPLATE_ID": "   ",
                "BC_NOTIFY_HOUSING_EMAIL_REPLY_TO_ID": "\t",
            }
        )
        mock_notification = Mock(spec=Notification)

        housing = BCNotifyHousing(mock_notification)

        self.assertEqual(housing.gc_notify_template_id, "bc_notify_template")
        self.assertEqual(housing.gc_notify_email_reply_to_id, "bc_notify_reply_to")

    # ------------------------------------------------------------------
    # Inheritance tests
    # ------------------------------------------------------------------

    def test_inherits_from_bc_notify_and_gc_notify(self):
        """BCNotifyHousing must inherit from BCNotify (and therefore GCNotify)."""
        mock_notification = Mock(spec=Notification)
        housing = BCNotifyHousing(mock_notification)

        self.assertIsInstance(housing, BCNotify)
        self.assertIsInstance(housing, GCNotify)
        self.assertTrue(hasattr(housing, "send"))
        self.assertTrue(hasattr(housing, "_prepare_personalisation"))

    def test_bc_notify_housing_config_keys_constant(self):
        """BC_NOTIFY_HOUSING_CONFIG_KEYS should map the expected environment-variable names."""
        expected = {
            "api_key": "BC_NOTIFY_HOUSING_API_KEY",
            "template_id": "BC_NOTIFY_HOUSING_TEMPLATE_ID",
            "reply_to_id": "BC_NOTIFY_HOUSING_EMAIL_REPLY_TO_ID",
        }
        self.assertEqual(BCNotifyHousing.BC_NOTIFY_HOUSING_CONFIG_KEYS, expected)

    # ------------------------------------------------------------------
    # Send / integration tests
    # ------------------------------------------------------------------

    @patch("notify_delivery.services.providers.bc_notify_housing.NotificationsAPIClient")
    @patch("notify_delivery.services.providers.bc_notify.NotificationsAPIClient")
    @patch("notify_delivery.services.providers.gc_notify.NotificationsAPIClient")
    def test_send_uses_housing_template(self, mock_base_client, mock_bc_client, mock_housing_client):
        """send() should use the housing-specific template ID and reply-to ID."""
        mock_content = Mock(spec=NotificationContent)
        mock_content.subject = "Housing Test"
        mock_content.body = "Plain text body"
        mock_content.attachments = None

        mock_notification = Mock(spec=Notification)
        mock_notification.content = [mock_content]
        mock_notification.recipients = "user@example.com"

        mock_client_instance = Mock()
        mock_client_instance.send_email_notification.return_value = {"id": "housing-response-id"}
        mock_housing_client.return_value = mock_client_instance

        housing = BCNotifyHousing(mock_notification)
        result = housing.send()

        self.assertIsNotNone(result)
        self.assertEqual(len(result.recipients), 1)
        self.assertEqual(result.recipients[0].response_id, "housing-response-id")

        call_kwargs = mock_client_instance.send_email_notification.call_args.kwargs
        self.assertEqual(call_kwargs["template_id"], "bc_notify_housing_template_123")
        self.assertEqual(call_kwargs["email_reply_to_id"], "bc_notify_housing_reply_to_456")

    @patch("notify_delivery.services.providers.bc_notify_housing.NotificationsAPIClient")
    @patch("notify_delivery.services.providers.bc_notify.NotificationsAPIClient")
    @patch("notify_delivery.services.providers.gc_notify.NotificationsAPIClient")
    def test_send_no_content_returns_empty(self, mock_base_client, mock_bc_client, mock_housing_client):
        """send() should return an empty recipients list when notification has no content."""
        mock_notification = Mock(spec=Notification)
        mock_notification.content = []
        mock_notification.recipients = "user@example.com"

        housing = BCNotifyHousing(mock_notification)
        result = housing.send()

        self.assertEqual(len(result.recipients), 0)
        mock_housing_client.return_value.send_email_notification.assert_not_called()
