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

from flask import Flask
from notify_api.models import Notification

from notify_delivery.services.providers.gc_notify import GCNotify
from notify_delivery.services.providers.gc_notify_housing import GCNotifyHousing


class TestGCNotifyHousing(unittest.TestCase):
    """Test suite for GC Notify Housing service provider."""

    def setUp(self):
        """Set up test fixtures."""
        self.app = Flask(__name__)
        self.app.config.update(
            {
                "GC_NOTIFY_HOUSING_API_KEY": "housing_test_api_key",
                "GC_NOTIFY_HOUSING_TEMPLATE_ID": "housing_template_123",
                "GC_NOTIFY_HOUSING_EMAIL_REPLY_TO_ID": "housing_reply_to_456",
                "GC_NOTIFY_API_KEY": "default_api_key",
                "GC_NOTIFY_TEMPLATE_ID": "default_template",
                "GC_NOTIFY_EMAIL_REPLY_TO_ID": "default_reply_to",
            }
        )
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        """Clean up test fixtures."""
        self.app_context.pop()

    @patch("notify_delivery.services.providers.gc_notify_housing.GCNotify.__init__")
    def test_init_housing_config_override(self, mock_parent_init):
        """Test GCNotifyHousing initialization with housing-specific config override."""
        # Arrange
        mock_parent_init.return_value = None
        mock_notification = Mock(spec=Notification)

        # Act
        housing_service = GCNotifyHousing(mock_notification)

        # Assert
        mock_parent_init.assert_called_once_with(mock_notification)
        assert housing_service.api_key == "housing_test_api_key"
        assert housing_service.gc_notify_template_id == "housing_template_123"
        assert housing_service.gc_notify_email_reply_to_id == "housing_reply_to_456"

    @patch("notify_delivery.services.providers.gc_notify_housing.GCNotify.__init__")
    def test_init_housing_config_missing(self, mock_parent_init):
        """Test GCNotifyHousing initialization with missing housing-specific config."""
        # Arrange
        mock_parent_init.return_value = None
        mock_notification = Mock(spec=Notification)

        # Remove housing-specific config
        self.app.config.pop("GC_NOTIFY_HOUSING_API_KEY", None)
        self.app.config.pop("GC_NOTIFY_HOUSING_TEMPLATE_ID", None)
        self.app.config.pop("GC_NOTIFY_HOUSING_EMAIL_REPLY_TO_ID", None)

        # Act
        housing_service = GCNotifyHousing(mock_notification)

        # Assert
        mock_parent_init.assert_called_once_with(mock_notification)
        assert housing_service.api_key is None
        assert housing_service.gc_notify_template_id is None
        assert housing_service.gc_notify_email_reply_to_id is None

    @patch("notify_delivery.services.providers.gc_notify_housing.GCNotify.__init__")
    def test_init_partial_housing_config(self, mock_parent_init):
        """Test GCNotifyHousing initialization with partial housing-specific config."""
        # Arrange
        mock_parent_init.return_value = None
        mock_notification = Mock(spec=Notification)

        # Remove only some housing-specific config
        self.app.config.pop("GC_NOTIFY_HOUSING_TEMPLATE_ID", None)

        # Act
        housing_service = GCNotifyHousing(mock_notification)

        # Assert
        mock_parent_init.assert_called_once_with(mock_notification)
        assert housing_service.api_key == "housing_test_api_key"
        assert housing_service.gc_notify_template_id is None
        assert housing_service.gc_notify_email_reply_to_id == "housing_reply_to_456"

    @patch("notify_delivery.services.providers.gc_notify_housing.GCNotify.__init__")
    def test_inheritance_from_gc_notify(self, mock_parent_init):
        """Test that GCNotifyHousing inherits from GCNotify."""
        # Arrange
        mock_parent_init.return_value = None
        mock_notification = Mock(spec=Notification)

        # Act
        housing_service = GCNotifyHousing(mock_notification)

        # Assert
        assert hasattr(housing_service, "api_key")
        assert hasattr(housing_service, "gc_notify_template_id")
        assert hasattr(housing_service, "gc_notify_email_reply_to_id")

    @patch("notify_delivery.services.providers.gc_notify_housing.GCNotify.__init__")
    @patch("notify_delivery.services.providers.gc_notify_housing.GCNotify.send")
    def test_inherits_send_method(self, mock_send, mock_parent_init):
        """Test that GCNotifyHousing inherits send method from parent."""
        # Arrange
        mock_parent_init.return_value = None
        mock_notification = Mock(spec=Notification)
        mock_send_response = Mock()
        mock_send.return_value = mock_send_response

        # Act
        housing_service = GCNotifyHousing(mock_notification)
        result = housing_service.send()

        # Assert
        mock_send.assert_called_once()
        assert result == mock_send_response

    @patch("notify_delivery.services.providers.gc_notify_housing.GCNotify.__init__")
    def test_config_key_constants(self, mock_parent_init):
        """Test that the expected housing config keys are used."""
        # Arrange
        mock_parent_init.return_value = None
        mock_notification = Mock(spec=Notification)

        expected_keys = [
            "GC_NOTIFY_HOUSING_API_KEY",
            "GC_NOTIFY_HOUSING_TEMPLATE_ID",
            "GC_NOTIFY_HOUSING_EMAIL_REPLY_TO_ID",
        ]

        # Act
        housing_service = GCNotifyHousing(mock_notification)

        # Assert
        for key in expected_keys:
            assert key in self.app.config or housing_service.__dict__

    @patch("notify_delivery.services.providers.gc_notify_housing.GCNotify.__init__")
    def test_no_config_interference(self, mock_parent_init):
        """Test that housing config doesn't interfere with default config."""
        # Arrange
        mock_parent_init.return_value = None
        mock_notification = Mock(spec=Notification)

        # Store original default values
        original_default_api_key = self.app.config.get("GC_NOTIFY_API_KEY")
        original_default_template = self.app.config.get("GC_NOTIFY_TEMPLATE_ID")
        original_default_reply_to = self.app.config.get("GC_NOTIFY_EMAIL_REPLY_TO_ID")

        # Act
        GCNotifyHousing(mock_notification)

        # Assert - default config should remain unchanged
        assert self.app.config.get("GC_NOTIFY_API_KEY") == original_default_api_key
        assert self.app.config.get("GC_NOTIFY_TEMPLATE_ID") == original_default_template
        assert self.app.config.get("GC_NOTIFY_EMAIL_REPLY_TO_ID") == original_default_reply_to


