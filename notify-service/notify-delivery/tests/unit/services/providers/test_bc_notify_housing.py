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

_VALID_API_KEY = "a1b2c3d4-e5f6-g7h8-i9j0-k1l2m3n4o5p6-q1r2s3t4-u5v6-w7x8-y9z0-a1b2c3d4e5f6"
_BC_NOTIFY_URL = "https://api.gov.bc.ca"


class TestBCNotifyHousing(unittest.TestCase):
    """Test suite for BC Notify Housing service provider."""

    def setUp(self):
        """Set up BC Notify Housing and base BC Notify configuration."""
        self.app = Flask(__name__)
        self.app.config.update(
            {
                "BC_NOTIFY_API_URL": _BC_NOTIFY_URL,
                "BC_NOTIFY_HOUSING_API_KEY": _VALID_API_KEY,
                "BC_NOTIFY_API_KEY": _VALID_API_KEY,
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

    @patch("notify_delivery.services.providers.bc_notify.requests.post")
    def test_init_housing_config_override(self, mock_post):
        """BCNotifyHousing should pick up housing-specific config when present."""
        mock_notification = Mock(spec=Notification)

        housing = BCNotifyHousing(mock_notification)

        self.assertEqual(housing.api_key, _VALID_API_KEY)
        mock_post.assert_not_called()

    @patch("notify_delivery.services.providers.bc_notify.requests.post")
    def test_init_housing_config_missing_falls_back_to_bc_notify(self, mock_post):
        """Missing housing keys should fall back to the BC Notify (non-housing) values."""
        self.app.config.pop("BC_NOTIFY_HOUSING_API_KEY", None)
        mock_notification = Mock(spec=Notification)

        housing = BCNotifyHousing(mock_notification)

        self.assertEqual(housing.api_key, _VALID_API_KEY)

    @patch("notify_delivery.services.providers.bc_notify.requests.post")
    def test_init_housing_and_bc_api_keys_missing(self, mock_post):
        """When both BC API keys are absent, the API key remains unset."""
        for key in ("BC_NOTIFY_HOUSING_API_KEY", "BC_NOTIFY_API_KEY"):
            self.app.config.pop(key, None)
        mock_notification = Mock(spec=Notification)

        housing = BCNotifyHousing(mock_notification)

        self.assertIsNone(housing.api_key)
        mock_post.assert_not_called()

    @patch("notify_delivery.services.providers.bc_notify.requests.post")
    def test_init_empty_housing_config_falls_back(self, mock_post):
        """Blank housing values should fall back to BC Notify values."""
        self.app.config["BC_NOTIFY_HOUSING_API_KEY"] = ""
        mock_notification = Mock(spec=Notification)

        housing = BCNotifyHousing(mock_notification)

        self.assertEqual(housing.api_key, _VALID_API_KEY)

    @patch("notify_delivery.services.providers.bc_notify.requests.post")
    def test_init_whitespace_housing_config_falls_back(self, mock_post):
        """Whitespace-only housing values should be treated as absent."""
        self.app.config["BC_NOTIFY_HOUSING_API_KEY"] = "   "
        mock_notification = Mock(spec=Notification)

        housing = BCNotifyHousing(mock_notification)

        self.assertEqual(housing.api_key, _VALID_API_KEY)

    # ------------------------------------------------------------------
    # Inheritance tests
    # ------------------------------------------------------------------

    def test_inherits_from_bc_notify(self):
        """BCNotifyHousing should inherit the BC Notify delivery behavior."""
        mock_notification = Mock(spec=Notification)
        housing = BCNotifyHousing(mock_notification)

        self.assertIsInstance(housing, BCNotify)
        self.assertTrue(hasattr(housing, "send"))
        self.assertTrue(hasattr(housing, "_send_with_retry"))

    def test_bc_notify_housing_config_keys_constant(self):
        """BC_NOTIFY_HOUSING_CONFIG_KEYS should map the expected environment-variable names."""
        expected = {
            "api_key": "BC_NOTIFY_HOUSING_API_KEY",
        }
        self.assertEqual(BCNotifyHousing.BC_NOTIFY_HOUSING_CONFIG_KEYS, expected)

    # ------------------------------------------------------------------
    # Send / integration tests
    # ------------------------------------------------------------------

    @patch("notify_delivery.services.providers.bc_notify.requests.post")
    def test_send_uses_new_bc_notify_payload(self, mock_post):
        """send() should use the direct-email BC Notify payload."""
        mock_content = Mock(spec=NotificationContent)
        mock_content.subject = "Housing Test"
        mock_content.body = "Plain text body"
        mock_content.attachments = None

        mock_notification = Mock(spec=Notification)
        mock_notification.content = [mock_content]
        mock_notification.recipients = "user@example.com"

        mock_response = Mock()
        mock_response.json.return_value = {"id": "housing-response-id"}
        mock_response.status_code = 201
        mock_post.return_value = mock_response

        housing = BCNotifyHousing(mock_notification)
        result = housing.send()

        self.assertIsNotNone(result)
        self.assertEqual(len(result.recipients), 1)
        self.assertEqual(result.recipients[0].response_id, "housing-response-id")

        call_kwargs = mock_post.call_args.kwargs
        self.assertEqual(
            call_kwargs["json"],
            {
                "recipients": {
                    "to": ["user@example.com"],
                    "bcc": [],
                },
                "content": {
                    "subject": "Housing Test",
                    "body": "Plain text body",
                    "bodyType": "html",
                },
            },
        )

    @patch("notify_delivery.services.providers.bc_notify.requests.post")
    def test_send_no_content_returns_empty(self, mock_post):
        """send() should return an empty recipients list when notification has no content."""
        mock_notification = Mock(spec=Notification)
        mock_notification.content = []
        mock_notification.recipients = "user@example.com"

        housing = BCNotifyHousing(mock_notification)
        result = housing.send()

        self.assertEqual(len(result.recipients), 0)
        mock_post.assert_not_called()
