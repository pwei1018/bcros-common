# Copyright © 2022 Province of British Columbia
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
"""Test suite for EmailSMTP service provider."""

import smtplib
import unittest
from email.mime.multipart import MIMEMultipart
from unittest.mock import MagicMock, Mock, patch

import pytest
from notify_api.models import (
    Attachment,
    Content,
    Notification,
    NotificationSendResponse,
    NotificationSendResponses,
)

from notify_delivery.services.providers.email_smtp import EmailSMTP


class TestEmailSMTPService(unittest.TestCase):
    """Test EmailSMTP service provider."""

    # Test constants
    TEST_SMTP_PORT = 587
    EXPECTED_RECIPIENT_COUNT = 3

    def setUp(self):
        """Set up test fixtures."""
        self.mock_content = Content(
            subject="Test Subject", body="<html><body>Test email body</body></html>", attachments=[]
        )

        self.mock_notification = Notification(
            id=1,
            recipients="test@example.com",
            content=[self.mock_content],
            status_code=Notification.NotificationStatus.QUEUED,
            provider_code=Notification.NotificationProvider.SMTP,
        )

    @patch("notify_delivery.services.providers.email_smtp.current_app", new_callable=Mock)
    def test_email_smtp_init(self, mock_current_app):
        """Test EmailSMTP initialization."""
        # Arrange
        mock_config = MagicMock()
        mock_config.get.side_effect = lambda key: {
            "MAIL_SERVER": "smtp.example.com",
            "MAIL_PORT": self.TEST_SMTP_PORT,
            "MAIL_FROM_ID": "sender@example.com",
        }.get(key)
        mock_current_app.config = mock_config

        # Act
        email_smtp = EmailSMTP(self.mock_notification)

        # Assert
        assert email_smtp.mail_server == "smtp.example.com"
        assert email_smtp.mail_port == self.TEST_SMTP_PORT
        assert email_smtp.mail_from_id == "sender@example.com"
        assert email_smtp.notification == self.mock_notification

    @patch("notify_delivery.services.providers.email_smtp.smtplib.SMTP")
    @patch("notify_delivery.services.providers.email_smtp.current_app", new_callable=Mock)
    def test_send_email_success_single_recipient(self, mock_current_app, mock_smtp_class):
        """Test successful email send to single recipient."""
        # Arrange
        mock_config = {
            "MAIL_SERVER": "smtp.example.com",
            "MAIL_PORT": 587,
            "MAIL_FROM_ID": "sender@example.com",
            "DEPLOYMENT_ENV": "production",
        }
        mock_current_app.config.get.side_effect = lambda key, default=None: mock_config.get(key, default)

        mock_server = Mock()
        mock_smtp_class.return_value.__enter__.return_value = mock_server
        mock_server.sendmail.return_value = None

        email_smtp = EmailSMTP(self.mock_notification)

        # Act
        result = email_smtp.send()

        # Assert
        assert isinstance(result, NotificationSendResponses)
        assert len(result.recipients) == 1
        assert result.recipients[0].recipient == "test@example.com"
        assert result.recipients[0].response_id is None

        mock_smtp_class.assert_called_once_with(host="smtp.example.com", port=587)
        mock_server.sendmail.assert_called_once()

    @patch("notify_delivery.services.providers.email_smtp.smtplib.SMTP")
    @patch("notify_delivery.services.providers.email_smtp.current_app", new_callable=Mock)
    def test_send_email_success_multiple_recipients(self, mock_current_app, mock_smtp_class):
        """Test successful email send to multiple recipients."""
        # Arrange
        mock_config = {
            "MAIL_SERVER": "smtp.example.com",
            "MAIL_PORT": 587,
            "MAIL_FROM_ID": "sender@example.com",
            "DEPLOYMENT_ENV": "production",
        }
        mock_current_app.config.get.side_effect = lambda key, default=None: mock_config.get(key, default)

        # Create notification with multiple recipients
        multi_recipient_notification = Notification(
            id=1,
            recipients="test1@example.com,test2@example.com,test3@example.com",
            content=[self.mock_content],
            status_code=Notification.NotificationStatus.QUEUED,
            provider_code=Notification.NotificationProvider.SMTP,
        )

        mock_server = Mock()
        mock_smtp_class.return_value.__enter__.return_value = mock_server
        mock_server.sendmail.return_value = None

        email_smtp = EmailSMTP(multi_recipient_notification)

        # Act
        result = email_smtp.send()

        # Assert
        assert isinstance(result, NotificationSendResponses)
        assert len(result.recipients) == self.EXPECTED_RECIPIENT_COUNT

        expected_emails = ["test1@example.com", "test2@example.com", "test3@example.com"]
        for i, response in enumerate(result.recipients):
            assert response.recipient == expected_emails[i]
            assert response.response_id is None

        assert mock_server.sendmail.call_count == self.EXPECTED_RECIPIENT_COUNT

    @patch("notify_delivery.services.providers.email_smtp.smtplib.SMTP")
    @patch("notify_delivery.services.providers.email_smtp.current_app", new_callable=Mock)
    def test_send_email_with_development_environment(self, mock_current_app, mock_smtp_class):
        """Test email send in development environment adds env suffix to subject."""
        # Arrange
        mock_config = {
            "MAIL_SERVER": "smtp.example.com",
            "MAIL_PORT": 587,
            "MAIL_FROM_ID": "sender@example.com",
            "DEPLOYMENT_ENV": "development",
        }
        mock_current_app.config.get.side_effect = lambda key, default=None: mock_config.get(key, default)

        mock_server = Mock()
        mock_smtp_class.return_value.__enter__.return_value = mock_server

        email_smtp = EmailSMTP(self.mock_notification)

        # Act
        email_smtp.send()

        # Assert
        # Verify the message was created with environment suffix
        call_args = mock_server.sendmail.call_args
        message_str = call_args[0][2]  # The message string is the third argument
        assert "Test Subject - from DEVELOPMENT environment" in message_str

    @patch("notify_delivery.services.providers.email_smtp.smtplib.SMTP")
    @patch("notify_delivery.services.providers.email_smtp.current_app", new_callable=Mock)
    def test_send_email_with_attachments(self, mock_current_app, mock_smtp_class):
        """Test email send with file attachments."""
        # Arrange
        mock_config = {
            "MAIL_SERVER": "smtp.example.com",
            "MAIL_PORT": 587,
            "MAIL_FROM_ID": "sender@example.com",
            "DEPLOYMENT_ENV": "production",
        }
        mock_current_app.config.get.side_effect = lambda key, default=None: mock_config.get(key, default)

        # Create content with attachments
        attachment = Attachment(file_name="test_document.pdf", file_bytes=b"fake pdf content")
        content_with_attachments = Content(
            subject="Test Subject", body="<html><body>Test email body</body></html>", attachments=[attachment]
        )
        notification_with_attachments = Notification(
            id=1,
            recipients="test@example.com",
            content=[content_with_attachments],
            status_code=Notification.NotificationStatus.QUEUED,
            provider_code=Notification.NotificationProvider.SMTP,
        )

        mock_server = Mock()
        mock_smtp_class.return_value.__enter__.return_value = mock_server

        email_smtp = EmailSMTP(notification_with_attachments)

        # Act
        result = email_smtp.send()

        # Assert
        assert isinstance(result, NotificationSendResponses)
        assert len(result.recipients) == 1

        # Verify attachment was processed
        call_args = mock_server.sendmail.call_args
        message_str = call_args[0][2]
        assert "test_document.pdf" in message_str

    @patch("notify_delivery.services.providers.email_smtp.smtplib.SMTP")
    @patch("notify_delivery.services.providers.email_smtp.current_app", new_callable=Mock)
    def test_send_email_attachment_unicode_filename(self, mock_current_app, mock_smtp_class):
        """Test email send with unicode characters in attachment filename."""
        # Arrange
        mock_config = {
            "MAIL_SERVER": "smtp.example.com",
            "MAIL_PORT": 587,
            "MAIL_FROM_ID": "sender@example.com",
            "DEPLOYMENT_ENV": "production",
        }
        mock_current_app.config.get.side_effect = lambda key, default=None: mock_config.get(key, default)

        # Create content with unicode filename attachment
        attachment = Attachment(file_name="tëst_dócümént_ñäme.pdf", file_bytes=b"fake pdf content")
        content_with_attachments = Content(
            subject="Test Subject", body="<html><body>Test email body</body></html>", attachments=[attachment]
        )
        notification_with_attachments = Notification(
            id=1,
            recipients="test@example.com",
            content=[content_with_attachments],
            status_code=Notification.NotificationStatus.QUEUED,
            provider_code=Notification.NotificationProvider.SMTP,
        )

        mock_server = Mock()
        mock_smtp_class.return_value.__enter__.return_value = mock_server

        email_smtp = EmailSMTP(notification_with_attachments)

        # Act
        result = email_smtp.send()

        # Assert
        assert isinstance(result, NotificationSendResponses)

        # Verify unicode filename was normalized
        call_args = mock_server.sendmail.call_args
        message_str = call_args[0][2]
        # The unicode characters should be converted to ASCII
        assert "test_document_name.pdf" in message_str

    @patch("notify_delivery.services.providers.email_smtp.smtplib.SMTP")
    @patch("notify_delivery.services.providers.email_smtp.current_app", new_callable=Mock)
    @patch("notify_delivery.services.providers.email_smtp.logger")
    def test_send_email_smtp_connection_error(self, mock_logger, mock_current_app, mock_smtp_class):
        """Test email send with SMTP connection error."""
        # Arrange
        mock_config = {
            "MAIL_SERVER": "smtp.example.com",
            "MAIL_PORT": 587,
            "MAIL_FROM_ID": "sender@example.com",
            "DEPLOYMENT_ENV": "production",
        }
        mock_current_app.config.get.side_effect = lambda key, default=None: mock_config.get(key, default)

        mock_smtp_class.side_effect = smtplib.SMTPException("Connection failed")

        email_smtp = EmailSMTP(self.mock_notification)

        # Act
        result = email_smtp.send()

        # Assert
        assert isinstance(result, NotificationSendResponses)
        assert len(result.recipients) == 0  # No successful sends
        mock_logger.error.assert_called_with("Error connecting to SMTP server: Connection failed")

    @patch("notify_delivery.services.providers.email_smtp.smtplib.SMTP")
    @patch("notify_delivery.services.providers.email_smtp.current_app", new_callable=Mock)
    @patch("notify_delivery.services.providers.email_smtp.logger")
    def test_send_email_individual_send_error(self, mock_logger, mock_current_app, mock_smtp_class):
        """Test email send with error sending to individual recipient."""
        # Arrange
        mock_config = {
            "MAIL_SERVER": "smtp.example.com",
            "MAIL_PORT": 587,
            "MAIL_FROM_ID": "sender@example.com",
            "DEPLOYMENT_ENV": "production",
        }
        mock_current_app.config.get.side_effect = lambda key, default=None: mock_config.get(key, default)

        # Create notification with multiple recipients
        multi_recipient_notification = Notification(
            id=1,
            recipients="good@example.com,bad@example.com",
            content=[self.mock_content],
            status_code=Notification.NotificationStatus.QUEUED,
            provider_code=Notification.NotificationProvider.SMTP,
        )

        mock_server = Mock()
        mock_smtp_class.return_value.__enter__.return_value = mock_server

        # Mock sendmail to succeed for first email, fail for second
        def sendmail_side_effect(from_addr, to_addrs, msg):
            if "bad@example.com" in to_addrs:
                raise Exception("Invalid recipient")

        mock_server.sendmail.side_effect = sendmail_side_effect

        email_smtp = EmailSMTP(multi_recipient_notification)

        # Act
        result = email_smtp.send()

        # Assert
        assert isinstance(result, NotificationSendResponses)
        assert len(result.recipients) == 1  # Only successful send
        assert result.recipients[0].recipient == "good@example.com"
        mock_logger.error.assert_called_with("Error sending email to bad@example.com: Invalid recipient")

    @patch("notify_delivery.services.providers.email_smtp.current_app", new_callable=Mock)
    def test_send_email_empty_deployment_env(self, mock_current_app):
        """Test email send with empty deployment environment."""
        # Arrange
        mock_config = {
            "MAIL_SERVER": "smtp.example.com",
            "MAIL_PORT": 587,
            "MAIL_FROM_ID": "sender@example.com",
            "DEPLOYMENT_ENV": "",
        }
        mock_current_app.config.get.side_effect = lambda key, default=None: mock_config.get(key, default)

        email_smtp = EmailSMTP(self.mock_notification)

        # Act & Assert
        # Should not raise an exception and handle empty env gracefully
        with patch("notify_delivery.services.providers.email_smtp.smtplib.SMTP") as mock_smtp_class:
            mock_server = Mock()
            mock_smtp_class.return_value.__enter__.return_value = mock_server

            email_smtp.send()

            # Verify message creation doesn't fail with empty environment
            call_args = mock_server.sendmail.call_args
            message_str = call_args[0][2]
            assert "Test Subject - from UNKNOWN environment" in message_str

    @patch("notify_delivery.services.providers.email_smtp.current_app", new_callable=Mock)
    def test_send_email_missing_deployment_env(self, mock_current_app):
        """Test email send with missing deployment environment config."""
        # Arrange
        mock_config = {
            "MAIL_SERVER": "smtp.example.com",
            "MAIL_PORT": 587,
            "MAIL_FROM_ID": "sender@example.com",
            # DEPLOYMENT_ENV is missing
        }
        mock_current_app.config.get.side_effect = lambda key, default=None: mock_config.get(key, default)

        email_smtp = EmailSMTP(self.mock_notification)

        # Act & Assert
        with patch("notify_delivery.services.providers.email_smtp.smtplib.SMTP") as mock_smtp_class:
            mock_server = Mock()
            mock_smtp_class.return_value.__enter__.return_value = mock_server

            email_smtp.send()

            # Should use default and handle gracefully
            call_args = mock_server.sendmail.call_args
            message_str = call_args[0][2]
            assert "Test Subject - from UNKNOWN environment" in message_str

    @patch("notify_delivery.services.providers.email_smtp.smtplib.SMTP")
    @patch("notify_delivery.services.providers.email_smtp.current_app", new_callable=Mock)
    def test_send_email_production_environment_no_suffix(self, mock_current_app, mock_smtp_class):
        """Test email send in production environment doesn't add suffix to subject."""
        # Arrange
        mock_config = {
            "MAIL_SERVER": "smtp.example.com",
            "MAIL_PORT": 587,
            "MAIL_FROM_ID": "sender@example.com",
            "DEPLOYMENT_ENV": "production",
        }
        mock_current_app.config.get.side_effect = lambda key, default=None: mock_config.get(key, default)

        mock_server = Mock()
        mock_smtp_class.return_value.__enter__.return_value = mock_server

        email_smtp = EmailSMTP(self.mock_notification)

        # Act
        email_smtp.send()

        # Assert
        call_args = mock_server.sendmail.call_args
        message_str = call_args[0][2]
        assert "Subject: Test Subject\n" in message_str  # Original subject without suffix
        assert "from PRODUCTION environment" not in message_str

    @patch("notify_delivery.services.providers.email_smtp.current_app", new_callable=Mock)
    def test_email_smtp_with_none_content(self, mock_current_app):
        """Test EmailSMTP with notification having no content."""
        # Arrange
        mock_config = {
            "MAIL_SERVER": "smtp.example.com",
            "MAIL_PORT": 587,
            "MAIL_FROM_ID": "sender@example.com",
            "DEPLOYMENT_ENV": "production",
        }
        mock_current_app.config.get.side_effect = lambda key, default=None: mock_config.get(key, default)

        notification_no_content = Notification(
            id=1,
            recipients="test@example.com",
            content=[],  # Empty content
            status_code=Notification.NotificationStatus.QUEUED,
            provider_code=Notification.NotificationProvider.SMTP,
        )

        email_smtp = EmailSMTP(notification_no_content)

        # Act & Assert - Test that send() returns None when no content
        result = email_smtp.send()
        assert result is None
