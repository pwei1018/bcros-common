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
"""Tests for LaunchDarkly feature flags and provider toggles."""

from unittest.mock import Mock, patch

from flask import Flask
import pytest

from notify_api.models import Notification, SmsRequest
from notify_api.services.flags import FeatureFlag, Flags
from notify_api.services.notify_service import NotifyService


class TestFlags:
    """Test suite for the Flags extension."""

    @staticmethod
    def test_no_sdk_key_uses_default():
        """Without an SDK key no client is created and defaults are returned."""
        app = Flask(__name__)
        app.config["LD_SDK_KEY"] = None
        flags = Flags(app)

        assert flags.client is None
        assert flags.is_on(FeatureFlag.BC_NOTIFY, True) is True
        assert flags.is_on(FeatureFlag.BC_NOTIFY, False) is False

    @staticmethod
    def test_sdk_key_initializes_client():
        """An SDK key configures and stores the LaunchDarkly client."""
        app = Flask(__name__)
        app.config["LD_SDK_KEY"] = "sdk-key"
        client = Mock()

        with (
            patch("notify_api.services.flags.ldclient.set_config") as set_config,
            patch("notify_api.services.flags.ldclient.get", return_value=client),
        ):
            flags = Flags(app)

        set_config.assert_called_once()
        assert flags.client is client

    @staticmethod
    def test_variation_is_returned():
        """Flag value comes from the LaunchDarkly client when initialized."""
        flags = Flags()
        flags.client = Mock(is_initialized=Mock(return_value=True), variation=Mock(return_value=False))

        assert flags.is_on(FeatureFlag.GC_NOTIFY, True) is False
        assert flags.client.variation.call_args.args[0] == "enable-gc-notify"

    @staticmethod
    def test_uninitialized_client_uses_default():
        """An uninitialized client falls back to the default."""
        flags = Flags()
        flags.client = Mock(is_initialized=Mock(return_value=False))

        assert flags.is_on(FeatureFlag.BC_NOTIFY, True) is True
        flags.client.variation.assert_not_called()

    @staticmethod
    def test_evaluation_error_uses_default():
        """Errors during evaluation fall back to the default."""
        flags = Flags()
        flags.client = Mock(is_initialized=Mock(return_value=True), variation=Mock(side_effect=Exception("boom")))

        assert flags.is_on(FeatureFlag.BC_NOTIFY, True) is True


def _flag_values(values: dict):
    """Patch flag evaluation with fixed values, falling back to the default for unspecified flags."""
    return patch("notify_api.services.notify_service.flags.is_on", side_effect=values.get)


class TestProviderToggles:
    """Provider selection driven by feature flags."""

    @staticmethod
    @pytest.mark.parametrize(
        ("values", "expected"),
        [
            ({FeatureFlag.BC_NOTIFY: True}, Notification.NotificationProvider.BC_NOTIFY),
            ({FeatureFlag.BC_NOTIFY: False, FeatureFlag.GC_NOTIFY: True}, Notification.NotificationProvider.GC_NOTIFY),
            ({FeatureFlag.BC_NOTIFY: False, FeatureFlag.GC_NOTIFY: False}, Notification.NotificationProvider.SMTP),
        ],
    )
    def test_default_provider(app, values, expected):
        """Default email provider follows the BC Notify and GC Notify flags."""
        with app.app_context(), _flag_values(values):
            assert NotifyService.get_provider("test", "content") == expected

    @staticmethod
    @pytest.mark.parametrize(
        ("values", "expected"),
        [
            ({FeatureFlag.BC_NOTIFY_HOUSING: True}, Notification.NotificationProvider.BC_NOTIFY_HOUSING),
            (
                {FeatureFlag.BC_NOTIFY_HOUSING: False, FeatureFlag.GC_NOTIFY: True},
                Notification.NotificationProvider.HOUSING,
            ),
            (
                {FeatureFlag.BC_NOTIFY_HOUSING: False, FeatureFlag.GC_NOTIFY: False},
                Notification.NotificationProvider.SMTP,
            ),
        ],
    )
    def test_housing_provider(app, values, expected):
        """Housing email follows the BC Notify Housing flag, then the GC Notify flag, then SMTP."""
        with app.app_context(), _flag_values(values):
            assert NotifyService.get_provider("STRR", "content") == expected

    @staticmethod
    def test_invalid_request_by_respects_flags(app):
        """A non-string request_by still honours the flags instead of forcing GC Notify."""
        with app.app_context(), _flag_values({FeatureFlag.BC_NOTIFY: False, FeatureFlag.GC_NOTIFY: False}):
            assert NotifyService.get_provider(None, "content") == Notification.NotificationProvider.SMTP

    @staticmethod
    def test_flags_default_to_config(app):
        """Without LaunchDarkly, BC Notify is off and GC Notify follows config."""
        with app.app_context():
            app.config["GC_NOTIFY_ENABLE"] = True
            assert NotifyService.get_provider("test", "content") == Notification.NotificationProvider.GC_NOTIFY

    @staticmethod
    @pytest.mark.parametrize(
        ("request_by", "flag"),
        [("test", FeatureFlag.BC_NOTIFY_SMS), ("STRR", FeatureFlag.BC_NOTIFY_HOUSING_SMS)],
    )
    def test_sms_disabled_returns_failure(app, request_by, flag):
        """A disabled SMS flag rejects the SMS without queueing it."""
        sms_request = SmsRequest(recipients="+12505550123", requestBy=request_by, body="Hello")

        with (
            app.app_context(),
            _flag_values({flag: False}),
            patch.object(NotifyService, "_queue_recipients") as queue_recipients,
        ):
            result = NotifyService().queue_publish_sms(sms_request)

        assert result.status_code == Notification.NotificationStatus.FAILURE
        queue_recipients.assert_not_called()

    @staticmethod
    @pytest.mark.parametrize(
        ("request_by", "flag", "provider"),
        [
            ("test", FeatureFlag.BC_NOTIFY_SMS, Notification.NotificationProvider.BC_NOTIFY_SMS),
            ("STRR", FeatureFlag.BC_NOTIFY_HOUSING_SMS, Notification.NotificationProvider.BC_NOTIFY_HOUSING_SMS),
        ],
    )
    def test_sms_enabled_queues(app, request_by, flag, provider):
        """An enabled SMS flag queues the SMS with the matching provider."""
        sms_request = SmsRequest(recipients="+12505550123", requestBy=request_by, body="Hello")

        with (
            app.app_context(),
            _flag_values({flag: True}),
            patch.object(NotifyService, "_queue_recipients", return_value=Mock()) as queue_recipients,
        ):
            NotifyService().queue_publish_sms(sms_request)

        assert queue_recipients.call_args.args[1] == provider


