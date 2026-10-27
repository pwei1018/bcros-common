# Copyright © 2026 Province of British Columbia
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
"""Test suite for BC Notify SMS provider."""

import unittest
from unittest.mock import Mock, patch

from flask import Flask
from notify_api.models import Notification
from notify_api.models.content import Content as NotificationContent

from notify_delivery.services.providers.bc_notify import BCNotify
from notify_delivery.services.providers.bc_notify_sms import BCNotifySMS

_API_KEY = "test-api-key"
_BC_NOTIFY_URL = "https://api.gov.bc.ca/"


class TestBCNotifySMS(unittest.TestCase):
    """Test suite for BC Notify SMS provider."""

    def setUp(self):
        """Set up BC Notify test configuration."""
        self.app = Flask(__name__)
        self.app.config.update(
            {
                "BC_NOTIFY_API_URL": _BC_NOTIFY_URL,
                "BC_NOTIFY_API_KEY": _API_KEY,
                "DEPLOYMENT_ENV": "development",
            }
        )
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        """Clean up test fixtures."""
        self.app_context.pop()

    def _notification(self, recipients="+12505550123"):
        content = Mock(spec=NotificationContent)
        content.subject = "SMS"
        content.body = "Your code is 1234"
        content.attachments = []
        notification = Mock(spec=Notification)
        notification.recipients = recipients
        notification.content = [content]
        return notification

    def test_inherits_from_bc_notify(self):
        """BCNotifySMS reuses the BC Notify configuration and retry behaviour."""
        self.assertTrue(issubclass(BCNotifySMS, BCNotify))

    @patch("notify_delivery.services.providers.bc_notify.requests.post")
    def test_send_uses_sms_endpoint_and_payload(self, mock_post):
        """send() posts each recipient to the notifysimple SMS endpoint."""
        mock_post.return_value.json.return_value = {"notifyId": "notify-1"}

        responses = BCNotifySMS(self._notification("+12505550123, +16045550147")).send()

        self.assertEqual([r.recipient for r in responses.recipients], ["+12505550123", "+16045550147"])
        self.assertEqual(responses.recipients[0].response_id, "notify-1")
        first_call = mock_post.call_args_list[0]
        self.assertEqual(first_call.args[0], "https://api.gov.bc.ca/api/v1/notifysimple/sms")
        self.assertEqual(first_call.kwargs["headers"]["X-API-KEY"], _API_KEY)
        self.assertEqual(
            first_call.kwargs["json"],
            {"sms": {"recipients": {"to": ["+12505550123"]}, "content": {"body": "Your code is 1234"}}},
        )

    @patch("notify_delivery.services.providers.bc_notify.requests.post")
    def test_send_without_config_returns_empty(self, mock_post):
        """Missing API key results in no responses and no request."""
        self.app.config["BC_NOTIFY_API_KEY"] = ""

        responses = BCNotifySMS(self._notification()).send()

        self.assertEqual(responses.recipients, [])
        mock_post.assert_not_called()
