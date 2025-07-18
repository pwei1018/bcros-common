# Copyright © 2022 Province of British Columbia
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
"""Test suite for GC Notify Housing service provider."""

import unittest
from unittest.mock import Mock, patch

from flask import Flask, current_app
from notifications_python_client.errors import HTTPError
from notify_api.models import Notification
from notify_api.models.content import Content as NotificationContent

from notify_delivery.services.providers.gc_notify import GCNotify
from notify_delivery.services.providers.gc_notify_housing import GCNotifyHousing


class TestGCNotifyHousing(unittest.TestCase):
    """Test suite for GC Notify Housing service provider."""

    def setUp(self):
        """Set up test fixtures."""
        self.app = Flask(__name__)
        self.app.config.update(
            {
                "GC_NOTIFY_HOUSING_API_KEY": (
                    "a1b2c3d4-e5f6-g7h8-i9j0-k1l2m3n4o5p6-q1r2s3t4-u5v6-w7x8-y9z0-a1b2c3d4e5f6"
                ),
                "GC_NOTIFY_HOUSING_TEMPLATE_ID": "housing_template_123",
                "GC_NOTIFY_HOUSING_EMAIL_REPLY_TO_ID": "housing_reply_to_456",
                "GC_NOTIFY_API_KEY": ("a1b2c3d4-e5f6-g7h8-i9j0-k1l2m3n4o5p6-q1r2s3t4-u5v6-w7x8-y9z0-a1b2c3d4e5f6"),
                "GC_NOTIFY_API_URL": "https://api.notification.alpha.canada.ca",
                "GC_NOTIFY_TEMPLATE_ID": "default_template",
                "GC_NOTIFY_EMAIL_REPLY_TO_ID": "default_reply_to",
            }
        )
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        """Clean up test fixtures."""
        self.app_context.pop()

    @patch("notify_delivery.services.providers.gc_notify_housing.NotificationsAPIClient")
    @patch("notify_delivery.services.providers.gc_notify.NotificationsAPIClient")
    def test_init_housing_config_override(self, mock_base_notifications_client, mock_housing_notifications_client):
        """Test GCNotifyHousing initialization with housing-specific config override."""
        # Arrange
        mock_notification = Mock(spec=Notification)

        # Act
        housing_service = GCNotifyHousing(mock_notification)

        # Assert
        self.assertEqual(
            housing_service.api_key,
            "a1b2c3d4-e5f6-g7h8-i9j0-k1l2m3n4o5p6-q1r2s3t4-u5v6-w7x8-y9z0-a1b2c3d4e5f6",
        )
        self.assertEqual(housing_service.gc_notify_template_id, "housing_template_123")
        self.assertEqual(housing_service.gc_notify_email_reply_to_id, "housing_reply_to_456")
        # Should call the housing-specific client creation
        mock_housing_notifications_client.assert_called_once_with(
            api_key="a1b2c3d4-e5f6-g7h8-i9j0-k1l2m3n4o5p6-q1r2s3t4-u5v6-w7x8-y9z0-a1b2c3d4e5f6",
            base_url="https://api.notification.alpha.canada.ca",
        )

    @patch("notify_delivery.services.providers.gc_notify_housing.NotificationsAPIClient")
    @patch("notify_delivery.services.providers.gc_notify.NotificationsAPIClient")
    def test_init_housing_config_missing(self, mock_base_notifications_client, mock_housing_notifications_client):
        """Test GCNotifyHousing initialization with missing housing-specific config."""
        # Arrange
        self.app.config.pop("GC_NOTIFY_HOUSING_API_KEY", None)
        self.app.config.pop("GC_NOTIFY_HOUSING_TEMPLATE_ID", None)
        self.app.config.pop("GC_NOTIFY_HOUSING_EMAIL_REPLY_TO_ID", None)
        mock_notification = Mock(spec=Notification)

        # Act
        housing_service = GCNotifyHousing(mock_notification)

        # Assert - should fall back to default values
        self.assertEqual(
            housing_service.api_key,
            "a1b2c3d4-e5f6-g7h8-i9j0-k1l2m3n4o5p6-q1r2s3t4-u5v6-w7x8-y9z0-a1b2c3d4e5f6",
        )
        self.assertEqual(housing_service.gc_notify_template_id, "default_template")
        self.assertEqual(housing_service.gc_notify_email_reply_to_id, "default_reply_to")
        # Should call the housing-specific client creation with default API key
        mock_housing_notifications_client.assert_called_once_with(
            api_key="a1b2c3d4-e5f6-g7h8-i9j0-k1l2m3n4o5p6-q1r2s3t4-u5v6-w7x8-y9z0-a1b2c3d4e5f6",
            base_url="https://api.notification.alpha.canada.ca",
        )

    @patch("notify_delivery.services.providers.gc_notify_housing.NotificationsAPIClient")
    @patch("notify_delivery.services.providers.gc_notify.NotificationsAPIClient")
    def test_init_no_api_key(self, mock_base_notifications_client, mock_housing_notifications_client):
        """Test GCNotifyHousing initialization with no API key."""
        # Arrange
        self.app.config.pop("GC_NOTIFY_HOUSING_API_KEY", None)
        self.app.config.pop("GC_NOTIFY_API_KEY", None)
        mock_notification = Mock(spec=Notification)

        # Act
        housing_service = GCNotifyHousing(mock_notification)

        # Assert
        self.assertEqual(housing_service.api_key, None)
        self.assertIsNone(housing_service.client)
        mock_housing_notifications_client.assert_not_called()

    @patch("notify_delivery.services.providers.gc_notify_housing.NotificationsAPIClient")
    @patch("notify_delivery.services.providers.gc_notify.NotificationsAPIClient")
    def test_init_partial_housing_config(self, mock_base_notifications_client, mock_housing_notifications_client):
        """Test GCNotifyHousing initialization with partial housing-specific config."""
        # Arrange
        # Only set housing API key, not template or reply-to
        self.app.config.pop("GC_NOTIFY_HOUSING_TEMPLATE_ID", None)
        self.app.config.pop("GC_NOTIFY_HOUSING_EMAIL_REPLY_TO_ID", None)
        mock_notification = Mock(spec=Notification)

        # Act
        housing_service = GCNotifyHousing(mock_notification)

        # Assert
        self.assertEqual(
            housing_service.api_key,
            "a1b2c3d4-e5f6-g7h8-i9j0-k1l2m3n4o5p6-q1r2s3t4-u5v6-w7x8-y9z0-a1b2c3d4e5f6",
        )
        # Should fall back to default values for missing housing config
        self.assertEqual(housing_service.gc_notify_template_id, "default_template")
        self.assertEqual(housing_service.gc_notify_email_reply_to_id, "default_reply_to")
        mock_housing_notifications_client.assert_called_once()

    def test_inheritance_from_gc_notify(self):
        """Test that GCNotifyHousing properly inherits from GCNotify."""
        mock_notification = Mock(spec=Notification)
        housing_service = GCNotifyHousing(mock_notification)

        # Should inherit all methods from parent class
        self.assertTrue(hasattr(housing_service, "send"))
        self.assertTrue(hasattr(housing_service, "_prepare_personalisation"))
        self.assertIsInstance(housing_service, GCNotify)

    @patch("notify_delivery.services.providers.gc_notify_housing.NotificationsAPIClient")
    @patch("notify_delivery.services.providers.gc_notify.NotificationsAPIClient")
    def test_send_method_inherited(self, mock_base_notifications_client, mock_housing_notifications_client):
        """Test that send method works properly with housing configuration."""
        # Arrange
        mock_content = Mock(spec=NotificationContent)
        mock_content.subject = "Test Subject"
        mock_content.body = "Test Body"
        mock_content.attachments = None

        mock_notification = Mock(spec=Notification)
        mock_notification.content = [mock_content]
        mock_notification.recipients = "test@example.com"

        mock_client = Mock()
        mock_client.send_email_notification.return_value = {"id": "test-id"}
        mock_housing_notifications_client.return_value = mock_client

        # Act
        housing_service = GCNotifyHousing(mock_notification)
        result = housing_service.send()

        # Assert
        self.assertIsNotNone(result)
        self.assertEqual(len(result.recipients), 1)
        mock_client.send_email_notification.assert_called_once()
        # Verify housing-specific template ID is used
        call_args = mock_client.send_email_notification.call_args
        self.assertEqual(call_args.kwargs["template_id"], "housing_template_123")
        self.assertEqual(call_args.kwargs["email_reply_to_id"], "housing_reply_to_456")

    @patch("notify_delivery.services.providers.gc_notify_housing.NotificationsAPIClient")
    @patch("notify_delivery.services.providers.gc_notify.NotificationsAPIClient")
    def test_empty_housing_config_values(self, mock_base_notifications_client, mock_housing_notifications_client):
        """Test GCNotifyHousing initialization with empty housing-specific config values."""
        # Arrange
        self.app.config.update(
            {
                "GC_NOTIFY_HOUSING_API_KEY": "",
                "GC_NOTIFY_HOUSING_TEMPLATE_ID": "",
                "GC_NOTIFY_HOUSING_EMAIL_REPLY_TO_ID": "",
            }
        )
        mock_notification = Mock(spec=Notification)

        # Act
        housing_service = GCNotifyHousing(mock_notification)

        # Assert - should fall back to defaults when housing values are empty
        self.assertEqual(
            housing_service.api_key,
            "a1b2c3d4-e5f6-g7h8-i9j0-k1l2m3n4o5p6-q1r2s3t4-u5v6-w7x8-y9z0-a1b2c3d4e5f6",
        )
        self.assertEqual(housing_service.gc_notify_template_id, "default_template")
        self.assertEqual(housing_service.gc_notify_email_reply_to_id, "default_reply_to")

    def test_housing_config_keys_constant(self):
        """Test that housing configuration keys are properly defined."""
        expected_keys = {
            "api_key": "GC_NOTIFY_HOUSING_API_KEY",
            "template_id": "GC_NOTIFY_HOUSING_TEMPLATE_ID",
            "reply_to_id": "GC_NOTIFY_HOUSING_EMAIL_REPLY_TO_ID",
        }
        self.assertEqual(GCNotifyHousing.HOUSING_CONFIG_KEYS, expected_keys)

    @patch("notify_delivery.services.providers.gc_notify_housing.NotificationsAPIClient")
    @patch("notify_delivery.services.providers.gc_notify.NotificationsAPIClient")
    def test_get_config_value_method(self, mock_base_notifications_client, mock_housing_notifications_client):
        """Test the _get_config_value helper method."""
        mock_notification = Mock(spec=Notification)
        housing_service = GCNotifyHousing(mock_notification)

        # Test with existing housing config
        config = current_app.config
        result = housing_service._get_config_value(config, "api_key", "default_key")
        self.assertEqual(
            result,
            "a1b2c3d4-e5f6-g7h8-i9j0-k1l2m3n4o5p6-q1r2s3t4-u5v6-w7x8-y9z0-a1b2c3d4e5f6",
        )

        # Test with missing housing config
        config_copy = dict(config)
        config_copy.pop("GC_NOTIFY_HOUSING_API_KEY", None)
        with patch(
            "notify_delivery.services.providers.gc_notify_housing.current_app.config",
            config_copy,
        ):
            result = housing_service._get_config_value(config_copy, "api_key", "default_key")
            self.assertEqual(result, "default_key")

    @patch("notify_delivery.services.providers.gc_notify_housing.logger")
    @patch("notify_delivery.services.providers.gc_notify_housing.NotificationsAPIClient")
    @patch("notify_delivery.services.providers.gc_notify.NotificationsAPIClient")
    def test_initialize_client_with_warning(
        self,
        mock_base_notifications_client,
        mock_housing_notifications_client,
        mock_logger,
    ):
        """Test client initialization with warning when no API key is available."""
        # Arrange
        self.app.config.pop("GC_NOTIFY_HOUSING_API_KEY", None)
        self.app.config.pop("GC_NOTIFY_API_KEY", None)
        mock_notification = Mock(spec=Notification)

        # Act
        housing_service = GCNotifyHousing(mock_notification)

        # Assert
        self.assertIsNone(housing_service.client)
        mock_logger.warning.assert_called_once_with("No API key available for GC Notify Housing service")

    @patch("notify_delivery.services.providers.gc_notify_housing.NotificationsAPIClient")
    @patch("notify_delivery.services.providers.gc_notify.NotificationsAPIClient")
    def test_apply_housing_config_method(self, mock_base_notifications_client, mock_housing_notifications_client):
        """Test the _apply_housing_config method directly."""
        mock_notification = Mock(spec=Notification)
        housing_service = GCNotifyHousing(mock_notification)

        # Verify housing config was applied
        self.assertEqual(
            housing_service.api_key,
            "a1b2c3d4-e5f6-g7h8-i9j0-k1l2m3n4o5p6-q1r2s3t4-u5v6-w7x8-y9z0-a1b2c3d4e5f6",
        )
        self.assertEqual(housing_service.gc_notify_template_id, "housing_template_123")
        self.assertEqual(housing_service.gc_notify_email_reply_to_id, "housing_reply_to_456")

    @patch("notify_delivery.services.providers.gc_notify_housing.NotificationsAPIClient")
    @patch("notify_delivery.services.providers.gc_notify.NotificationsAPIClient")
    def test_mixed_housing_and_default_config(self, mock_base_notifications_client, mock_housing_notifications_client):
        """Test configuration with some housing values and some defaults."""
        # Arrange - remove only template ID, keep others
        self.app.config.pop("GC_NOTIFY_HOUSING_TEMPLATE_ID", None)
        mock_notification = Mock(spec=Notification)

        # Act
        housing_service = GCNotifyHousing(mock_notification)

        # Assert - should use housing API key and reply-to, but default template
        self.assertEqual(
            housing_service.api_key,
            "a1b2c3d4-e5f6-g7h8-i9j0-k1l2m3n4o5p6-q1r2s3t4-u5v6-w7x8-y9z0-a1b2c3d4e5f6",
        )
        self.assertEqual(housing_service.gc_notify_template_id, "default_template")
        self.assertEqual(housing_service.gc_notify_email_reply_to_id, "housing_reply_to_456")

    @patch("notify_delivery.services.providers.gc_notify_housing.NotificationsAPIClient")
    @patch("notify_delivery.services.providers.gc_notify.NotificationsAPIClient")
    def test_whitespace_housing_config_values(self, mock_base_notifications_client, mock_housing_notifications_client):
        """Test GCNotifyHousing with whitespace-only housing config values."""
        # Arrange
        self.app.config.update(
            {
                "GC_NOTIFY_HOUSING_API_KEY": "   ",
                "GC_NOTIFY_HOUSING_TEMPLATE_ID": "\t\n",
                "GC_NOTIFY_HOUSING_EMAIL_REPLY_TO_ID": "  \r  ",
            }
        )
        mock_notification = Mock(spec=Notification)

        # Act
        housing_service = GCNotifyHousing(mock_notification)

        # Assert - should fall back to defaults for whitespace values
        self.assertEqual(
            housing_service.api_key,
            "a1b2c3d4-e5f6-g7h8-i9j0-k1l2m3n4o5p6-q1r2s3t4-u5v6-w7x8-y9z0-a1b2c3d4e5f6",
        )
        self.assertEqual(housing_service.gc_notify_template_id, "default_template")
        self.assertEqual(housing_service.gc_notify_email_reply_to_id, "default_reply_to")