class TestResendToggles:
    """Resend honours the provider feature flags."""

    @staticmethod
    @pytest.mark.parametrize(
        ("stored", "values", "expected"),
        [
            (Notification.NotificationProvider.BC_NOTIFY, {}, Notification.NotificationProvider.BC_NOTIFY),
            (
                Notification.NotificationProvider.BC_NOTIFY,
                {FeatureFlag.BC_NOTIFY: False, FeatureFlag.GC_NOTIFY: True},
                Notification.NotificationProvider.GC_NOTIFY,
            ),
            (
                Notification.NotificationProvider.GC_NOTIFY,
                {FeatureFlag.BC_NOTIFY: True, FeatureFlag.GC_NOTIFY: False},
                Notification.NotificationProvider.BC_NOTIFY,
            ),
            (
                Notification.NotificationProvider.BC_NOTIFY_HOUSING,
                {FeatureFlag.BC_NOTIFY_HOUSING: False, FeatureFlag.GC_NOTIFY: True},
                Notification.NotificationProvider.HOUSING,
            ),
            (
                Notification.NotificationProvider.HOUSING,
                {FeatureFlag.BC_NOTIFY_HOUSING: False, FeatureFlag.GC_NOTIFY: False},
                Notification.NotificationProvider.SMTP,
            ),
            (Notification.NotificationProvider.SMTP, {}, Notification.NotificationProvider.SMTP),
        ],
    )
    def test_republish_reroutes_disabled_email_provider(app, stored, values, expected):
        """Email queued for a now-disabled provider is republished via the currently enabled one."""
        values = {FeatureFlag.BC_NOTIFY: True, FeatureFlag.BC_NOTIFY_HOUSING: True, **values}
        notification = Mock(id=1, provider_code=stored, retry_count=0)

        with (
            app.app_context(),
            _flag_values(values),
            patch.object(NotifyService, "_get_delivery_topic", return_value="topic") as get_topic,
            patch("notify_api.services.notify_service.queue"),
            patch("notify_api.services.notify_service.GcpQueue"),
            patch.object(NotifyService, "_update_notification_status") as update_status,
        ):
            assert NotifyService._republish_single_notification(notification) is True

        get_topic.assert_called_once_with(expected)
        assert update_status.call_args.args[1] == expected

    @staticmethod
    @pytest.mark.parametrize(
        ("stored", "flag"),
        [
            (Notification.NotificationProvider.BC_NOTIFY_SMS, FeatureFlag.BC_NOTIFY_SMS),
            (Notification.NotificationProvider.BC_NOTIFY_HOUSING_SMS, FeatureFlag.BC_NOTIFY_HOUSING_SMS),
        ],
    )
    def test_republish_skips_disabled_sms(app, stored, flag):
        """SMS queued for a now-disabled provider is not republished."""
        notification = Mock(id=1, provider_code=stored, retry_count=0)

        with (
            app.app_context(),
            _flag_values({flag: False}),
            patch("notify_api.services.notify_service.queue") as queue,
        ):
            assert NotifyService._republish_single_notification(notification) is False

        queue.publish.assert_not_called()
