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

import requests
from flask import Flask
from notify_api.models import Notification
from notify_api.models.content import Content as NotificationContent

from notify_delivery.services.providers.bc_notify import BCNotify

_VALID_API_KEY = "a1b2c3d4-e5f6-g7h8-i9j0-k1l2m3n4o5p6-q1r2s3t4-u5v6-w7x8-y9z0-a1b2c3d4e5f6"
_BC_NOTIFY_URL = "https://api.gov.bc.ca"


class TestBCNotify(unittest.TestCase):
    """Test suite for BC Notify service provider."""

    def setUp(self):
        """Set up BC Notify test configuration."""
        self.app = Flask(__name__)
        self.app.config.update(
            {
                "BC_NOTIFY_API_URL": _BC_NOTIFY_URL,
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
    def test_init_bc_notify_config(self, mock_post):
        """BCNotify should load its API configuration."""
        mock_notification = Mock(spec=Notification)

        bc_notify = BCNotify(mock_notification)

        self.assertEqual(bc_notify.bc_notify_url, _BC_NOTIFY_URL)
        self.assertEqual(bc_notify.api_key, _VALID_API_KEY)
        mock_post.assert_not_called()

    @patch("notify_delivery.services.providers.bc_notify.requests.post")
    def test_init_missing_api_key(self, mock_post):
        """BCNotify should leave a missing API key unset."""
        self.app.config.pop("BC_NOTIFY_API_KEY", None)
        mock_notification = Mock(spec=Notification)

        bc_notify = BCNotify(mock_notification)

        self.assertIsNone(bc_notify.api_key)
        mock_post.assert_not_called()

    @patch("notify_delivery.services.providers.bc_notify.requests.post")
    def test_init_no_api_key(self, mock_post):
        """BCNotify should initialize without an API key."""
        self.app.config.pop("BC_NOTIFY_API_KEY", None)
        mock_notification = Mock(spec=Notification)

        bc_notify = BCNotify(mock_notification)

        self.assertIsNone(bc_notify.api_key)
        mock_post.assert_not_called()

    def test_bc_notify_is_standalone_provider(self):
        """BCNotify should own the behavior required by the delivery service."""
        mock_notification = Mock(spec=Notification)
        bc_notify = BCNotify(mock_notification)

        self.assertTrue(hasattr(bc_notify, "send"))
        self.assertTrue(hasattr(bc_notify, "_send_with_retry"))

    def test_bc_notify_config_keys_constant(self):
        """BC_NOTIFY_CONFIG_KEYS should map the expected environment-variable names."""
        expected = {
            "api_url": "BC_NOTIFY_API_URL",
            "api_key": "BC_NOTIFY_API_KEY",
        }
        self.assertEqual(BCNotify.BC_NOTIFY_CONFIG_KEYS, expected)

    @patch("notify_delivery.services.providers.bc_notify.requests.post")
    def test_init_uses_bc_notify_api_gateway_url(self, mock_post):
        """BCNotify should use the BC gateway URL when BC_NOTIFY_API_URL is set."""
        self.app.config["BC_NOTIFY_API_URL"] = "https://api.gov.bc.ca"
        mock_notification = Mock(spec=Notification)

        bc_notify = BCNotify(mock_notification)

        self.assertEqual(bc_notify.bc_notify_url, "https://api.gov.bc.ca")
        mock_post.assert_not_called()

    # ------------------------------------------------------------------
    # Send / integration tests
    # ------------------------------------------------------------------

    @patch("notify_delivery.services.providers.bc_notify.requests.post")
    def test_send_uses_new_bc_notify_payload(self, mock_post):
        """send() should use the direct-email BC Notify payload."""
        mock_content = Mock(spec=NotificationContent)
        mock_content.subject = "BC Notify Test"
        mock_content.body = "Plain text body"
        mock_content.attachments = None

        mock_notification = Mock(spec=Notification)
        mock_notification.content = [mock_content]
        mock_notification.recipients = "user@example.com"

        mock_response = Mock()
        mock_response.json.return_value = {"id": "bc-response-id"}
        mock_response.status_code = 201
        mock_post.return_value = mock_response

        bc_notify = BCNotify(mock_notification)
        result = bc_notify.send()

        self.assertIsNotNone(result)
        self.assertEqual(len(result.recipients), 1)
        self.assertEqual(result.recipients[0].response_id, "bc-response-id")
        self.assertEqual(result.recipients[0].recipient, "user@example.com")

        call_kwargs = mock_post.call_args.kwargs
        self.assertEqual(
            call_kwargs["json"],
            {
                "recipients": {
                    "to": ["user@example.com"],
                    "bcc": [],
                },
                "content": {
                    "subject": "BC Notify Test",
                    "body": "Plain text body",
                    "bodyType": "html",
                },
            },
        )
        self.assertEqual(call_kwargs["headers"]["X-API-KEY"], _VALID_API_KEY)

    @patch("notify_delivery.services.providers.bc_notify.requests.post")
    def test_send_multiple_recipients(self, mock_post):
        """send() should send to every recipient and return a response per recipient."""
        mock_content = Mock(spec=NotificationContent)
        mock_content.subject = "Subject"
        mock_content.body = "Body"
        mock_content.attachments = None

        mock_notification = Mock(spec=Notification)
        mock_notification.content = [mock_content]
        mock_notification.recipients = "alice@example.com, bob@example.com"

        mock_resp_1 = Mock()
        mock_resp_1.json.return_value = {"id": "id-alice"}
        mock_resp_2 = Mock()
        mock_resp_2.json.return_value = {"id": "id-bob"}

        mock_post.side_effect = [mock_resp_1, mock_resp_2]

        bc_notify = BCNotify(mock_notification)
        result = bc_notify.send()

        self.assertEqual(len(result.recipients), 2)
        self.assertEqual(mock_post.call_count, 2)

    @patch("notify_delivery.services.providers.bc_notify.requests.post")
    def test_send_no_content_returns_empty(self, mock_post):
        """send() should return an empty recipients list when notification has no content."""
        mock_notification = Mock(spec=Notification)
        mock_notification.content = []
        mock_notification.recipients = "user@example.com"

        bc_notify = BCNotify(mock_notification)
        result = bc_notify.send()

        self.assertEqual(len(result.recipients), 0)
        mock_post.assert_not_called()

    @patch("notify_delivery.services.providers.bc_notify.time.sleep")
    @patch("notify_delivery.services.providers.bc_notify.requests.post")
    def test_send_retries_on_rate_limit(self, mock_post, mock_sleep):
        """send() should retry when the API returns a 429 rate-limit response."""
        mock_content = Mock(spec=NotificationContent)
        mock_content.subject = "Subject"
        mock_content.body = "Body"
        mock_content.attachments = None

        mock_notification = Mock(spec=Notification)
        mock_notification.content = [mock_content]
        mock_notification.recipients = "user@example.com"

        mock_error_resp = Mock()
        mock_error_resp.status_code = 429
        mock_error_resp.text = "Exceeded rate limit"
        rate_limit_error = requests.exceptions.HTTPError(response=mock_error_resp)

        mock_success_resp = Mock()
        mock_success_resp.json.return_value = {"id": "success-after-retry"}
        mock_success_resp.status_code = 200

        mock_post.side_effect = [
            rate_limit_error,
            mock_success_resp,
        ]

        bc_notify = BCNotify(mock_notification)
        result = bc_notify.send()

        self.assertEqual(len(result.recipients), 1)
        self.assertEqual(result.recipients[0].response_id, "success-after-retry")
        mock_sleep.assert_called_once()

    def test_get_bc_notify_config_value_whitespace_only_falls_back(self):
        """Config values that are whitespace-only should be treated as absent."""
        self.app.config["BC_NOTIFY_API_KEY"] = "   "
        mock_notification = Mock(spec=Notification)

        bc_notify = BCNotify(mock_notification)

        self.assertIsNone(bc_notify.api_key)
