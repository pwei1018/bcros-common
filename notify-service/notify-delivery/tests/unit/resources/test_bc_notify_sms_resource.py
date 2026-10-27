# Copyright © 2026 Province of British Columbia
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
"""Test suite for BC Notify SMS resource handlers."""

import unittest
from http import HTTPStatus
from unittest.mock import Mock, patch

from flask import Flask

from notify_delivery.resources.bc_notify_sms import EXPECTED_EVENT_TYPE, bp, worker
from notify_delivery.services.providers.bc_notify_sms import BCNotifySMS


class TestBCNotifySMSResource(unittest.TestCase):
    """Test suite for BC Notify SMS resource handlers."""

    def setUp(self):
        """Set up test fixtures."""
        self.app = Flask(__name__)
        self.app.config.update({"TESTING": True, "VERIFY_PUBSUB_VIA_JWT": False})
        self.app.register_blueprint(bp)
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        """Clean up test fixtures."""
        self.app_context.pop()

    def test_expected_event_type(self):
        """The worker accepts the bc_notify_sms cloud event type."""
        self.assertEqual(EXPECTED_EVENT_TYPE, "bc.registry.notify.bc_notify_sms")

    @patch("notify_delivery.resources.bc_notify_sms.get_cloud_event")
    @patch("notify_delivery.resources.bc_notify_sms.validate_event_type", return_value=True)
    @patch("notify_delivery.resources.bc_notify_sms.process_notification")
    def test_worker_processes_with_sms_provider(self, mock_process, _mock_validate, mock_get_event):
        """Worker processes the notification with the BC Notify SMS provider."""
        mock_ce = Mock(type=EXPECTED_EVENT_TYPE, data={"notificationId": 1}, id="event_1")
        mock_get_event.return_value = mock_ce

        with self.app.test_request_context("/", method="POST", data="test data"):
            response, status = worker()

        self.assertEqual(status, HTTPStatus.OK)
        self.assertEqual(response, {})
        mock_process.assert_called_once_with(mock_ce.data, BCNotifySMS)

    @patch("notify_delivery.resources.bc_notify_sms.get_cloud_event")
    @patch("notify_delivery.resources.bc_notify_sms.validate_event_type", return_value=False)
    def test_worker_invalid_event_type(self, _mock_validate, mock_get_event):
        """Worker rejects other event types."""
        mock_get_event.return_value = Mock(type="bc.registry.notify.bc_notify")

        with self.app.test_request_context("/", method="POST", data="test data"):
            _, status = worker()

        self.assertEqual(status, HTTPStatus.BAD_REQUEST)

    @patch("notify_delivery.resources.bc_notify_sms.get_cloud_event")
    @patch("notify_delivery.resources.bc_notify_sms.validate_event_type", return_value=True)
    @patch("notify_delivery.resources.bc_notify_sms.process_notification", side_effect=ValueError("bad"))
    def test_worker_validation_error(self, _mock_process, _mock_validate, mock_get_event):
        """Validation errors return 400."""
        mock_get_event.return_value = Mock(type=EXPECTED_EVENT_TYPE, data={})

        with self.app.test_request_context("/", method="POST", data="test data"):
            _, status = worker()

        self.assertEqual(status, HTTPStatus.BAD_REQUEST)