class TestGCNotifyHousingErrorHandling(unittest.TestCase):
    """Test suite for error handling in GC Notify Housing service provider."""

    def setUp(self):
        """Set up test fixtures."""
        self.app = Flask(__name__)
        self.app.config.update(
            {
                "GC_NOTIFY_API_KEY": "default_key",
                "GC_NOTIFY_API_URL": "https://api.notification.alpha.canada.ca",
                "GC_NOTIFY_TEMPLATE_ID": "default_template",
                "GC_NOTIFY_EMAIL_REPLY_TO_ID": "default_reply_to",
                "GC_NOTIFY_HOUSING_API_KEY": "housing_key",
                "GC_NOTIFY_HOUSING_TEMPLATE_ID": "housing_template",
                "GC_NOTIFY_HOUSING_EMAIL_REPLY_TO_ID": "housing_reply_to",
            }
        )
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        """Clean up test fixtures."""
        self.app_context.pop()

    @patch("notify_delivery.services.providers.gc_notify_housing.NotificationsAPIClient")
    @patch("notify_delivery.services.providers.gc_notify.NotificationsAPIClient")
    def test_send_with_housing_specific_error_handling(
        self, mock_base_notifications_client, mock_housing_notifications_client
    ):
        """Test error handling during send with housing-specific configuration."""
        # Arrange
        mock_content = Mock(spec=NotificationContent)
        mock_content.subject = "Test Subject"
        mock_content.body = "Test Body"
        mock_content.attachments = None

        mock_notification = Mock(spec=Notification)
        mock_notification.content = [mock_content]
        mock_notification.recipients = "test@example.com"

        mock_client = Mock()
        mock_client.send_email_notification.side_effect = HTTPError("Housing service error")
        mock_housing_notifications_client.return_value = mock_client

        # Act
        housing_service = GCNotifyHousing(mock_notification)
        result = housing_service.send()

        # Assert - should handle error gracefully
        self.assertIsNotNone(result)
        self.assertEqual(len(result.recipients), 0)
        mock_client.send_email_notification.assert_called_once()

    @patch("notify_delivery.services.providers.gc_notify_housing.NotificationsAPIClient")
    @patch("notify_delivery.services.providers.gc_notify.NotificationsAPIClient")
    def test_configuration_precedence(self, mock_base_notifications_client, mock_housing_notifications_client):
        """Test that housing configuration takes precedence over default configuration."""
        # Arrange
        mock_notification = Mock(spec=Notification)

        # Act
        housing_service = GCNotifyHousing(mock_notification)

        # Assert - housing values should override defaults
        self.assertEqual(housing_service.api_key, "housing_key")
        self.assertEqual(housing_service.gc_notify_template_id, "housing_template")
        self.assertEqual(housing_service.gc_notify_email_reply_to_id, "housing_reply_to")
        self.assertNotEqual(housing_service.api_key, "default_key")
        self.assertNotEqual(housing_service.gc_notify_template_id, "default_template")
        self.assertNotEqual(housing_service.gc_notify_email_reply_to_id, "default_reply_to")

    @patch("notify_delivery.services.providers.gc_notify_housing.NotificationsAPIClient")
    @patch("notify_delivery.services.providers.gc_notify.NotificationsAPIClient")
    def test_send_to_multiple_recipients_with_housing_config(
        self, mock_base_notifications_client, mock_housing_notifications_client
    ):
        """Test sending to multiple recipients with housing configuration."""
        # Arrange
        mock_content = Mock(spec=NotificationContent)
        mock_content.subject = "Test Subject"
        mock_content.body = "Test Body"
        mock_content.attachments = None

        mock_notification = Mock(spec=Notification)
        mock_notification.content = [mock_content]
        mock_notification.recipients = "test1@example.com, test2@example.com, test3@example.com"

        mock_client = Mock()
        mock_client.send_email_notification.return_value = {"id": "test-id"}
        mock_housing_notifications_client.return_value = mock_client

        # Act
        housing_service = GCNotifyHousing(mock_notification)
        result = housing_service.send()

        # Assert
        self.assertIsNotNone(result)
        self.assertEqual(len(result.recipients), 3)
        self.assertEqual(mock_client.send_email_notification.call_count, 3)

        # Verify housing configuration is used for all recipients
        for call in mock_client.send_email_notification.call_args_list:
            self.assertEqual(call.kwargs["template_id"], "housing_template")
            self.assertEqual(call.kwargs["email_reply_to_id"], "housing_reply_to")

    @patch("notify_delivery.services.providers.gc_notify_housing.NotificationsAPIClient")
    @patch("notify_delivery.services.providers.gc_notify.NotificationsAPIClient")
    def test_config_validation_edge_cases(self, mock_base_notifications_client, mock_housing_notifications_client):
        """Test configuration validation with various edge cases."""
        # Test with None values
        self.app.config.update(
            {
                "GC_NOTIFY_HOUSING_API_KEY": None,
                "GC_NOTIFY_HOUSING_TEMPLATE_ID": None,
                "GC_NOTIFY_HOUSING_EMAIL_REPLY_TO_ID": None,
            }
        )

        mock_notification = Mock(spec=Notification)
        housing_service = GCNotifyHousing(mock_notification)

        # Should fall back to defaults
        self.assertEqual(housing_service.api_key, "default_key")
        self.assertEqual(housing_service.gc_notify_template_id, "default_template")
        self.assertEqual(housing_service.gc_notify_email_reply_to_id, "default_reply_to")
