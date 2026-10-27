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
"""Test suite for BC Notify Housing SMS provider and resource."""

import unittest
from http import HTTPStatus
from unittest.mock import Mock, patch

from flask import Flask
from notify_api.models import Notification
from notify_api.models.content import Content as NotificationContent

from notify_delivery.resources.bc_notify_housing_sms import EXPECTED_EVENT_TYPE, bp, worker
from notify_delivery.services.providers.bc_notify_housing_sms import BCNotifyHousingSMS


class TestBCNotifyHousingSMS(unittest.TestCase):
    """Test suite for BC Notify Housing SMS."""

    def setUp(self):
        """Set up test configuration."""
        self.app = Flask(__name__)
        self.app.config.update(
            {
                "TESTING": True,
                "VERIFY_PUBSUB_VIA_JWT": False,
                "BC_NOTIFY_API_URL": "https://api.gov.bc.ca",
                "BC_NOTIFY_API_KEY": "bc-key",
                "BC_NOTIFY_HOUSING_API_KEY": "housing-key",
            }
        )
        self.app.register_blueprint(bp)
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        """Clean up test fixtures."""
        self.app_context.pop()

    def _notification(self):
        content = Mock(spec=NotificationContent)
        content.subject = "SMS"
        content.body = "Hello"
        content.attachments = []
        notification = Mock(spec=Notification)
        notification.recipients = "+12505550123"
        notification.content = [content]
        return notification

    @patch("notify_delivery.services.providers.bc_notify.requests.post")
    def test_send_uses_housing_key_and_sms_endpoint(self, mock_post):
        """Housing SMS posts to the SMS endpoint with the Housing API key."""
        mock_post.return_value.json.return_value = {"notifyId": "notify-1"}

        responses = BCNotifyHousingSMS(self._notification()).send()

        self.assertEqual(responses.recipients[0].response_id, "notify-1")
        call = mock_post.call_args
        self.assertEqual(call.args[0], "https://api.gov.bc.ca/api/v1/notifysimple/sms")
        self.assertEqual(call.kwargs["headers"]["X-API-KEY"], "housing-key")
        self.assertEqual(
            call.kwargs["json"], {"sms": {"recipients": {"to": ["+12505550123"]}, "content": {"body": "Hello"}}}
        )

    def test_falls_back_to_bc_notify_key(self):
        """Missing Housing API key falls back to the BC Notify key."""
        self.app.config["BC_NOTIFY_HOUSING_API_KEY"] = ""
        self.assertEqual(BCNotifyHousingSMS(self._notification()).api_key, "bc-key")

    @patch("notify_delivery.resources.bc_notify_housing_sms.get_cloud_event")
    @patch("notify_delivery.resources.bc_notify_housing_sms.validate_event_type", return_value=True)
    @patch("notify_delivery.resources.bc_notify_housing_sms.process_notification")
    def test_worker_processes_with_housing_sms_provider(self, mock_process, _mock_validate, mock_get_event):
        """Worker processes the notification with the Housing SMS provider."""
        self.assertEqual(EXPECTED_EVENT_TYPE, "bc.registry.notify.bc_notify_housing_sms")
        mock_ce = Mock(type=EXPECTED_EVENT_TYPE, data={"notificationId": 1}, id="event_1")
        mock_get_event.return_value = mock_ce

        with self.app.test_request_context("/", method="POST", data="test data"):
            _, status = worker()

        self.assertEqual(status, HTTPStatus.OK)
        mock_process.assert_called_once_with(mock_ce.data, BCNotifyHousingSMS)