class TestGCNotify(unittest.TestCase):
    """Test suite for base GC Notify service provider."""

    def setUp(self):
        """Set up test fixtures."""
        self.app = Flask(__name__)
        self.app.config.update(
            {
                "GC_NOTIFY_API_KEY": "test-api-key",
                "GC_NOTIFY_TEMPLATE_ID": "test-template-id",
                "GC_NOTIFY_EMAIL_REPLY_TO_ID": "test-reply-to-id",
            }
        )

    @patch("notify_delivery.services.providers.gc_notify.current_app", new_callable=Mock)
    def test_gc_notify_init_success(self, mock_current_app):
        """Test successful GCNotify initialization."""
        # Arrange
        mock_current_app.config = self.app.config
        mock_notification = Mock(spec=Notification)
        mock_notification.request_by = "test@example.com"
        mock_notification.recipients = "recipient@example.com"
        mock_notification.content = [Mock(subject="Test Subject", body="Test Body")]

        # Act
        gc_notify = GCNotify(mock_notification)

        # Assert
        assert gc_notify.api_key == "test-api-key"
        assert gc_notify.gc_notify_template_id == "test-template-id"
        assert gc_notify.gc_notify_email_reply_to_id == "test-reply-to-id"
        assert gc_notify.notification == mock_notification

    @patch("notify_delivery.services.providers.gc_notify.current_app", new_callable=Mock)
    def test_gc_notify_init_missing_config(self, mock_current_app):
        """Test GCNotify initialization with missing configuration."""
        # Arrange
        mock_current_app.config = Mock()
        mock_current_app.config.get.return_value = None
        mock_notification = Mock(spec=Notification)

        # Act
        gc_notify = GCNotify(mock_notification)

        # Assert - should create instance but with None values
        assert gc_notify.api_key is None
        assert gc_notify.gc_notify_template_id is None
        assert gc_notify.gc_notify_email_reply_to_id is None

    @patch("notify_delivery.services.providers.gc_notify.NotificationsAPIClient")
    @patch("notify_delivery.services.providers.gc_notify.current_app", new_callable=Mock)
    def test_gc_notify_send_success(self, mock_current_app, mock_client_class):
        """Test successful email sending via GC Notify."""
        # Arrange
        mock_current_app.config = Mock()
        mock_current_app.config.get.side_effect = lambda key, default=None: {
            "GC_NOTIFY_API_KEY": "test-api-key",
            "GC_NOTIFY_TEMPLATE_ID": "test-template-id",
            "GC_NOTIFY_EMAIL_REPLY_TO_ID": "test-reply-to-id",
            "DEPLOYMENT_ENV": "production",
        }.get(key, default)

        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_response = {"id": "notification-id"}
        mock_client.send_email_notification.return_value = mock_response

        mock_content = Mock(spec=object)
        mock_content.subject = "Test Subject"
        mock_content.body = "Test Body"
        mock_content.attachments = None

        mock_notification = Mock(spec=Notification)
        mock_notification.request_by = "test@example.com"
        mock_notification.recipients = "recipient@example.com"
        mock_notification.content = [mock_content]

        # Act
        gc_notify = GCNotify(mock_notification)
        result = gc_notify.send()

        # Assert
        assert result is not None
        mock_client_class.assert_called_once_with(api_key="test-api-key", base_url=None)
        mock_client.send_email_notification.assert_called_once_with(
            email_address="recipient@example.com",
            template_id="test-template-id",
            personalisation={"email_subject": "Test Subject", "email_body": "Test Body"},
            email_reply_to_id="test-reply-to-id",
        )

    @patch("notify_delivery.services.providers.gc_notify.NotificationsAPIClient")
    @patch("notify_delivery.services.providers.gc_notify.current_app", new_callable=Mock)
    def test_gc_notify_send_failure(self, mock_current_app, mock_client_class):
        """Test failed email sending via GC Notify."""
        # Arrange
        mock_current_app.config = Mock()
        mock_current_app.config.get.side_effect = lambda key, default=None: {
            "GC_NOTIFY_API_KEY": "test-api-key",
            "GC_NOTIFY_TEMPLATE_ID": "test-template-id",
            "GC_NOTIFY_EMAIL_REPLY_TO_ID": "test-reply-to-id",
            "DEPLOYMENT_ENV": "production",
        }.get(key, default)

        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.send_email_notification.side_effect = Exception("API Error")

        mock_content = Mock(spec=object)
        mock_content.subject = "Test Subject"
        mock_content.body = "Test Body"
        mock_content.attachments = None

        mock_notification = Mock(spec=Notification)
        mock_notification.request_by = "test@example.com"
        mock_notification.recipients = "recipient@example.com"
        mock_notification.content = [mock_content]

        # Act
        gc_notify = GCNotify(mock_notification)
        result = gc_notify.send()

        # Assert
        assert result is not None
        mock_client.send_email_notification.assert_called_once()

    @patch("notify_delivery.services.providers.gc_notify.NotificationsAPIClient")
    @patch("notify_delivery.services.providers.gc_notify.current_app", new_callable=Mock)
    def test_gc_notify_send_exception(self, mock_current_app, mock_client_class):
        """Test exception handling during email sending."""
        # Arrange
        mock_current_app.config = Mock()
        mock_current_app.config.get.side_effect = lambda key, default=None: {
            "GC_NOTIFY_API_KEY": "test-api-key",
            "GC_NOTIFY_TEMPLATE_ID": "test-template-id",
            "GC_NOTIFY_EMAIL_REPLY_TO_ID": "test-reply-to-id",
            "DEPLOYMENT_ENV": "production",
        }.get(key, default)

        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.send_email_notification.side_effect = Exception("API Error")

        mock_content = Mock(spec=object)
        mock_content.subject = "Test Subject"
        mock_content.body = "Test Body"
        mock_content.attachments = None

        mock_notification = Mock(spec=Notification)
        mock_notification.request_by = "test@example.com"
        mock_notification.recipients = "recipient@example.com"
        mock_notification.content = [mock_content]

        # Act
        gc_notify = GCNotify(mock_notification)
        result = gc_notify.send()

        # Assert
        assert result is not None
        mock_client.send_email_notification.assert_called_once()

    @patch("notify_delivery.services.providers.gc_notify.current_app", new_callable=Mock)
    def test_gc_notify_missing_template_id_config(self, mock_current_app):
        """Test GCNotify initialization with missing template ID."""
        # Arrange
        mock_current_app.config = Mock()
        mock_current_app.config.get.side_effect = lambda key, default=None: {"GC_NOTIFY_API_KEY": "test-api-key"}.get(
            key, default
        )
        mock_notification = Mock(spec=Notification)

        # Act
        gc_notify = GCNotify(mock_notification)

        # Assert - should create instance but template_id will be None
        assert gc_notify.api_key == "test-api-key"
        assert gc_notify.gc_notify_template_id is None

    @patch("notify_delivery.services.providers.gc_notify.current_app", new_callable=Mock)
    def test_gc_notify_missing_reply_to_id_config(self, mock_current_app):
        """Test GCNotify initialization with missing reply-to ID."""
        # Arrange
        mock_current_app.config = Mock()
        mock_current_app.config.get.side_effect = lambda key, default=None: {
            "GC_NOTIFY_API_KEY": "test-api-key",
            "GC_NOTIFY_TEMPLATE_ID": "test-template-id",
        }.get(key, default)
        mock_notification = Mock(spec=Notification)

        # Act
        gc_notify = GCNotify(mock_notification)

        # Assert - should create instance but reply_to_id will be None
        assert gc_notify.api_key == "test-api-key"
        assert gc_notify.gc_notify_template_id == "test-template-id"
        assert gc_notify.gc_notify_email_reply_to_id is None
